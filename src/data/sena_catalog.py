"""
Catálogo de ocupaciones TI del Observatorio SENA (CNO/CUOC).
Clasificación Nacional de Ocupaciones - Grupo 2145, 2171, 2172, 2173, 2281, 2331.
+ Niveles de cualificación del mercado laboral por departamento.
"""

from typing import Dict, List, Tuple, Optional

# Niveles de cualificación del SENA (Hoja 2 del Excel)
QUALIFICATION_LEVELS = {
    "directivo": "Ocupaciones nivel directivo",
    "profesional": "Ocupaciones nivel profesional",
    "tecnico_tecnologo": "Ocupaciones nivel técnicos profesionales - tecnólogos",
    "calificado": "Ocupaciones nivel calificados",
    "elemental": "Ocupaciones nivel elemental",
}

# Ocupaciones TI organizadas por categoria del SENA CNO
SENA_OCCUPATIONS: Dict[str, List[Dict[str, str]]] = {
    "Gerentes y Directores TI": [
        {"codigo": "0013", "nombre": "Gerente general compañía servicios de informática", "cno": "0013"},
        {"codigo": "0123", "nombre": "Gerente servicios de informática", "cno": "0123"},
        {"codigo": "0213", "nombre": "Director departamento de informática", "cno": "0213"},
        {"codigo": "0213", "nombre": "Director sistemas informáticos", "cno": "0213"},
        {"codigo": "0213", "nombre": "Gerente sistemas de información y procesamiento de datos", "cno": "0213"},
    ],
    "Ingenieros de TI": [
        {"codigo": "2145", "nombre": "Ingeniero de sistemas e informática", "cno": "2145"},
        {"codigo": "2145", "nombre": "Ingeniero de software", "cno": "2145"},
        {"codigo": "2145", "nombre": "Ingeniero de desarrollo software", "cno": "2145"},
        {"codigo": "2145", "nombre": "Ingeniero de desarrollo informático", "cno": "2145"},
        {"codigo": "2145", "nombre": "Arquitecto de software", "cno": "2145"},
        {"codigo": "2145", "nombre": "Ingeniero de sistemas redes y comunicación de datos", "cno": "2145"},
        {"codigo": "2145", "nombre": "Auditor de TI", "cno": "2145"},
        {"codigo": "2145", "nombre": "Coordinador de proyecto informático", "cno": "2145"},
    ],
    "Analistas de Sistemas": [
        {"codigo": "2171", "nombre": "Analista de sistemas informáticos", "cno": "2171"},
        {"codigo": "2171", "nombre": "Analista sistemas informáticos aplicaciones", "cno": "2171"},
        {"codigo": "2171", "nombre": "Analista software", "cno": "2171"},
        {"codigo": "2171", "nombre": "Científico de datos", "cno": "2171"},
        {"codigo": "2171", "nombre": "Analista de datos", "cno": "2171"},
        {"codigo": "2171", "nombre": "Gestor de datos", "cno": "2171"},
        {"codigo": "2171", "nombre": "Ingeniero de big data y analítica", "cno": "2171"},
    ],
    "Administradores de TI": [
        {"codigo": "2172", "nombre": "Administrador seguridad informática", "cno": "2172"},
        {"codigo": "2172", "nombre": "Administrador sistemas informáticos", "cno": "2172"},
        {"codigo": "2172", "nombre": "Consultor seguridad informática", "cno": "2172"},
        {"codigo": "2172", "nombre": "Administrador de base de datos", "cno": "2172"},
        {"codigo": "2172", "nombre": "Administrador de red de datos", "cno": "2172"},
        {"codigo": "2172", "nombre": "Administrador de data center", "cno": "2172"},
    ],
    "Desarrolladores": [
        {"codigo": "2173", "nombre": "Programador aplicaciones informáticas", "cno": "2173"},
        {"codigo": "2173", "nombre": "Programador de software", "cno": "2173"},
        {"codigo": "2173", "nombre": "Desarrollador de aplicaciones informáticas", "cno": "2173"},
        {"codigo": "2173", "nombre": "Desarrollador de front-end", "cno": "2173"},
        {"codigo": "2173", "nombre": "Desarrollador de back-end", "cno": "2173"},
        {"codigo": "2173", "nombre": "Desarrollador full stack", "cno": "2173"},
        {"codigo": "2173", "nombre": "Desarrollador de sitios web", "cno": "2173"},
        {"codigo": "2173", "nombre": "Desarrollador de video juegos", "cno": "2173"},
        {"codigo": "2173", "nombre": "Líder de desarrollo ti", "cno": "2173"},
        {"codigo": "2173", "nombre": "Diseñador de soluciones de software", "cno": "2173"},
    ],
    "Técnicos en TI": [
        {"codigo": "2281", "nombre": "Técnico en sistemas informáticos", "cno": "2281"},
        {"codigo": "2281", "nombre": "Técnico en mantenimiento de red informática", "cno": "2281"},
        {"codigo": "2281", "nombre": "Tecnólogo en sistemas informáticos", "cno": "2281"},
        {"codigo": "2281", "nombre": "Tecnólogo en análisis y desarrollo de software", "cno": "2281"},
        {"codigo": "2281", "nombre": "Tecnólogo en gestión de redes de datos", "cno": "2281"},
        {"codigo": "2281", "nombre": "Técnico administrador de centro de datos", "cno": "2281"},
    ],
    "Soporte TI": [
        {"codigo": "2331", "nombre": "Auxiliar sistemas informáticos", "cno": "2331"},
        {"codigo": "2331", "nombre": "Instalador de programas informáticos", "cno": "2331"},
        {"codigo": "2331", "nombre": "Instalador de redes informáticas", "cno": "2331"},
        {"codigo": "2331", "nombre": "Operador servicio de asistencia informática", "cno": "2331"},
        {"codigo": "2331", "nombre": "Técnico soporte sistemas e informática", "cno": "2331"},
    ],
}


