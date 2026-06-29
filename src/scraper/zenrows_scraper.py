import re
import json
import time
import random
import datetime
from typing import List, Dict, Any, Callable, Optional
from urllib.parse import quote
from src.interfaces.scraper_strategy import ScraperStrategy
from src.utils.loggers import get_logger

logger = get_logger("scraper.zenrows")


class ZenRowsScraper(ScraperStrategy):
    """ZenRows API scraper - bypasses Cloudflare automatically.
    Free tier: 1000 requests/month at https://zenrows.com"""

    ZENROWS_API = "https://api.zenrows.com/v1/"

    def __init__(self, api_key: str = "", timeout: int = 45, **kwargs):
        self.api_key = api_key
        self.timeout = timeout
        self.session = None

    def _get_session(self):
        if self.session is None:
            import requests
            self.session = requests.Session()
            self.session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            })
        return self.session

    def fetch_data(self, search_queries: List[str], progress_callback: Optional[Callable] = None) -> List[Dict[str, Any]]:
        if not self.api_key:
            logger.warning("[ZenRows] No API key provided")
            return []

        session = self._get_session()
        all_results = []
        global_seen = set()
        total_queries = len(search_queries)

        for i, query in enumerate(search_queries):
            # Report progress
            if progress_callback:
                progress_callback(
                    current=i + 1,
                    total=total_queries,
                    query=query,
                    records=len(all_results),
                    status="scraping"
                )

            try:
                results = self._scrape_query(session, query, global_seen)
                all_results.extend(results)
                logger.info(f"[ZenRows] {len(results)} records for '{query}' (total: {len(all_results)})")
            except Exception as e:
                logger.error(f"[ZenRows] Failed for '{query}': {e}")

            # Rate limit: ~1 request per second
            time.sleep(random.uniform(1.0, 2.0))

        # Final progress
        if progress_callback:
            progress_callback(
                current=total_queries,
                total=total_queries,
                query="Completado",
                records=len(all_results),
                status="done"
            )

        logger.info(f"[ZenRows] Total: {len(all_results)} records")
        return all_results

    def _scrape_query(self, session, query: str, global_seen: set) -> List[Dict[str, Any]]:
        search_words = query.lower().replace("medellín", "").replace("colombia", "").strip()
        search_words = re.sub(r"\s+", " ", search_words).strip()
        search_slug = search_words.replace(" ", "-")
        search_slug = re.sub(r"[^a-z0-9\-áéíóúñ]", "", search_slug).strip("-")
        base_url = f"https://www.elempleo.com/co/ofertas-empleo/{quote(search_slug)}/medellin"

        results = []
        page_num = 1

        while len(results) < 60 and page_num <= 3:
            url = f"{base_url}?p={page_num}" if page_num > 1 else base_url
            try:
                # ZenRows API request
                params = {
                    "url": url,
                    "apikey": self.api_key,
                    "js_render": "true",
                    "anti_bot": "true",
                }
                resp = session.get(self.ZENROWS_API, params=params, timeout=self.timeout)

                if resp.status_code != 200:
                    logger.warning(f"[ZenRows] Status {resp.status_code} for {url}")
                    break

                html = resp.text

                # Check for Cloudflare challenge
                if "cf-browser-verification" in html or "Just a moment..." in html:
                    logger.warning(f"[ZenRows] Cloudflare challenge for {url}")
                    break

                # Parse cards
                cards = re.findall(
                    r'<div[^>]*class="[^"]*result-item[^"]*"[^>]*>(.*?)</div>\s*</div>\s*</div>',
                    html, re.DOTALL
                )
                if not cards:
                    cards = re.findall(r'<article[^>]*>(.*?)</article>', html, re.DOTALL)
                if not cards:
                    break

                for card in cards:
                    if len(results) >= 60:
                        break
                    record = self._parse_card(card, query, global_seen)
                    if record:
                        results.append(record)

                page_num += 1
                time.sleep(random.uniform(1.0, 2.0))

            except Exception as e:
                logger.error(f"[ZenRows] Request error for {url}: {e}")
                break

        return results

    def _parse_card(self, card: str, query: str, global_seen: set) -> Dict[str, Any]:
        """Parse a job card from HTML."""
        try:
            title_match = re.search(r'<h2[^>]*>(.*?)</h2>', card, re.DOTALL)
            title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip() if title_match else ""
            if not title:
                return None

            company_match = re.search(r'<span[^>]*class="[^"]*company[^"]*"[^>]*>(.*?)</span>', card, re.DOTALL)
            company = re.sub(r'<[^>]+>', '', company_match.group(1)).strip() if company_match else ""

            location_match = re.search(r'<span[^>]*class="[^"]*location[^"]*"[^>]*>(.*?)</span>', card, re.DOTALL)
            location = re.sub(r'<[^>]+>', '', location_match.group(1)).strip() if location_match else "Medellín"

            salary_match = re.search(r'<span[^>]*class="[^"]*salary[^"]*"[^>]*>(.*?)</span>', card, re.DOTALL)
            salary_text = re.sub(r'<[^>]+>', '', salary_match.group(1)).strip() if salary_match else ""

            sal_min, sal_max = self._parse_salary(salary_text)
            if not sal_min and not sal_max:
                return None

            record_id = f"{title[:50]}_{company[:30]}_{sal_min}"
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
