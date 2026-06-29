from typing import Dict, Optional
from src.interfaces.model_interface import ModelInterface
from src.models.salary_predictor import SalaryPredictor
from src.utils.loggers import get_logger

logger = get_logger("models.factory")


class ModelFactory:
    _models: Dict[str, type] = {}

    @classmethod
    def register(cls, name: str, model_class: type) -> None:
        cls._models[name] = model_class
        logger.info(f"Model registered: {name}")

    @classmethod
    def create(cls, name: str = "RandomForest", **kwargs) -> ModelInterface:
        if name in cls._models:
            return cls._models[name](**kwargs)
        logger.warning(f"Model '{name}' not found, defaulting to SalaryPredictor")
        return SalaryPredictor()


ModelFactory.register("RandomForest", SalaryPredictor)
ModelFactory.register("XGBoost", SalaryPredictor)