def get_categories() -> List[str]:
    """Devuelve la lista de categorías ocupacionales."""
    return list(SENA_OCCUPATIONS.keys())


def get_occupations_by_category(category: str) -> List[Dict[str, str]]:
    """Devuelve las ocupaciones de una categoría específica."""
    return SENA_OCCUPATIONS.get(category, [])


def match_occupation_to_category(occupation_text: str) -> str:
    """
    Intenta emparejar un texto de ocupación (del archivo subido) con una categoría SENA.
    Retorna la categoría o 'Otros' si no hay match.
    """
    import re
    text = occupation_text.lower().strip()

    category_keywords = {
        "Gerentes y Directores TI": [
            r"gerente", r"director", r"vp", r"vicepresidente", r"jefe.*sistema",
            r"jefe.*inform", r"jefe.*ti", r"líder.*ti", r"leader.*ti",
        ],
        "Ingenieros de TI": [
            r"ingeniero", r"engineer", r"arquitecto", r"architect",
            r"coordinador.*proyecto", r"auditor.*ti",
        ],
        "Analistas de Sistemas": [
            r"analista", r"analyst", r"científico.*dato", r"data scientist",
            r"business intelligence", r"\bbi\b", r"big data",
        ],
        "Administradores de TI": [
            r"administrador", r"administrator", r"consultor.*seguridad",
            r"dbadmin", r"admin.*base.*dato", r"admin.*red",
            r"data center",
        ],
        "Desarrolladores": [
            r"desarrollador", r"developer", r"programador", r"programmer",
            r"full.?stack", r"front.?end", r"back.?end", r"web.*develop",
            r"software.*develop", r"video.*juego",
        ],
        "Técnicos en TI": [
            r"técnic", r"technic", r"tecnólog", r"tecnolog",
            r"soporte", r"support", r"mantenimiento.*red",
        ],
        "Soporte TI": [
            r"soporte", r"help.*desk", r"service.*desk", r"instalador",
            r"auxiliar.*sist", r"operador.*asistencia",
        ],
    }

    for category, keywords in category_keywords.items():
        for kw in keywords:
            if re.search(kw, text):
                return category

    return "Otros"


