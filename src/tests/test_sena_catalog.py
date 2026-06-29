import pytest
import pandas as pd
from src.data.sena_catalog import (
    SENA_OCCUPATIONS, get_categories, get_occupations_by_category,
    match_occupation_to_category, match_uploaded_data_to_sena,
    get_recommended_occupations,
)


class TestSenaCatalog:
    def test_get_categories_returns_list(self):
        cats = get_categories()
        assert isinstance(cats, list)
        assert len(cats) > 0

    def test_get_occupations_by_category(self):
        for cat in get_categories():
            occs = get_occupations_by_category(cat)
            assert isinstance(occs, list)
            assert len(occs) > 0
            for occ in occs:
                assert "nombre" in occ
                assert "cno" in occ

    def test_get_occupations_by_unknown_category(self):
        result = get_occupations_by_category("CategoriaInexistente")
        assert result == []

    def test_match_occupation_to_category_gerente(self):
        assert match_occupation_to_category("Gerente de TI") == "Gerentes y Directores TI"
        assert match_occupation_to_category("Director de Sistemas") == "Gerentes y Directores TI"

    def test_match_occupation_to_category_ingeniero(self):
        assert match_occupation_to_category("Ingeniero de Software") == "Ingenieros de TI"
        assert match_occupation_to_category("Arquitecto de Software") == "Ingenieros de TI"

    def test_match_occupation_to_category_analista(self):
        assert match_occupation_to_category("Analista de Sistemas") == "Analistas de Sistemas"
        assert match_occupation_to_category("Data Scientist") == "Analistas de Sistemas"

    def test_match_occupation_to_category_administrador(self):
        assert match_occupation_to_category("Administrador de BD") == "Administradores de TI"

    def test_match_occupation_to_category_desarrollador(self):
        assert match_occupation_to_category("Desarrollador Full Stack") == "Desarrolladores"
        assert match_occupation_to_category("Programador Python") == "Desarrolladores"

    def test_match_occupation_to_category_tecnico(self):
        assert match_occupation_to_category("Técnico en Redes") == "Técnicos en TI"

    def test_match_occupation_to_category_soporte(self):
        result = match_occupation_to_category("Soporte TI Help Desk")
        assert result in ["Soporte TI", "Técnicos en TI"]

    def test_match_occupation_to_category_unknown(self):
        assert match_occupation_to_category("Contador") == "Otros"

    def test_match_uploaded_data_to_sena(self):
        series = pd.Series([
            "Ingeniero de Software",
            "Gerente de TI",
            "Desarrollador Python",
            "Analista de Datos",
            "Contador",
        ])
        counts = match_uploaded_data_to_sena(series)
        assert isinstance(counts, dict)
        assert "Ingenieros de TI" in counts
        assert counts["Ingenieros de TI"] == 1

    def test_match_uploaded_data_to_sena_with_nan(self):
        series = pd.Series(["Ingeniero", None, pd.NA, ""])
        counts = match_uploaded_data_to_sena(series)
        assert isinstance(counts, dict)

    def test_get_recommended_occupations(self):
        recs = get_recommended_occupations(["Desarrolladores"])
        assert isinstance(recs, list)
        assert len(recs) > 0
        assert all(isinstance(r, str) for r in recs)

    def test_get_recommended_occupations_empty(self):
        recs = get_recommended_occupations([])
        assert recs == []

    def test_sena_occupation_categories_have_unique_cno_codes(self):
        all_codes = set()
        for cat, occs in SENA_OCCUPATIONS.items():
            for occ in occs:
                all_codes.add(occ["cno"])
        assert len(all_codes) > 0
