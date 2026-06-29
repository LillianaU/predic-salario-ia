"""
Factory para creación de scrapers con fallback automático.

Implementa el patrón Factory + Strategy para seleccionar el scraper
adecuado según el entorno (local vs Streamlit Cloud). Registra 6
tipos de scrapers y selecciona el mejor disponible con fallback.

Author: Lilliana Uribe González
Version: 2.0
"""

from typing import List, Dict, Any
from src.interfaces.scraper_strategy import ScraperStrategy
from src.scraper.playwright_scraper import PlaywrightScraper
from src.scraper.http_scraper import HttpScraper
from src.scraper.zenrows_scraper import ZenRowsScraper
from src.scraper.multi_scraper import MultiSourceScraper
from src.scraper.glassdoor_scraper import GlassdoorScraper
from src.scraper.dane_scraper import DaneScraper
from src.utils.loggers import get_logger
from src.utils.environment import is_streamlit_cloud, get_playwright_available, get_zenrows_key

logger = get_logger("scraper.factory")


class ScraperFactory:
    """Factory para creación de scrapers con fallback ambiental.

    Registra 6 tipos de scrapers: playwright, http, zenrows, multi,
    glassdoor, dane. El método create_with_fallback() selecciona
    automáticamente el mejor scraper según el entorno.

    Fallback local: MultiSource → Playwright → HTTP
    Fallback Cloud: MultiSource → ZenRows → HTTP → Playwright
    """
    _strategies = {}

    @classmethod
    def register(cls, name: str, strategy_class: type) -> None:
        """Registra un tipo de scraper en el factory.

        Args:
            name: Nombre identificador del scraper.
            strategy_class: Clase que implementa ScraperStrategy.
        """
        cls._strategies[name] = strategy_class
        logger.info(f"Scraper registered: {name}")

    @classmethod
    def create(cls, name: str = "playwright", **kwargs) -> ScraperStrategy:
        """Crea un scraper por nombre.

        Args:
            name: Nombre del scraper registrado.
            kwargs: Argumentos adicionales para el constructor.

        Returns:
            Instancia del scraper solicitado.
        """
        if name in cls._strategies:
            return cls._strategies[name](**kwargs)
        logger.warning(f"Scraper '{name}' not found, defaulting to PlaywrightScraper")
        return PlaywrightScraper(**kwargs)

    @classmethod
    def create_with_fallback(cls, **kwargs) -> ScraperStrategy:
        """Selecciona el mejor scraper automáticamente según el entorno.

        Fallback local: MultiSource → Playwright → HTTP
        Fallback Cloud: MultiSource → ZenRows → HTTP → Playwright

        Returns:
            ScraperStrategy disponible y funcional.
        """
        """Environment-aware scraper selection with multi-source support."""
        
        # Detect environment
        on_cloud = is_streamlit_cloud()
        playwright_ok = get_playwright_available()
        
        logger.info(f"Environment: {'Streamlit Cloud' if on_cloud else 'Local'}")
        logger.info(f"Playwright available: {playwright_ok}")
        
        # Use multi-source scraper (combines all available sources)
        try:
            multi = MultiSourceScraper(**kwargs)
            sources = multi.get_source_stats()
            logger.info(f"Scraper: MultiSource ({sources['total_scrapers']} fuentes: {', '.join(sources['sources'])})")
            return multi
        except Exception as e:
            logger.warning(f"Multi-source scraper failed: {e}")

        # Streamlit Cloud: Try ZenRows first (bypasses Cloudflare)
        if on_cloud:
            zenrows_key = get_zenrows_key()
            if zenrows_key:
                try:
                    zenrows = ZenRowsScraper(api_key=zenrows_key, **kwargs)
                    logger.info("Scraper: ZenRows API (Cloudflare bypass)")
                    return zenrows
                except Exception as e:
                    logger.warning(f"ZenRows failed: {e}")
            
            # Fallback to HTTP
            logger.info("Streamlit Cloud - using HTTP scraper")
            try:
                http = HttpScraper(**kwargs)
                logger.info("Scraper: HTTP (cloudscraper) - Streamlit Cloud mode")
                return http
            except Exception as e:
                logger.warning(f"HTTP scraper failed: {e}")
        
        # Local with Playwright available
        elif playwright_ok:
            try:
                pw = PlaywrightScraper(**kwargs)
                logger.info("Scraper: Playwright (local mode)")
                return pw
            except Exception as e:
                logger.warning(f"Playwright failed: {e}")
        
        # Fallback to HTTP (works on both environments)
        try:
            http = HttpScraper(**kwargs)
            logger.info("Scraper: HTTP (cloudscraper) - fallback")
            return http
        except Exception as e:
            logger.warning(f"HTTP scraper failed: {e}")

        # Last resort
        logger.warning("No scrapers available. Using Playwright anyway.")
        return PlaywrightScraper(**kwargs)


ScraperFactory.register("playwright", PlaywrightScraper)
ScraperFactory.register("http", HttpScraper)
ScraperFactory.register("zenrows", ZenRowsScraper)
ScraperFactory.register("multi", MultiSourceScraper)
ScraperFactory.register("glassdoor", GlassdoorScraper)
ScraperFactory.register("dane", DaneScraper)
