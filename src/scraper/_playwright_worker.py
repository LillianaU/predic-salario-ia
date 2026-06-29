"""Playwright worker — runs in a separate process to avoid greenlet conflicts."""
import sys
import json
import time
import random
import re
import datetime
from urllib.parse import quote
from playwright.sync_api import sync_playwright


def _parse_salary(salary_text):
    if not salary_text or "confidencial" in salary_text.lower():
        return 0.0, 0.0
    nums = re.findall(r"[\d.,]+", salary_text)
    sal_nums = []
    for n in nums:
        try:
            n_clean = n.replace(".", "").replace(",", ".")
            sal_nums.append(float(n_clean))
        except ValueError:
            pass
    sal_min, sal_max = 0.0, 0.0
    if len(sal_nums) >= 2:
        sal_min, sal_max = min(sal_nums), max(sal_nums)
    elif len(sal_nums) == 1:
        sal_min, sal_max = sal_nums[0] * 0.8, sal_nums[0] * 1.2
    if "millon" in salary_text.lower():
        if sal_max > 0 and sal_max < 100:
            sal_min *= 1_000_000
            sal_max *= 1_000_000
    return sal_min, sal_max


def _parse_salary_from_card(card_text):
    patterns = [
        r"(?i)\$\s*(\d{1,3}(?:[\.,]\d{3})*(?:[\.,]\d+)?)\s*(?:a|al|-\s*|hasta)\s*\$?\s*(\d{1,3}(?:[\.,]\d{3})*(?:[\.,]\d+)?)",
        r"(?i)(\d{1,3}(?:[\.,]\d{3})*(?:[\.,]\d+)?)\s*(?:a|al|-\s*|hasta)\s*(\d{1,3}(?:[\.,]\d{3})*(?:[\.,]\d+)?)\s*(?:millones?|millons?)",
        r"(?i)(\d{1,3}(?:[\.,]\d{3})*(?:[\.,]\d+)?)\s*(?:millones?)\s*(?:mensuales?)?",
    ]
    for sp in patterns:
        m = re.search(sp, card_text)
        if m:
            try:
                a = float(m.group(1).replace(".", "").replace(",", "."))
                b = float(m.group(2).replace(".", "").replace(",", ".")) if m.lastindex >= 2 else a
                if a > 0:
                    if a < 100:
                        a *= 1_000_000
                    if b < 100:
                        b *= 1_000_000
                    return min(a, b), max(a, b)
            except (ValueError, IndexError):
                pass
    return 0.0, 0.0


def _detect_municipio(text):
    municipios = [
        "Barbosa", "Girardota", "Copacabana",
        "Bello", "Medellín", "Medellin", "Itagüí", "Itagui",
        "Envigado", "Sabaneta", "La Estrella", "Caldas",
    ]
    for m in municipios:
        if re.search(rf"\b{re.escape(m)}\b", text, re.IGNORECASE):
            return "Medellín" if m == "Medellin" else m
    return ""


