import json
import subprocess
import sys
from typing import List, Dict, Any

from src.interfaces.scraper_strategy import ScraperStrategy
from src.utils.loggers import get_logger

logger = get_logger("scraper.playwright")


class PlaywrightScraper(ScraperStrategy):
    def __init__(self, headless: bool = True, timeout: int = 45):
        self.headless = headless
        self.timeout = timeout

    def fetch_data(self, search_queries: List[str]) -> List[Dict[str, Any]]:
        worker_script = str(
            __import__("pathlib").Path(__file__).parent / "_playwright_worker.py"
        )
        cmd = [
            sys.executable,
            worker_script,
            json.dumps(search_queries),
            str(self.timeout * 1000),
        ]
        logger.info(f"[Playwright] Starting subprocess for {len(search_queries)} queries")
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout + 30,
                encoding="utf-8",
                errors="replace",
            )
            if result.returncode != 0:
                stderr = result.stderr.strip()[-500:] if result.stderr else ""
                logger.error(f"[Playwright] Subprocess failed (rc={result.returncode}): {stderr}")
                return []

            data = json.loads(result.stdout)
            logger.info(f"[Playwright] Got {len(data)} records from subprocess")
            return data

        except subprocess.TimeoutExpired:
            logger.error(f"[Playwright] Subprocess timeout ({self.timeout + 30}s)")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"[Playwright] Invalid JSON from subprocess: {e}")
            return []
        except Exception as e:
            logger.error(f"[Playwright] Subprocess error: {e}")
            return []
