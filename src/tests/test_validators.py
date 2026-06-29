import pytest
from src.utils.validators import (
    extract_experience_years,
    extract_skills,
    identify_cargo_level,
    identify_modalidad,
    identify_role_category,
    validate_salary_range,
    sanitize_user_input,
)
from src.utils.security import compute_file_hash, mask_token
from src.utils.news import fetch_news
from pathlib import Path


class TestValidators:
    def test_extract_experience_years(self):
        assert extract_experience_years("5 años de experiencia") == 5.0
        assert extract_experience_years("3 años") == 3.0
        assert extract_experience_years("sin experiencia") == 0.0
        assert extract_experience_years("reciente graduado") == 0.0
        assert extract_experience_years(None) is None
        assert extract_experience_years("") is None

    def test_extract_skills(self):
        text = "Python y AWS con Docker"
        skills = extract_skills(text)
        assert "Python" in skills
        assert "AWS" in skills
        assert "Docker" in skills

    def test_extract_skills_empty(self):
        assert extract_skills("") == []
        assert extract_skills(None) == []

    def test_identify_cargo_level(self):
        assert identify_cargo_level("Senior Software Engineer") == "senior"
        assert identify_cargo_level("Técnico en Sistemas") == "tecnico"
        assert identify_cargo_level("Tecnólogo en Sistemas") == "tecnologo"
        assert identify_cargo_level("Ingeniero de Software") == "ingeniero"
        assert identify_cargo_level("Desarrollador Full Stack") == "ingeniero"
        assert identify_cargo_level("") == "ingeniero"

    def test_identify_modalidad(self):
        assert identify_modalidad("Trabajo remoto") == "remoto"
        assert identify_modalidad("Modalidad híbrida") == "hibrido"
        assert identify_modalidad("Presencial") == "presencial"
        assert identify_modalidad("") == "presencial"

    def test_validate_salary_range(self):
        assert validate_salary_range(3_000_000, "tecnico") is True
        assert validate_salary_range(10_000_000, "senior") is True
        assert validate_salary_range(100, "ingeniero") is False

    def test_identify_role_category(self):
        assert identify_role_category("Data Scientist Senior", "machine learning python") == "Ciencia de Datos"
        assert identify_role_category("Desarrollador Full Stack", "react nodejs") == "Desarrollo de Software"
        assert identify_role_category("Data Engineer", "spark etl") == "Ingeniería de Datos"
        assert identify_role_category("ML Engineer", "deep learning nlp") == "Machine Learning"
        assert identify_role_category("Ingeniero IA", "inteligencia artificial") == "Inteligencia Artificial"
        assert identify_role_category("Contador", "finanzas") == "Otros"

    def test_sanitize_user_input(self):
        assert sanitize_user_input("  hola  ") == "hola"
        assert sanitize_user_input("") == ""
        assert sanitize_user_input(None) == ""


class TestNews:
    def test_fetch_news_returns_list(self):
        items = fetch_news(max_items=3)
        assert isinstance(items, list)
        assert len(items) <= 3
        if items:
            assert "title" in items[0]
            assert "url" in items[0]


class TestSecurity:
    def test_mask_token(self):
        assert mask_token("abcdefgh12345678") == "abcd...5678"
        assert mask_token("") == ""
        assert mask_token("short") == "***"

    def test_compute_file_hash_nonexistent(self, tmp_path):
        h = compute_file_hash(tmp_path / "nonexistent.txt")
        assert h is None