def _parse_card(card, query, seen_ids):
    try:
        area_bind = card.query_selector("div.js-area-bind")
        if not area_bind:
            return None
        detail_url = area_bind.get_attribute("data-url") or ""
        if not detail_url:
            return None
        data_attr = area_bind.get_attribute("data-ga4-offerdata") or "{}"
        try:
            offer_data = json.loads(data_attr)
        except json.JSONDecodeError:
            offer_data = {}
        offer_id = str(offer_data.get("id", ""))
        if offer_id and offer_id in seen_ids:
            return None
        if offer_id:
            seen_ids.add(offer_id)
        title = offer_data.get("title", "") or ""
        company = offer_data.get("company", "") or ""
        salary_text = offer_data.get("salary", "") or ""
        if not title:
            title_el = card.query_selector("a.js-offer-title, a.titulo, h2 a")
            title = title_el.inner_text().strip() if title_el else ""
        if not title or len(title) < 5:
            return None
        if not company:
            company_el = card.query_selector("span.info-company-name, .company-name-text span span")
            company = company_el.inner_text().strip() if company_el else ""
        card_text = card.inner_text()
        ciudad = offer_data.get("location", "") or "Medellín"
        modalidad = "presencial"
        ct_match = re.search(r"(?:Presencial|Remoto|Híbrido|Virtual|Teletrabajo|Mixto)\s*\n\s*Modalidad laboral", card_text)
        if ct_match:
            mode_val = ct_match.group(0).split("\n")[0].strip().lower()
            if "remoto" in mode_val or "virtual" in mode_val or "teletrabajo" in mode_val:
                modalidad = "remoto"
            elif "híbrid" in mode_val or "hibrid" in mode_val or "mixto" in mode_val:
                modalidad = "hibrido"
        if modalidad == "presencial":
            for kw in ["Remoto", "Virtual", "Teletrabajo"]:
                if kw.lower() in card_text.lower():
                    lines = card_text.split("\n")
                    for i, line in enumerate(lines):
                        if kw.lower() in line.lower() and i + 1 < len(lines) and "modalidad" in lines[i + 1].lower():
                            modalidad = "remoto"
                            break
        contract_type = ""
        ct_match2 = re.search(r"(Indefinido|Definido|Prestación de Servicios|Contrato de aprendizaje|Por obra o labor|Otro)\s*\n\s*Tipo de contrato", card_text)
        if ct_match2:
            contract_type = ct_match2.group(1).strip()
        date_text = ""
        for kw in ["Hoy", "Ayer"]:
            if kw in card_text:
                date_text = kw
                break
        if not date_text:
            dm = re.search(r"hace\s+(\d+)\s+(días|dias|horas|minutos)", card_text, re.IGNORECASE)
            if dm:
                date_text = dm.group(0)
        sal_min, sal_max = _parse_salary(salary_text)
        if not sal_min and not sal_max:
            sal_min, sal_max = _parse_salary_from_card(card_text)
        if not sal_min and not sal_max:
            return None
        municipio = _detect_municipio(card_text)
        if municipio:
            ciudad = municipio
        return {
            "titulo": title[:200],
            "empresa": company[:150] if company else "",
            "salario_minimo": sal_min,
            "salario_maximo": sal_max,
            "moneda": "COP",
            "ubicacion": f"{ciudad}, Colombia" if ciudad else "Medellín, Colombia",
            "experiencia_requerida": "",
            "tipo_contrato": contract_type,
            "skills": "",
            "fecha_publicacion": date_text if date_text else datetime.date.today().isoformat(),
            "descripcion": "",
            "modalidad": modalidad,
        }
    except Exception:
        return None


def _scrape_query(page, query, timeout, global_seen_ids=None):
    search_words = query.lower().replace("medellín", "").replace("colombia", "").strip()
    search_words = re.sub(r"\s+", " ", search_words).strip()
    search_slug = search_words.replace(" ", "-")
    search_slug = re.sub(r"[^a-z0-9\-áéíóúñ]", "", search_slug).strip("-")
    base_url = f"https://www.elempleo.com/co/ofertas-empleo/{quote(search_slug)}/medellin"
    results = []
    page_num = 1
    seen_ids = global_seen_ids if global_seen_ids is not None else set()
    while len(results) < 60:
        url = f"{base_url}?p={page_num}" if page_num > 1 else base_url
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            page.wait_for_timeout(3000)
        except Exception:
            break
        items = page.query_selector_all("div.result-item")
        if not items:
            break
        for item in items:
            if len(results) >= 60:
                break
            record = _parse_card(item, query, seen_ids)
            if record:
                results.append(record)
        page_num += 1
        if page_num > 20:
            break
    return results


def main():
    search_queries = json.loads(sys.argv[1]) if len(sys.argv) > 1 else []
    timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 45000
    all_results = []
    global_seen_ids = set()

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768},
            locale="es-CO",
        )
        page = context.new_page()
        page.set_default_timeout(timeout)

        for query in search_queries:
            try:
                results = _scrape_query(page, query, timeout, global_seen_ids)
                if results:
                    all_results.extend(results)
            except Exception:
                pass
            time.sleep(random.uniform(1.5, 3.0))

        context.close()
        browser.close()

    json.dump(all_results, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