def match_uploaded_data_to_sena(occupation_series) -> Dict[str, int]:
    """
    Recibe una serie de pandas con nombres de ocupación y retorna
    un conteo de cuántas filas pertenecen a cada categoría SENA.
    """
    import pandas as pd
    counts = {}
    for occ in occupation_series.dropna():
        cat = match_occupation_to_category(str(occ))
        counts[cat] = counts.get(cat, 0) + 1
    return counts


def get_recommended_occupations(selected_categories: List[str]) -> List[str]:
    """
    Dadas categorías seleccionadas, retorna las denominaciones
    ocupacionales recomendadas para filtrar datos.
    """
    recommended = []
    for cat in selected_categories:
        for occ in SENA_OCCUPATIONS.get(cat, []):
            recommended.append(occ["nombre"])
    return recommended


def parse_qualification_sheet(xl: 'pd.ExcelFile', sheet_name: str = None) -> Optional['pd.DataFrame']:
    """
    Parsea la hoja de niveles de cualificación del Excel del SENA.
    Soporta: 'Total nacional' y 'por Departamento' (con filtro Antioquia).
    Retorna un DataFrame con columnas normalizadas o None si no se puede parsear.
    """
    import pandas as pd

    if sheet_name is None:
        for name in xl.sheet_names:
            if "total" in name.lower() and "nacional" in name.lower():
                sheet_name = name
                break
        if sheet_name is None:
            for name in xl.sheet_names:
                if "departamento" in name.lower():
                    sheet_name = name
                    break
        if sheet_name is None and len(xl.sheet_names) > 0:
            sheet_name = xl.sheet_names[0]

    if sheet_name is None:
        return None

    try:
        df = pd.read_excel(xl, sheet_name=sheet_name, header=None)
    except Exception:
        return None

    level_keywords = {
        "nivel directivo": "directivo",
        "nivel profesional": "profesional",
        "nivel t": "tecnico_tecnologo",
        "nivel calificados": "calificado",
        "nivel calificado": "calificado",
        "nivel elemental": "elemental",
    }

    records = []
    current_level = None

    for idx, row in df.iterrows():
        row_str = " ".join(str(v).lower() for v in row.values if pd.notna(v))

        if "nivel de cualificaci" in row_str:
            continue

        for keyword, level_key in level_keywords.items():
            if keyword in row_str:
                current_level = level_key
                break

        if current_level is None:
            continue

        if "total inscritos en ocupaciones" in row_str:
            row_vals = [v if pd.notna(v) else 0 for v in row.iloc[3:15]]
            if len(row_vals) >= 12:
                try:
                    record = {
                        "nivel_cualificacion": current_level,
                        "nivel_nombre": QUALIFICATION_LEVELS.get(current_level, current_level),
                        "ocupacion": f"Total nivel {current_level}",
                        "inscritas_mujeres_2025": int(float(row_vals[0])) if row_vals[0] else 0,
                        "inscritos_hombres_2025": int(float(row_vals[1])) if row_vals[1] else 0,
                        "inscritas_mujeres_2026": int(float(row_vals[2])) if row_vals[2] else 0,
                        "inscritos_hombres_2026": int(float(row_vals[3])) if row_vals[3] else 0,
                        "participacion_mujeres_2025": float(row_vals[4]) if row_vals[4] else 0,
                        "participacion_hombres_2025": float(row_vals[5]) if row_vals[5] else 0,
                        "participacion_mujeres_2026": float(row_vals[6]) if row_vals[6] else 0,
                        "participacion_hombres_2026": float(row_vals[7]) if row_vals[7] else 0,
                        "variacion_mujeres": row_vals[8] if row_vals[8] else "0%",
                        "variacion_hombres": row_vals[9] if row_vals[9] else "0%",
                        "contribucion_mujeres": row_vals[10] if len(row_vals) > 10 and row_vals[10] else "0%",
                        "contribucion_hombres": row_vals[11] if len(row_vals) > 11 and row_vals[11] else "0%",
                    }
                    records.append(record)
                except (ValueError, IndexError):
                    continue

        col1_val = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
        if col1_val and col1_val.isdigit() and len(col1_val) == 4:
            row_vals = [v if pd.notna(v) else 0 for v in row.iloc[3:15]]
            if len(row_vals) >= 12:
                try:
                    record = {
                        "nivel_cualificacion": current_level,
                        "nivel_nombre": QUALIFICATION_LEVELS.get(current_level, current_level),
                        "ocupacion": f"CNO {col1_val}",
                        "codigo_cno": col1_val,
                        "nombre_ocupacion": str(row.iloc[2]) if pd.notna(row.iloc[2]) else "",
                        "inscritas_mujeres_2025": int(float(row_vals[0])) if row_vals[0] else 0,
                        "inscritos_hombres_2025": int(float(row_vals[1])) if row_vals[1] else 0,
                        "inscritas_mujeres_2026": int(float(row_vals[2])) if row_vals[2] else 0,
                        "inscritos_hombres_2026": int(float(row_vals[3])) if row_vals[3] else 0,
                        "participacion_mujeres_2025": float(row_vals[4]) if row_vals[4] else 0,
                        "participacion_hombres_2025": float(row_vals[5]) if row_vals[5] else 0,
                        "participacion_mujeres_2026": float(row_vals[6]) if row_vals[6] else 0,
                        "participacion_hombres_2026": float(row_vals[7]) if row_vals[7] else 0,
                        "variacion_mujeres": row_vals[8] if row_vals[8] else "0%",
                        "variacion_hombres": row_vals[9] if row_vals[9] else "0%",
                        "contribucion_mujeres": row_vals[10] if len(row_vals) > 10 and row_vals[10] else "0%",
                        "contribucion_hombres": row_vals[11] if len(row_vals) > 11 and row_vals[11] else "0%",
                    }
                    records.append(record)
                except (ValueError, IndexError):
                    continue

    if not records:
        return None

    return pd.DataFrame(records)


