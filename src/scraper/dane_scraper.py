import re
import time
import random
import datetime
from typing import List, Dict, Any, Callable, Optional
from src.interfaces.scraper_strategy import ScraperStrategy
from src.utils.loggers import get_logger

logger = get_logger("scraper.dane")


class DaneScraper(ScraperStrategy):
    """DANE/MinTrabajo scraper - Official Colombian government salary data.
    Scrapes from DANE (Departamento Administrativo Nacional de Estadística)
    and MinTrabajo (Ministerio del Trabajo) open data portals."""

    # DANE API endpoints (open data)
    DANE_API = "https://apis.datos.gov.co/dane/servicios"
    MINTRABAJO_API = "https://www.mintrabajo.gov.co/servicios"
    
    # Known public endpoints for salary data
    SALARY_URLS = [
        "https://www.dane.gov.co/index.php/estadisticas-por-tema/laboral-y-empleo",
        "https://www.mintrabajo.gov.co/jornada-laboral-y-salarios/salario-minimo",
    ]

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
        total_steps = len(self.SALARY_URLS) + 1  # URLs + salary table

        if progress_callback:
            progress_callback(
                current=0,
                total=total_steps,
                query="[DANE/MinTrabajo] Iniciando",
                records=0,
                status="scraping"
            )

        # 1. Try DANE employment statistics
        try:
            results = self._scrape_dane(session)
            all_results.extend(results)
            logger.info(f"[DANE] Got {len(results)} records from DANE")
        except Exception as e:
            logger.error(f"[DANE] Failed: {e}")

        if progress_callback:
            progress_callback(
                current=1,
                total=total_steps,
                query="[DANE] Estadísticas DANE",
                records=len(all_results),
                status="scraping"
            )

        time.sleep(random.uniform(2.0, 3.0))

        # 2. Try MinTrabajo salary data
        try:
            results = self._scrape_mintrabajo(session)
            all_results.extend(results)
            logger.info(f"[MinTrabajo] Got {len(results)} records")
        except Exception as e:
            logger.error(f"[MinTrabajo] Failed: {e}")

        if progress_callback:
            progress_callback(
                current=2,
                total=total_steps,
                query="[DANE/MinTrabajo] Datos MinTrabajo",
                records=len(all_results),
                status="scraping"
            )

        time.sleep(random.uniform(2.0, 3.0))

        # 3. Try to extract salary table from known URLs
        try:
            results = self._scrape_salary_table(session)
            all_results.extend(results)
            logger.info(f"[Salary Table] Got {len(results)} records")
        except Exception as e:
            logger.error(f"[Salary Table] Failed: {e}")

        if progress_callback:
            progress_callback(
                current=total_steps,
                total=total_steps,
                query="[DANE/MinTrabajo] Completado",
                records=len(all_results),
                status="done"
            )

        logger.info(f"[DANE/MinTrabajo] Total: {len(all_results)} records")
        return all_results

    def _scrape_dane(self, session) -> List[Dict[str, Any]]:
        """Scrape DANE employment statistics."""
        results = []
        
        try:
            resp = session.get(
                "https://www.dane.gov.co/index.php/estadisticas-por-tema/laboral-y-empleo",
                timeout=self.timeout
            )
            
            if resp.status_code != 200:
                return results

            # Extract salary information from DANE pages
            # Look for tables with salary data
            tables = re.findall(r'<table[^>]*>(.*?)</table>', resp.text, re.DOTALL)
            
            for table in tables:
                rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table, re.DOTALL)
                for row in rows:
                    cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                    if len(cells) >= 2:
                        # Look for salary-like data
                        text = " ".join(cells)
                        if re.search(r'\$[\d.,]+', text):
                            record = self._parse_salary_row(cells, "DANE")
                            if record:
                                results.append(record)

        except Exception as e:
            logger.error(f"[DANE] Scrape error: {e}")

        return results

    def _scrape_mintrabajo(self, session) -> List[Dict[str, Any]]:
        """Scrape MinTrabajo salary data."""
        results = []
        
        try:
            resp = session.get(
                "https://www.mintrabajo.gov.co/jornada-laboral-y-salarios/salario-minimo",
                timeout=self.timeout
            )
            
            if resp.status_code != 200:
                return results

            # Extract salary information
            salary_matches = re.findall(
                r'salario.*?mínimo.*?\$?([\d.,]+)',
                resp.text.lower(),
                re.IGNORECASE
            )
            
            for match in salary_matches:
                try:
                    salary = float(match.replace(".", "").replace(",", "."))
                    if salary > 1_000_000:  # Reasonable salary range
                        results.append({
                            "titulo": "Salario Mínimo Colombia",
                            "empresa": "MinTrabajo",
                            "salario_minimo": salary,
                            "salario_maximo": salary,
                            "moneda": "COP",
                            "ubicacion": "Colombia",
                            "experiencia_requerida": "",
                            "tipo_contrato": "",
                            "skills": "",
                            "fecha_publicacion": datetime.date.today().isoformat(),
                            "descripcion": f"Salario mínimo legal para {datetime.date.today().year}",
                            "modalidad": "presencial",
                            "fuente": "mintrabajo.gov.co",
                        })
                        break  # Only need one entry
                except ValueError:
                    pass

        except Exception as e:
            logger.error(f"[MinTrabajo] Scrape error: {e}")

        return results

    def _scrape_salary_table(self, session) -> List[Dict[str, Any]]:
        """Scrape salary tables from known sources."""
        results = []
        return results

    def _parse_salary_row(self, cells: List[str], source: str) -> Optional[Dict[str, Any]]:
        """Parse a table row with salary data."""
        try:
            text = " ".join(cells)
            
            # Extract salary amounts
            salary_matches = re.findall(r'\$?([\d.,]+)', text)
            salaries = []
            for match in salary_matches:
                try:
                    val = float(match.replace(".", "").replace(",", "."))
                    if val > 1_000_000:  # Reasonable salary range
                        salaries.append(val)
                except ValueError:
                    pass
            
            if not salaries:
                return None
            
            sal_min = min(salaries)
            sal_max = max(salaries)
            
            # Extract title (first cell usually)
            title = re.sub(r'<[^>]+>', '', cells[0]).strip()
            if not title or len(title) < 3:
                return None
            
            return {
                "titulo": title[:200],
                "empresa": f"Fuente oficial ({source})",
                "salario_minimo": sal_min,
                "salario_maximo": sal_max,
                "moneda": "COP",
                "ubicacion": "Colombia",
                "experiencia_requerida": "",
                "tipo_contrato": "",
                "skills": "",
                "fecha_publicacion": datetime.date.today().isoformat(),
                "descripcion": text[:500],
                "modalidad": "presencial",
                "fuente": f"{source}.gov.co",
            }
            
        except Exception:
            return None
