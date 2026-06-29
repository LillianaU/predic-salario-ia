import re
import time
import random
import datetime
from typing import List, Dict, Any, Callable, Optional
from src.interfaces.scraper_strategy import ScraperStrategy
from src.utils.loggers import get_logger

logger = get_logger("scraper.glassdoor")


class GlassdoorScraper(ScraperStrategy):
    """Glassdoor scraper - Salary benchmarks and company reviews.
    Note: Glassdoor has aggressive anti-bot measures.
    Best-effort scraping with HTTP; may require ZenRows for Cloudflare bypass."""

    BASE_URL = "https://www.glassdoor.com/Job/medellin-software-engineer-SRCH_IL.0,8_IC2835852_KO9,27.htm"
    SEARCH_URL = "https://www.glassdoor.com/Job/medellin-{query_slug}-SRCH_IL.0,8_IC2835852_KO9,{end_pos}.htm"

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
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "es-CO,es;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Cache-Control": "max-age=0",
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
                    query=f"[Glassdoor] {query}",
                    records=len(all_results),
                    status="scraping"
                )

            try:
                results = self._scrape_query(session, query, global_seen)
                all_results.extend(results)
                logger.info(f"[Glassdoor] {len(results)} records for '{query}' (total: {len(all_results)})")
            except Exception as e:
                logger.error(f"[Glassdoor] Failed for '{query}': {e}")

            time.sleep(random.uniform(3.0, 6.0))

        if progress_callback:
            progress_callback(
                current=total_queries,
                total=total_queries,
                query="[Glassdoor] Completado",
                records=len(all_results),
                status="done"
            )

        logger.info(f"[Glassdoor] Total: {len(all_results)} records")
        return all_results

    def _scrape_query(self, session, query: str, global_seen: set) -> List[Dict[str, Any]]:
        query_slug = query.lower().replace(" ", "-").replace("medellín", "").strip("-")
        results = []

        url = f"https://www.glassdoor.com/Job/medellin-{query_slug}-SRCH_IL.0,8_IC2835852.htm"

        try:
            resp = session.get(url, timeout=self.timeout, allow_redirects=True)

            if resp.status_code == 403 or "cf-browser-verification" in resp.text.lower():
                logger.warning(f"[Glassdoor] Cloudflare block for '{query}'")
                return results

            if resp.status_code != 200:
                logger.warning(f"[Glassdoor] HTTP {resp.status_code} for '{query}'")
                return results

            # Parse job cards - Glassdoor uses multiple patterns
            cards = re.findall(
                r'<li[^>]*class="[^"]*JobsList_jobListItem[^"]*"[^>]*>(.*?)</li>',
                resp.text, re.DOTALL
            )
            if not cards:
                cards = re.findall(
                    r'<div[^>]*data-test="[^"]*jobListing[^"]*"[^>]*>(.*?)</div>\s*</div>',
                    resp.text, re.DOTALL
                )
            if not cards:
                # Fallback: try to find job links
                cards = re.findall(
                    r'<a[^>]*href="/Job/[^"]*"[^>]*>(.*?)</a>',
                    resp.text, re.DOTALL
                )

            for card in cards:
                if len(results) >= 100:
                    break
                record = self._parse_card(card, query, global_seen)
                if record:
                    results.append(record)

        except Exception as e:
            logger.error(f"[Glassdoor] Request error: {e}")

        return results

    def _parse_card(self, card: str, query: str, global_seen: set) -> Dict[str, Any]:
        try:
            # Title
            title_match = re.search(r'<a[^>]*data-test="[^"]*job-title[^"]*"[^>]*>(.*?)</a>', card, re.DOTALL)
            if not title_match:
                title_match = re.search(r'<h2[^>]*>(.*?)</h2>', card, re.DOTALL)
            title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip() if title_match else ""
            if not title:
                return None

            # Company
            company_match = re.search(r'<span[^>]*class="[^"]*EmployerName[^"]*"[^>]*>(.*?)</span>', card, re.DOTALL)
            if not company_match:
                company_match = re.search(r'<div[^>]*class="[^"]*job-listing-company[^"]*"[^>]*>(.*?)</div>', card, re.DOTALL)
            company = re.sub(r'<[^>]+>', '', company_match.group(1)).strip() if company_match else ""

            # Location
            location_match = re.search(r'<div[^>]*class="[^"]*JobDetails/jobLocation[^"]*"[^>]*>(.*?)</div>', card, re.DOTALL)
            if not location_match:
                location_match = re.search(r'<span[^>]*class="[^"]*jobLocation[^"]*"[^>]*>(.*?)</span>', card, re.DOTALL)
            location = re.sub(r'<[^>]+>', '', location_match.group(1)).strip() if location_match else "Medellín"

            # Salary
            salary_match = re.search(r'<div[^>]*class="[^"]*Salary[^"]*"[^>]*>(.*?)</div>', card, re.DOTALL)
            if not salary_match:
                salary_match = re.search(r'<span[^>]*class="[^"]*salary[^"]*"[^>]*>(.*?)</span>', card, re.DOTALL)
            salary_text = re.sub(r'<[^>]+>', '', salary_match.group(1)).strip() if salary_match else ""

            sal_min, sal_max = self._parse_salary(salary_text)

            record_id = f"gd_{title[:40]}_{company[:20]}_{sal_min}"
            if record_id in global_seen:
                return None
            global_seen.add(record_id)

            modalidad = "presencial"
            card_lower = card.lower()
            if "remote" in card_lower or "remoto" in card_lower:
                modalidad = "remoto"
            elif "hybrid" in card_lower or "híbrido" in card_lower:
                modalidad = "hibrido"

            return {
                "titulo": title[:200],
                "empresa": company[:150] if company else "No especificada",
                "salario_minimo": sal_min,
                "salario_maximo": sal_max,
                "moneda": "COP",
                "ubicacion": f"{location}, Colombia" if "Colombia" not in location else location,
                "experiencia_requerida": "",
                "tipo_contrato": "",
                "skills": "",
                "fecha_publicacion": datetime.date.today().isoformat(),
                "descripcion": "",
                "modalidad": modalidad,
                "fuente": "glassdoor.com",
            }
        except Exception:
            return None

    def _parse_salary(self, text: str):
        if not text or "confidential" in text.lower() or "confidencial" in text.lower():
            return 0.0, 0.0
        nums = re.findall(r"[\d.,]+", text)
        sal_nums = []
        for n in nums:
            try:
                n_clean = n.replace(",", "")
                sal_nums.append(float(n_clean))
            except ValueError:
                pass
        sal_min, sal_max = 0.0, 0.0
        if len(sal_nums) >= 2:
            sal_min, sal_max = min(sal_nums), max(sal_nums)
        elif len(sal_nums) == 1:
            sal_min, sal_max = sal_nums[0] * 0.8, sal_nums[0] * 1.2
        return sal_min, sal_max
