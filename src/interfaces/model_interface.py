from abc import ABC, abstractmethod
from typing import Dict, Any
import pandas as pd


class ModelInterface(ABC):
    @abstractmethod
    def train(self, X: pd.DataFrame, y: pd.Series) -> None:
        pass

    @abstractmethod
    def predict(self, features: pd.DataFrame) -> Dict[str, Any]:
        pass

    @abstractmethod
    def save(self, path: str) -> None:
        pass

    @abstractmethod
    def load(self, path: str) -> None:
        pass

    @abstractmethod
    def get_metrics(self) -> Dict[str, float]:
        pass