def compute_qualification_summary(qual_df: 'pd.DataFrame') -> Dict[str, Dict]:
    """
    Calcula resumen por nivel de cualificación.
    """
    import pandas as pd

    summary = {}
    for level in qual_df["nivel_cualificacion"].unique():
        level_data = qual_df[qual_df["nivel_cualificacion"] == level]
        summary[level] = {
            "nombre": level_data["nivel_nombre"].iloc[0] if len(level_data) > 0 else level,
            "total_mujeres_2026": int(level_data["inscritas_mujeres_2026"].sum()),
            "total_hombres_2026": int(level_data["inscritos_hombres_2026"].sum()),
            "total_mujeres_2025": int(level_data["inscritas_mujeres_2025"].sum()),
            "total_hombres_2025": int(level_data["inscritos_hombres_2025"].sum()),
            "total_2026": int(level_data["inscritas_mujeres_2026"].sum() + level_data["inscritos_hombres_2026"].sum()),
            "total_2025": int(level_data["inscritas_mujeres_2025"].sum() + level_data["inscritos_hombres_2025"].sum()),
        }
        total_2025 = summary[level]["total_2025"]
        total_2026 = summary[level]["total_2026"]
        if total_2025 > 0:
            summary[level]["variacion_pct"] = round((total_2026 - total_2025) / total_2025 * 100, 1)
        else:
            summary[level]["variacion_pct"] = 0

    return summary
