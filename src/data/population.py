import re
import requests
from typing import Dict, Optional
from src.utils.loggers import get_logger

logger = get_logger("data.population")

WIKI_API = "https://es.wikipedia.org/w/api.php"
WIKI_PAGE = "Área metropolitana del Valle de Aburrá"
WIKI_HEADERS = {"User-Agent": "PredicSalarioIA/1.0 (github.com/LillianaU/predic-salario-ia)"}

FALLBACK_POPULATION = {
    "Barbosa": {"region": "Norte", "poblacion": 55969, "fuente": "DANE 2022"},
    "Girardota": {"region": "Norte", "poblacion": 63611, "fuente": "DANE 2022"},
    "Copacabana": {"region": "Norte", "poblacion": 74884, "fuente": "DANE 2022"},
    "Bello": {"region": "Centro", "poblacion": 532154, "fuente": "DANE 2022"},
    "Medellín": {"region": "Centro", "poblacion": 2533424, "fuente": "DANE 2022"},
    "Itagüí": {"region": "Centro", "poblacion": 276744, "fuente": "DANE 2022"},
    "Envigado": {"region": "Sur", "poblacion": 228848, "fuente": "DANE 2022"},
    "Sabaneta": {"region": "Sur", "poblacion": 79638, "fuente": "DANE 2022"},
    "La Estrella": {"region": "Sur", "poblacion": 70445, "fuente": "DANE 2022"},
    "Caldas": {"region": "Sur", "poblacion": 81275, "fuente": "DANE 2022"},
}

MUNICIPIOS_ORDER = [
    ("Norte", ["Barbosa", "Girardota", "Copacabana"]),
    ("Centro", ["Bello", "Medellín", "Itagüí"]),
    ("Sur", ["Envigado", "Sabaneta", "La Estrella", "Caldas"]),
]

KNOWN_MUNICIPIOS = set()
for _, munis in MUNICIPIOS_ORDER:
    KNOWN_MUNICIPIOS.update(munis)

# Also accept alternate names from Wikipedia links
WIKI_NAME_MAP = {
    "Bello (Antioquia)": "Bello",
    "Bello (Colombia)": "Bello",
    "Caldas (Antioquia)": "Caldas",
    "La Estrella (Antioquia)": "La Estrella",
    "La Estrella (Colombia)": "La Estrella",
    "Sabaneta (Antioquia)": "Sabaneta",
    "Sabaneta (Colombia)": "Sabaneta",
    "Copacabana (Antioquia)": "Copacabana",
    "Barbosa (Antioquia)": "Barbosa",
}


def fetch_population_from_wiki() -> Optional[Dict[str, dict]]:
    """Fetch population from Wikipedia HTML table."""
    try:
        resp = requests.get(
            WIKI_API,
            params={
                "action": "parse",
                "page": WIKI_PAGE,
                "prop": "text",
                "format": "json",
            },
            headers=WIKI_HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        html = resp.json().get("parse", {}).get("text", {}).get("*", "")
        if not html:
            return None

        result = {}
        # Find all <tr> rows
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.DOTALL)
        for row in rows:
            cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.DOTALL)
            if len(cells) < 4:
                continue

            # Clean each cell
            clean_cells = []
            for c in cells:
                text = re.sub(r"<[^>]+>", "", c).strip()
                text = text.replace("&nbsp;", " ").strip()
                clean_cells.append(text)

            # Check if first cell contains a known municipality
            municipio = None
            first_cell = clean_cells[0]
            for wiki_name, real_name in WIKI_NAME_MAP.items():
                if wiki_name in first_cell or real_name == first_cell:
                    municipio = real_name
                    break
            if not municipio and first_cell in KNOWN_MUNICIPIOS:
                municipio = first_cell

            if not municipio:
                continue

            # Find population: look for the largest number in the row
            # (population is always the largest numeric value)
            pop_value = 0
            for cell in clean_cells[1:]:
                # Remove dots used as thousands separators, keep digits
                nums = re.findall(r"[\d.]+", cell)
                for n in nums:
                    clean_n = n.replace(".", "")
                    if clean_n.isdigit():
                        val = int(clean_n)
                        if val > pop_value and val >= 10000:
                            pop_value = val

            if pop_value > 0:
                for region, municipios in MUNICIPIOS_ORDER:
                    if municipio in municipios:
                        result[municipio] = {
                            "region": region,
                            "poblacion": pop_value,
                            "fuente": "Wikipedia (DANE)",
                        }
                        break

        if result:
            logger.info(f"Fetched population for {len(result)} municipalities from Wikipedia")
            return result
        logger.warning("Could not parse population from Wikipedia")
        return None

    except Exception as e:
        logger.error(f"Failed to fetch from Wikipedia: {e}")
        return None


def get_population_data() -> Dict[str, dict]:
    """Get population: Wikipedia first, fallback to DANE 2022."""
    wiki_data = fetch_population_from_wiki()
    if wiki_data and len(wiki_data) >= 8:
        return wiki_data
    logger.info("Using fallback DANE 2022 population data")
    return FALLBACK_POPULATION.copy()


def format_population(pop: int) -> str:
    return f"{pop:,}".replace(",", ".")


def get_population_table_html(data: Dict[str, dict]) -> str:
    lines = ["| Región | Municipio | Población | Fuente |", "|---|---|---|---|"]
    for region, municipios in MUNICIPIOS_ORDER:
        for m in municipios:
            info = data.get(m, {})
            pop = info.get("poblacion", 0)
            fuente = info.get("fuente", "?")
            bold = "**" if m == "Medellín" else ""
            lines.append(f"| **{region}** | {bold}{m}{bold} | {format_population(pop)} | {fuente} |")
    return "\n".join(lines)
