from abc import ABC, abstractmethod
from typing import List, Dict, Any, Callable, Optional


class ScraperStrategy(ABC):
    @abstractmethod
    def fetch_data(self, search_queries: List[str], progress_callback: Optional[Callable] = None) -> List[Dict[str, Any]]:
        pass
