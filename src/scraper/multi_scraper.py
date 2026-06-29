"""
Scraper multi-fuente que agrega datos de múltiples portales de empleo.

Combina datos de elempleo.com, computrabajo.com, indeed.com,
glassdoor.com y dane.gov.co. Usa scraping paralelo con
ThreadPoolExecutor en local y secuencial en Streamlit Cloud.

Author: Lilliana Uribe González
Version: 2.0
"""

import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Callable, Optional
from src.interfaces.scraper_strategy import ScraperStrategy
from src.utils.loggers import get_logger
from src.utils.environment import is_streamlit_cloud, get_zenrows_key

logger = get_logger("scraper.multi")


class MultiSourceScraper(ScraperStrategy):
    """Scraper que combina datos de múltiples portales de empleo.

    Agrega datos de 5-6 fuentes con deduplicación cross-source.
    En local usa ThreadPoolExecutor (3 workers) para paralelizar.
    En Streamlit Cloud ejecuta secuencialmente.

    Attributes:
        timeout: Timeout en segundos por request.
        max_workers: Número máximo de workers paralelos.
        scrapers: Lista de tuplas (nombre, scraper) inicializados.
    """

    def __init__(self, timeout: int = 30, max_workers: int = 3, **kwargs):
        """Inicializa el scraper multi-fuente.

        Args:
            timeout: Timeout por request en segundos (default: 30).
            max_workers: Workers paralelos en local (default: 3).
        """
        self.timeout = timeout
        self.max_workers = max_workers
        self.scrapers = []
        self._init_scrapers()

    def _init_scrapers(self):
        """Inicializa los scrapers disponibles según el entorno.

        Siempre incluye elempleo.com. Agrega ZenRows si hay API key,
        Computrabajo, Indeed, Glassdoor y DANE si están disponibles.
        """
        """Initialize available scrapers based on environment."""
        on_cloud = is_streamlit_cloud()

        # Always try elempleo (primary source)
        try:
            from src.scraper.http_scraper import HttpScraper
            self.scrapers.append(("elempleo.com", HttpScraper(timeout=self.timeout)))
            logger.info("[Multi] Added elempleo.com scraper")
        except Exception as e:
            logger.warning(f"[Multi] Failed to add elempleo scraper: {e}")

        # Try ZenRows if available (better Cloudflare bypass)
        zenrows_key = get_zenrows_key()
        if zenrows_key:
            try:
                from src.scraper.zenrows_scraper import ZenRowsScraper
                self.scrapers.append(("elempleo.com (ZenRows)", ZenRowsScraper(api_key=zenrows_key, timeout=self.timeout)))
                logger.info("[Multi] Added ZenRows scraper")
            except Exception as e:
                logger.warning(f"[Multi] Failed to add ZenRows scraper: {e}")

        # Try Computrabajo
        try:
            from src.scraper.computrabajo_scraper import ComputrabajoScraper
            self.scrapers.append(("computrabajo.com", ComputrabajoScraper(timeout=self.timeout)))
            logger.info("[Multi] Added computrabajo.com scraper")
        except Exception as e:
            logger.warning(f"[Multi] Failed to add Computrabajo scraper: {e}")

        # Try Indeed
        try:
            from src.scraper.indeed_scraper import IndeedScraper
            self.scrapers.append(("indeed.com", IndeedScraper(timeout=self.timeout)))
            logger.info("[Multi] Added indeed.com scraper")
        except Exception as e:
            logger.warning(f"[Multi] Failed to add Indeed scraper: {e}")

        # Try Glassdoor (salary benchmarks)
        try:
            from src.scraper.glassdoor_scraper import GlassdoorScraper
            self.scrapers.append(("glassdoor.com", GlassdoorScraper(timeout=self.timeout)))
            logger.info("[Multi] Added glassdoor.com scraper")
        except Exception as e:
            logger.warning(f"[Multi] Failed to add Glassdoor scraper: {e}")

        # Try DANE/MinTrabajo (official government data)
        try:
            from src.scraper.dane_scraper import DaneScraper
            self.scrapers.append(("dane.gov.co", DaneScraper(timeout=self.timeout)))
            logger.info("[Multi] Added dane.gov.co scraper")
        except Exception as e:
            logger.warning(f"[Multi] Failed to add DANE scraper: {e}")

        logger.info(f"[Multi] Initialized {len(self.scrapers)} scrapers")

    def fetch_data(self, search_queries: List[str], progress_callback: Optional[Callable] = None) -> List[Dict[str, Any]]:
        """Obtiene datos de todas las fuentes disponibles.

        Ejecuta scraping en paralelo (local) o secuencial (Cloud).
        Deduplica registros cross-source por (titulo, empresa, salario).

        Args:
            search_queries: Lista de queries de búsqueda (97 por defecto).
            progress_callback: Función opcional para reportar progreso.

        Returns:
            Lista de registros únicos de todas las fuentes.
        """
        all_results = []
        global_seen = set()
        total_scrapers = len(self.scrapers)

        def scrape_source(scraper_idx, source_name, scraper):
            """Scrape a single source and return results."""
            results = []
            try:
                def source_callback(current, total, query, records, status):
                    """Wrap progress callback with source info."""
                    if progress_callback:
                        scraper_progress = (scraper_idx + (current / total)) / total_scrapers if total > 0 else 0
                        progress_callback(
                            current=int(scraper_progress * 100),
                            total=100,
                            query=f"[{source_name}] {query}",
                            records=len(all_results) + records,
                            status=status
                        )

                results = scraper.fetch_data(search_queries, progress_callback=source_callback)
                logger.info(f"[Multi] {source_name}: {len(results)} records")

            except Exception as e:
                logger.error(f"[Multi] {source_name} failed: {e}")

            return source_name, results

        # Parallel scraping
        if total_scrapers > 1 and not is_streamlit_cloud():
            # Local: use parallel scraping
            logger.info(f"[Multi] Parallel scraping with {min(self.max_workers, total_scrapers)} workers")
            with ThreadPoolExecutor(max_workers=min(self.max_workers, total_scrapers)) as executor:
                futures = {
                    executor.submit(scrape_source, idx, name, scraper): (idx, name)
                    for idx, (name, scraper) in enumerate(self.scrapers)
                }

                for future in as_completed(futures):
                    try:
                        source_name, results = future.result(timeout=120)
                        # Deduplicate across sources
                        for record in results:
                            record_id = f"{record.get('titulo', '')[:50]}_{record.get('empresa', '')[:30]}_{record.get('salario_minimo', 0)}"
                            if record_id not in global_seen:
                                global_seen.add(record_id)
                                all_results.append(record)
                    except Exception as e:
                        logger.error(f"[Multi] Future failed: {e}")
        else:
            # Cloud or single scraper: sequential
            for scraper_idx, (source_name, scraper) in enumerate(self.scrapers):
                logger.info(f"[Multi] Scraping from {source_name} ({scraper_idx + 1}/{total_scrapers})")
                _, results = scrape_source(scraper_idx, source_name, scraper)

                # Deduplicate across sources
                for record in results:
                    record_id = f"{record.get('titulo', '')[:50]}_{record.get('empresa', '')[:30]}_{record.get('salario_minimo', 0)}"
                    if record_id not in global_seen:
                        global_seen.add(record_id)
                        all_results.append(record)

                # Delay between sources (sequential only)
                if scraper_idx < total_scrapers - 1:
                    time.sleep(random.uniform(0.5, 1.0))

        # Final progress
        if progress_callback:
            progress_callback(
                current=100,
                total=100,
                query="Completado",
                records=len(all_results),
                status="done"
            )

        logger.info(f"[Multi] Total: {len(all_results)} records from {total_scrapers} sources")
        return all_results

    def get_source_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de las fuentes disponibles.

        Returns:
            Dict con total_scrapers y lista de nombres de fuentes.
        """
        """Get statistics about available sources."""
        return {
            "total_scrapers": len(self.scrapers),
            "sources": [name for name, _ in self.scrapers],
        }
