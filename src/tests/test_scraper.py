import pytest
from unittest.mock import patch, MagicMock
from src.scraper.playwright_scraper import PlaywrightScraper
from src.scraper.http_scraper import HttpScraper
from src.scraper.scraper_factory import ScraperFactory
from src.interfaces.scraper_strategy import ScraperStrategy


class TestScraper:
    def test_scraper_factory_default(self):
        scraper = ScraperFactory.create("nonexistent")
        assert isinstance(scraper, PlaywrightScraper)

    def test_scraper_factory_creates_playwright(self):
        scraper = ScraperFactory.create("playwright")
        assert isinstance(scraper, PlaywrightScraper)

    def test_scraper_factory_creates_http(self):
        scraper = ScraperFactory.create("http")
        assert isinstance(scraper, HttpScraper)
