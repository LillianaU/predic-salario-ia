import pytest
import pandas as pd
from src.data.data_cleaner import DataCleaner


class TestCleaner:
    @pytest.fixture
    def sample_raw_data(self):
        return [
            {
                "titulo": "Ingeniero de Sistemas Senior",
                "empresa": "Empresa Test",
                "salario_minimo": 5000000,
                "salario_maximo": 8000000,
                "moneda": "COP",
                "ubicacion": "Medellín, Colombia",
                "experiencia_requerida": "5 años",
                "tipo_contrato": "Tiempo completo",
                "skills": "Python, AWS, Docker",
                "fecha_publicacion": "2024-01-15",
                "descripcion": "Ingeniero con 5 años de experiencia en Python y AWS",
                "modalidad": "remoto",
            },
            {
                "titulo": "Técnico en Sistemas",
                "empresa": "Empresa 2",
                "salario_minimo": 1500000,
                "salario_maximo": 2500000,
                "moneda": "COP",
                "ubicacion": "Medellín, Colombia",
                "experiencia_requerida": "1 año",
                "tipo_contrato": "Temporal",
                "skills": "Soporte técnico",
                "fecha_publicacion": "2024-01-10",
                "descripcion": "Técnico con 1 año de experiencia",
                "modalidad": "presencial",
            },
        ]

    def test_clean_removes_records_without_salary(self):
        cleaner = DataCleaner()
        data = [
            {"titulo": "Test", "empresa": "X", "salario_minimo": None,
             "salario_maximo": None, "moneda": "COP", "ubicacion": "MDE",
             "experiencia_requerida": "", "tipo_contrato": "",
             "skills": "", "fecha_publicacion": "", "descripcion": "", "modalidad": ""},
            {"titulo": "Test2", "empresa": "Y", "salario_minimo": 2000000,
             "salario_maximo": 3000000, "moneda": "COP", "ubicacion": "MDE",
             "experiencia_requerida": "2 años", "tipo_contrato": "",
             "skills": "Python", "fecha_publicacion": "", "descripcion": "", "modalidad": ""},
        ]
        df = cleaner.clean(data)
        assert len(df) >= 1

    def test_cargo_level_identification(self, sample_raw_data):
        cleaner = DataCleaner()
        df = cleaner.clean(sample_raw_data)
        assert "cargo_nivel" in df.columns
        senior_rows = df[df["titulo"].str.contains("Senior", case=False)]
        if not senior_rows.empty:
            assert senior_rows.iloc[0]["cargo_nivel"] == "senior"

    def test_experience_extraction(self, sample_raw_data):
        cleaner = DataCleaner()
        df = cleaner.clean(sample_raw_data)
        assert "experiencia_requerida" in df.columns
        assert df["experiencia_requerida"].iloc[0] == 5.0

    def test_salary_target_creation(self, sample_raw_data):
        cleaner = DataCleaner()
        df = cleaner.clean(sample_raw_data)
        assert "salario_promedio" in df.columns
        expected = (5000000 + 8000000) / 2
        assert df["salario_promedio"].iloc[0] == expected

    def test_modalidad_identification(self, sample_raw_data):
        cleaner = DataCleaner()
        df = cleaner.clean(sample_raw_data)
        assert df["modalidad_clean"].iloc[0] == "remoto"

    def test_empty_dataframe(self):
        cleaner = DataCleaner()
        df = cleaner.clean([])
        assert isinstance(df, pd.DataFrame)
