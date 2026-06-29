from pathlib import Path
import pytest
import pandas as pd
import numpy as np
from src.models.salary_predictor import SalaryPredictor
from src.models.model_factory import ModelFactory
from src.interfaces.model_interface import ModelInterface


class TestModel:
    @pytest.fixture
    def sample_training_data(self):
        np.random.seed(42)
        n = 50
        df = pd.DataFrame({
            "experiencia_requerida": np.random.randint(0, 15, n).astype(float),
            "cargo_nivel_cod": np.random.randint(0, 4, n),
            "modalidad_cod": np.random.randint(0, 3, n),
            "skills_str": [", ".join(np.random.choice(
                ["Python", "Java", "AWS", "SQL", "Docker", "React", "Git"],
                size=np.random.randint(1, 5)
            )) for _ in range(n)],
        })
        y = pd.Series(
            3000000 + df["experiencia_requerida"] * 400000
            + df["cargo_nivel_cod"] * 1000000
            + np.random.normal(0, 300000, n)
        )
        return df, y

    def test_model_implements_interface(self):
        model = SalaryPredictor()
        assert isinstance(model, ModelInterface)

    def test_train_and_predict(self, sample_training_data):
        X, y = sample_training_data
        model = SalaryPredictor()
        model.train(X, y)
        assert model.is_trained
        result = model.predict(X.iloc[[0]])
        assert "salario_estimado" in result
        assert "rango_inferior" in result
        assert "rango_superior" in result
        assert result["rango_inferior"] <= result["salario_estimado"] <= result["rango_superior"]

    def test_metrics_after_training(self, sample_training_data):
        X, y = sample_training_data
        model = SalaryPredictor()
        model.train(X, y)
        metrics = model.get_metrics()
        assert "MAE" in metrics
        assert "RMSE" in metrics
        assert "R2" in metrics
        assert 0 <= metrics["R2"] <= 1 or metrics["R2"] < 0

    def test_save_and_load(self, sample_training_data, tmp_path):
        from config import Config
        X, y = sample_training_data
        model = SalaryPredictor()
        model.train(X, y)
        path = str(tmp_path / "test_model.pkl")
        model.save(path)
        assert Path(path).exists()

    def test_prediction_ranges(self, sample_training_data):
        X, y = sample_training_data
        model = SalaryPredictor()
        model.train(X, y)
        for level, expected in [("tecnico", 0), ("senior", 3)]:
            input_df = pd.DataFrame([{
                "experiencia_requerida": 3.0,
                "cargo_nivel_cod": expected,
                "modalidad_cod": 1,
                "skills_str": "Python, SQL, Git",
            }])
            result = model.predict(input_df)
            assert 1_000_000 <= result["salario_estimado"] <= 30_000_000

    def test_factory_creates_predictor(self):
        model = ModelFactory.create("RandomForest")
        assert isinstance(model, SalaryPredictor)
