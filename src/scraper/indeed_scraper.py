import re
import time
import random
import datetime
from typing import List, Dict, Any, Callable, Optional
from urllib.parse import quote
from src.interfaces.scraper_strategy import ScraperStrategy
from src.utils.loggers import get_logger

logger = get_logger("scraper.indeed")


class IndeedScraper(ScraperStrategy):
    """Indeed Colombia scraper - global job portal.
    Works on Streamlit Cloud with HTTP requests."""

    BASE_URL = "https://co.indeed.com/jobs"

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
                    query=f"[Indeed] {query}",
                    records=len(all_results),
                    status="scraping"
                )

            try:
                results = self._scrape_query(session, query, global_seen)
                all_results.extend(results)
                logger.info(f"[Indeed] {len(results)} records for '{query}' (total: {len(all_results)})")
            except Exception as e:
                logger.error(f"[Indeed] Failed for '{query}': {e}")

            time.sleep(random.uniform(2.0, 4.0))

        if progress_callback:
            progress_callback(
                current=total_queries,
                total=total_queries,
                query="[Indeed] Completado",
                records=len(all_results),
                status="done"
            )

        logger.info(f"[Indeed] Total: {len(all_results)} records")
        return all_results

    def _scrape_query(self, session, query: str, global_seen: set) -> List[Dict[str, Any]]:
        search_words = query.lower().replace("colombia", "").strip()
        params = {
            "q": search_words,
            "l": "Medellín",
            "sort": "date",
        }

        results = []
        page_num = 0

        while len(results) < 100 and page_num < 10:
            if page_num > 0:
                params["start"] = page_num * 10

            try:
                resp = session.get(self.BASE_URL, params=params, timeout=self.timeout)
                if resp.status_code != 200:
                    break

                # Parse job cards
                cards = re.findall(
                    r'<div[^>]*class="[^"]*job_seen_beacon[^"]*"[^>]*>(.*?)</div>\s*</div>\s*</div>',
                    resp.text, re.DOTALL
                )
                if not cards:
                    cards = re.findall(
                        r'<table[^>]*class="[^"]*jobCard[^"]*"[^>]*>(.*?)</table>',
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
                logger.error(f"[Indeed] Request error: {e}")
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
            company_match = re.search(r'<span[^>]*data-testid="[^"]*company[^"]*"[^>]*>(.*?)</span>', card, re.DOTALL)
            if not company_match:
                company_match = re.search(r'<span[^>]*class="[^"]*companyName[^"]*"[^>]*>(.*?)</span>', card, re.DOTALL)
            company = re.sub(r'<[^>]+>', '', company_match.group(1)).strip() if company_match else ""

            # Location
            location_match = re.search(r'<div[^>]*data-testid="[^"]*location[^"]*"[^>]*>(.*?)</div>', card, re.DOTALL)
            if not location_match:
                location_match = re.search(r'<div[^>]*class="[^"]*companyLocation[^"]*"[^>]*>(.*?)</div>', card, re.DOTALL)
            location = re.sub(r'<[^>]+>', '', location_match.group(1)).strip() if location_match else "Medellín"

            # Salary
            salary_match = re.search(r'<div[^>]*class="[^"]*salary-snippet[^"]*"[^>]*>(.*?)</div>', card, re.DOTALL)
            salary_text = re.sub(r'<[^>]+>', '', salary_match.group(1)).strip() if salary_match else ""

            sal_min, sal_max = self._parse_salary(salary_text)
            if not sal_min and not sal_max:
                return None

            record_id = f"indeed_{title[:40]}_{company[:20]}_{sal_min}"
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
                "fuente": "indeed.com",
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
