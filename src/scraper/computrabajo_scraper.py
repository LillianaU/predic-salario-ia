import re
import time
import random
import datetime
from typing import List, Dict, Any, Callable, Optional
from urllib.parse import quote
from src.interfaces.scraper_strategy import ScraperStrategy
from src.utils.loggers import get_logger

logger = get_logger("scraper.computrabajo")


class ComputrabajoScraper(ScraperStrategy):
    """Computrabajo scraper - Colombian job portal.
    Works on Streamlit Cloud with HTTP requests."""

    BASE_URL = "https://www.computrabajo.com.co/trabajo-de"

    def __init__(self, timeout: int = 30, **kwargs):
        self.timeout = timeout
        self.session = None

    def _get_session(self):
        if self.session is None:
            try:
                import cloudscraper
                self.session = cloudscraper.create_scraper(
                    browser={"browser": "chrome", "platform": "windows", "desktop": True}
                )
            except ImportError:
                import requests
                self.session = requests.Session()

            self.session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
            })
        return self.session

    def fetch_data(self, search_queries: List[str], progress_callback: Optional[Callable] = None) -> List[Dict[str, Any]]:
        session = self._get_session()
        all_results = []
        global_seen = set()
        total_queries = len(search_queries)

        for i, query in enumerate(search_queries):
            if progress_callback:
                progress_callback(
                    current=i + 1,
                    total=total_queries,
                    query=f"[Computrabajo] {query}",
                    records=len(all_results),
                    status="scraping"
                )

            try:
                results = self._scrape_query(session, query, global_seen)
                all_results.extend(results)
                logger.info(f"[Computrabajo] {len(results)} records for '{query}' (total: {len(all_results)})")
            except Exception as e:
                logger.error(f"[Computrabajo] Failed for '{query}': {e}")

            time.sleep(random.uniform(2.0, 4.0))

        if progress_callback:
            progress_callback(
                current=total_queries,
                total=total_queries,
                query="[Computrabajo] Completado",
                records=len(all_results),
                status="done"
            )

        logger.info(f"[Computrabajo] Total: {len(all_results)} records")
        return all_results

    def _scrape_query(self, session, query: str, global_seen: set) -> List[Dict[str, Any]]:
        search_words = query.lower().replace("medellín", "").replace("colombia", "").strip()
        search_slug = search_words.replace(" ", "-")
        search_slug = re.sub(r"[^a-z0-9\-áéíóúñ]", "", search_slug).strip("-")
        base_url = f"{self.BASE_URL}-{search_slug}"

        results = []
        page_num = 1

        while len(results) < 100 and page_num <= 10:
            url = f"{base_url}/?p={page_num}" if page_num > 1 else base_url
            try:
                resp = session.get(url, timeout=self.timeout)
                if resp.status_code != 200:
                    break

                # Parse job cards
                cards = re.findall(
                    r'<article[^>]*class="[^"]*box_list[^"]*"[^>]*>(.*?)</article>',
                    resp.text, re.DOTALL
                )
                if not cards:
                    cards = re.findall(
                        r'<div[^>]*class="[^"]*iO[^"]*"[^>]*>(.*?)</div>\s*</div>',
                        resp.text, re.DOTALL
                    )
                if not cards:
                    break

                for card in cards:
                    if len(results) >= 100:
                        break
                    record = self._parse_card(card, query, global_seen)
                    if record:
                        results.append(record)

                page_num += 1
                time.sleep(random.uniform(1.0, 2.0))

            except Exception as e:
                logger.error(f"[Computrabajo] Request error: {e}")
                break

        return results

    def _parse_card(self, card: str, query: str, global_seen: set) -> Dict[str, Any]:
        try:
            # Title
            title_match = re.search(r'<h2[^>]*>(.*?)</h2>', card, re.DOTALL)
            title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip() if title_match else ""
            if not title:
                return None

            # Company
            company_match = re.search(r'<span[^>]*class="[^"]*empresa[^"]*"[^>]*>(.*?)</span>', card, re.DOTALL)
            company = re.sub(r'<[^>]+>', '', company_match.group(1)).strip() if company_match else ""

            # Location
            location_match = re.search(r'<span[^>]*class="[^"]*ubicacion[^"]*"[^>]*>(.*?)</span>', card, re.DOTALL)
            location = re.sub(r'<[^>]+>', '', location_match.group(1)).strip() if location_match else "Medellín"

            # Salary
            salary_match = re.search(r'<span[^>]*class="[^"]*salario[^"]*"[^>]*>(.*?)</span>', card, re.DOTALL)
            salary_text = re.sub(r'<[^>]+>', '', salary_match.group(1)).strip() if salary_match else ""

            sal_min, sal_max = self._parse_salary(salary_text)
            if not sal_min and not sal_max:
                return None

            record_id = f"ct_{title[:40]}_{company[:20]}_{sal_min}"
            if record_id in global_seen:
                return None
            global_seen.add(record_id)

            modalidad = "presencial"
            card_lower = card.lower()
            if "remoto" in card_lower or "virtual" in card_lower:
                modalidad = "remoto"
            elif "híbrido" in card_lower or "hibrido" in card_lower:
                modalidad = "hibrido"

            return {
                "titulo": title[:200],
                "empresa": company[:150] if company else "No especificada",
                "salario_minimo": sal_min,
                "salario_maximo": sal_max,
                "moneda": "COP",
                "ubicacion": f"{location}, Colombia" if location else "Medellín, Colombia",
                "experiencia_requerida": "",
                "tipo_contrato": "",
                "skills": "",
                "fecha_publicacion": datetime.date.today().isoformat(),
                "descripcion": "",
                "modalidad": modalidad,
                "fuente": "computrabajo.com",
            }
        except Exception:
            return None

    def _parse_salary(self, text: str):
        if not text or "confidencial" in text.lower():
            return 0.0, 0.0
        nums = re.findall(r"[\d.,]+", text)
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
        if "millon" in text.lower():
            if sal_max > 0 and sal_max < 100:
                sal_min *= 1_000_000
                sal_max *= 1_000_000
        return sal_min, sal_max
