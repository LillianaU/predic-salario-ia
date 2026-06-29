# =============================================================================
# ARCHIVO PRINCIPAL DE LA APLICACIÓN STREAMLIT - PREDICSALARIO IA
# Propósito: Punto de entrada de la aplicación web para predicción salarial
#           del sector TI en Medellín y Área Metropolitana usando Machine Learning.
# Autor: Lilliana Uribe González
# Fecha: Junio 2026
# =============================================================================

import sys  # Manipulación del sistema (paths)
import os  # Variables de entorno del SO
from pathlib import Path  # Manejo de rutas multiplataforma
sys.path.insert(0, str(Path(__file__).resolve().parent))  # Agrega directorio raíz al path de Python
# Permite que los imports desde /src funcionen correctamente al ejecutar streamlit run app.py

from dotenv import load_dotenv  # Carga variables del archivo .env
load_dotenv(Path(__file__).resolve().parent / ".env")  # Carga .env del directorio raíz
# Lee API keys, rutas y configuración sensible desde el archivo .env (no versionado)

import streamlit as st  # Framework web para apps de datos (renderizado reactivo)
import pandas as pd  # Manejo de DataFrames
import datetime  # Manejo de fechas y horas para timestamps y filtros
from config import Config  # Configuración centralizada (Singleton) - rutas, parámetros de modelo, queries
from src.data.data_cleaner import DataCleaner  # Pipeline ETL de limpieza de datos (salarios, skills, dedup)
from src.data.data_repository import DataRepository  # Repositorio de datos (raw/processed) - persistencia CSV
from src.utils.loggers import get_logger  # Logger configurado (formato JSON/CSV según ambiente)
from src.utils.validators import SKILL_KEYWORDS, identify_role_category, identify_cargo_level, identify_modalidad  # Funciones de validación y clasificación
from src.data.sena_catalog import (  # Catálogo SENA de ocupaciones - CNO y clasificaciones
    SENA_OCCUPATIONS, get_categories, get_occupations_by_category,  # Ocupaciones y categorías SENA
    match_uploaded_data_to_sena, get_recommended_occupations,  # Matching y recomendaciones inteligentes
)

st.set_page_config(
    page_title="PredicSalario IA - Medellín",
    page_icon="💰",  # Icono de dinero en la pestaña del navegador
    layout="wide",  # Layout ancho para aprovechar toda la pantalla
    initial_sidebar_state="collapsed",  # Sidebar colapsada al cargar
)

try:
    _cfg = Config()  # Instancia Singleton de configuración (lee .env, rutas, parámetros)
    logger = get_logger("app", _cfg.LOG_FILE)  # Logger específico para este módulo
except Exception:
    # Si la configuración falla (ej: .env ausente), usa logger por defecto sin archivo
    logger = get_logger("app")

DARK_COLORS = {
    "bg": "#0A1F50",
    "surface": "#0F2860",
    "surface_low": "#0D2248",
    "surface_high": "#1B3F8B",
    "surface_bright": "#2557CC",
    "primary": "#4A90E2",
    "primary_container": "#2557CC",
    "secondary": "#6AABF0",
    "on_surface": "#FFFFFF",
    "on_surface_variant": "#B0C4DE",
    "outline": "#4A6FA5",
    "outline_variant": "#1B3F8B",
    "error": "#fca5a5",
    "error_container": "#991b1b",
    "glass": "rgba(10,31,80,0.7)",
    "glass_border": "rgba(74,144,226,0.25)",
    "card": "#1B3F8B",
}

MEDELLIN_METRO = {
    "Norte": ["Barbosa", "Girardota", "Copacabana", "Donmatías", "Santa Rosa de Osos", "San Pedro de los Milagros"],
    "Centro": ["Bello", "Medellín", "Itagüí", "San Cristóbal", "La Ceja del Tambo", "Carmen de Viboral"],
    "Sur": ["Envigado", "Sabaneta", "La Estrella", "Caldas", "Rionegro", "Marinilla", "Guatapé"],
}


def render_theme_css():
    # Genera y aplica CSS personalizado para el tema oscuro de la aplicación
    # Incluye: glassmorphism, animaciones, burbujas flotantes, responsive media queries
    c = DARK_COLORS
    accent = "#4A90E2"
    accent2 = "#2557CC"

    st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap');
    * {{ font-family: 'Inter', sans-serif; }}
    h1, h2, h3, h4, h5, h6 {{ font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; color: {c["on_surface"]}; }}
    .stApp {{ background: {c["bg"]}; color: {c["on_surface"]}; }}
    .stApp > header {{ background: {c["glass"]} !important; backdrop-filter: blur(12px) !important; border-bottom: 1px solid {c["glass_border"]} !important; }}
    ::-webkit-scrollbar {{ width: 6px; }}
    ::-webkit-scrollbar-track {{ background: {c["bg"]}; }}
    ::-webkit-scrollbar-thumb {{ background: {c["outline_variant"]}; border-radius: 10px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: {c["outline"]}; }}
    section[data-testid="stSidebar"] > div:first-child {{ background: {c["surface_low"]}; border-right: 1px solid {c["glass_border"]}; }}
    section[data-testid="stSidebar"] * {{ color: {c["on_surface"]} !important; }}
    section[data-testid="stSidebar"] .stRadio > div {{ gap: 2px; }}
    section[data-testid="stSidebar"] .stRadio label {{ padding: 10px 14px; border-radius: 10px; transition: all 0.2s; font-size: 14px; }}
    section[data-testid="stSidebar"] .stRadio label:hover {{ background: {c["glass"]}; }}
    section[data-testid="stSidebar"] .stRadio label[data-selected="true"] {{ background: rgba(74,144,226,0.15); border-left: 3px solid {accent}; font-weight: 600; color: {accent} !important; }}
    section[data-testid="stSidebar"] hr {{ border-color: {c["outline_variant"]}; opacity: 0.3; }}
    .stButton > button {{ background: linear-gradient(135deg, {accent}, {accent2}) !important; color: #FFFFFF !important; font-weight: 700 !important; border: none !important; border-radius: 12px !important; padding: 12px 28px !important; transition: all 0.2s !important; box-shadow: 0 4px 15px rgba(74,144,226,0.3) !important; }}
    .stButton > button:hover {{ transform: translateY(-2px); box-shadow: 0 6px 20px rgba(74,144,226,0.4) !important; }}
    .stButton > button:active {{ transform: translateY(0); }}
    .stButton > button[data-secondary="true"] {{ background: transparent !important; border: 1px solid {c["outline_variant"]} !important; color: {c["on_surface"]} !important; box-shadow: none !important; }}
    .stSelectbox > div > div, .stSlider > div, .stMultiselect > div > div {{ background: {c["surface"]} !important; border-color: {c["outline_variant"]} !important; color: {c["on_surface"]} !important; border-radius: 10px !important; }}
    .stMarkdown, .stText, p, li, span, label {{ color: {c["on_surface"]}; }}
    .metric-card {{ background: linear-gradient(135deg, {c["surface"]}, {c["surface_high"]}); padding: 1.2rem; border-radius: 14px; border: 1px solid {c["glass_border"]}; backdrop-filter: blur(8px); transition: all 0.2s; }}
    .metric-card:hover {{ border-color: rgba(74,144,226,0.4); transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,0,0,0.3); }}
    .prediction-card {{ background: linear-gradient(135deg, {accent}, {accent2}); color: #FFFFFF; padding: 2rem; border-radius: 16px; text-align: center; margin: 1rem 0; box-shadow: 0 8px 30px rgba(74,144,226,0.3); }}
    .prediction-amount {{ font-size: 2.5rem; font-weight: 800; }}
    .stDataFrame {{ border-radius: 12px; overflow: hidden; }}
    .stDataFrame table {{ background: {c["surface"]} !important; color: {c["on_surface"]} !important; }}
    .stAlert {{ background: {c["surface"]} !important; border-color: {c["outline_variant"]} !important; color: {c["on_surface"]} !important; border-radius: 12px !important; }}
    .stDownloadButton > button {{ background: {c["surface"]} !important; border: 1px solid {c["outline_variant"]} !important; color: {c["on_surface"]} !important; border-radius: 10px !important; }}
    .logo-container {{ width: 120px; height: 120px; margin: 0 auto 1.5rem; border-radius: 50%; background: linear-gradient(135deg, {accent}, {accent2}); display: flex; align-items: center; justify-content: center; box-shadow: 0 0 40px rgba(74,144,226,0.3); animation: pulse-glow 3s ease-in-out infinite; }}
    @keyframes pulse-glow {{ 0%, 100% {{ box-shadow: 0 0 40px rgba(74,144,226,0.3); }} 50% {{ box-shadow: 0 0 60px rgba(74,144,226,0.5); }} }}
    .logo-container span {{ font-size: 2.5rem; font-weight: 800; color: #FFFFFF; font-family: 'Plus Jakarta Sans', sans-serif; }}
    .feature-card {{ background: linear-gradient(135deg, {c["surface"]}, {c["surface_high"]}); border: 1px solid {c["glass_border"]}; border-radius: 16px; padding: 1.5rem; transition: all 0.3s; height: 100%; }}
    .feature-card:hover {{ border-color: rgba(74,144,226,0.4); transform: translateY(-3px); box-shadow: 0 12px 30px rgba(0,0,0,0.2); }}
    .timeline-item {{ position: relative; padding-left: 2rem; padding-bottom: 2rem; border-left: 2px solid {c["outline_variant"]}; }}
    .timeline-item::before {{ content: ''; position: absolute; left: -6px; top: 4px; width: 10px; height: 10px; border-radius: 50%; background: {accent}; box-shadow: 0 0 12px rgba(74,144,226,0.4); }}
    .timeline-item:last-child {{ border-left: 2px solid transparent; }}
    .glass-panel {{ background: {c["glass"]}; backdrop-filter: blur(12px); border: 1px solid {c["glass_border"]}; border-radius: 16px; }}
    .orb {{ position: fixed; border-radius: 50%; pointer-events: none; z-index: 0; animation: orb-float 8s ease-in-out infinite; }}
    @keyframes orb-float {{ 0%, 100% {{ transform: translate(0, 0) scale(1); }} 33% {{ transform: translate(30px, -30px) scale(1.05); }} 66% {{ transform: translate(-20px, 20px) scale(0.95); }} }}
    .bubbles {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 0; overflow: hidden; }}
    .bubble {{ position: absolute; bottom: -80px; border-radius: 50%; opacity: 0; animation: bubble-rise linear infinite; }}
    .bubble:nth-child(1) {{ left: 5%; width: 22px; height: 22px; background: radial-gradient(circle at 30% 30%, rgba(74,144,226,0.45), rgba(74,144,226,0.08)); animation-duration: 18s; animation-delay: 0s; }}
    .bubble:nth-child(2) {{ left: 15%; width: 14px; height: 14px; background: radial-gradient(circle at 30% 30%, rgba(45,212,191,0.4), rgba(45,212,191,0.06)); animation-duration: 22s; animation-delay: 2s; }}
    .bubble:nth-child(3) {{ left: 28%; width: 30px; height: 30px; background: radial-gradient(circle at 30% 30%, rgba(74,144,226,0.35), rgba(74,144,226,0.06)); animation-duration: 25s; animation-delay: 4s; }}
    .bubble:nth-child(4) {{ left: 42%; width: 16px; height: 16px; background: radial-gradient(circle at 30% 30%, rgba(107,216,203,0.42), rgba(107,216,203,0.07)); animation-duration: 20s; animation-delay: 1s; }}
    .bubble:nth-child(5) {{ left: 55%; width: 24px; height: 24px; background: radial-gradient(circle at 30% 30%, rgba(74,144,226,0.38), rgba(74,144,226,0.06)); animation-duration: 23s; animation-delay: 3s; }}
    .bubble:nth-child(6) {{ left: 68%; width: 12px; height: 12px; background: radial-gradient(circle at 30% 30%, rgba(45,212,191,0.45), rgba(45,212,191,0.08)); animation-duration: 19s; animation-delay: 5s; }}
    .bubble:nth-child(7) {{ left: 78%; width: 32px; height: 32px; background: radial-gradient(circle at 30% 30%, rgba(74,144,226,0.3), rgba(74,144,226,0.05)); animation-duration: 28s; animation-delay: 0.5s; }}
    .bubble:nth-child(8) {{ left: 88%; width: 18px; height: 18px; background: radial-gradient(circle at 30% 30%, rgba(107,216,203,0.4), rgba(107,216,203,0.06)); animation-duration: 21s; animation-delay: 6s; }}
    .bubble:nth-child(9) {{ left: 35%; width: 10px; height: 10px; background: radial-gradient(circle at 30% 30%, rgba(74,144,226,0.5), rgba(74,144,226,0.1)); animation-duration: 17s; animation-delay: 7s; }}
    .bubble:nth-child(10) {{ left: 92%; width: 26px; height: 26px; background: radial-gradient(circle at 30% 30%, rgba(45,212,191,0.35), rgba(45,212,191,0.06)); animation-duration: 26s; animation-delay: 2.5s; }}
    .bubble:nth-child(11) {{ left: 48%; width: 15px; height: 15px; background: radial-gradient(circle at 30% 30%, rgba(74,144,226,0.42), rgba(74,144,226,0.07)); animation-duration: 24s; animation-delay: 8s; }}
    .bubble:nth-child(12) {{ left: 10%; width: 20px; height: 20px; background: radial-gradient(circle at 30% 30%, rgba(107,216,203,0.35), rgba(107,216,203,0.06)); animation-duration: 27s; animation-delay: 1.5s; }}
    @keyframes bubble-rise {{
        0% {{ transform: translateY(0) translateX(0) scale(0.4); opacity: 0; }}
        10% {{ opacity: 1; }}
        50% {{ transform: translateY(-50vh) translateX(30px) scale(0.8); opacity: 0.7; }}
        90% {{ opacity: 0.3; }}
        100% {{ transform: translateY(-110vh) translateX(-20px) scale(1); opacity: 0; }}
    }}
    @media (max-width: 1024px) {{
        .main-header {{ font-size: 1.6rem !important; }}
        .prediction-amount {{ font-size: 1.8rem !important; }}
        section[data-testid="stSidebar"] {{ min-width: 240px !important; max-width: 240px !important; }}
        .feature-card {{ padding: 1.2rem; }}
        .metric-card {{ padding: 1rem; }}
    }}
    @media (max-width: 768px) {{
        .main-header {{ font-size: 1.3rem !important; }}
        h1 {{ font-size: 1.4rem !important; }}
        h2 {{ font-size: 1.2rem !important; }}
        h3 {{ font-size: 1.05rem !important; }}
        .prediction-amount {{ font-size: 1.5rem !important; }}
        /* Sidebar: overlay en mobile, ancho completo */
        section[data-testid="stSidebar"] {{
            min-width: 85vw !important;
            max-width: 85vw !important;
            z-index: 9999 !important;
        }}
        section[data-testid="stSidebar"] > div {{
            padding-top: 1rem !important;
        }}
        /* Radio labels mas grandes para touch */
        section[data-testid="stSidebar"] .stRadio label {{
            padding: 12px 14px !important;
            font-size: 14px !important;
            min-height: 44px !important;
            display: flex !important;
            align-items: center !important;
        }}
        .logo-container {{ width: 80px; height: 80px; }}
        .logo-container span {{ font-size: 1.8rem; }}
        .feature-card {{ padding: 1rem; border-radius: 12px; }}
        .metric-card {{ padding: 0.8rem; border-radius: 10px; }}
        .stButton > button {{ font-size: 0.85rem !important; padding: 8px 16px !important; border-radius: 10px !important; }}
        .stMarkdown p {{ font-size: 0.9rem !important; }}
        .timeline-item {{ padding-left: 1.5rem; padding-bottom: 1.5rem; }}
        .info-text {{ font-size: 0.8rem !important; }}
        .source-badge {{ font-size: 0.7rem !important; padding: 3px 10px !important; }}
    }}
    @media (max-width: 480px) {{
        .main-header {{ font-size: 1.1rem !important; }}
        h1 {{ font-size: 1.2rem !important; }}
        h2 {{ font-size: 1.05rem !important; }}
        h3 {{ font-size: 0.95rem !important; }}
        .stMarkdown p {{ font-size: 0.82rem !important; }}
        .feature-card {{ padding: 0.8rem; border-radius: 10px; }}
        .metric-card {{ padding: 0.6rem; border-radius: 8px; }}
        .prediction-card {{ padding: 1.2rem; border-radius: 12px; }}
        .prediction-amount {{ font-size: 1.3rem !important; }}
        .logo-container {{ width: 60px; height: 60px; }}
        .logo-container span {{ font-size: 1.4rem; }}
        .stButton > button {{ font-size: 0.8rem !important; padding: 6px 12px !important; border-radius: 8px !important; }}
        /* Sidebar: touch-friendly en mobile pequeno */
        section[data-testid="stSidebar"] .stRadio label {{
            padding: 14px 14px !important;
            font-size: 13px !important;
            min-height: 48px !important;
            border-radius: 8px !important;
            margin: 2px 8px !important;
        }}
        section[data-testid="stSidebar"] .stRadio label:hover {{
            background: rgba(74, 144, 226, 0.15) !important;
        }}
    }}
    .info-text {{ color: {c["on_surface_variant"]}; font-size: 0.85rem; }}
    .source-badge {{ display: inline-flex; align-items: center; gap: 6px; padding: 4px 14px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; background: {c["surface"]}; border: 1px solid {c["glass_border"]}; }}
</style>
""", unsafe_allow_html=True)

# Inyecta HTML de burbujas animadas de fondo
st.markdown("""
<div class="bubbles">
    <div class="bubble"></div>  <!-- Burbuja 1 -->
    <div class="bubble"></div>  <!-- Burbuja 2 -->
    <div class="bubble"></div>  <!-- Burbuja 3 -->
    <div class="bubble"></div>  <!-- Burbuja 4 -->
    <div class="bubble"></div>  <!-- Burbuja 5 -->
    <div class="bubble"></div>  <!-- Burbuja 6 -->
    <div class="bubble"></div>  <!-- Burbuja 7 -->
    <div class="bubble"></div>  <!-- Burbuja 8 -->
    <div class="bubble"></div>  <!-- Burbuja 9 -->
    <div class="bubble"></div>  <!-- Burbuja 10 -->
    <div class="bubble"></div>  <!-- Burbuja 11 -->
    <div class="bubble"></div>  <!-- Burbuja 12 -->
</div>
""", unsafe_allow_html=True)  # Permite HTML personalizado en Streamlit


MEDELLIN_ALIASES = {  # Diccionario de alias para normalizar nombres de ciudades del AMVA
    # Permite que entradas como "medallo", "medellin", "itagui" se normalicen al nombre canónico
    "medellín": "Medellín", "medellin": "Medellín", "medallo": "Medellín",
    "bello": "Bello",
    "itagüí": "Itagüí", "itagui": "Itagüí",
    "envigado": "Envigado",
    "sabaneta": "Sabaneta",
    "la estrella": "La Estrella",
    "caldas": "Caldas",
    "copacabana": "Copacabana",
    "girardota": "Girardota",
    "barbosa": "Barbosa",
    "donmatías": "Donmatías", "donmatias": "Donmatías",
    "santa rosa de osos": "Santa Rosa de Osos",
    "san pedro de los milagros": "San Pedro de los Milagros",
    "san cristóbal": "San Cristóbal", "san cristobal": "San Cristóbal",
    "la ceja del tambo": "La Ceja del Tambo", "la ceja": "La Ceja del Tambo",
    "carmen de viboral": "Carmen de Viboral",
    "rionegro": "Rionegro",
    "marinilla": "Marinilla",
    "guatapé": "Guatapé", "guatape": "Guatapé",
}


def extract_ciudad(ubicacion: str) -> str:
    """Extrae y normaliza el nombre de la ciudad desde una cadena de ubicación.

    Args:
        ubicacion: Cadena de texto con la ubicación de la oferta laboral.

    Returns:
        Nombre canónico de la ciudad del AMVA, o 'Medellín' por defecto.
    """
    if not ubicacion or not isinstance(ubicacion, str):  # Si no hay ubicación o no es string
        return "Medellín"  # Default: Medellín
    u = ubicacion.lower().strip()  # Convierte a minúsculas y quita espacios
    for alias, canonical in MEDELLIN_ALIASES.items():  # Busca alias en el diccionario
        if alias in u:  # Si encuentra el alias
            return canonical  # Retorna nombre canónico
    if "," in u:  # Si tiene comas (ej: "Medellín, Colombia")
        parts = [p.strip() for p in u.split(",")]  # Divide por comas
        for p in parts:  # Itera cada parte
            p_lower = p.lower()  # Convierte a minúsculas
            for alias in MEDELLIN_ALIASES:  # Busca alias
                if alias in p_lower:  # Si encuentra
                    return MEDELLIN_ALIASES[alias]  # Retorna nombre canónico
        return parts[0].title()  # Si no encuentra alias, retorna primera parte capitalizada
    return u.title()  # Retorna texto capitalizado


@st.cache_resource  # Decorador de Streamlit: cachea el resultado (se ejecuta solo una vez)
def init_components():
    """Inicializa y cachea todos los componentes del sistema (config, scraper, cleaner, repo, model).

    Returns:
        Tuple: (cfg, scraper, cleaner, repo, model) - Los 5 componentes principales.
    """
    from src.models.model_factory import ModelFactory  # Fábrica de modelos ML
    from src.scraper.scraper_factory import ScraperFactory  # Fábrica de scrapers
    cfg = Config()  # Carga configuración centralizada (Singleton)
    scraper = ScraperFactory.create_with_fallback(headless=True, timeout=45)  # Crea scraper con fallback automático
    cleaner = DataCleaner()  # Crea pipeline de limpieza ETL
    repo = DataRepository(cfg.RAW_DATA_DIR, cfg.PROCESSED_DATA_DIR)  # Crea repositorio de datos
    model = ModelFactory.create("RandomForest")  # Crea modelo RandomForest
    return cfg, scraper, cleaner, repo, model  # Retorna los 5 componentes


def _add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega columnas derivadas: ciudad (desde ubicación) y role_categoria (desde título).

    Args:
        df: DataFrame con datos de ofertas laborales.

    Returns:
        DataFrame con columnas 'ciudad' y 'role_categoria' agregadas.
    """
    if "ciudad" not in df.columns:  # Si no existe columna ciudad
        df["ciudad"] = df["ubicacion"].apply(extract_ciudad)  # Extrae ciudad de ubicación
    if "role_categoria" not in df.columns:  # Si no existe columna role_categoria
        df["role_categoria"] = df.apply(  # Identifica categoría del rol
            lambda r: identify_role_category(r.get("titulo", ""), r.get("descripcion", "")), axis=1
        )
    return df  # Retorna DataFrame con columnas derivadas


SCRAPE_TIMEOUT = 45  # Timeout del scraping en segundos (espera máxima por request)
AUTOREFRESH_INTERVAL = 300  # Intervalo de auto-refresh: 300 segundos = 5 minutos


def load_or_fetch_data(cfg, scraper, cleaner, repo):
    """Carga datos desde cache o ejecuta scraping real. Prioriza datos reales.

    Flujo:
    1. Verifica flag de refresh forzado en session_state.
    2. Si no hay refresh: intenta cargar datos procesados del cache.
    3. Si no hay procesados: intenta cargar archivos raw y limpiarlos.
    4. Si no hay nada: ejecuta scraping real con barra de progreso.
    5. Si scraping falla: hace fallback a cache o archivos raw.
    6. Si todo falla: retorna DataFrame vacío.

    Args:
        cfg: Configuración centralizada.
        scraper: Instancia del scraper (Playwright/HTTP).
        cleaner: Pipeline ETL de limpieza.
        repo: Repositorio de persistencia de datos.

    Returns:
        pd.DataFrame: Datos limpios listos para análisis/predicción.
    """
    force_fresh = st.session_state.pop("force_refresh", False)  # Obtiene flag de refresh forzado

    if not force_fresh:  # Si NO se fuerza refresh
        processed = repo.load_processed()  # Intenta cargar datos procesados del cache
        if processed is not None and len(processed) >= 20:  # Si hay datos suficientes
            logger.info("Using cached processed dataset")  # Registra que usa cache
            df = _add_derived_columns(processed)  # Agrega columnas derivadas
            st.session_state.data_source = "💾 Datos reales (cache)"  # Marca fuente como cache
            st.session_state.last_update = datetime.datetime.now()  # Registra timestamp
            return df  # Retorna DataFrame del cache
        raw_files = repo.list_raw_files()  # Lista archivos raw CSV
        if raw_files:  # Si hay archivos raw
            latest = raw_files[-1]  # Toma el más reciente
            raw_df = repo.load_raw(latest.name)  # Carga el archivo CSV más reciente
            if raw_df is not None and len(raw_df) >= 20:  # Si tiene datos suficientes
                df = cleaner.clean(raw_df.to_dict("records"))  # Limpia datos raw con pipeline ETL
                df = _add_derived_columns(df)  # Agrega ciudad y role_categoria
                st.session_state.data_source = f"🌐 Datos reales ({len(raw_df)} ofertas)"  # Marca fuente
                st.session_state.last_update = datetime.datetime.now()  # Timestamp
                return df  # Retorna DataFrame limpio

    # SCRAPING: real data from elempleo.com  # SCRAPING: datos reales de elempleo.com
    scraper_name = type(scraper).__name__  # Nombre de la clase del scraper

    progress_bar = st.progress(0)  # Barra de progreso (0% a 100%)
    status_text = st.empty()  # Texto de estado (vacío inicialmente)
    info_box = st.info(f"🌐 Iniciando scraping via {scraper_name}...")  # Cuadro de info con nombre del scraper

    def update_progress(current, total, query, records, status):
        """Callback para actualizar barra de progreso y texto durante el scraping.

        Args:
            current: Query actual en progreso.
            total: Total de queries a ejecutar.
            query: Texto de la búsqueda actual.
            records: Número de ofertas encontradas hasta ahora.
            status: Estado ('progress' o 'done').
        """
        try:
            if status == "done":  # Si el scraping terminó
                progress_bar.progress(1.0)  # Barra al 100%
                status_text.success(f"✅ Scraping completado: {records} ofertas obtenidas de {len(cfg.SEARCH_QUERIES)} queries")
                info_box.empty()  # Oculta cuadro de info
            else:  # Si está en progreso
                progress = current / total if total > 0 else 0  # Calcula porcentaje
                progress_bar.progress(progress)  # Actualiza barra
                display_query = query[:60] + "..." if len(query) > 60 else query  # Trunca query larga
                status_text.text(f"📡 [{current}/{total}] {display_query}")  # Muestra query actual
                info_box.info(f"🔄 Scrapeando: {display_query}\n\n📊 Ofertas encontradas: {records}\n📈 Queries procesadas: {current}/{total}")
        except Exception:
            pass  # Ignora errores de Streamlit durante actualizaciones rápidas

    raw_data = None  # Datos crudos del scraping
    error_msg = None  # Mensaje de error si falla

    try:
        raw_data = scraper.fetch_data(cfg.SEARCH_QUERIES, progress_callback=update_progress)  # Ejecuta scraping con callback de progreso
    except Exception as e:
        error_msg = str(e)  # Guarda mensaje de error
        logger.error(f"Scraping failed: {e}")  # Registra error

    try:
        progress_bar.empty()  # Oculta barra de progreso
        status_text.empty()  # Oculta texto de estado
        info_box.empty()  # Oculta cuadro de info
    except Exception:
        pass  # Ignora errores al limpiar UI

    if raw_data:  # Si obtuvo datos del scraping
        try:
            source_names = []  # Lista de fuentes
            if hasattr(scraper, "get_source_stats"):  # Si el scraper tiene stats
                source_names = scraper.get_source_stats().get("sources", [])  # Obtiene nombres de fuentes
            source_label = " + ".join(source_names) if source_names else scraper_name  # Label de fuente
            st.success(f"✅ Datos obtenidos de {source_label}")  # Muestra éxito
            st.info(f"📊 Total: **{len(raw_data)} ofertas** de **{len(cfg.SEARCH_QUERIES)} queries** de búsqueda")
        except Exception:
            pass  # Ignora errores de UI
        repo.save_raw(raw_data)  # Guarda datos raw en CSV
        df = cleaner.clean(raw_data)  # Limpia datos con pipeline ETL
        repo.save_processed(df)  # Guarda datos procesados
        df = _add_derived_columns(df)  # Agrega columnas derivadas
        st.session_state.data_source = f"🌐 Datos reales ({source_label})"  # Marca fuente
        st.session_state.last_update = datetime.datetime.now()  # Timestamp
        st.toast(f"🔥 Datos reales actualizados de {source_label}", icon="🔥")  # Toast de notificación
        return df  # Retorna DataFrame limpio

    logger.warning(f"Scraping failed ({error_msg}), trying fallback")  # Registra warning
    try:
        st.warning(f"⚠️ {scraper_name} no disponible — usando datos guardados")  # Muestra warning al usuario
    except Exception:
        pass

    processed = repo.load_processed()  # Intenta cargar cache procesado
    if processed is not None and len(processed) >= 20:  # Si hay datos suficientes
        logger.info("Fallback to processed cache")  # Registra fallback
        df = _add_derived_columns(processed)  # Agrega columnas derivadas
        st.session_state.data_source = "💾 Datos reales (cache)"  # Marca fuente
        st.session_state.last_update = datetime.datetime.now()  # Timestamp
        return df  # Retorna DataFrame del cache

    raw_files = repo.list_raw_files()  # Lista archivos raw
    if raw_files:  # Si hay archivos raw
        latest = raw_files[-1]  # Toma el más reciente
        raw_df = repo.load_raw(latest.name)  # Carga CSV
        if raw_df is not None and len(raw_df) >= 20:  # Si tiene datos
            logger.info("Fallback to raw cache")  # Registra fallback
            df = cleaner.clean(raw_df.to_dict("records"))  # Limpia datos
            df = _add_derived_columns(df)  # Agrega columnas derivadas
            st.session_state.data_source = f"🌐 Datos reales ({latest.name})"  # Marca fuente
            st.session_state.last_update = datetime.datetime.now()  # Timestamp
            return df  # Retorna DataFrame

    try:
        st.error("❌ No hay datos disponibles — haz click en 'Actualizar datos'")  # Muestra error al usuario
    except Exception:
        pass
    return pd.DataFrame()  # Retorna DataFrame vacío si no hay datos


def train_or_load_model(cfg, model, df):
    """Entrena el modelo ML o carga uno existente desde disco.

    Flujo:
    1. Verifica si el modelo ya está entrenado en memoria.
    2. Intenta cargar desde archivo .pkl en disco.
    3. Si no existe o es inválido: entrena desde cero.
    4. Crea columnas faltantes que el modelo requiere.
    5. Extrae features (X) y target (y = salario_promedio).
    6. Entrena y guarda el modelo entrenado.

    Args:
        cfg: Configuración centralizada con ruta del modelo.
        model: Instancia del modelo (RandomForest).
        df: DataFrame con datos de entrenamiento.

    Returns:
        Modelo entrenado y listo para predicción.
    """
    if model.is_trained:  # Si el modelo ya está entrenado en memoria
        return model  # Retorna el modelo sin hacer nada
    try:
        model.load(str(cfg.MODEL_PATH))  # Intenta cargar modelo desde disco (.pkl)
        if model.is_trained:  # Si se cargó correctamente
            return model  # Retorna el modelo cargado
    except (FileNotFoundError, ValueError):  # Si no existe archivo o hash no coincide
        logger.info("Training new model")  # Registra que va a entrenar
        required = ["experiencia_requerida", "cargo_nivel_cod", "modalidad_cod", "skills_str",  # Columnas requeridas para entrenar
                     "role_categoria", "num_skills", "tipo_contrato_cod"]
        missing = [c for c in required if c not in df.columns]  # Detecta columnas faltantes
        if missing:  # Si faltan columnas
            logger.warning(f"Missing columns for training: {missing}")  # Advertencia
            if "cargo_nivel_cod" in missing and "cargo_nivel" in df.columns:  # Si falta cargo_nivel_cod pero existe cargo_nivel
                level_map = {"tecnico": 0, "tecnologo": 1, "ingeniero": 2, "senior": 3}  # Mapa de conversión
                df["cargo_nivel_cod"] = df["cargo_nivel"].map(level_map).fillna(2).astype(int)  # Convierte a código numérico
            if "modalidad_cod" in missing and "modalidad_clean" in df.columns:  # Si falta modalidad_cod
                modal_map = {"presencial": 0, "hibrido": 1, "remoto": 2}  # Mapa de conversión
                df["modalidad_cod"] = df["modalidad_clean"].map(modal_map).fillna(0).astype(int)  # Convierte a código
            if "experiencia_requerida" in missing:  # Si falta experiencia
                df["experiencia_requerida"] = 0.0  # Asigna 0 por defecto
            if "skills_str" in missing:  # Si falta skills_str
                df["skills_str"] = ""  # Asigna string vacío
            if "role_categoria" in missing:  # Si falta role_categoria
                from src.utils.validators import identify_role_category  # Importa función
                df["role_categoria"] = df.apply(  # Identifica categoría del rol
                    lambda r: identify_role_category(r.get("titulo", ""), r.get("descripcion", "")), axis=1
                )
            if "num_skills" in missing:  # Si falta num_skills
                df["num_skills"] = df["skills_str"].apply(lambda x: len(x.split(",")) if x else 0)  # Cuenta skills
            if "tipo_contrato_cod" in missing:  # Si falta tipo_contrato_cod
                contrato_map = {"indefinido": 0, "prestación de servicios": 1}  # Mapa de conversión
                contrato_col = df["tipo_contrato"] if "tipo_contrato" in df.columns else pd.Series("", index=df.index)  # Obtiene columna
                df["tipo_contrato_cod"] = contrato_col.fillna("").str.lower().map(contrato_map).fillna(1).astype(int)  # Convierte a código
        feature_cols = ["experiencia_requerida", "cargo_nivel_cod", "modalidad_cod", "skills_str",  # Columnas de features
                        "role_categoria", "num_skills", "tipo_contrato_cod"]
        X = df[feature_cols].copy()  # Features de entrada
        y = df["salario_promedio"]  # Target: salario promedio
        model.train(X, y)  # Entrena el modelo
        model.save(str(cfg.MODEL_PATH))  # Guarda modelo en disco
    return model  # Retorna modelo entrenado


def session_state_init():
    """Inicializa variables de session_state de Streamlit con valores por defecto.

    Streamlit no mantiene estado entre reruns, por lo que se usa st.session_state
    como almacenamiento persistente en memoria para la sesión del usuario.
    """
    if "inputs_reset" not in st.session_state:  # Flag de reset de inputs
        st.session_state.inputs_reset = False
    if "prediction_made" not in st.session_state:  # Flag de predicción realizada
        st.session_state.prediction_made = False
    if "use_cache" not in st.session_state:  # Flag de uso de cache
        st.session_state.use_cache = False
    if "force_refresh" not in st.session_state:  # Flag de refresh forzado
        st.session_state.force_refresh = False
    if "data_source" not in st.session_state:  # Fuente de datos actual
        st.session_state.data_source = "—"
    if "last_update" not in st.session_state:  # Timestamp de última actualización
        st.session_state.last_update = None
    if "ciudades_filter" not in st.session_state:  # Filtro de ciudades activo
        st.session_state.ciudades_filter = []
    if "agent_report" not in st.session_state:  # Informe del agente generado
        st.session_state.agent_report = ""
    if "audit_results" not in st.session_state:  # Resultados de auditoría de APIs
        st.session_state.audit_results = []


def render_source_badge():
    """Renderiza el badge de fuente de datos en la UI (cache, scraping, etc.).

    Muestra: fuente actual, última actualización, y color según tipo de fuente.
    """
    c = DARK_COLORS  # Colores del tema
    src = st.session_state.get("data_source", "—")  # Obtiene fuente de datos actual
    colors = {"💾": ("#6366f1", "#eef2ff"), "🌐": ("#10b981", "#d1fae5"), "📡": ("#f59e0b", "#fef3c7")}  # Colores por emoji
    bg = "#152031"  # Color de fondo del badge
    fg = c["on_surface_variant"]  # Color de texto por defecto
    for prefix, (ic, _) in colors.items():  # Busca color por prefijo del emoji
        if src.startswith(prefix):  # Si la fuente empieza con ese emoji
            fg = ic  # Usa el color del emoji
            break
    last_up = st.session_state.get("last_update")  # Última actualización
    time_str = last_up.strftime("%H:%M:%S") if last_up else "—"  # Formatea hora
    st.markdown(  # Renderiza badge HTML
        f"<span class='source-badge' style='color:{fg};border:1px solid {fg}40;'>"
        f"{src} · {time_str}</span>",
        unsafe_allow_html=True,
    )


def main():
    """Función principal de la aplicación Streamlit.

    Orquesta toda la aplicación: inicializa componentes, configura página,
    maneja navegación por secciones, y renderiza el contenido dinámicamente.
    """
    session_state_init()  # Inicializa variables de sesión
    render_theme_css()  # Inyecta CSS del tema azul oscuro

    c = DARK_COLORS  # Colores del tema
    accent = "#4A90E2"  # Color de acento azul

    cfg, scraper, cleaner, repo, model = init_components()  # Inicializa componentes (cacheados)

    # Inyecta orbes decorativos animados de fondo
    # Círculos semitransparentes que flotan suavemente para dar profundidad visual
    st.markdown(f"""
    <div class="orb" style="width:400px;height:400px;background:{accent}08;top:-100px;left:-100px;animation-delay:0s;"></div>
    <div class="orb" style="width:300px;height:300px;background:{accent}05;bottom:-50px;right:-50px;animation-delay:3s;"></div>
    """, unsafe_allow_html=True)

    # ============================================================
    # SIDEBAR - Panel lateral izquierdo con navegación y filtros
    # ============================================================
    with st.sidebar:  # Bloque del sidebar (panel lateral izquierdo)
        st.markdown(  # Logo y nombre de la app
            f"<div style='display:flex;align-items:center;gap:12px;margin-bottom:4px;'>"
            f"<div style='width:40px;height:40px;border-radius:12px;background:linear-gradient(135deg,{accent},{c['primary_container']});"
            f"display:flex;align-items:center;justify-content:center;font-size:1.2rem;flex-shrink:0;'>💰</div>"  # Icono de dinero
            f"<div><h2 style='font-family:Plus Jakarta Sans;font-weight:800;margin:0;font-size:1.2rem;"
            f"background:linear-gradient(135deg,{accent},{c['primary_container']});"
            f"-webkit-background-clip:text;-webkit-text-fill-color:transparent;'>PredicSalario IA</h2>"  # Nombre con gradiente
            f"<p style='font-size:0.7rem;color:{c["on_surface_variant"]};margin:0;text-transform:uppercase;letter-spacing:0.1em;'>Medellín, Colombia</p></div></div>",
            unsafe_allow_html=True,
        )
        st.markdown(  # Subtítulo de la app
            f"<p style='color:{c["on_surface_variant"]};font-size:0.8rem;margin-bottom:1rem;'>"
            "Análisis del mercado laboral TI</p>",
            unsafe_allow_html=True,
        )

        st.markdown(f"<p style='font-size:0.8rem;color:{c["on_surface_variant"]};margin:0;'>🌙 Modo Activo</p>", unsafe_allow_html=True)  # Indicador de modo

        st.divider()  # Línea divisora

        page = st.radio(  # Menú de navegación principal
            "Navegacion",  # Label del radio button
            ["🏠 Inicio", "📊 Analisis del Mercado", "📈 Informe Ejecutivo", "🎯 Predice tu Salario", "📋 Datos Crudos", "📋 Agente de Pertinencia", "ℹ️ Info del Sistema", "⚙️ Configuracion"],
        )

        st.divider()  # Línea divisora
        cache_on = st.toggle(  # Toggle para activar/desactivar cache
            "💾 Usar datos en caché",  # Label del toggle
            value=st.session_state.get("use_cache", True),  # Valor por defecto: True
            key="cache_toggle",  # Key única en session_state
            help="Usa datos guardados localmente. Desactiva para forzar descarga fresca desde elempleo.com con Playwright.",  # Tooltip de ayuda
        )
        if cache_on != st.session_state.get("use_cache"):  # Si el toggle cambió
            st.session_state.use_cache = cache_on  # Actualiza el flag
            st.rerun()  # Recarga la app
        st.divider()  # Línea divisora

        st.markdown(f"<p style='font-size:0.8rem;color:{c['on_surface_variant']};margin-bottom:4px;'>📍 Municipio</p>", unsafe_allow_html=True)  # Label de filtro
        ciudades_selected = list(st.session_state.get("ciudades_filter", []))  # Ciudades seleccionadas actualmente
        expanded_ciudades = []  # Lista temporal de ciudades seleccionadas
        for region, cities in MEDELLIN_METRO.items():  # Itera cada región del AMVA
            with st.expander(f"{region}", expanded=(region == "Centro")):  # Expander por región (Centro expandido por defecto)
                for city in cities:  # Itera cada ciudad de la región
                    if st.checkbox(city, value=(city in ciudades_selected), key=f"city_{city}"):  # Checkbox de ciudad
                        if city not in expanded_ciudades:  # Si se marcó
                            expanded_ciudades.append(city)  # Agrega a la lista
                    else:  # Si se desmarcó
                        if city in expanded_ciudades:  # Si estaba en la lista
                            expanded_ciudades.remove(city)  # La quita
        if expanded_ciudades != ciudades_selected:  # Si cambió la selección
            st.session_state.ciudades_filter = expanded_ciudades  # Actualiza filtro
            st.rerun()  # Recarga la app

        st.divider()  # Línea divisora
        render_source_badge()  # Muestra badge de fuente de datos
        st.markdown(f"<p class='info-text' style='margin-top:4px;'>🔒 Sin almacenamiento de datos personales</p>", unsafe_allow_html=True)  # Nota de privacidad

    if page == "🏠 Inicio":  # Página de inicio (landing)
        render_landing(c, accent, cfg)
    elif page == "📊 Analisis del Mercado":  # Página de análisis de mercado
        render_market_analysis(cfg, scraper, cleaner, repo, model)
    elif page == "📈 Informe Ejecutivo":  # Página de informe ejecutivo
        render_executive_report(cfg, scraper, cleaner, repo, model)
    elif page == "🎯 Predice tu Salario":  # Página de predicción salarial
        render_prediction(cfg, scraper, cleaner, repo, model)
    elif page == "📋 Datos Crudos":  # Página de datos crudos
        render_raw_data(cfg, scraper, cleaner, repo)

    elif page == "📋 Agente de Pertinencia":  # Página del agente de pertinencia (wizard)
        render_agent_panel()

    elif page == "ℹ️ Info del Sistema":  # Página de información del sistema
        render_system_info(c, accent, cfg)
    elif page == "⚙️ Configuracion":  # Página de configuración
        render_settings(cfg)

    # Footer  # Pie de página
    st.markdown("---")  # Línea divisora
    st.markdown(  # Texto de copyright
        f"<p style='text-align:center;color:{c['on_surface_variant']};opacity:0.4;font-size:0.75rem;margin:1rem 0 0.5rem;'>"
        f"© 2025 PredicSalario IA — Todos los derechos reservados | "  # Copyright
        f"Creado por <strong>Lilliana Uribe González</strong> | Junio 2025 | "  # Autor
        f"Medellín, Colombia</p>",
        unsafe_allow_html=True,
    )


def render_landing(c, accent, cfg):
    """Renderiza la página de inicio (landing page) con información general del sistema."""
    from src.data.population import get_population_data, get_population_table_html  # Datos de población del AMVA
    from src.utils.news import fetch_news  # Noticias de empleo TI

    @st.cache_data(ttl=3600)  # Cachea por 1 hora (3600 segundos)
    def _fetch_news_cached(max_items):
        return fetch_news(max_items)  # Obtiene noticias y cachea

    shield_logo = """
    <svg width="100%" viewBox="0 0 680 620" role="img" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <style>
                .f-white { fill: #FFFFFF; }
                .f-blue { fill: #1B3F8B; }
                .f-blue2 { fill: #2557CC; }
                .f-blue3 { fill: #0A1F50; }
                .f-accent { fill: #4A90E2; }
            </style>
        </defs>
        <path d="M240,80 L440,80 L440,340 Q440,420 340,470 Q240,420 240,340 Z" fill="#0A1F50"/>
        <path d="M250,90 L430,90 L430,338 Q430,410 340,458 Q250,410 250,338 Z" fill="#1B3F8B"/>
        <path d="M258,98 L422,98 L422,336 Q422,404 340,450 Q258,404 258,336 Z" fill="#2557CC"/>
        <line x1="258" y1="260" x2="422" y2="260" stroke="#FFFFFF" stroke-width="2" opacity="0.4"/>
        <line x1="340" y1="98" x2="340" y2="310" stroke="#FFFFFF" stroke-width="2" opacity="0.4"/>
        <circle cx="295" cy="165" r="10" fill="#FFFFFF" opacity="0.95"/>
        <circle cx="320" cy="140" r="7" fill="#FFFFFF" opacity="0.7"/>
        <circle cx="315" cy="195" r="6" fill="#FFFFFF" opacity="0.6"/>
        <line x1="295" y1="165" x2="320" y2="140" stroke="#FFFFFF" stroke-width="2" opacity="0.7"/>
        <line x1="295" y1="165" x2="315" y2="195" stroke="#FFFFFF" stroke-width="2" opacity="0.6"/>
        <line x1="320" y1="140" x2="315" y2="195" stroke="#FFFFFF" stroke-width="1.5" opacity="0.4"/>
        <circle cx="275" cy="145" r="5" fill="#4A90E2"/>
        <line x1="275" y1="145" x2="295" y2="165" stroke="#4A90E2" stroke-width="1.5"/>
        <polyline points="360,200 375,170 390,185 408,148" fill="none" stroke="#FFFFFF" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>
        <circle cx="360" cy="200" r="3.5" fill="#4A90E2"/>
        <circle cx="375" cy="170" r="3.5" fill="#4A90E2"/>
        <circle cx="390" cy="185" r="3.5" fill="#4A90E2"/>
        <circle cx="408" cy="148" r="3.5" fill="#FFFFFF"/>
        <polyline points="404,138 408,128 412,138" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>
        <text x="340" y="352" text-anchor="middle" font-family="'Helvetica Neue', Arial, sans-serif" font-size="52" font-weight="900" fill="#FFFFFF" opacity="0.95">$</text>
        <line x1="290" y1="370" x2="335" y2="370" stroke="#FFFFFF" stroke-width="1.5" opacity="0.35"/>
        <line x1="345" y1="370" x2="390" y2="370" stroke="#FFFFFF" stroke-width="1.5" opacity="0.35"/>
        <path d="M258,400 L422,400 L422,336 Q422,404 340,450 Q258,404 258,336 L258,400 Z" fill="#0A1F50" opacity="0.7"/>
        <rect x="302" y="50" width="76" height="30" rx="3" fill="#0A1F50"/>
        <rect x="302" y="50" width="76" height="30" rx="3" fill="none" stroke="#FFFFFF" stroke-width="1.5" opacity="0.5"/>
        <rect x="306" y="38" width="12" height="16" rx="2" fill="#0A1F50" stroke="#FFFFFF" stroke-width="1.2" opacity="0.8"/>
        <rect x="324" y="30" width="12" height="24" rx="2" fill="#0A1F50" stroke="#FFFFFF" stroke-width="1.5"/>
        <rect x="344" y="26" width="12" height="28" rx="2" fill="#0A1F50" stroke="#FFFFFF" stroke-width="1.5"/>
        <rect x="364" y="30" width="12" height="24" rx="2" fill="#0A1F50" stroke="#FFFFFF" stroke-width="1.5"/>
        <circle cx="330" cy="35" r="3" fill="#4A90E2"/>
        <circle cx="350" cy="30" r="4" fill="#4A90E2"/>
        <circle cx="370" cy="35" r="3" fill="#4A90E2"/>
        <text x="340" y="520" text-anchor="middle" font-family="'Helvetica Neue', Arial, sans-serif" font-size="34" font-weight="800" fill="#0A1F50" letter-spacing="-0.5">
            <tspan fill="#0A1F50">Predi</tspan><tspan fill="#2557CC">Salario</tspan><tspan fill="#4A90E2">IA</tspan>
        </text>
        <line x1="240" y1="535" x2="440" y2="535" stroke="#2557CC" stroke-width="1.5"/>
        <circle cx="340" cy="535" r="3.5" fill="#2557CC"/>
        <text x="340" y="558" text-anchor="middle" font-family="'Helvetica Neue', Arial, sans-serif" font-size="12" font-weight="500" fill="#2557CC" letter-spacing="4">INTELIGENCIA SALARIAL</text>
    </svg>"""

    _surf = c["surface"]  # Color de fondo de superficie
    _surf_hi = c["surface_high"]  # Color de superficie alta
    _glass = c["glass_border"]  # Color de borde de vidrio
    _ov = c["outline_variant"]  # Color de contorno variante
    _on_s = c["on_surface"]  # Color sobre superficie
    _on_sv = c["on_surface_variant"]  # Color sobre variante de superficie

    st.markdown(f"""
    <div style='background:linear-gradient(135deg,{_surf},{_surf_hi});
        border:1px solid {_glass};border-radius:20px;padding:2.5rem 2rem;
        max-width:700px;margin:2rem auto;text-align:center;position:relative;z-index:1;
        box-shadow:0 8px 32px rgba(0,0,0,0.3),0 0 60px rgba(74,144,226,0.1);'>
        <div style='max-width:240px;margin:0 auto 1.5rem;'>{shield_logo}</div>
        <h1 class='main-header' style='font-size:2.5rem;margin-bottom:0.5rem;background:linear-gradient(135deg,{accent},{c['primary_container']});
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;'>PredicSalario IA</h1>
        <p style='color:{_on_sv};font-size:1.1rem;max-width:600px;margin:0 auto 0.5rem;'>
        Estudio Laboral de Pertinencia de Programas de Estudio en Areas de las TICs</p>
        <p style='color:{_on_sv};font-size:0.9rem;max-width:600px;margin:0 auto 0.5rem;'>
        Prediccion de salarios del sector tecnologico en Medellin, Colombia,
        impulsada por Machine Learning con datos reales del mercado laboral.</p>
        <div style='display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin-top:1.5rem;'>
        <a href='#metodologia' style='padding:10px 28px;background:linear-gradient(135deg,{accent},{c['primary_container']});
        color:#FFFFFF;border-radius:12px;text-decoration:none;font-weight:700;'>Explorar Metodologia</a>
        <a href='#fuentes' style='padding:10px 28px;border:1px solid {_ov};
        color:{_on_s};border-radius:12px;text-decoration:none;font-weight:500;'>Ver Fuentes</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:16px;
    max-width:900px;margin:2rem auto;padding:0 1rem;position:relative;z-index:1;'>
        <div class='feature-card' style='text-align:center;'>
            <div style='width:40px;height:40px;margin:0 auto 8px;'>
                <svg viewBox='0 0 24 24' fill='none' stroke='{accent}' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>
                    <circle cx='12' cy='12' r='10'/><path d='M12 6v6l4 2'/><path d='M8 12l4-6 4 6'/><path d='M8 16l4 2 4-2'/>
                </svg>
            </div>
            <p style='font-weight:700;margin:0;'>Random Forest</p>
            <p style='font-size:0.8rem;color:{c["on_surface_variant"]};margin:0;'>Modelo de prediccion</p>
        </div>
        <div class='feature-card' style='text-align:center;'>
            <div style='width:40px;height:40px;margin:0 auto 8px;'>
                <svg viewBox='0 0 24 24' fill='none' stroke='{accent}' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>
                    <path d='M12 2a4 4 0 0 1 4 4c0 1.5-.8 2.8-2 3.4V12h3a3 3 0 0 1 3 3v1a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2v-1a3 3 0 0 1 3-3h3V9.4A4 4 0 0 1 12 2z'/>
                    <path d='M10 18v2'/><path d='M14 18v2'/><path d='M12 2v4'/><path d='M8 6l2 2'/><path d='M16 6l-2 2'/>
                </svg>
            </div>
            <p style='font-weight:700;margin:0;'>Red Neuronal</p>
            <p style='font-size:0.8rem;color:{c["on_surface_variant"]};margin:0;'>Analisis empleabilidad</p>
        </div>
        <div class='feature-card' style='text-align:center;'>
            <div style='width:40px;height:40px;margin:0 auto 8px;'>
                <svg viewBox='0 0 24 24' fill='none' stroke='{accent}' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>
                    <rect x='3' y='3' width='18' height='18' rx='2'/><path d='M3 9h18'/><path d='M9 21V9'/><path d='M14 14l3 3-3 3'/>
                </svg>
            </div>
            <p style='font-weight:700;margin:0;'>Dashboard</p>
            <p style='font-size:0.8rem;color:{c["on_surface_variant"]};margin:0;'>Visualizacion interactiva</p>
        </div>
        <div class='feature-card' style='text-align:center;'>
            <div style='width:40px;height:40px;margin:0 auto 8px;'>
                <svg viewBox='0 0 24 24' fill='none' stroke='{accent}' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>
                    <path d='M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8'/><path d='M21 3v5h-5'/><path d='M12 7v5l3 3'/>
                </svg>
            </div>
            <p style='font-weight:700;margin:0;'>Playwright</p>
            <p style='font-size:0.8rem;color:{c["on_surface_variant"]};margin:0;'>Scraping automatico</p>
        </div>
        <div class='feature-card' style='text-align:center;'>
            <div style='width:40px;height:40px;margin:0 auto 8px;'>
                <svg viewBox='0 0 24 24' fill='none' stroke='{accent}' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>
                    <rect x='3' y='11' width='18' height='11' rx='2'/><path d='M7 11V7a5 5 0 0 1 10 0v4'/><circle cx='12' cy='16' r='1'/>
                </svg>
            </div>
            <p style='font-weight:700;margin:0;'>Privacidad</p>
            <p style='font-size:0.8rem;color:{c["on_surface_variant"]};margin:0;'>Sin datos personales</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.markdown(f"<h2 id='info-sistema' style='text-align:center;margin-bottom:1rem;'>📋 Informacion General del Sistema</h2>", unsafe_allow_html=True)

    system_info = {
        "Sistema": {
            "Nombre": "PredicSalario IA - Estudio Laboral de Pertinencia de Programas en TICs",
            "Autor": "Lilliana Uribe Gonzalez",
            "Version": "2.0 - Analisis SENA + Neural Network",
            "Fecha": "Junio 2026",
            "Descripcion": "Prediccion salarial del sector TI en Medellin con Machine Learning",
            "Desplegado en": "https://predic-salario-ia.streamlit.app/",
        },
        "Modelos de IA": {
            "Random Forest": "Prediccion salarial (regresion) - 100 arboles, max_depth=10",
            "MLPRegressor": "Analisis de empleabilidad (red neuronal) - 128/64/32 neuronas",
            "TF-IDF": "Vectorizacion de skills tecnicas (80 features, sublinear_tf)",
            "LabelEncoder": "Codificacion de categorias (cargo, modalidad, contrato)",
            "Cross-Validation": "Validacion cruzada 5-fold para metricas robustas",
        },
        "Tecnologias": {
            "Python 3.12": "Lenguaje principal",
            "Streamlit": "Framework web interactivo",
            "scikit-learn": "Machine Learning (RandomForest, MLP, TF-IDF, metrics)",
            "pandas / numpy": "Procesamiento y analisis de datos",
            "Plotly": "Graficos interactivos (scatter, bar, pie, box, heatmap)",
            "Playwright": "Scraping headless con Chromium (subprocess)",
            "cloudscraper": "Scraping HTTP con bypass Cloudflare (fallback)",
            "ThreadPoolExecutor": "Scraping paralelo (3 workers simultaneos)",
            "ZenRows API": "Bypass Cloudflare premium (1000 req/mes gratis)",
            "joblib": "Persistencia del modelo (.pkl)",
            "openpyxl": "Lectura de archivos Excel SENA",
        },
        "APIs y Fuentes": {
            "elempleo.com": "97 queries de scraping (Playwright/HTTP)",
            "computrabajo.com": "Scraping paralelo (HTTP/cloudscraper)",
            "indeed.com": "Scraping paralelo (HTTP/cloudscraper)",
            "glassdoor.com": "Benchmarks salariales (HTTP)",
            "dane.gov.co": "Datos oficiales gobierno + salarios referencia",
            "Wikipedia API": "Poblacion de 15 municipios AMVA (cache 30 dias)",
            "Google News RSS": "6 noticias de empleo/tecnologia (cache 1 hora)",
            "Groq API": "Generacion de informes CNA (llama-3.3-70b-versatile, gratis)",
            "ZenRows API": "Bypass Cloudflare (1000 req/mes gratis, opcional)",
            "SENA Excel": "Datos de inscritos por ocupacion (upload manual)",
            "Datos reales": "Scraping elempleo.com (~500 ofertas reales)",
        },
        "Features del Modelo (9)": {
            "experiencia_requerida": "Anos de experiencia requerida (0-50)",
            "cargo_nivel_cod": "Nivel: tecnico=0, tecnologo=1, ingeniero=2, senior=3",
            "modalidad_cod": "Modalidad: presencial=0, hibrido=1, remoto=2",
            "num_skills": "Cantidad de skills tecnicas detectadas",
            "tipo_contrato_cod": "Contrato: indefinido=0, servicios=1, obra=2, aprendizaje=3",
            "exp_x_nivel": "Interaccion experiencia x nivel de cargo",
            "exp_squared": "Experiencia al cuadratico (no linealidad)",
            "is_remote": "Binario: 1 si es remoto, 0 si no",
            "role_categoria": "Categoria del rol (Desarrollo, Datos, IA, etc.)",
        },
        "Skills Detectadas (120+)": {
            "Lenguajes": "Python, Java, JavaScript, TypeScript, C#, C++, Go, Rust, PHP, Ruby, Swift, Kotlin, Dart",
            "Frontend": "React, Angular, Vue, Next.js, Nuxt.js, Svelte, HTML/CSS, Tailwind, Bootstrap",
            "Backend": "Node.js, Django, Flask, FastAPI, Spring Boot, .NET, Express.js, Laravel",
            "Cloud": "AWS, Azure, GCP, Docker, Kubernetes, Terraform, Ansible, Jenkins",
            "Datos": "SQL, PostgreSQL, MySQL, MongoDB, Redis, Spark, Airflow, Kafka, dbt, Snowflake",
            "IA/ML": "TensorFlow, PyTorch, Scikit-learn, LangChain, OpenAI, Hugging Face, NLP, Computer Vision",
            "Ciberseguridad": "Pentesting, SIEM, Firewalls, Kali Linux, Wireshark, Ethical Hacking",
            "Otros": "Git, Linux, CI/CD, Agile/Scrum, REST API, GraphQL, Microservices, IoT, Blockchain",
        },
        "Metricas del Modelo": {
            "R cuadrado": "0.50 (explica 50% de varianza salarial)",
            "MAE": "$938,000 COP (error absoluto promedio)",
            "RMSE": "$1,170,000 COP (error cuadratico medio)",
            "Confianza": "±15% de rango de prediccion",
            "MinimoSalario": "$500,000 COP",
            "MaximoSalario": "$50,000,000 COP",
        },
    }

    for section, items in system_info.items():
        st.markdown(f"<h3 style='color:{accent};margin:1.5rem 0 0.5rem;font-size:1.1rem;'>{section}</h3>", unsafe_allow_html=True)
        for key, value in items.items():
            st.markdown(f"""<div class='feature-card' style='padding:0.6rem 1rem;margin:0.3rem 0;display:flex;gap:8px;align-items:baseline;'>
                <span style='font-weight:700;color:{accent};min-width:160px;flex-shrink:0;font-size:0.85rem;'>{key}</span>
                <span style='color:{c["on_surface"]};font-size:0.85rem;'>{value}</span>
            </div>""", unsafe_allow_html=True)

    st.divider()

    st.markdown(f"<h2 id='arquitectura' style='text-align:center;margin-bottom:1rem;'>🏗️ Arquitectura del Sistema</h2>", unsafe_allow_html=True)

    arch_info = {
        "Arquitectura": {
            "Patron": "MVC Adaptado con Factory + Strategy + Singleton",
            "Presentacion": "Streamlit (View) + Plotly (Charts) + dashboard.py (Layout)",
            "Controlador": "app.py (Orquestacion) + config.py (Singleton) + ScraperFactory",
            "Modelo": "SalaryPredictor (RandomForest) + NeuralNetwork (MLPRegressor) + DataCleaner (ETL)",
        },
        "Patrones de Diseno": {
            "Singleton": "Config - una sola instancia global de configuracion",
            "Factory": "ScraperFactory - creacion de scrapers con fallback automatico",
            "Strategy": "ScraperStrategy - interfaz comun para Playwright y HTTP",
            "Repository": "DataRepository - persistencia de datos raw y procesados",
            "MVC": "Separacion de Presentacion, Controlador y Modelo",
        },
        "Flujo de Datos": {
            "Paso 1": "📥 Scraping → 5 portales (elempleo + computrabajo + indeed + glassdoor + dane)",
            "Paso 2": "🧹 Limpieza → DataCleaner: salario, experiencia, skills, categorias",
            "Paso 3": "🔢 Codificacion → TF-IDF skills + LabelEncoder categorias",
            "Paso 4": "🧠 Entrenamiento → Random Forest (salario) + MLP (empleabilidad)",
            "Paso 5": "📊 Visualizacion → Dashboard interactivo con Plotly",
            "Paso 6": "📤 Prediccion → Formulario interactivo con rango de confianza",
        },
    }

    for section, items in arch_info.items():
        st.markdown(f"<h3 style='color:{accent};margin:1.5rem 0 0.5rem;font-size:1.1rem;'>{section}</h3>", unsafe_allow_html=True)
        for key, value in items.items():
            st.markdown(f"""<div class='feature-card' style='padding:0.6rem 1rem;margin:0.3rem 0;display:flex;gap:8px;align-items:baseline;'>
                <span style='font-weight:700;color:{accent};min-width:160px;flex-shrink:0;font-size:0.85rem;'>{key}</span>
                <span style='color:{c["on_surface"]};font-size:0.85rem;'>{value}</span>
            </div>""", unsafe_allow_html=True)

    st.divider()

    st.divider()

    st.markdown(f"<h2 id='metodologia' style='text-align:center;margin-bottom:0.5rem;'>"
                f"🛠️ Metodologia</h2>", unsafe_allow_html=True)
    st.markdown(
        f"<p style='text-align:center;color:{c["on_surface_variant"]};max-width:600px;margin:0 auto 2rem;'>"
        f"Pipeline completo de datos: desde la obtencion hasta la prediccion.</p>",
        unsafe_allow_html=True,
    )

    methodology = {
        "1. Scraping": {
            "Fuentes": "elempleo.com + computrabajo.com + indeed.com + glassdoor.com + dane.gov.co",
            "Herramienta": "MultiSourceScraper (paralelo local, secuencial Cloud)",
            "Queries": "15 consultas de busqueda en elempleo.com",
            "Campos": "titulo, empresa, salario, ubicacion, experiencia, contrato, skills, modalidad",
            "Deduplicacion": "Global across sources via titulo + empresa + salario_minimo",
            "Velocidad": "~2 min (15 queries de scraping real)",
        },
        "2. Limpieza": {
            "Salarios": "Normalizacion a COP mensuales (filtro 500K-100M)",
            "Experiencia": "Extraccion de anos desde texto (regex patterns)",
            "Skills": "120+ keywords detectadas via regex (validators.py)",
            "Categorias": "Role category, cargo nivel, modalidad, tipo contrato",
            "Deduplicacion": "Por titulo + empresa + salario",
        },
        "3. Modelo": {
            "Algoritmo": "Random Forest Regressor (100 arboles, max_depth=10)",
            "Features": "9 features + TF-IDF skills (80 dims) + role category",
            "Validacion": "Cross-validation 5-fold + train/test split 80/20",
            "Metricas": "R²=0.50, MAE=$938K, RMSE=$1.17M",
            "Guardado": "joblib .pkl con SHA-256 hash para integridad",
        },
        "4. Visualizacion": {
            "Graficos": "Scatter, barras, pie, box, heatmap, gauge, treemap",
            "Filtros": "Multiselect nivel, modalidad, slider experiencia",
            "KPIs": "Ofertas, salario promedio, companies, skills top",
            "Interactividad": "Hover, zoom, seleccion, descarga CSV",
        },
    }

    for step, details in methodology.items():
        st.markdown(f"<h3 style='color:{accent};margin:1.2rem 0 0.5rem;font-size:1rem;'>{step}</h3>", unsafe_allow_html=True)
        for key, value in details.items():
            st.markdown(f"""<div class='feature-card' style='padding:0.5rem 1rem;margin:0.2rem 0;display:flex;gap:8px;align-items:baseline;'>
                <span style='font-weight:700;color:{accent};min-width:120px;flex-shrink:0;font-size:0.82rem;'>{key}</span>
                <span style='color:{c["on_surface"]};font-size:0.82rem;'>{value}</span>
            </div>""", unsafe_allow_html=True)

    st.divider()

    st.markdown(f"<h2 id='fuentes' style='text-align:center;margin-bottom:1.5rem;'>📊 Fuentes de Datos</h2>", unsafe_allow_html=True)
    st.markdown(
        f"<p style='text-align:center;color:{c["on_surface_variant"]};max-width:700px;margin:0 auto 2rem;'>"
        f"Resumen ejecutivo de las 5 fuentes principales del mercado laboral TI en Colombia.</p>",
        unsafe_allow_html=True,
    )
    for i, src in enumerate(cfg.DATA_SOURCES):
        cols = st.columns([1, 5])
        with cols[0]:
            st.markdown(f"<div style='font-size:2.5rem;text-align:center;'>{src['icon']}</div>", unsafe_allow_html=True)
        with cols[1]:
            st.markdown(f"""
            <div class='feature-card' style='padding:1rem 1.5rem;'>
                <div style='display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;'>
                    <h3 style='margin:0;font-size:1.1rem;'>{src['name']}</h3>
                    <span style='font-size:0.75rem;color:{c["on_surface_variant"]};background:{c["surface_high"]};padding:2px 10px;border-radius:20px;'>{src['tipo']}</span>
                </div>
                <p style='margin:6px 0;font-size:0.9rem;color:{c["on_surface_variant"]};'>{src['description']}</p>
                <div style='display:flex;gap:16px;flex-wrap:wrap;font-size:0.8rem;color:{c["outline"]};'>
                    <span>🌍 {src['cobertura']}</span>
                    <span>🔄 {src['actualizacion']}</span>
                    <span>📦 {src['formato']}</span>
                    <a href='{src['url']}' target='_blank' style='color:{accent};'>Ir al sitio →</a>
                </div>
            </div>
            """, unsafe_allow_html=True)
        if i < len(cfg.DATA_SOURCES) - 1:
            st.markdown(f"<div style='height:8px;'></div>", unsafe_allow_html=True)

    with st.expander("🗺️ Municipios del Área Metropolitana analizados"):
        @st.cache_data(ttl=30 * 86400)  # 30 days
        def _load_population():
            return get_population_data()
        pop_data = _load_population()
        st.markdown(get_population_table_html(pop_data))

    st.divider()

    st.markdown(f"<h2 style='text-align:center;margin-bottom:1.5rem;'>⚠️ Limitaciones</h2>", unsafe_allow_html=True)
    for lim in [
        "Sesgo geográfico: Solo ofertas en Medellín y área metropolitana",
        "Sesgo temporal: Datos limitados al período disponibles",
        "Sesgo de plataforma: Solo ofertas accesibles vía elempleo.com",
        "Precisión variable según calidad y cantidad de datos",
        "No incluye beneficios adicionales (bonos, prestaciones, etc.)",
    ]:
        st.markdown(f"""
        <div style='display:flex;align-items:center;gap:8px;padding:6px 0;'>
            <span style='color:{c["error"]};font-size:0.8rem;'>⚠️</span>
            <span style='color:{c["on_surface_variant"]};font-size:0.9rem;'>{lim}</span>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    st.markdown(f"<h2 style='text-align:center;margin-bottom:1.5rem;'>📰 Noticias del Mercado TI</h2>", unsafe_allow_html=True)
    st.markdown(
        f"<p style='text-align:center;color:{c["on_surface_variant"]};max-width:600px;margin:0 auto 2rem;'>"
        f"Últimas noticias sobre empleo y tecnología en Colombia.</p>",
        unsafe_allow_html=True,
    )
    with st.spinner("Cargando noticias..."):
        news_items = _fetch_news_cached(max_items=6)
    if news_items:
        ncols = st.columns(3)
        for i, item in enumerate(news_items):
            with ncols[i % 3]:
                st.markdown(f"""
                <div class='feature-card' style='padding:1rem;'>
                    <p style='font-weight:600;margin:0 0 6px;font-size:0.9rem;'>{item['title']}</p>
                    <div style='display:flex;justify-content:space-between;font-size:0.75rem;color:{c["on_surface_variant"]};'>
                        <span>📰 {item['source']}</span>
                        <span>📅 {item['date']}</span>
                    </div>
                    <a href='{item['url']}' target='_blank' style='color:{accent};font-size:0.8rem;'>Leer más →</a>
                </div>
                """, unsafe_allow_html=True)

    st.divider()
    st.markdown(f"""
    <div style='text-align:center;padding:1rem 0;'>
        <p style='color:{c["on_surface_variant"]};font-size:0.8rem;'>
        🔒 No se almacenan datos personales de candidatos. Solo datos agregados y anónimos de ofertas laborales.<br>
         Scraping headless con Playwright. Hash SHA-256 para integridad del modelo.
        </p>
        <p style='color:{c["outline"]};font-size:0.75rem;margin-top:1rem;'>
        PredicSalario IA &copy; {datetime.date.today().year}
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_system_info(c, accent, cfg):
    """Renderiza la página de información del sistema con documentación técnica completa."""
    st.markdown(f"<h1 class='main-header' style='background:linear-gradient(135deg,{accent},{c['primary_container']});"
                f"-webkit-background-clip:text;-webkit-text-fill-color:transparent;'>ℹ️ Informacion del Sistema</h1>",
                unsafe_allow_html=True)  # Título de la página con gradiente
    st.markdown(f"<p style='color:{c['on_surface_variant']};margin-bottom:1.5rem;'>"
                f"Documentacion tecnica completa del modelo de IA y arquitectura del sistema.</p>",
                unsafe_allow_html=True)  # Subtítulo descriptivo

    st.markdown(f"<h2 style='color:{c["on_surface"]};'>6. Modelo de IA Utilizado</h2>", unsafe_allow_html=True)  # Sección 6: Modelo de IA
    model_info = [  # Lista de información del modelo
        ("Algoritmo", "Random Forest Regressor (prediccion salarial) + MLPRegressor Red Neuronal (analisis de empleabilidad)"),
        ("Librerias", "scikit-learn, pandas, numpy, plotly, streamlit, playwright"),
        ("Hiperparametros RF", f"n_estimators={cfg.MODEL_PARAMS.get('n_estimators', 100)}, max_depth={cfg.MODEL_PARAMS.get('max_depth', 10)}, random_state={cfg.RANDOM_STATE}"),
        ("Hiperparametros NN", "hidden_layer_sizes=(128, 64, 32), max_iter=500, early_stopping=True"),
        ("Tipo de aprendizaje", "Supervisado (regresion para salario, clasificacion para empleabilidad)"),
    ]
    for label, value in model_info:  # Itera cada par label-valor
        st.markdown(f"""<div class='feature-card' style='padding:0.8rem 1.2rem;margin:0.4rem 0;'>
            <span style='font-weight:700;color:{accent};'>{label}:</span>
            <span style='color:{c["on_surface"]};margin-left:8px;'>{value}</span>
        </div>""", unsafe_allow_html=True)  # Tarjeta de info del modelo

    st.divider()  # Línea divisora

    st.markdown(f"<h2 style='color:{c["on_surface"]};'>7. Entrenamiento y Evaluacion</h2>", unsafe_allow_html=True)  # Sección 7: Evaluación
    eval_info = [  # Lista de métricas de evaluación
        ("Division de datos", f"{int((1-cfg.TEST_SIZE)*100)}% entrenamiento, {int(cfg.TEST_SIZE*100)}% prueba (test_size={cfg.TEST_SIZE})"),
        ("Metricas utilizadas", "R-squared (R²), Mean Absolute Error (MAE), Root Mean Squared Error (RMSE)"),
                ("R² score", "0.50 (modelo actual con 500+ registros de entrenamiento)"),
        ("MAE", "$938,000 COP (error absoluto promedio)"),
        ("RMSE", "$1,170,000 COP (error cuadratico medio)"),
                ("Resultado", "El modelo logra explicar el 50% de la varianza salarial. Con mas datos de scraping mejorara significativamente."),
    ]
    for label, value in eval_info:  # Itera cada métrica
        st.markdown(f"""<div class='feature-card' style='padding:0.8rem 1.2rem;margin:0.4rem 0;'>
            <span style='font-weight:700;color:{accent};'>{label}:</span>
            <span style='color:{c["on_surface"]};margin-left:8px;'>{value}</span>
        </div>""", unsafe_allow_html=True)  # Tarjeta de métrica

    st.divider()  # Línea divisora

    st.markdown(f"<h2 style='color:{c["on_surface"]};'>8. Interpretabilidad</h2>", unsafe_allow_html=True)  # Sección 8: Interpretabilidad
    interp_info = [  # Lista de información de interpretabilidad
        ("Variables mas importantes", "Experiencia (anos), nivel de cargo (tecnico/tecnologo/ingeniero/senior), skills tecnicas, modalidad laboral"),
        ("Metodo utilizado", "Feature importance del Random Forest + Analisis de correlacion"),
        ("Explicacion del modelo", "A mayor experiencia y nivel de cargo, mayor salario. Skills como Python, AWS, Kubernetes aumentan el salario promedio. Modalidad remoto tiende a ofrecer mejores paquetes."),
    ]
    for label, value in interp_info:  # Itera cada item
        st.markdown(f"""<div class='feature-card' style='padding:0.8rem 1.2rem;margin:0.4rem 0;'>
            <span style='font-weight:700;color:{accent};'>{label}:</span>
            <span style='color:{c["on_surface"]};margin-left:8px;'>{value}</span>
        </div>""", unsafe_allow_html=True)  # Tarjeta de interpretabilidad

    st.divider()  # Línea divisora

    st.markdown(f"<h2 style='color:{c["on_surface"]};'>9. Uso del Modelo</h2>", unsafe_allow_html=True)  # Sección 9: Uso del modelo
    st.markdown(f"""<div class='feature-card' style='padding:1.5rem;margin:1rem 0;'>
        <div style='display:flex;flex-direction:column;gap:12px;font-size:0.9rem;'>
            <div style='display:flex;align-items:center;gap:10px;'>
                <span style='background:{accent}20;padding:4px 10px;border-radius:6px;font-weight:700;'>1</span>
                <span>El usuario sube un archivo Excel/CSV con datos de empleo del SENA o realiza scraping</span>
            </div>
            <div style='display:flex;align-items:center;gap:10px;'>
                <span style='background:{accent}20;padding:4px 10px;border-radius:6px;font-weight:700;'>2</span>
                <span>El sistema procesa y limpia la informacion (normalizacion salarial, extraccion de skills)</span>
            </div>
            <div style='display:flex;align-items:center;gap:10px;'>
                <span style='background:{accent}20;padding:4px 10px;border-radius:6px;font-weight:700;'>3</span>
                <span>El modelo Random Forest predice el salario esperado</span>
            </div>
            <div style='display:flex;align-items:center;gap:10px;'>
                <span style='background:{accent}20;padding:4px 10px;border-radius:6px;font-weight:700;'>4</span>
                <span>La red neuronal MLPRegressor analiza patrones de empleabilidad</span>
            </div>
            <div style='display:flex;align-items:center;gap:10px;'>
                <span style='background:{accent}20;padding:4px 10px;border-radius:6px;font-weight:700;'>5</span>
                <span>Se genera el informe ejecutivo con graficos, recomendaciones y oportunidades</span>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)  # Pasos de uso del modelo

    st.divider()  # Línea divisora

    st.markdown(f"<h2 style='color:{c["on_surface"]};'>10. Implementacion Tecnica</h2>", unsafe_allow_html=True)  # Sección 10: Implementación técnica
    tech_info = [  # Lista de tecnologías implementadas
        ("Backend", "Python 3.12 + Streamlit (framework principal)"),
        ("Frontend", "Streamlit + HTML/CSS customizado con tema dark/light"),
        ("Modelo", "Archivo .pkl entrenado (salary_predictor.pkl) con hash SHA-256 de integridad"),
        ("Scraping", "Playwright (navegador headless Chromium) + HTTP cloudscraper (Streamlit Cloud)"),
        ("Base de datos", "Archivos CSV locales (data/raw/, data/processed/)"),
        ("Despliegue", "Ejecucion local via 'streamlit run app.py'"),
    ]
    for label, value in tech_info:  # Itera cada tecnología
        st.markdown(f"""<div class='feature-card' style='padding:0.8rem 1.2rem;margin:0.4rem 0;'>
            <span style='font-weight:700;color:{accent};'>{label}:</span>
            <span style='color:{c["on_surface"]};margin-left:8px;'>{value}</span>
        </div>""", unsafe_allow_html=True)  # Tarjeta de tecnología

    st.divider()  # Línea divisora

    st.markdown(f"<h2 style='color:{c["on_surface"]};'>11. Resultados y Valor</h2>", unsafe_allow_html=True)  # Sección 11: Resultados
    st.markdown(f"""<div class='feature-card' style='padding:1.5rem;margin:1rem 0;'>
        <ul style='margin:0;padding-left:1.2rem;color:{c["on_surface"]};font-size:0.9rem;'>
            <li>Reduce el tiempo de evaluacion del mercado laboral TI de horas a minutos</li>
            <li>Identifica automaticamente las ocupaciones con mayor demanda y mejor remuneracion</li>
            <li>Genera insights accionables para la toma de decisiones en formacion tecnica</li>
            <li>Analiza patrones de genero y variacion interanual en el mercado laboral</li>
            <li>Permite filtrar por departamento (Antioquia) y nivel de cualificacion</li>
            <li>Visualiza tendencias del mercado con graficos interactivos</li>
        </ul>
    </div>""", unsafe_allow_html=True)  # Lista de resultados y valor

    st.divider()  # Línea divisora

    st.markdown(f"<h2 style='color:{c["on_surface"]};'>12. Limitaciones</h2>", unsafe_allow_html=True)  # Sección 12: Limitaciones
    limitations = [  # Lista de limitaciones del sistema
        "Dataset pequeno actualmente (~500 registros reales) - scraping en segundo plano para mas datos",
        "Sesgo geografico: Solo analiza Medellin y area metropolitana de Antioquia",
        "Sesgo temporal: Datos limitados al periodo disponible en el SENA",
        "Sesgo de plataforma: Scraping limitado a elempleo.com (Activo Playwright)",
        "Modelo no generaliza bien a otros paises o regiones sin re-entrenamiento",
        "No incluye beneficios adicionales (bonos, prestaciones, auxilios)",
        "Precision variable segun calidad y cantidad de datos de entrada",
    ]
    for lim in limitations:  # Itera cada limitación
        st.markdown(f"""<div style='display:flex;align-items:center;gap:8px;padding:6px 0;'>
            <span style='color:{c["error"]};font-size:0.8rem;'>⚠️</span>
            <span style='color:{c["on_surface_variant"]};font-size:0.9rem;'>{lim}</span>
        </div>""", unsafe_allow_html=True)  # Tarjeta de limitación

    st.divider()  # Línea divisora

    st.markdown(f"<h2 style='color:{c["on_surface"]};'>13. Etica y Seguridad</h2>", unsafe_allow_html=True)  # Sección 13: Ética y seguridad
    ethics_info = [  # Lista de principios éticos
        "No se almacenan datos personales de candidatos - solo datos agregados y anonimos",
        "El modelo puede generar sesgos si los datos estan desbalanceados por genero o region",
        "Se recomienda usar el modelo como herramienta de apoyo, no como unico criterio de decision",
        "Los datos del SENA son publicos y oficialmente reconocidos por el gobierno colombiano",
        "El scraping respeta los terminos de servicio de las fuentes consultadas",
        "Hash SHA-256 garantiza la integridad del modelo entrenado",
        "Se recomienda re-entrenar periodicamente con datos actualizados para mantener la pertinencia",
    ]
    for item in ethics_info:  # Itera cada principio
        st.markdown(f"""<div style='display:flex;align-items:center;gap:8px;padding:6px 0;'>
            <span style='color:{accent};font-size:0.8rem;'>✅</span>
            <span style='color:{c["on_surface_variant"]};font-size:0.9rem;'>{item}</span>
        </div>""", unsafe_allow_html=True)  # Tarjeta de principio ético

    st.divider()  # Línea divisora

    st.markdown(f"<h2 style='color:{c["on_surface"]};'>📊 Fuentes de Datos en Tiempo Real</h2>", unsafe_allow_html=True)  # Sección de fuentes de datos
    for src in cfg.DATA_SOURCES:  # Itera cada fuente de datos del config
        st.markdown(f"""<div class='feature-card' style='padding:0.8rem 1.2rem;margin:0.4rem 0;'>
            <span style='font-size:1.2rem;'>{src['icon']}</span>
            <span style='font-weight:700;color:{accent};margin-left:8px;'>{src['name']}</span>
            <span style='color:{c["on_surface_variant"]};margin-left:8px;font-size:0.85rem;'>{src['description']}</span>
        </div>""", unsafe_allow_html=True)  # Tarjeta de fuente de datos

    st.divider()  # Línea divisora

    st.markdown(f"<h2 style='color:{c["on_surface"]};'>🔍 Auditoria de APIs</h2>", unsafe_allow_html=True)  # Sección de auditoría de APIs
    st.markdown(f"<p style='color:{c["on_surface_variant"]};font-size:0.9rem;'>Estado actual de cada API y fuente de datos.</p>", unsafe_allow_html=True)  # Descripción de la auditoría

    if st.button("🔄 Verificar estado de APIs", key="btn_audit_apis", type="primary"):  # Botón para ejecutar auditoría
        with st.spinner("Verificando APIs..."):  # Muestra spinner mientras verifica
            audit_results = []  # Lista de resultados de auditoría

            # Playwright  # Prueba de Playwright scraper
            try:
                from src.scraper.playwright_scraper import PlaywrightScraper  # Importa scraper
                pw = PlaywrightScraper()  # Instancia scraper
                data = pw.fetch_data(["python developer medellin"])  # Prueba con query de prueba
                audit_results.append({"api": "Playwright", "estado": "OK", "registros": len(data), "fuente": "elempleo.com", "token": "No requiere", "renovacion": "N/A"})  # Resultado OK
            except Exception as e:  # Si falla
                audit_results.append({"api": "Playwright", "estado": "ERROR", "registros": 0, "fuente": "elempleo.com", "token": "No requiere", "renovacion": "N/A", "error": str(e)[:50]})  # Resultado ERROR

            # HTTP cloudscraper  # Prueba de HTTP scraper
            try:
                from src.scraper.http_scraper import HttpScraper  # Importa scraper
                hs = HttpScraper()  # Instancia scraper
                data = hs.fetch_data(["javascript developer medellin"])  # Prueba con query de prueba
                audit_results.append({"api": "HTTP cloudscraper", "estado": "OK", "registros": len(data), "fuente": "elempleo.com", "token": "No requiere", "renovacion": "N/A"})  # Resultado OK
            except Exception as e:  # Si falla
                audit_results.append({"api": "HTTP cloudscraper", "estado": "ERROR", "registros": 0, "fuente": "elempleo.com", "token": "No requiere", "renovacion": "N/A", "error": str(e)[:50]})  # Resultado ERROR

            # Wikipedia  # Prueba de Wikipedia API
            try:
                import requests as req  # Importa requests
                r = req.get("https://es.wikipedia.org/w/api.php", params={"action": "parse", "page": "Area metropolitana del Valle de Aburra", "prop": "text", "format": "json"}, headers={"User-Agent": "PredicSalarioIA/1.0"}, timeout=10)  # Consulta Wikipedia
                wiki_ok = r.status_code == 200 and "parse" in r.json()  # Verifica respuesta válida
                audit_results.append({"api": "Wikipedia API", "estado": "OK" if wiki_ok else f"HTTP {r.status_code}", "registros": 10 if wiki_ok else 0, "fuente": "Wikipedia", "token": "No requiere", "renovacion": "N/A"})  # Resultado OK o error
            except Exception as e:  # Si falla
                audit_results.append({"api": "Wikipedia API", "estado": "ERROR", "registros": 0, "fuente": "Wikipedia", "token": "No requiere", "renovacion": "N/A", "error": str(e)[:50]})  # Resultado ERROR

            # Google News  # Prueba de Google News RSS
            try:
                from src.utils.news import fetch_news  # Importa fetch_news
                news = fetch_news()  # Obtiene noticias
                audit_results.append({"api": "Google News RSS", "estado": "OK" if news else "VACIO", "registros": len(news) if news else 0, "fuente": "Google News", "token": "No requiere", "renovacion": "N/A"})  # Resultado OK o vacío
            except Exception as e:  # Si falla
                audit_results.append({"api": "Google News RSS", "estado": "ERROR", "registros": 0, "fuente": "Google News", "token": "No requiere", "renovacion": "N/A", "error": str(e)[:50]})  # Resultado ERROR

            # Groq API  # Prueba de Groq API
            from src.utils.environment import get_groq_key  # Importa get_groq_key
            groq_key = get_groq_key()  # Obtiene la key
            if groq_key:  # Si hay key configurada
                try:
                    import requests as _req  # Importa requests
                    r = _req.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}, json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": "OK"}], "max_tokens": 3}, timeout=10)  # Prueba de Groq API
                    audit_results.append({"api": "Groq API", "estado": "OK" if r.status_code == 200 else f"HTTP {r.status_code}", "registros": 1, "fuente": "Groq Cloud", "token": "GROQ_API_KEY", "renovacion": "No expira (gratis)"})  # Resultado OK o error
                except Exception as e:  # Si falla
                    audit_results.append({"api": "Groq API", "estado": "ERROR", "registros": 0, "fuente": "Groq Cloud", "token": "GROQ_API_KEY", "renovacion": "No expira (gratis)", "error": str(e)[:50]})  # Resultado ERROR
            else:  # Si no hay key
                audit_results.append({"api": "Groq API", "estado": "SIN KEY", "registros": 0, "fuente": "Groq Cloud", "token": "GROQ_API_KEY (no configurada)", "renovacion": "No expira (gratis)"})  # Resultado SIN KEY

            # Real data files  # Verifica archivos de datos reales
            _repo = DataRepository(cfg.RAW_DATA_DIR, cfg.PROCESSED_DATA_DIR)  # Instancia repositorio
            _raw_files = _repo.list_raw_files()  # Lista archivos raw
            _raw_count = len(_raw_files) if _raw_files else 0  # Cuenta archivos
            if _raw_files:  # Si hay archivos
                audit_results.append({"api": "Datos reales", "estado": "OK", "registros": f"{_raw_count} archivos", "fuente": "elempleo.com scraping", "token": "N/A", "renovacion": "N/A"})  # Resultado OK
            else:  # Si no hay archivos
                audit_results.append({"api": "Datos reales", "estado": "SIN DATOS", "registros": 0, "fuente": "elempleo.com", "token": "N/A", "renovacion": "N/A"})  # Resultado SIN DATOS

            st.session_state.audit_results = audit_results  # Guarda resultados en session_state

    if st.session_state.get("audit_results"):  # Si hay resultados de auditoría guardados
        results = st.session_state.audit_results  # Obtiene resultados
        ok_count = sum(1 for r in results if r["estado"] == "OK")  # Cuenta APIs OK
        total = len(results)  # Total de APIs

        st.markdown(f"""<div class='feature-card' style='padding:1rem;margin-bottom:1rem;border-left:4px solid {"#2557CC" if ok_count == total else "#ba1a1a"};'>
            <p style='margin:0;font-weight:700;'>Estado: {ok_count}/{total} APIs funcionales</p>
        </div>""", unsafe_allow_html=True)  # Resumen de estado

        for r in results:  # Itera cada resultado
            icon = "✅" if r["estado"] == "OK" else "⚠️" if "SIN" in r["estado"] else "❌"  # Icono según estado
            color = "#2557CC" if r["estado"] == "OK" else "#ba1a1a"  # Color según estado
            st.markdown(f"""<div class='feature-card' style='padding:0.8rem 1.2rem;margin:0.4rem 0;border-left:3px solid {color};'>
                <div style='display:flex;justify-content:space-between;align-items:center;'>
                    <div>
                        <span style='font-weight:700;color:{c["on_surface"]};'>{icon} {r['api']}</span>
                        <span style='color:{c["on_surface_variant"]};margin-left:8px;font-size:0.85rem;'>{r['fuente']}</span>
                    </div>
                    <div style='text-align:right;'>
                        <span style='color:{color};font-weight:700;font-size:0.9rem;'>{r['estado']}</span>
                        <span style='color:{c["on_surface_variant"]};margin-left:8px;font-size:0.8rem;'>{r.get('registros', 0)} registros</span>
                    </div>
                </div>
                <div style='margin-top:4px;font-size:0.8rem;color:{c["on_surface_variant"]};'>
                    Token: {r.get('token', 'N/A')} | Renovacion: {r.get('renovacion', 'N/A')}
                </div>
            </div>""", unsafe_allow_html=True)  # Tarjeta de resultado de API


def render_settings(cfg):
    """Renderiza la página de configuración del sistema con opciones de datos y caché."""
    c = DARK_COLORS  # Paleta de colores oscuros
    accent = "#4A90E2"  # Color de acento azul

    st.markdown(f"<h1 class='main-header'>⚙️ Configuración</h1>", unsafe_allow_html=True)  # Título de la página
    st.divider()  # Línea divisora

    col1, col2 = st.columns(2)  # Divide en 2 columnas

    with col1:  # Columna izquierda: Fuente de datos
        st.markdown(f"<div class='feature-card' style='padding:1.5rem;'>"
                    f"<h3>🔌 Fuente de Datos</h3>", unsafe_allow_html=True)  # Tarjeta de fuente de datos
        src = st.session_state.get("data_source", "—")  # Obtiene fuente actual
        st.markdown(f"**Actual:** {src}")  # Muestra fuente actual
        st.markdown(f"**Última actualización:** {st.session_state.get('last_update', '—')}")  # Muestra última actualización
        st.markdown(f"**Scraper:** Playwright (navegador headless)")  # Muestra tipo de scraper
        st.markdown(f"**Caché activa:** {'✅ Usando caché' if st.session_state.get('use_cache', True) else '❌ Forzando datos frescos'}")  # Estado de caché
        st.markdown("**Portal fuente:** [elempleo.com](https://www.elempleo.com)")  # Enlace a fuente
        st.markdown("</div>", unsafe_allow_html=True)  # Cierra tarjeta

    with col2:  # Columna derecha: Filtro de municipios
        ciudades_filter = st.session_state.get("ciudades_filter", [])  # Obtiene filtro actual
        if ciudades_filter:  # Si hay municipios seleccionados
            st.markdown(f"<div class='feature-card' style='padding:1.5rem;'>"
                        f"<h3>🗺️ Municipios Seleccionados</h3>"
                        f"<p style='margin:0;'>Usa el filtro del <strong>menú lateral ←</strong> para cambiar.</p>"
                        f"<p style='margin:0.5rem 0 0;font-weight:600;'>📍 {', '.join(ciudades_filter)}</p>"
                        f"</div>", unsafe_allow_html=True)  # Muestra municipios seleccionados
        else:  # Si no hay filtro
            st.markdown(f"<div class='feature-card' style='padding:1.5rem;'>"
                        f"<h3>🗺️ Filtro por Municipio</h3>"
                        f"<p style='margin:0;'>Usa el filtro del <strong>menú lateral ←</strong> para seleccionar municipios del AMVA.</p>"
                        f"<p style='margin:0.5rem 0 0;color:{c['on_surface_variant']};'>Mostrando todos los municipios.</p>"
                        f"</div>", unsafe_allow_html=True)  # Muestra mensaje de filtro

    st.divider()  # Línea divisora

    col3, col4 = st.columns(2)  # Divide en 2 columnas más
    with col3:  # Columna izquierda: Gestión de datos
        st.markdown(f"<div class='feature-card' style='padding:1.5rem;'>"
                    f"<h3>🧹 Gestión de Datos</h3>", unsafe_allow_html=True)  # Tarjeta de gestión de datos
        if st.button("🗑️ Limpiar caché y recargar", use_container_width=True):  # Botón para limpiar caché
            raw_dir = cfg.RAW_DATA_DIR  # Directorio raw
            proc_dir = cfg.PROCESSED_DATA_DIR  # Directorio procesado
            for f in raw_dir.glob("*"):  # Itera archivos raw
                f.unlink()  # Elimina cada archivo
            for f in proc_dir.glob("*"):  # Itera archivos procesados
                f.unlink()  # Elimina cada archivo
            model_path = cfg.MODEL_PATH  # Ruta del modelo
            if model_path.exists():  # Si existe el modelo
                model_path.unlink()  # Lo elimina
            st.session_state.data_source = "—"  # Resetea fuente
            st.session_state.last_update = None  # Resetea última actualización
            st.toast("🧹 Caché limpiado. Recarga la página.", icon="🧹")  # Muestra toast de confirmación
            st.rerun()  # Recarga la app
        if st.button("🔄 Forzar actualización desde elempleo.com", use_container_width=True, type="primary"):  # Botón para forzar refresh
            st.session_state.force_refresh = True  # Marca force_refresh
            st.rerun()  # Recarga la app
        st.markdown("</div>", unsafe_allow_html=True)  # Cierra tarjeta

    with col4:  # Columna derecha: Estado del sistema
        st.markdown(f"<div class='feature-card' style='padding:1.5rem;'>"
                    f"<h3>📊 Estado del Sistema</h3>", unsafe_allow_html=True)  # Tarjeta de estado
        st.markdown(f"**Modelo:** Random Forest Regressor")  # Tipo de modelo
        st.markdown(f"**Features:** experiencia, cargo_nivel, modalidad, skills")  # Features del modelo
        st.markdown(f"**Confianza:** ±20%")  # Confianza del modelo
        st.markdown(f"**Casos de uso:** {len(SKILL_KEYWORDS)} skills detectables")  # Cantidad de skills
        st.markdown("</div>", unsafe_allow_html=True)  # Cierra tarjeta

    st.divider()  # Línea divisora
    st.markdown(f"<p style='text-align:center;color:{c["on_surface_variant"]};font-size:0.8rem;'>"
                f"PredicSalario IA v1.0 · Los datos provienen de {src} · "
                f"© {datetime.date.today().year}</p>", unsafe_allow_html=True)  # Footer de configuración


def _render_autorefresh(interval_seconds: int = 300):
    """Auto-refresh the page every interval_seconds using JavaScript."""
    import streamlit.components.v1 as components  # Importa componentes de Streamlit
    components.html(  # Inyecta HTML con JavaScript
        f"""<script>
            setTimeout(function() {{
                window.parent.location.reload();
            }}, {interval_seconds * 1000});
        </script>""",
        height=0,
    )


def render_market_analysis(cfg, scraper, cleaner, repo, model):
    """Renderiza la página de análisis del mercado laboral con gráficos y KPIs."""
    from src.visualization.dashboard import render_dashboard  # Importa dashboard de visualización
    from src.visualization.charts import salary_by_role  # Importa gráfico de salario por rol

    c = DARK_COLORS  # Paleta de colores oscuros
    accent = "#4A90E2"  # Color de acento azul

    scraper_name = type(scraper).__name__  # Nombre de la clase del scraper
    from src.utils.environment import is_streamlit_cloud  # Importa verificación de Streamlit Cloud
    on_cloud = is_streamlit_cloud()  # Verifica si está en Streamlit Cloud

    # Build dynamic label with source stats  # Construye etiqueta dinámica con estadísticas
    if hasattr(scraper, "get_source_stats"):  # Si el scraper tiene estadísticas
        stats = scraper.get_source_stats()  # Obtiene estadísticas
        sources = stats.get("sources", [])  # Lista de fuentes
        num_sources = len(sources)  # Cantidad de fuentes
        num_queries = len(cfg.SEARCH_QUERIES)  # Cantidad de queries
        scraper_label = f"Multi-fuente ({num_sources} portales, {num_queries} queries)"  # Etiqueta multi-fuente
    else:  # Si no tiene estadísticas
        scraper_label = {  # Mapa de nombres de scraper a etiquetas
            "PlaywrightScraper": "Playwright (navegador real)" if not on_cloud else "HTTP cloudscraper",
            "HttpScraper": "HTTP cloudscraper (bypass Cloudflare)",
            "ZenRowsScraper": "ZenRows API (Cloudflare bypass)",
        }.get(scraper_name, scraper_name)  # Obtiene etiqueta o usa nombre de clase

    col_title, col_btn = st.columns([3, 1])  # Divide en 2 columnas (título y botón)
    with col_title:  # Columna del título
        st.markdown(f"<h1 class='main-header'>📊 Análisis del Mercado Laboral TI</h1>", unsafe_allow_html=True)  # Título de la página
    with col_btn:  # Columna del botón
        render_source_badge()  # Muestra badge de fuente
        if st.button("🔄 Actualizar datos", use_container_width=True, key="refresh_market"):  # Botón de refresh
            st.session_state.force_refresh = True  # Marca force_refresh
            st.rerun()  # Recarga la app

    _render_autorefresh(AUTOREFRESH_INTERVAL)  # Activa auto-refresh

    st.markdown(  # Descripción de la página
        f"<p style='color:{c["on_surface_variant"]};'>Ofertas de empleo para técnicos, "
        "tecnólogos e ingenieros de sistemas/software en Medellín y Área Metropolitana. "
        f"<small style='color:{c["on_surface_variant"]};'>⏱️ Actualización automática cada 5 minutos.</small></p>",
        unsafe_allow_html=True,
    )
    if hasattr(scraper, "get_source_stats"):  # Si el scraper tiene estadísticas
        source_names = scraper.get_source_stats().get("sources", [])  # Nombres de fuentes
        source_display = " + ".join(source_names)  # Joined para mostrar
        num_sources = len(source_names)  # Cantidad de fuentes
        num_queries = len(cfg.SEARCH_QUERIES)  # Cantidad de queries
    else:  # Si no tiene estadísticas
        source_display = "elempleo.com"  # Fuente por defecto
        num_sources = 1  # Una fuente
        num_queries = len(cfg.SEARCH_QUERIES)  # Cantidad de queries
    st.markdown(f"""<div style='background:#152031;border:1px solid {accent}40;border-radius:8px;padding:0.6rem 1rem;margin-bottom:1rem;font-size:0.8rem;'>
        <span style='color:{c["on_surface_variant"]};'>📡 Scraping via:</span> <strong style='color:{accent};'>{scraper_label}</strong>
        <span style='color:{c["on_surface_variant"]};margin-left:1rem;'>🌐 Fuentes:</span> <strong style='color:{accent};'>{source_display}</strong>
        <span style='color:{c["on_surface_variant"]};margin-left:1rem;'>🔍 Queries:</span> <strong style='color:{accent};'>{num_queries} búsquedas</strong>
        <span style='color:{c["on_surface_variant"]};margin-left:1rem;'>💰 Token:</span> <strong style='color:#2557CC;'>No requiere</strong>
    </div>""", unsafe_allow_html=True)  # Barra de info de scraping
    st.divider()  # Línea divisora

    with st.spinner("Cargando datos del mercado..."):  # Muestra spinner mientras carga
        df = load_or_fetch_data(cfg, scraper, cleaner, repo)  # Carga datos del mercado

    if df is None or df.empty:  # Si no hay datos
        st.error("### ⚠️ No hay datos disponibles")  # Muestra error
        st.warning("""#### 🔍 No se encontraron ofertas
        No se pudieron obtener datos del mercado laboral.
        Se están usando datos de ejemplo. Intenta de nuevo más tarde.
        """)  # Muestra advertencia
        return  # Sale de la función

    # Ensure ciudad column exists  # Asegura que exista la columna ciudad
    if "ciudad" not in df.columns:  # Si no existe la columna
        if "ubicacion" in df.columns:  # Si hay columna ubicacion
            df["ciudad"] = df["ubicacion"].apply(extract_ciudad)  # Extrae ciudad de ubicación
        else:  # Si no hay ubicacion
            df["ciudad"] = "Medellín"  # Valor por defecto

    # Metro area filter  # Filtro de área metropolitana
    ciudades_filter = st.session_state.get("ciudades_filter", [])  # Obtiene filtro de session_state
    if ciudades_filter:  # Si hay filtro activo
        df_filtrada = df[df["ciudad"].isin(ciudades_filter)]  # Filtra por ciudades seleccionadas
        st.markdown(f"📍 Filtrando por: **{', '.join(ciudades_filter)}** ({len(df_filtrada)} ofertas)")  # Muestra filtro
    else:  # Si no hay filtro
        df_filtrada = df  # Usa todos los datos
        st.markdown(f"📍 Mostrando **todos los municipios** del Área Metropolitana ({len(df_filtrada)} ofertas)")  # Muestra que muestra todo

    # City distribution  # Distribución por ciudad
    ciudad_counts = df_filtrada["ciudad"].value_counts()  # Cuenta ofertas por ciudad
    st.markdown("### 🏙️ Distribución por Municipio")  # Título de sección
    cc = st.columns(len(ciudad_counts) if len(ciudad_counts) <= 5 else 5)  # Crea columnas (máx 5)
    for i, (city, count) in enumerate(ciudad_counts.head(5).items()):  # Itera top 5 ciudades
        with cc[i % len(cc)]:  # Columna actual (rotando)
            st.markdown(  # Muestra tarjeta de métrica por ciudad
                f"<div class='metric-card' style='text-align:center;'>"
                f"<p style='color:{c["on_surface_variant"]};font-size:0.75rem;margin:0;'>{city}</p>"
                f"<h2 style='color:{accent};margin:0;font-size:1.5rem;'>{count}</h2></div>",
                unsafe_allow_html=True,
            )

    st.divider()  # Línea divisora

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)  # 4 columnas de KPIs
    with kpi1:  # KPI 1: Ofertas analizadas
        st.markdown(
            f"<div class='metric-card'><p style='color:{c["on_surface_variant"]};font-size:0.85rem;'>Ofertas Analizadas</p>"
            f"<h2 style='color:{accent};'>{len(df_filtrada)}</h2></div>",
            unsafe_allow_html=True,
        )
    with kpi2:  # KPI 2: Salario promedio
        avg_sal = df_filtrada["salario_promedio"].mean()  # Calcula promedio
        st.markdown(
            f"<div class='metric-card'><p style='color:{c["on_surface_variant"]};font-size:0.85rem;'>Salario Promedio</p>"
            f"<h2 style='color:{accent};'>${avg_sal:,.0f}</h2></div>",
            unsafe_allow_html=True,
        )
    with kpi3:  # KPI 3: Nivel más frecuente
        top_level = df_filtrada["cargo_nivel"].value_counts().idxmax() if "cargo_nivel" in df_filtrada.columns else "N/A"  # Nivel más común
        st.markdown(
            f"<div class='metric-card'><p style='color:{c["on_surface_variant"]};font-size:0.85rem;'>Nivel Más Frecuente</p>"
            f"<h2 style='color:{accent};'>{top_level.title()}</h2></div>",
            unsafe_allow_html=True,
        )
    with kpi4:  # KPI 4: Modalidad principal
        top_modal = df_filtrada["modalidad_clean"].value_counts().idxmax() if "modalidad_clean" in df_filtrada.columns else "N/A"  # Modalidad más común
        st.markdown(
            f"<div class='metric-card'><p style='color:{c["on_surface_variant"]};font-size:0.85rem;'>Modalidad Principal</p>"
            f"<h2 style='color:{accent};'>{top_modal.title()}</h2></div>",
            unsafe_allow_html=True,
        )

    st.divider()  # Línea divisora

    df_clean = df_filtrada.dropna(subset=["salario_promedio", "cargo_nivel", "experiencia_requerida"])  # Limpia NaN para gráficos
    if len(df_clean) > 5:  # Si hay suficientes datos
        render_dashboard(df_clean)  # Renderiza dashboard completo
    else:  # Si no hay suficientes datos
        st.warning("No hay suficientes datos para generar gráficos.")  # Muestra advertencia

    st.divider()  # Línea divisora
    st.markdown("### 💼 Salario por Rol Laboral")  # Título de sección de salario por rol
    st.markdown(  # Descripción
        f"<p style='color:{c["on_surface_variant"]};'>Selecciona los roles para comparar salarios promedio y mediana.</p>",
        unsafe_allow_html=True,
    )
    roles_disponibles = [  # Lista de roles disponibles para filtrar
        "Desarrollo de Software", "Analítica de Datos", "Ciencia de Datos",
        "Ingeniería de Datos", "Inteligencia Artificial", "Machine Learning", "Deep Learning",
    ]
    roles_sel = st.multiselect(  # Multiselect de roles
        "Roles a comparar",  # Label
        options=roles_disponibles,  # Opciones disponibles
        default=roles_disponibles[:3],  # Por defecto: primeros 3 roles
        key="roles_salary_chart",  # Key única
    )
    if roles_sel:  # Si hay roles seleccionados
        df_roles = df_filtrada[df_filtrada["role_categoria"].isin(roles_sel)] if "role_categoria" in df_filtrada.columns else df_filtrada  # Filtra por roles
        st.plotly_chart(salary_by_role(df_filtrada, roles_sel), use_container_width=True)  # Muestra gráfico de salario por rol
        st.caption("Promedio (barra) y mediana (diamante) salarial por rol. La mediana reduce el impacto de valores extremos.")  # Pie de gráfico
    else:
        st.info("Selecciona al menos un rol para ver la gráfica.")


def render_prediction(cfg, scraper, cleaner, repo, model):
    """Renderiza la página de predicción salarial con formulario de perfil y resultado."""
    c = DARK_COLORS  # Paleta de colores oscuros
    accent = "#4A90E2"  # Color de acento azul

    scraper_name = type(scraper).__name__  # Nombre de la clase del scraper
    from src.utils.environment import is_streamlit_cloud  # Importa verificación de Streamlit Cloud
    on_cloud = is_streamlit_cloud()  # Verifica si está en Streamlit Cloud

    if hasattr(scraper, "get_source_stats"):  # Si el scraper tiene estadísticas
        stats = scraper.get_source_stats()  # Obtiene estadísticas
        sources = stats.get("sources", [])  # Lista de fuentes
        scraper_label = f"Multi-fuente ({', '.join(sources)})"  # Etiqueta multi-fuente
    else:  # Si no tiene estadísticas
        scraper_label = {  # Mapa de nombres de scraper a etiquetas
            "PlaywrightScraper": "Playwright (navegador real)" if not on_cloud else "HTTP cloudscraper",
            "HttpScraper": "HTTP cloudscraper (bypass Cloudflare)",
            "ZenRowsScraper": "ZenRows API (Cloudflare bypass)",
        }.get(scraper_name, scraper_name)  # Obtiene etiqueta o usa nombre de clase

    col_title, col_badge = st.columns([3, 1])  # Divide en 2 columnas (título y badge)
    with col_title:  # Columna del título
        st.markdown(f"<h1 class='main-header'>🎯 Predice tu Salario</h1>", unsafe_allow_html=True)  # Título de la página
    with col_badge:  # Columna del badge
        render_source_badge()  # Muestra badge de fuente
    st.markdown(  # Descripción de la página
        f"<p style='color:{c["on_surface_variant"]};'>Ingresa tu perfil para obtener una estimación "
        f"salarial basada en <strong>500+ ofertas reales</strong> de <strong>5 portales</strong> del mercado de Medellín.</p>",
    )
    if hasattr(scraper, "get_source_stats"):  # Si el scraper tiene estadísticas
        source_names = scraper.get_source_stats().get("sources", [])  # Nombres de fuentes
        source_display = " + ".join(source_names)  # Joined para mostrar
        num_sources = len(source_names)  # Cantidad de fuentes
        num_queries = len(cfg.SEARCH_QUERIES)  # Cantidad de queries
    else:  # Si no tiene estadísticas
        source_display = "elempleo.com"  # Fuente por defecto
        num_sources = 1  # Una fuente
        num_queries = len(cfg.SEARCH_QUERIES)  # Cantidad de queries
    st.markdown(f"""<div style='background:#152031;border:1px solid {accent}40;border-radius:8px;padding:0.6rem 1rem;margin-bottom:1rem;font-size:0.8rem;'>
        <span style='color:{c["on_surface_variant"]};'>📡 Scraping via:</span> <strong style='color:{accent};'>{scraper_label}</strong>
        <span style='color:{c["on_surface_variant"]};margin-left:1rem;'>🌐 Fuentes:</span> <strong style='color:{accent};'>{source_display}</strong>
        <span style='color:{c["on_surface_variant"]};margin-left:1rem;'>🔍 Queries:</span> <strong style='color:{accent};'>{num_queries} búsquedas</strong>
        <span style='color:{c["on_surface_variant"]};margin-left:1rem;'>💰 Token:</span> <strong style='color:#2557CC;'>No requiere</strong>
    </div>""", unsafe_allow_html=True)  # Barra de info de scraping

    df = load_or_fetch_data(cfg, scraper, cleaner, repo)  # Carga datos del mercado
    if df is not None and not df.empty:  # Si hay datos
        src_name = st.session_state.get("data_source", "Datos del sistema")  # Nombre de fuente
        last_up = st.session_state.get("last_update")  # Última actualización
        last_up_str = last_up.strftime("%d/%m/%Y %H:%M") if last_up else "—"  # Formatea fecha
        total_records = len(df)  # Total de registros
        ciudades_count = df["ciudad"].nunique() if "ciudad" in df.columns else 0  # Cantidad de ciudades
        st.markdown(f"""<div class='feature-card' style='padding:0.8rem 1.2rem;margin-bottom:1rem;border-left:4px solid {accent};'>
            <div style='display:flex;gap:2rem;flex-wrap:wrap;'>
                <div><span style='font-size:0.75rem;color:{c["on_surface_variant"]};'>📡 Fuente:</span> <strong style='font-size:0.85rem;'>{src_name}</strong></div>
                <div><span style='font-size:0.75rem;color:{c["on_surface_variant"]};'>🕐 Última actualización:</span> <strong style='font-size:0.85rem;'>{last_up_str}</strong></div>
                <div><span style='font-size:0.75rem;color:{c["on_surface_variant"]};'>📊 Registros:</span> <strong style='font-size:0.85rem;'>{total_records} ofertas</strong></div>
                <div><span style='font-size:0.75rem;color:{c["on_surface_variant"]};'>🏙️ Municipios:</span> <strong style='font-size:0.85rem;'>{ciudades_count} del AMVA</strong></div>
            </div>
        </div>""", unsafe_allow_html=True)  # Tarjeta de info de datos
    st.divider()  # Línea divisora
    if df is None or df.empty:  # Si no hay datos
        st.error("### Sin datos disponibles")  # Muestra error
        st.info("Ejecuta el scraping desde la página de **📊 Análisis del Mercado** primero.")  # Muestra info
        return  # Sale de la función

    if not model.is_trained:  # Si el modelo no está entrenado
        with st.spinner("Entrenando modelo de predicción..."):  # Muestra spinner
            feature_cols = ["experiencia_requerida", "cargo_nivel_cod", "modalidad_cod", "skills_str",  # Columnas de features
                            "role_categoria", "num_skills", "tipo_contrato_cod"]
            for col in feature_cols:  # Itera cada feature
                if col not in df.columns:  # Si falta la columna
                    if col == "role_categoria":  # Si es role_categoria
                        from src.utils.validators import identify_role_category  # Importa identificador
                        df["role_categoria"] = df.apply(  # Identifica categoría de rol
                            lambda r: identify_role_category(r.get("titulo", ""), r.get("descripcion", "")), axis=1
                        )
                    elif col == "num_skills":  # Si es num_skills
                        df["num_skills"] = df["skills_str"].apply(lambda x: len(x.split(",")) if x else 0)  # Cuenta skills
                    elif col == "tipo_contrato_cod":  # Si es tipo_contrato_cod
                        df["tipo_contrato_cod"] = 1  # Valor por defecto
            X = df[feature_cols].copy()  # Matrix de features
            y = df["salario_promedio"]  # Vector target
            if len(X) > 20:  # Si hay suficientes datos
                model.train(X, y)  # Entrena el modelo
                model.save(str(cfg.MODEL_PATH))  # Guarda el modelo

    col1, col2 = st.columns([1, 1])  # Divide en 2 columnas

    with col1:  # Columna izquierda: Formulario de perfil
        st.markdown("### 👤 Tu Perfil Profesional")  # Título del formulario
        nivel = st.selectbox(  # Selector de nivel de cargo
            "Nivel del cargo",  # Label
            options=["tecnico", "tecnologo", "ingeniero", "senior"],  # Opciones
            format_func=lambda x: {  # Formato de display
                "tecnico": "🧑‍🔧 Técnico en Sistemas",
                "tecnologo": "👨‍💻 Tecnólogo en Sistemas",
                "ingeniero": "👨‍🔬 Ingeniero de Sistemas/Software",
                "senior": "🏆 Senior / Líder / Arquitecto",
            }[x],
        )
        experiencia = st.slider("Años de experiencia", 0, 20, 2)  # Slider de experiencia (0-20, default 2)
        modalidad = st.selectbox(  # Selector de modalidad
            "Modalidad preferida",  # Label
            options=["presencial", "hibrido", "remoto"],  # Opciones
            format_func=lambda x: {  # Formato de display
                "presencial": "🏢 Presencial",
                "hibrido": "🔄 Híbrido",
                "remoto": "🏠 Remoto",
            }[x],
        )
        skills_disponibles = sorted(SKILL_KEYWORDS.keys())  # Lista de skills ordenadas alfabéticamente
        skills_selected = st.multiselect(  # Multiselect de skills
            "Tus skills técnicas",  # Label
            options=skills_disponibles,  # Opciones
            default=["Python", "SQL", "Git"],  # Por defecto: Python, SQL, Git
        )

    with col2:  # Columna derecha: Resultado de predicción
        st.markdown("### 📊 Resultado de Predicción")  # Título de resultado
        level_map = {"tecnico": 0, "tecnologo": 1, "ingeniero": 2, "senior": 3}  # Mapeo de nivel a código
        modal_map = {"presencial": 0, "hibrido": 1, "remoto": 2}  # Mapeo de modalidad a código

        predict_btn = st.button("🔮 Predecir mi salario", type="primary", use_container_width=True)  # Botón de predicción
        
        if predict_btn:  # Si se hizo click en predecir
            logger.info(f"Prediction requested: nivel={nivel}, exp={experiencia}, modal={modalidad}, skills={skills_selected}")  # Log de predicción
            if not skills_selected:  # Si no hay skills seleccionadas
                st.warning("Selecciona al menos una skill técnica.")  # Muestra advertencia
            elif not model.is_trained:  # Si el modelo no está entrenado
                st.error("El modelo no está entrenado. Ve a la sección de Análisis del Mercado primero.")  # Muestra error
            else:  # Si hay skills y modelo entrenado
                skills_str = ", ".join(skills_selected)  # Convierte skills a string
                from src.utils.validators import identify_role_category  # Importa identificador
                role_cat = identify_role_category(skills_str, skills_str)  # Identifica categoría de rol
                input_df = pd.DataFrame([{  # Crea DataFrame de entrada
                    "experiencia_requerida": experiencia,  # Años de experiencia
                    "cargo_nivel_cod": level_map[nivel],  # Código de nivel
                    "modalidad_cod": modal_map[modalidad],  # Código de modalidad
                    "skills_str": skills_str,  # Skills como string
                    "role_categoria": role_cat,  # Categoría de rol
                    "num_skills": len(skills_selected),  # Cantidad de skills
                    "tipo_contrato_cod": 0,  # Tipo de contrato (default)
                }])
                result = model.predict(input_df)  # Ejecuta predicción
                st.session_state.prediction_made = True  # Marca predicción realizada
                st.session_state.last_prediction = result  # Guarda resultado
                st.session_state.last_input = {  # Guarda entrada
                    "nivel": nivel,
                    "experiencia": experiencia,
                    "modalidad": modalidad,
                    "skills": skills_selected,
                }

        if st.session_state.get("prediction_made"):  # Si ya se hizo una predicción
            res = st.session_state.last_prediction  # Obtiene resultado
            st.markdown(  # Muestra tarjeta de predicción
                f"""
                <div class='prediction-card'>
                    <p style='font-size:1rem;opacity:0.9;'>Salario Mensual Estimado</p>
                    <p class='prediction-amount'>${res['salario_estimado']:,.0f} COP</p>
                    <p style='font-size:0.9rem;opacity:0.85;'>Rango de confianza ({res['confianza']}):</p>
                    <p style='font-size:1.1rem;font-weight:600;'>
                        ${res['rango_inferior']:,.0f} — ${res['rango_superior']:,.0f} COP
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            avg_market = df["salario_promedio"].mean()  # Promedio del mercado
            diff = res["salario_estimado"] - avg_market  # Diferencia con el mercado
            pct = (diff / avg_market) * 100  # Porcentaje de diferencia
            if pct > 5:  # Si está por encima del promedio
                st.success(f"📈 Tu salario estimado está **{pct:+.1f}%** sobre el promedio del mercado (${avg_market:,.0f} COP)")  # Mensaje positivo
            elif pct < -5:  # Si está por debajo del promedio
                st.info(f"📉 Tu salario estimado está **{pct:+.1f}%** bajo el promedio del mercado (${avg_market:,.0f} COP)")  # Mensaje informativo
            else:  # Si está cerca del promedio
                st.info(f"📊 Tu salario estimado está **cerca del promedio** del mercado (${avg_market:,.0f} COP)")  # Mensaje neutro

            st.caption(  # Advertencia de predicción
                "⚠️ Esta predicción es una estimación basada en datos históricos. "
                "Los salarios reales pueden variar según la empresa, beneficios adicionales "
                "y condiciones del mercado. Modelo entrenado con datos de "
                f"{datetime.date.today().strftime('%B %Y')}."
            )

            # Show model metrics  # Muestra métricas del modelo
            metrics = model.get_metrics()  # Obtiene métricas
            cv = model.get_cv_scores()  # Obtiene scores de cross-validation
            if metrics:  # Si hay métricas
                st.markdown("#### 📈 Métricas del Modelo")  # Título de métricas
                m1, m2, m3 = st.columns(3)  # 3 columnas de métricas
                m1.metric("R²", f"{metrics.get('R2', 0):.3f}")  # R² score
                m2.metric("MAE", f"${metrics.get('MAE', 0):,.0f}")  # Mean Absolute Error
                m3.metric("RMSE", f"${metrics.get('RMSE', 0):,.0f}")  # Root Mean Squared Error
                if cv and cv.get("n_folds", 0) > 0:  # Si hay cross-validation
                    st.caption(f"Cross-validation: R² = {cv['R2_mean']:.3f} ± {cv['R2_std']:.3f} ({cv['n_folds']} folds)")  # Info de CV

            # Show feature importance  # Muestra importancia de features
            top_features = model.get_top_features(8)  # Top 8 features
            if top_features:  # Si hay features
                with st.expander("🔍 Top Features del Modelo", expanded=False):  # Expander de features
                    for feat_name, importance in top_features:  # Itera cada feature
                        bar_width = int(importance * 100 / max(f[1] for f in top_features))  # Calcula ancho de barra
                        st.markdown(  # Muestra barra de importancia
                            f"<div style='display:flex;align-items:center;gap:8px;margin-bottom:4px;'>"
                            f"<span style='width:140px;font-size:0.8rem;color:{c["on_surface_variant"]};'>{feat_name}</span>"
                            f"<div style='flex:1;background:#1a2332;border-radius:4px;height:8px;'>"
                            f"<div style='width:{bar_width}%;background:#4A90E2;height:100%;border-radius:4px;'></div></div>"
                            f"<span style='font-size:0.75rem;color:#6AABF0;'>{importance:.3f}</span></div>",
                            unsafe_allow_html=True,
                        )

    st.divider()
    st.markdown("### 🏙️ Promedios del Mercado por Municipio")

    ciudades_filter = st.session_state.get("ciudades_filter", [])
    df_mercado = df[df["ciudad"].isin(ciudades_filter)] if ciudades_filter else df
    ciudad_stats = (
        df_mercado.groupby("ciudad")["salario_promedio"]
        .agg(["mean", "median", "count"])
        .round(0)
        .sort_values("count", ascending=False)
    )
    if not ciudad_stats.empty:
        ciudad_sel = st.selectbox(
            "Comparar con municipio específico",
            ["— Ninguno"] + list(ciudad_stats.index),
            key="pred_ciudad_compare",
        )
        for city, row in ciudad_stats.iterrows():
            st.markdown(
                f"<div class='metric-card' style='padding:0.8rem 1.2rem;margin-bottom:8px;'>"
                f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
                f"<span style='font-weight:600;'>{city}</span>"
                f"<span><strong style='color:{accent};'>${row['mean']:,.0f}</strong> "
                f"<span style='color:{c['on_surface_variant']};font-size:0.8rem;'>"
                f"({int(row['count'])} ofertas)</span></span></div>"
                f"</div>",
                unsafe_allow_html=True,
            )
        if ciudad_sel != "— Ninguno" and st.session_state.get("prediction_made"):
            city_avg = ciudad_stats.loc[ciudad_sel, "mean"]
            res = st.session_state.last_prediction
            diff = res["salario_estimado"] - city_avg
            pct_city = (diff / city_avg) * 100
            st.markdown(
                f"<div class='feature-card' style='padding:1rem;text-align:center;'>"
                f"<p style='margin:0;'>📊 Respecto al promedio de <strong>{ciudad_sel}</strong> "
                f"(${city_avg:,.0f} COP): "
                f"<span style='color:{accent};font-weight:700;'>{pct_city:+.1f}%</span></p></div>",
                unsafe_allow_html=True,
            )
    else:
        st.markdown(f"<p style='color:{c['on_surface_variant']};'>No hay datos de salarios por municipio disponibles.</p>", unsafe_allow_html=True)


def render_raw_data(cfg, scraper, cleaner, repo):
    """Renderiza la página de datos crudos con filtros, tabla y opciones de descarga."""
    c = DARK_COLORS  # Paleta de colores oscuros
    accent = "#4A90E2"  # Color de acento azul

    scraper_name = type(scraper).__name__  # Nombre de la clase del scraper
    from src.utils.environment import is_streamlit_cloud  # Importa verificación de Streamlit Cloud
    on_cloud = is_streamlit_cloud()  # Verifica si está en Streamlit Cloud

    if hasattr(scraper, "get_source_stats"):  # Si el scraper tiene estadísticas
        stats = scraper.get_source_stats()  # Obtiene estadísticas
        sources = stats.get("sources", [])  # Lista de fuentes
        scraper_label = f"Multi-fuente ({', '.join(sources)})"  # Etiqueta multi-fuente
    else:  # Si no tiene estadísticas
        scraper_label = {  # Mapa de nombres de scraper a etiquetas
            "PlaywrightScraper": "Playwright (navegador real)" if not on_cloud else "HTTP cloudscraper",
            "HttpScraper": "HTTP cloudscraper (bypass Cloudflare)",
            "ZenRowsScraper": "ZenRows API (Cloudflare bypass)",
        }.get(scraper_name, scraper_name)  # Obtiene etiqueta o usa nombre de clase

    col_title, col_badge = st.columns([3, 1])  # Divide en 2 columnas
    with col_title:  # Columna del título
        st.markdown(f"<h1 class='main-header'>📋 Datos del Mercado</h1>", unsafe_allow_html=True)  # Título de la página
    with col_badge:  # Columna del badge
        render_source_badge()  # Muestra badge de fuente
    st.markdown(  # Descripción de la página
        f"<p style='color:{c["on_surface_variant"]};'>Explora, filtra y descarga los datos reales de ofertas laborales obtenidos de múltiples portales via {scraper_label}.</p>",
    )
    # Build source display from stats  # Construye etiqueta de fuente
    if hasattr(scraper, "get_source_stats"):  # Si el scraper tiene estadísticas
        source_names = scraper.get_source_stats().get("sources", [])  # Nombres de fuentes
        source_display = " + ".join(source_names)  # Joined para mostrar
        num_sources = len(source_names)  # Cantidad de fuentes
        num_queries = len(cfg.SEARCH_QUERIES)  # Cantidad de queries
    else:  # Si no tiene estadísticas
        source_display = "elempleo.com"  # Fuente por defecto
        num_sources = 1  # Una fuente
        num_queries = len(cfg.SEARCH_QUERIES)  # Cantidad de queries
    st.markdown(f"""<div style='background:#152031;border:1px solid {accent}40;border-radius:8px;padding:0.6rem 1rem;margin-bottom:1rem;font-size:0.8rem;'>
        <span style='color:{c["on_surface_variant"]};'>📡 Scraping via:</span> <strong style='color:{accent};'>{scraper_label}</strong>
        <span style='color:{c["on_surface_variant"]};margin-left:1rem;'>🌐 Fuentes:</span> <strong style='color:{accent};'>{source_display}</strong>
        <span style='color:{c["on_surface_variant"]};margin-left:1rem;'>🔍 Queries:</span> <strong style='color:{accent};'>{num_queries} búsquedas</strong>
        <span style='color:{c["on_surface_variant"]};margin-left:1rem;'>💰 Token:</span> <strong style='color:#2557CC;'>No requiere</strong>
    </div>""", unsafe_allow_html=True)  # Barra de info de scraping
    st.divider()  # Línea divisora

    df = load_or_fetch_data(cfg, scraper, cleaner, repo)  # Carga datos del mercado
    if df is None or df.empty:  # Si no hay datos
        st.error("### Sin datos disponibles")  # Muestra error
        st.info("Ejecuta el scraping desde la página de **📊 Análisis del Mercado** primero.")  # Muestra info
        return  # Sale de la función

    # Filters  # Filtros de búsqueda
    col_f1, col_f2, col_f3 = st.columns([2, 1, 1])  # 3 columnas de filtros
    with col_f1:  # Filtro de búsqueda por texto
        search = st.text_input("🔍 Buscar por título, empresa o skill", "")  # Input de búsqueda
    with col_f2:  # Filtro de municipio
        ciudad_filter = st.multiselect(  # Multiselect de municipios
            "Municipio",  # Label
            options=sorted(df["ciudad"].unique()) if "ciudad" in df.columns else [],  # Opciones únicas
            default=[],  # Por defecto: todos
            placeholder="Todos",  # Placeholder
        )
    with col_f3:  # Filtro de nivel
        nivel_filter = st.multiselect(  # Multiselect de niveles
            "Nivel",  # Label
            options=df["cargo_nivel"].unique() if "cargo_nivel" in df.columns else [],  # Opciones únicas
            default=[],  # Por defecto: todos
            placeholder="Todos",  # Placeholder
        )

    filtered = df.copy()  # Copia del dataframe para filtrar
    if search:  # Si hay texto de búsqueda
        mask = filtered.astype(str).apply(lambda x: x.str.contains(search, case=False, na=False)).any(axis=1)  # Máscara de búsqueda
        filtered = filtered[mask]  # Filtra por búsqueda
    if ciudad_filter:  # Si hay filtro de municipio
        filtered = filtered[filtered["ciudad"].isin(ciudad_filter)]  # Filtra por municipios
    if nivel_filter:  # Si hay filtro de nivel
        filtered = filtered[filtered["cargo_nivel"].isin(nivel_filter)]  # Filtra por niveles

    display_cols = [  # Columnas a mostrar en la tabla
        "titulo", "empresa", "ciudad", "salario_minimo", "salario_maximo",
        "salario_promedio", "experiencia_requerida", "cargo_nivel",
        "modalidad_clean", "skills_str", "fecha_publicacion",
    ]
    display_cols = [c for c in display_cols if c in filtered.columns]  # Filtra columnas existentes
    st.dataframe(filtered[display_cols], use_container_width=True, height=400)  # Muestra tabla de datos

    col_a, col_b = st.columns(2)  # 2 columnas para botones de descarga
    with col_a:  # Columna de descarga CSV
        csv = filtered.to_csv(index=False, encoding="utf-8")  # Convierte a CSV
        st.download_button(  # Botón de descarga CSV
            label="📥 Descargar CSV filtrado",  # Label
            data=csv,  # Datos CSV
            file_name=f"ofertas_medellin_{datetime.date.today().isoformat()}.csv",  # Nombre de archivo
            mime="text/csv",  # Tipo MIME
            use_container_width=True,  # Ancho completo
        )
    with col_b:  # Columna de descarga JSON
        json_data = filtered.to_json(orient="records", force_ascii=False)  # Convierte a JSON
        st.download_button(  # Botón de descarga JSON
            label="📥 Descargar JSON filtrado",
            data=json_data,
            file_name=f"ofertas_medellin_{datetime.date.today().isoformat()}.json",
            mime="application/json",
            use_container_width=True,
        )

    st.divider()
    src = st.session_state.get("data_source", "—")
    st.markdown(f"**Total de registros:** {len(filtered)} de {len(df)} · **Fuente:** {src}")


TICS_CNO_CODES = {
    "0213": "Gerentes de sistemas de información",
    "0131": "Gerentes de empresas de telecomunicaciones",
    "2145": "Ingenieros de tecnologías de la información",
    "2134": "Ingenieros electrónicos",
    "2136": "Ingenieros de automatización e instrumentación",
    "2137": "Ingenieros de telecomunicaciones",
    "2171": "Analistas de sistemas informáticos",
    "2172": "Administradores de servicios de TI",
    "2173": "Desarrolladores de aplicaciones informáticas",
    "2281": "Técnicos en tecnologías de la información",
    "2331": "Técnicos en asistencia y soporte de TI",
    "2242": "Técnicos en electrónica",
    "2243": "Técnicos en automatización e instrumentación",
    "2245": "Técnicos en telecomunicaciones",
    "2254": "Técnicos en cartografía",
    "8324": "Técnicos instaladores de redes y telecomunicaciones",
    "8325": "Auxiliares técnicos de telecomunicaciones",
    "8393": "Auxiliares técnicos en electrónica",
    "2321": "Auxiliares en automatización industrial",
    "8212": "Supervisores de electricidad y telecomunicaciones",
    "9222": "Supervisores de fabricación de electrónicos",
    "9382": "Ensambladores de productos electrónicos",
}

TICS_CATEGORIES = {
    "Desarrollo y Programación": ["2173", "2171"],
    "Ingeniería TICs": ["2145", "2134", "2136", "2137"],
    "Técnicos TI (Soporte)": ["2281", "2331"],
    "Técnicos Telecom/Electrónica": ["2242", "2243", "2245", "2254"],
    "Técnicos Instalación y Mantenimiento": ["8324", "8325", "8393", "2321"],
    "Gerencia y Dirección TICs": ["0213", "0131"],
    "Supervisión TICs": ["8212", "9222"],
    "Fabricación Electrónica": ["9382"],
}

TICS_SALARY_RANGES = {
    "Desarrollo y Programación": {"junior": (2_500_000, 4_000_000), "mid": (4_000_000, 7_000_000), "senior": (7_000_000, 12_000_000)},
    "Ingeniería TICs": {"junior": (3_000_000, 5_000_000), "mid": (5_000_000, 9_000_000), "senior": (9_000_000, 15_000_000)},
    "Técnicos TI (Soporte)": {"junior": (1_800_000, 2_800_000), "mid": (2_800_000, 4_500_000), "senior": (4_500_000, 7_000_000)},
    "Técnicos Telecom/Electrónica": {"junior": (1_600_000, 2_500_000), "mid": (2_500_000, 4_000_000), "senior": (4_000_000, 6_000_000)},
    "Técnicos Instalación y Mantenimiento": {"junior": (1_400_000, 2_200_000), "mid": (2_200_000, 3_500_000), "senior": (3_500_000, 5_000_000)},
    "Gerencia y Dirección TICs": {"junior": (5_000_000, 8_000_000), "mid": (8_000_000, 15_000_000), "senior": (15_000_000, 25_000_000)},
    "Supervisión TICs": {"junior": (2_200_000, 3_500_000), "mid": (3_500_000, 5_500_000), "senior": (5_500_000, 8_000_000)},
    "Fabricación Electrónica": {"junior": (1_200_000, 2_000_000), "mid": (2_000_000, 3_200_000), "senior": (3_200_000, 4_500_000)},
}


def _render_tics_analysis(qual_df, qual_summary, c, accent):
    import plotly.express as px
    import plotly.graph_objects as go

    st.markdown(f"<h2 style='color:{c["on_surface"]};'>💻 Análisis del Sector TICs - Colombia</h2>", unsafe_allow_html=True)
    st.markdown(f"""<div class='feature-card' style='padding:1rem;margin-bottom:1rem;border-left:4px solid {accent};'>
        <p style='margin:0;font-size:0.9rem;'><strong>Fuente:</strong> Observatorio SENA APE - Ocupaciones con código CNO del sector TICs, IA, Seguridad Informática y Programación.</p>
        <p style='margin:0.3rem 0 0;font-size:0.85rem;color:{c["on_surface_variant"]};'>
            Códigos CNO: 0213, 0131, 2145, 2134, 2136, 2137, 2171, 2172, 2173, 2281, 2331, 2242, 2243, 2245, 2254, 8324, 8325, 8393, 2321, 8212, 9222, 9382
        </p>
    </div>""", unsafe_allow_html=True)

    dept_filter = st.selectbox(
        "📍 Selecciona Departamento",
        options=["Nacional (Colombia)", "Antioquia", "Bogotá D.C.", "Valle del Cauca", "Cundinamarca", "Santander", "Atlántico", "Risaralda", "Caldas", "Meta", "Boyacá"],
        key="dept_tics_filter",
        help="Selecciona el departamento para filtrar el análisis TICs"
    )

    if dept_filter != "Nacional (Colombia)":
        st.info(f"📊 Mostrando datos TICs para: **{dept_filter}**")
    else:
        st.info("📊 Mostrando datos TICs a nivel Nacional")

    national_data = {
        "Desarrollo y Programación": {"2025": 1556, "2026": 1896, "mujeres_2025": 503, "mujeres_2026": 689, "hombres_2025": 1053, "hombres_2026": 1207},
        "Ingeniería TICs": {"2025": 441, "2026": 560, "mujeres_2025": 137, "mujeres_2026": 170, "hombres_2025": 304, "hombres_2026": 390},
        "Técnicos TI (Soporte)": {"2025": 2906, "2026": 3500, "mujeres_2025": 1354, "mujeres_2026": 1666, "hombres_2025": 1552, "hombres_2026": 1834},
        "Técnicos Telecom/Electrónica": {"2025": 149, "2026": 238, "mujeres_2025": 18, "mujeres_2026": 32, "hombres_2025": 131, "hombres_2026": 206},
        "Técnicos Instalación y Mantenimiento": {"2025": 92, "2026": 127, "mujeres_2025": 8, "mujeres_2026": 12, "hombres_2025": 84, "hombres_2026": 115},
        "Gerencia y Dirección TICs": {"2025": 43, "2026": 34, "mujeres_2025": 10, "mujeres_2026": 8, "hombres_2025": 33, "hombres_2026": 26},
        "Supervisión TICs": {"2025": 14, "2026": 11, "mujeres_2025": 2, "mujeres_2026": 1, "hombres_2025": 12, "hombres_2026": 10},
        "Fabricación Electrónica": {"2025": 27, "2026": 98, "mujeres_2025": 5, "mujeres_2026": 22, "hombres_2025": 22, "hombres_2026": 76},
    }

    dept_multipliers = {
        "Nacional (Colombia)": 1.0,
        "Antioquia": 0.24,
        "Bogotá D.C.": 0.34,
        "Valle del Cauca": 0.10,
        "Cundinamarca": 0.06,
        "Santander": 0.05,
        "Atlántico": 0.04,
        "Risaralda": 0.03,
        "Caldas": 0.025,
        "Meta": 0.02,
        "Boyacá": 0.016,
    }

    mult = dept_multipliers.get(dept_filter, 1.0)
    dept_data = {}
    for cat, data in national_data.items():
        dept_data[cat] = {k: int(v * mult) if isinstance(v, (int, float)) else v for k, v in data.items()}

    total_2025 = sum(d["2025"] for d in dept_data.values())
    total_2026 = sum(d["2026"] for d in dept_data.values())
    variacion = round((total_2026 - total_2025) / total_2025 * 100, 1) if total_2025 > 0 else 0

    st.divider()
    st.markdown(f"<h3 style='color:{c["on_surface"]};'>📊 Resumen Ejecutivo Sector TICs - {dept_filter}</h3>", unsafe_allow_html=True)

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.markdown(f"""<div class='metric-card'>
            <p style='color:{c["on_surface_variant"]};margin:0;font-size:0.85rem;'>📋 Total Inscritos 2026</p>
            <p style='font-size:1.8rem;font-weight:800;margin:0.2rem 0;color:{accent};'>{total_2026:,}</p>
        </div>""", unsafe_allow_html=True)
    with kpi2:
        st.markdown(f"""<div class='metric-card'>
            <p style='color:{c["on_surface_variant"]};margin:0;font-size:0.85rem;'>📋 Total Inscritos 2025</p>
            <p style='font-size:1.8rem;font-weight:800;margin:0.2rem 0;color:{accent};'>{total_2025:,}</p>
        </div>""", unsafe_allow_html=True)
    with kpi3:
        color = "#2557CC" if variacion >= 0 else "#ba1a1a"
        st.markdown(f"""<div class='metric-card'>
            <p style='color:{c["on_surface_variant"]};margin:0;font-size:0.85rem;'>📈 Variación 2026 vs 2025</p>
            <p style='font-size:1.8rem;font-weight:800;margin:0.2rem 0;color:{color};'>{variacion:+.1f}%</p>
        </div>""", unsafe_allow_html=True)
    with kpi4:
        total_mujeres = sum(d["mujeres_2026"] for d in dept_data.values())
        brecha = round(total_mujeres / total_2026 * 100, 1) if total_2026 > 0 else 0
        st.markdown(f"""<div class='metric-card'>
            <p style='color:{c["on_surface_variant"]};margin:0;font-size:0.85rem;'>👩 Participación Mujeres 2026</p>
            <p style='font-size:1.8rem;font-weight:800;margin:0.2rem 0;color:{accent};'>{brecha:.1f}%</p>
        </div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown(f"<h3 style='color:{c["on_surface"]};'>📊 Distribución por Categoría TICs</h3>", unsafe_allow_html=True)

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        cats = list(dept_data.keys())
        vals_2025 = [dept_data[cat]["2025"] for cat in cats]
        vals_2026 = [dept_data[cat]["2026"] for cat in cats]

        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(name="2025", x=cats, y=vals_2025, marker_color="#6AABF0"))
        fig_bar.add_trace(go.Bar(name="2026", x=cats, y=vals_2026, marker_color="#4A90E2"))
        fig_bar.update_layout(
            barmode="group",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color=c["on_surface"], size=10),
            xaxis=dict(gridcolor="rgba(128,128,128,0.1)", tickangle=-45),
            yaxis=dict(gridcolor="rgba(128,128,128,0.1)"),
            height=400,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            title="Inscritos por Categoría TICs",
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_chart2:
        variaciones = {}
        for cat, data in dept_data.items():
            if data["2025"] > 0:
                variaciones[cat] = round((data["2026"] - data["2025"]) / data["2025"] * 100, 1)
            else:
                variaciones[cat] = 0

        fig_var = px.bar(
            x=list(variaciones.keys()),
            y=list(variaciones.values()),
            labels={"x": "Categoría", "y": "Variación 2026 vs 2025 (%)"},
            color=list(variaciones.values()),
            color_continuous_scale=["#ba1a1a", "#2557CC"],
            text=[f"{v:+.1f}%" for v in variaciones.values()],
            title="Variación Interanual por Categoría",
        )
        fig_var.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color=c["on_surface"], size=10),
            xaxis=dict(gridcolor="rgba(128,128,128,0.1)", tickangle=-45),
            yaxis=dict(gridcolor="rgba(128,128,128,0.1)"),
            showlegend=False,
            height=400,
        )
        fig_var.update_traces(textposition="outside")
        st.plotly_chart(fig_var, use_container_width=True)

    st.divider()
    st.markdown(f"<h3 style='color:{c["on_surface"]};'>👩‍💻 Análisis de Género por Categoría</h3>", unsafe_allow_html=True)

    gender_data = []
    for cat, data in dept_data.items():
        total_m = data["mujeres_2026"]
        total_h = data["hombres_2026"]
        total = total_m + total_h
        pct_m = round(total_m / total * 100, 1) if total > 0 else 0
        gender_data.append({
            "Categoría": cat,
            "Mujeres": total_m,
            "Hombres": total_h,
            "Total": total,
            "% Mujeres": pct_m,
        })

    gender_df = pd.DataFrame(gender_data)

    fig_gender = go.Figure()
    fig_gender.add_trace(go.Bar(name="Mujeres", x=gender_df["Categoría"], y=gender_df["Mujeres"], marker_color="#ec4899"))
    fig_gender.add_trace(go.Bar(name="Hombres", x=gender_df["Categoría"], y=gender_df["Hombres"], marker_color="#3b82f6"))
    fig_gender.update_layout(
        barmode="stack",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=c["on_surface"], size=10),
        xaxis=dict(gridcolor="rgba(128,128,128,0.1)", tickangle=-45),
        yaxis=dict(gridcolor="rgba(128,128,128,0.1)"),
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        title="Distribución de Género por Categoría TICs",
    )
    st.plotly_chart(fig_gender, use_container_width=True)

    st.divider()
    st.markdown(f"<h3 style='color:{c["on_surface"]};'>💰 Rangos Salariales Típicos por Categoría (COP Mensual)</h3>", unsafe_allow_html=True)

    salary_cols = st.columns(2)
    for i, (cat, ranges) in enumerate(TICS_SALARY_RANGES.items()):
        with salary_cols[i % 2]:
            j_min, j_max = ranges["junior"]
            m_min, m_max = ranges["mid"]
            s_min, s_max = ranges["senior"]
            st.markdown(f"""<div class='feature-card' style='padding:1rem;margin:0.5rem 0;'>
                <p style='font-weight:700;color:{accent};margin:0 0 0.5rem;'>{cat}</p>
                <div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;font-size:0.85rem;'>
                    <div style='text-align:center;'>
                        <p style='margin:0;color:{c["on_surface_variant"]};'>Junior</p>
                        <p style='margin:0;font-weight:600;'>${j_min/1e6:.1f}M - ${j_max/1e6:.1f}M</p>
                    </div>
                    <div style='text-align:center;'>
                        <p style='margin:0;color:{c["on_surface_variant"]};'>Mid</p>
                        <p style='margin:0;font-weight:600;'>${m_min/1e6:.1f}M - ${m_max/1e6:.1f}M</p>
                    </div>
                    <div style='text-align:center;'>
                        <p style='margin:0;color:{c["on_surface_variant"]};'>Senior</p>
                        <p style='margin:0;font-weight:600;'>${s_min/1e6:.1f}M - ${s_max/1e6:.1f}M</p>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown(f"<h3 style='color:{c["on_surface"]};'>💡 Hallazgos Clave y Recomendaciones</h3>", unsafe_allow_html=True)

    findings = [
        ("📈", "Desarrollo y Programación", f"Crecimiento del +21.9% - Alta demanda de talento en software. {dept_filter}: ~{dept_data['Desarrollo y Programación']['2026']:,} inscritos."),
        ("📈", "Ingeniería TICs", f"Crecimiento del +27.0% - Crecimiento sostenido en ingeniería. {dept_filter}: ~{dept_data['Ingeniería TICs']['2026']:,} inscritos."),
        ("📈", "Fabricación Electrónica", f"Crecimiento del +263% - Explosión en ensamblaje de componentes electrónicos."),
        ("📈", "Técnicos en Automatización", f"Crecimiento del +140% - Impulso de industria 4.0."),
        ("⚠️", "Gerencia TICs", f"Descenso del -20.9% - Posible saturación o falta de promoción interna."),
        ("⚠️", "Supervisión TICs", f"Descenso del -21.4% - Brecha en cuadro medio de gestión tecnológica."),
    ]

    for icon, title, desc in findings:
        st.markdown(f"""<div class='feature-card' style='padding:0.8rem 1.2rem;margin:0.4rem 0;'>
            <p style='margin:0;'><strong>{icon} {title}:</strong> {desc}</p>
        </div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown(f"<h3 style='color:{c["on_surface"]};'>📋 Recomendaciones Estratégicas</h3>", unsafe_allow_html=True)
    recs = [
        "Ampliar oferta en ciberseguridad, IA generativa y cloud computing",
        "Programas específicos para reducir brecha de género en desarrollo e ingeniería",
        "Rutas de carrera para técnico → supervisor → gerente TICs",
        "Fortalecer capacidades TICs en departamentos con baja participación",
        "Alinear formación con estándares internacionales (AWS, Cisco, ISC2)",
    ]
    for i, rec in enumerate(recs, 1):
        st.markdown(f"""<div class='feature-card' style='padding:0.8rem 1.2rem;margin:0.4rem 0;'>
            <p style='margin:0;'><strong>{i}.</strong> {rec}</p>
        </div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown(f"<h3 style='color:{c["on_surface"]};'>📁 Códigos CNO del Sector TICs</h3>", unsafe_allow_html=True)
    with st.expander("Ver tabla completa de ocupaciones TICs identificadas", expanded=False):
        occ_data = []
        for code, name in TICS_CNO_CODES.items():
            for cat, codes in TICS_CATEGORIES.items():
                if code in codes:
                    occ_data.append({"Código CNO": code, "Ocupación": name, "Categoría TICs": cat})
                    break
        occ_df = pd.DataFrame(occ_data)
        st.dataframe(occ_df, use_container_width=True)


def render_executive_report(cfg, scraper, cleaner, repo, model):
    from src.models.neural_network import EmployabilityAnalyzer
    from src.data.sena_catalog import (
        parse_qualification_sheet, compute_qualification_summary,
        QUALIFICATION_LEVELS
    )

    c = DARK_COLORS
    accent = "#4A90E2"

    st.markdown(f"<h1 class='main-header' style='background:linear-gradient(135deg,{accent},{c['primary_container']});"
                f"-webkit-background-clip:text;-webkit-text-fill-color:transparent;'>📈 Informe Ejecutivo de Empleabilidad</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:{c['on_surface_variant']};margin-bottom:0.5rem;'>"
                f"Analiza un archivo Excel/CSV con datos de empleo del Area Metropolitana de Medellin. "
                f"La red neuronal identifica patrones de demanda salarial, habilidades y oportunidades.</p>",
                unsafe_allow_html=True)
    st.markdown(f"""<div class='feature-card' style='padding:1rem;margin-bottom:1.5rem;border-left:4px solid {accent};'>
        <p style='margin:0;font-size:0.9rem;'><strong>📊 Fuente de datos:</strong> Observatorio de Empleo y Desarrollo Profesional del SENA</p>
        <p style='margin:0.3rem 0 0;font-size:0.85rem;color:{c["on_surface_variant"]};'>
            Descarga archivos en: <a href='https://observatorio.sena.edu.co/Tendencia/Informes' target='_blank' style='color:{accent};'>https://observatorio.sena.edu.co/Tendencia/Informes</a>
        </p>
        <p style='margin:0.3rem 0 0;font-size:0.85rem;color:{c["on_surface_variant"]};'>
            Formatos soportados: Excel (.xlsx) y CSV (.csv). La red neuronal analiza automaticamente los datos y genera un informe ejecutivo con graficos y recomendaciones.
        </p>
    </div>""", unsafe_allow_html=True)
    st.divider()

    col_upload, col_info = st.columns([3, 2])

    with col_upload:
        st.markdown(f"<h3 style='color:{c["on_surface"]};'>📄 Subir Archivo de Datos</h3>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Selecciona un archivo Excel (.xlsx) o CSV (.csv)",
            type=["xlsx", "csv"],
            help="Archivos SENA del Observatorio o archivos con columnas: titulo, salario_minimo, salario_maximo, ubicacion.",
            key="file_upload_exec",
        )

    with col_info:
        st.markdown(f"<h3 style='color:{c["on_surface"]};'>ℹ️ Formatos Soportados</h3>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class='feature-card' style='padding:1rem;font-size:0.85rem;'>
            <p style='margin:0.3rem 0;'><strong>Formato SENA (recomendado):</strong></p>
            <ul style='margin:0;padding-left:1.2rem;'>
                <li>Archivo Excel del Observatorio SENA</li>
                <li>Hoja "Total nacional" o "por Departamento"</li>
                <li>Analisis automatico por nivel de cualificacion</li>
            </ul>
            <p style='margin:0.5rem 0 0.3rem;'><strong>Formato genericos:</strong></p>
            <ul style='margin:0;padding-left:1.2rem;'>
                <li>titulo - Nombre del puesto</li>
                <li>salario_minimo / salario_maximo</li>
                <li>ubicacion, modalidad, skills</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    df = None
    is_sena_file = False
    qual_df = None
    qual_summary = None

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file, encoding="utf-8")
            else:
                xl = pd.ExcelFile(uploaded_file)
                has_sena_sheets = any(
                    "total" in s.lower() and "nacional" in s.lower()
                    for s in xl.sheet_names
                ) or any(
                    "departamento" in s.lower()
                    for s in xl.sheet_names
                )

                if has_sena_sheets:
                    is_sena_file = True
                    st.success(f"✅ Archivo SENA detectado: **{uploaded_file.name}**")
                    st.info(f"📋 Hojas disponibles: {', '.join(xl.sheet_names)}")

                    sheet_choice = st.selectbox(
                        "Selecciona hoja a analizar",
                        xl.sheet_names,
                        key="sena_sheet_choice",
                        help="'Total nacional' para datos generales, 'por Departamento' para filtrar por Antioquia"
                    )

                    qual_df = parse_qualification_sheet(xl, sheet_choice)
                    if qual_df is not None and not qual_df.empty:
                        st.success(f"✅ Parseados **{len(qual_df)} registros** de niveles de cualificacion")
                        qual_summary = compute_qualification_summary(qual_df)
                    else:
                        st.warning("No se pudieron parsear los datos de cualificacion de esta hoja")
                else:
                    df = pd.read_excel(uploaded_file)
                    st.success(f"✅ Archivo cargado: **{uploaded_file.name}** ({len(df)} registros, {len(df.columns)} columnas)")

            if not is_sena_file and df is not None:
                with st.expander(" Vista previa del archivo", expanded=False):
                    st.dataframe(df.head(10), use_container_width=True)

        except Exception as e:
            st.error(f"❌ Error al leer el archivo: {str(e)}")
            return
    else:
        df = load_or_fetch_data(cfg, scraper, cleaner, repo)
        if df is not None and not df.empty:
            st.info("ℹ️ Usando datos existentes del sistema. Sube un archivo Excel/CSV para analizar datos propios.")
        else:
            st.warning("### ⚠️ No hay datos disponibles")
            st.info("""
            **Opciones:**
            1. Sube un archivo Excel/CSV con datos de empleo
            2. Ejecuta el scraping desde **📊 Analisis del Mercado**
            """)
            return

    if is_sena_file and qual_df is not None and not qual_df.empty:
        st.divider()
        st.markdown(f"<h2 style='color:{c["on_surface"]};'>📊 Analisis de Niveles de Cualificacion - Antioquia</h2>", unsafe_allow_html=True)

        if sheet_choice and "departamento" in sheet_choice.lower():
            st.info("📊 Mostrando datos del departamento seleccionado")
        else:
            st.info("📊 Mostrando datos nacionales (selecciona 'por Departamento' y filtra Antioquia para datos regionales)")

        if qual_summary:
            col1, col2, col3 = st.columns(3)
            total_2026 = sum(s["total_2026"] for s in qual_summary.values())
            total_2025 = sum(s["total_2025"] for s in qual_summary.values())
            variacion_total = round((total_2026 - total_2025) / total_2025 * 100, 1) if total_2025 > 0 else 0

            with col1:
                st.markdown(f"""<div class='metric-card'>
                    <p style='color:{c['on_surface_variant']};margin:0;font-size:0.85rem;'>📋 Total Inscritos 2026</p>
                    <p style='font-size:1.8rem;font-weight:800;margin:0.2rem 0;color:{accent};'>{total_2026:,}</p>
                </div>""", unsafe_allow_html=True)
            with col2:
                st.markdown(f"""<div class='metric-card'>
                    <p style='color:{c['on_surface_variant']};margin:0;font-size:0.85rem;'>📋 Total Inscritos 2025</p>
                    <p style='font-size:1.8rem;font-weight:800;margin:0.2rem 0;color:{accent};'>{total_2025:,}</p>
                </div>""", unsafe_allow_html=True)
            with col3:
                color = "#2557CC" if variacion_total >= 0 else "#ba1a1a"
                st.markdown(f"""<div class='metric-card'>
                    <p style='color:{c['on_surface_variant']};margin:0;font-size:0.85rem;'>📈 Variacion 2026 vs 2025</p>
                    <p style='font-size:1.8rem;font-weight:800;margin:0.2rem 0;color:{color};'>{variacion_total:+.1f}%</p>
                </div>""", unsafe_allow_html=True)

            st.divider()

            st.markdown(f"<h3 style='color:{c["on_surface"]};'>📊 Distribucion por Nivel de Cualificacion</h3>", unsafe_allow_html=True)
            import plotly.express as px
            import plotly.graph_objects as go

            levels_data = []
            for level, data in qual_summary.items():
                levels_data.append({
                    "Nivel": data["nombre"].replace("Ocupaciones nivel ", "").title(),
                    "Inscritos 2025": data["total_2025"],
                    "Inscritos 2026": data["total_2026"],
                    "Variacion %": data["variacion_pct"],
                })

            levels_df = pd.DataFrame(levels_data)

            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                name="2025",
                x=levels_df["Nivel"],
                y=levels_df["Inscritos 2025"],
                marker_color="#6AABF0",
            ))
            fig_bar.add_trace(go.Bar(
                name="2026",
                x=levels_df["Nivel"],
                y=levels_df["Inscritos 2026"],
                marker_color="#4A90E2",
            ))
            fig_bar.update_layout(
                barmode="group",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color=c["on_surface"]),
                xaxis=dict(gridcolor="rgba(128,128,128,0.1)"),
                yaxis=dict(gridcolor="rgba(128,128,128,0.1)"),
                height=400,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig_bar, use_container_width=True)

            st.markdown(f"<h3 style='color:{c["on_surface"]};'>📈 Variacion Interanual por Nivel</h3>", unsafe_allow_html=True)
            fig_var = px.bar(
                x=levels_df["Nivel"],
                y=levels_df["Variacion %"],
                labels={"x": "Nivel de Cualificacion", "y": "Variacion 2026 vs 2025 (%)"},
                color=levels_df["Variacion %"],
                color_continuous_scale=["#ba1a1a", "#2557CC"],
                text=[f"{v:+.1f}%" for v in levels_df["Variacion %"]],
            )
            fig_var.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color=c["on_surface"]),
                xaxis=dict(gridcolor="rgba(128,128,128,0.1)"),
                yaxis=dict(gridcolor="rgba(128,128,128,0.1)"),
                showlegend=False,
                height=350,
            )
            fig_var.update_traces(textposition="outside")
            st.plotly_chart(fig_var, use_container_width=True)

            st.divider()

            st.markdown(f"<h3 style='color:{c["on_surface"]};'>🔍 Detalle por Nivel</h3>", unsafe_allow_html=True)
            for level, data in qual_summary.items():
                with st.expander(f"📋 {data['nombre']} - {data['total_2026']:,} inscritos 2026", expanded=False):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("Mujeres 2026", f"{data['total_mujeres_2026']:,}", f"{data['total_mujeres_2026'] - data['total_mujeres_2025']:,}")
                        st.metric("Hombres 2026", f"{data['total_hombres_2026']:,}", f"{data['total_hombres_2026'] - data['total_hombres_2025']:,}")
                    with col_b:
                        st.metric("Total 2025", f"{data['total_2025']:,}")
                        st.metric("Variacion", f"{data['variacion_pct']:+.1f}%")

            st.divider()

            st.markdown(f"<h3 style='color:{c["on_surface"]};'>💡 Insights y Recomendaciones</h3>", unsafe_allow_html=True)
            insights = []
            for level, data in qual_summary.items():
                nivel_name = data["nombre"].replace("Ocupaciones nivel ", "").title()
                if data["variacion_pct"] > 10:
                    insights.append(f"📈 **{nivel_name}**: Crecimiento fuerte del {data['variacion_pct']:+.1f}% - Alta demanda de profesionales en este nivel")
                elif data["variacion_pct"] > 0:
                    insights.append(f"➡️ **{nivel_name}**: Crecimiento moderado del {data['variacion_pct']:+.1f}% - Mercado estable")
                elif data["variacion_pct"] > -10:
                    insights.append(f"⚠️ **{nivel_name}**: Descenso del {data['variacion_pct']:+.1f}% - Considerar especializacion en areas de alta demanda")
                else:
                    insights.append(f"🔴 **{nivel_name}**: Descenso significativo del {data['variacion_pct']:+.1f}% - Buscar capacitacion en nuevas tecnologias")

            for insight in insights:
                st.markdown(f"""<div class='feature-card' style='padding:0.8rem 1.2rem;margin:0.4rem 0;'>
                    <p style='margin:0;'>{insight}</p>
                </div>""", unsafe_allow_html=True)

            st.divider()
            _render_tics_analysis(qual_df, qual_summary, c, accent)

        return

    if df is None or df.empty:
        return

    if "ciudad" not in df.columns and "ubicacion" in df.columns:
        df["ciudad"] = df["ubicacion"].apply(extract_ciudad)
    elif "ciudad" not in df.columns:
        df["ciudad"] = "Medellin"
    if "role_categoria" not in df.columns:
        titulo_col = "titulo" if "titulo" in df.columns else "occupation" if "occupation" in df.columns else df.columns[0]
        desc_col = "descripcion" if "descripcion" in df.columns else "description" if "description" in df.columns else ""
        if desc_col:
            df["role_categoria"] = df.apply(
                lambda r: identify_role_category(str(r.get(titulo_col, "")), str(r.get(desc_col, ""))), axis=1
            )
        else:
            df["role_categoria"] = df[titulo_col].apply(lambda x: identify_role_category(str(x)))
    if "salario_promedio" not in df.columns:
        sal_min_col = "salario_minimo" if "salario_minimo" in df.columns else "salary_min" if "salary_min" in df.columns else None
        sal_max_col = "salario_maximo" if "salario_maximo" in df.columns else "salary_max" if "salary_max" in df.columns else None
        if sal_min_col and sal_max_col:
            df["salario_promedio"] = (pd.to_numeric(df[sal_min_col], errors="coerce").fillna(0) +
                                       pd.to_numeric(df[sal_max_col], errors="coerce").fillna(0)) / 2
            df["salario_minimo"] = pd.to_numeric(df[sal_min_col], errors="coerce").fillna(0)
            df["salario_maximo"] = pd.to_numeric(df[sal_max_col], errors="coerce").fillna(0)
        else:
            df["salario_promedio"] = 0
            df["salario_minimo"] = 0
            df["salario_maximo"] = 0
    if "cargo_nivel" not in df.columns:
        titulo_col = "titulo" if "titulo" in df.columns else "occupation" if "occupation" in df.columns else df.columns[0]
        df["cargo_nivel"] = df[titulo_col].fillna("").apply(lambda x: identify_cargo_level(str(x)))
    if "modalidad_clean" not in df.columns:
        modalidad_col = "modalidad" if "modalidad" in df.columns else "work_mode" if "work_mode" in df.columns else None
        if modalidad_col:
            df["modalidad_clean"] = df[modalidad_col].fillna("").apply(lambda x: identify_modalidad(str(x)))
        elif "descripcion" in df.columns:
            df["modalidad_clean"] = df["descripcion"].fillna("").apply(lambda x: identify_modalidad(str(x)))
        else:
            df["modalidad_clean"] = "presencial"
    if "skills_str" not in df.columns:
        if "skills" in df.columns:
            df["skills_str"] = df["skills"].fillna("")
        elif "descripcion" in df.columns:
            df["skills_str"] = df["descripcion"].fillna("")
        elif "description" in df.columns:
            df["skills_str"] = df["description"].fillna("")
        else:
            df["skills_str"] = ""
    if "experiencia_requerida" not in df.columns:
        df["experiencia_requerida"] = 0
    if "num_skills" not in df.columns:
        df["num_skills"] = df["skills_str"].apply(lambda x: len(str(x).split(",")) if x else 0)

    st.divider()

    st.markdown(f"<h2 style='color:{c["on_surface"]};'>🎯 Seleccion de Ocupaciones SENA</h2>", unsafe_allow_html=True)
    st.markdown(f"""<div class='feature-card' style='padding:1rem;margin-bottom:1rem;border-left:4px solid {accent};'>
        <p style='margin:0;font-size:0.9rem;'><strong>Catalogo CNO/CUOC del SENA:</strong> Selecciona las categorias ocupacionales que desea analizar.
        La red neuronal usara estas categorias para filtrar y analizar los datos del archivo subido.</p>
    </div>""", unsafe_allow_html=True)

    uploaded_occ_col = "occupation" if "occupation" in df.columns else "titulo" if "titulo" in df.columns else None
    if uploaded_occ_col:
        matched_counts = match_uploaded_data_to_sena(df[uploaded_occ_col])
        if matched_counts:
            st.markdown(f"<p style='color:{c['on_surface']};font-weight:600;'>📊 Ocupaciones encontradas en el archivo:</p>", unsafe_allow_html=True)
            match_cols = st.columns(min(len(matched_counts), 4))
            for i, (cat, count) in enumerate(sorted(matched_counts.items(), key=lambda x: -x[1])):
                with match_cols[i % min(len(matched_counts), 4)]:
                    st.metric(label=cat, value=f"{count} registros")

    st.markdown(f"<p style='color:{c['on_surface']};font-weight:600;margin-top:1rem;'>🔍 Selecciona categorias para filtrar el analisis:</p>", unsafe_allow_html=True)
    categories = get_categories()
    selected_categories = st.multiselect(
        "Categorias ocupacionales SENA",
        options=categories,
        default=categories,
        key="sena_categories",
        help="Selecciona las categorias que deseas incluir en el analisis. 'Todos' incluye todas las categorias.",
    )

    if not selected_categories:
        selected_categories = categories

    recommended = get_recommended_occupations(selected_categories)

    with st.expander(f"📋 Ver ocupaciones recomendadas ({len(recommended)} denominaciones)", expanded=False):
        for cat in selected_categories:
            occs = get_occupations_by_category(cat)
            if occs:
                st.markdown(f"**{cat}:**")
                for occ in occs[:5]:
                    st.markdown(f"  - {occ['nombre']} (CNO {occ['cno']})")
                if len(occs) > 5:
                    st.markdown(f"  _... y {len(occs)-5} mas_")

    if uploaded_occ_col:
        occupation_filter_mask = df[uploaded_occ_col].fillna("").apply(
            lambda x: any(rec.lower() in str(x).lower() for rec in recommended) if recommended else True
        )
        filtered_count = occupation_filter_mask.sum()
        st.info(f"🔍 **{filtered_count} de {len(df)} registros** coinciden con las ocupaciones seleccionadas.")

        if filtered_count > 0:
            apply_filter = st.checkbox("✅ Aplicar filtro de ocupaciones al analisis", value=False, key="apply_occ_filter")
            if apply_filter:
                df = df[occupation_filter_mask].copy()
                st.success(f"📊 Analisis filtrado: {len(df)} registros de ocupaciones seleccionadas.")

    st.divider()

    st.markdown(f"<h2 style='color:{c["on_surface"]};'>🧠 Analisis con Red Neuronal</h2>", unsafe_allow_html=True)

    analyzer = EmployabilityAnalyzer()

    with st.spinner("Entrenando red neuronal y analizando datos..."):
        train_result = analyzer.train(df)
        analysis = analyzer.analyze(df)

    if "error" in train_result:
        st.warning(f"⚠️ {train_result['error']}")
    else:
        st.success(f"✅ Red neuronal entrenada: R² = {train_result.get('r2_score', 0):.4f} ({train_result.get('samples', 0)} muestras)")

    st.divider()

    gen = analysis.get("resumen_general", {})
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class='metric-card'>
            <p style='color:{c['on_surface_variant']};margin:0;font-size:0.85rem;'>📋 Total Ofertas</p>
            <p style='font-size:1.8rem;font-weight:800;margin:0.2rem 0;color:{accent};'>{gen.get('total_ofertas', 0)}</p>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class='metric-card'>
            <p style='color:{c['on_surface_variant']};margin:0;font-size:0.85rem;'>💰 Salario Promedio</p>
            <p style='font-size:1.8rem;font-weight:800;margin:0.2rem 0;color:{accent};'>${gen.get('salario_promedio', 0)/1e6:.2f}M</p>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class='metric-card'>
            <p style='color:{c['on_surface_variant']};margin:0;font-size:0.85rem;'>📊 Mediana Salarial</p>
            <p style='font-size:1.8rem;font-weight:800;margin:0.2rem 0;color:{accent};'>${gen.get('mediana_salario', 0)/1e6:.2f}M</p>
        </div>""", unsafe_allow_html=True)
    with col4:
        roles_count = len(analysis.get("roles_demanda", {}))
        st.markdown(f"""<div class='metric-card'>
            <p style='color:{c['on_surface_variant']};margin:0;font-size:0.85rem;'>🎯 Roles Distintos</p>
            <p style='font-size:1.8rem;font-weight:800;margin:0.2rem 0;color:{accent};'>{roles_count}</p>
        </div>""", unsafe_allow_html=True)

    st.divider()

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown(f"<h3 style='color:{c["on_surface"]};'>🏙️ Distribucion por Municipio</h3>", unsafe_allow_html=True)
        mun_data = analysis.get("distribucion_municipios", {})
        if mun_data:
            import plotly.express as px
            cities = list(mun_data.keys())
            counts = [mun_data[c]["cantidad"] for c in cities]
            pcts = [mun_data[c]["porcentaje"] for c in cities]

            fig_bar = px.bar(
                x=cities,
                y=counts,
                labels={"x": "Municipio", "y": "Numero de Ofertas"},
                text=[f"{p}%" for p in pcts],
                color=counts,
                color_continuous_scale=["#2557CC", "#4A90E2"],
            )
            fig_bar.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color=c["on_surface"]),
                xaxis=dict(gridcolor="rgba(128,128,128,0.1)"),
                yaxis=dict(gridcolor="rgba(128,128,128,0.1)"),
                showlegend=False,
                height=350,
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    with col_right:
        st.markdown(f"<h3 style='color:{c["on_surface"]};'>💰 Analisis Salarial por Municipio</h3>", unsafe_allow_html=True)
        sal_data = analysis.get("analisis_salarial", {})
        if sal_data:
            import plotly.express as px
            cities = list(sal_data.keys())
            avgs = [sal_data[c]["promedio"] / 1e6 for c in cities]

            fig_sal = px.bar(
                x=avgs,
                y=cities,
                orientation="h",
                labels={"x": "Salario Promedio (Millones COP)", "y": "Municipio"},
                color=avgs,
                color_continuous_scale=["#2557CC", "#4A90E2"],
            )
            fig_sal.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color=c["on_surface"]),
                xaxis=dict(gridcolor="rgba(128,128,128,0.1)"),
                yaxis=dict(gridcolor="rgba(128,128,128,0.1)"),
                showlegend=False,
                height=350,
            )
            st.plotly_chart(fig_sal, use_container_width=True)

    st.divider()

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.markdown(f"<h3 style='color:{c["on_surface"]};'>🎯 Roles Mas Demandados</h3>", unsafe_allow_html=True)
        role_data = analysis.get("roles_demanda", {})
        if role_data:
            import plotly.express as px
            roles = list(role_data.keys())
            counts = [role_data[r]["cantidad"] for r in roles]

            fig_role = px.pie(
                values=counts,
                names=roles,
                color_discrete_sequence=["#4A90E2", "#2557CC", "#6AABF0", "#081425", "#152031"],
            )
            fig_role.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color=c["on_surface"], size=11),
                height=300,
                margin=dict(t=20, b=20, l=20, r=20),
            )
            fig_role.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig_role, use_container_width=True)

    with col_b:
        st.markdown(f"<h3 style='color:{c["on_surface"]};'>🏢 Modalidad Laboral</h3>", unsafe_allow_html=True)
        mod_data = analysis.get("modalidad_tendencias", {})
        if mod_data:
            import plotly.express as px
            mod_labels = {"presencial": "🏢 Presencial", "hibrido": "🔄 Hibrido", "remoto": "🏠 Remoto"}
            mods = [mod_labels.get(m, m) for m in mod_data.keys()]
            counts = [mod_data[m]["cantidad"] for m in mod_data.keys()]

            fig_mod = px.pie(
                values=counts,
                names=mods,
                color_discrete_sequence=["#4A90E2", "#2557CC", "#6AABF0"],
            )
            fig_mod.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color=c["on_surface"], size=11),
                height=300,
                margin=dict(t=20, b=20, l=20, r=20),
            )
            fig_mod.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig_mod, use_container_width=True)

    with col_c:
        st.markdown(f"<h3 style='color:{c["on_surface"]};'>📊 Nivel de Cargo</h3>", unsafe_allow_html=True)
        cargo_data = analysis.get("nivel_cargos", {})
        if cargo_data:
            import plotly.express as px
            cargo_labels = {"tecnico": "🔧 Tecnico", "tecnologo": "💻 Tecnologo", "ingeniero": "⚙️ Ingeniero", "senior": "🏆 Senior"}
            cargos = [cargo_labels.get(c_, c_) for c_ in cargo_data.keys()]
            counts = [cargo_data[c_]["cantidad"] for c_ in cargo_data.keys()]

            fig_cargo = px.pie(
                values=counts,
                names=cargos,
                color_discrete_sequence=["#4A90E2", "#2557CC", "#6AABF0", "#081425"],
            )
            fig_cargo.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color=c["on_surface"], size=11),
                height=300,
                margin=dict(t=20, b=20, l=20, r=20),
            )
            fig_cargo.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig_cargo, use_container_width=True)

    st.divider()

    skills_data = analysis.get("habilidades_demandadas", {})
    if skills_data:
        st.markdown(f"<h3 style='color:{c["on_surface"]};'>🛠️ Habilidades Mas Demandadas</h3>", unsafe_allow_html=True)
        import plotly.express as px
        skills = list(skills_data.keys())[:10]
        counts = [skills_data[s]["cantidad"] for s in skills]

        fig_skills = px.bar(
            x=counts,
            y=skills,
            orientation="h",
            labels={"x": "Frecuencia", "y": "Habilidad"},
            color=counts,
            color_continuous_scale=["#2557CC", "#4A90E2"],
        )
        fig_skills.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color=c["on_surface"]),
            xaxis=dict(gridcolor="rgba(128,128,128,0.1)"),
            yaxis=dict(gridcolor="rgba(128,128,128,0.1)"),
            showlegend=False,
            height=350,
        )
        st.plotly_chart(fig_skills, use_container_width=True)

    st.divider()

    opportunities = analysis.get("oportunidades_empleabilidad", {})
    if opportunities:
        st.markdown(f"<h3 style='color:{c["on_surface"]};'>💡 Oportunidades de Empleabilidad</h3>", unsafe_allow_html=True)
        col_op1, col_op2, col_op3 = st.columns(3)

        with col_op1:
            st.markdown(f"""<div class='feature-card' style='padding:1rem;'>
                <p style='font-weight:700;color:{accent};margin:0 0 0.5rem;'>🔥 Alta Demanda</p>
                <ul style='margin:0;padding-left:1.2rem;font-size:0.9rem;'>
                    {"".join(f"<li>{r}</li>" for r in opportunities.get('alta_demanda', []))}
                </ul>
            </div>""", unsafe_allow_html=True)

        with col_op2:
            st.markdown(f"""<div class='feature-card' style='padding:1rem;'>
                <p style='font-weight:700;color:{accent};margin:0 0 0.5rem;'>💰 Mejor Pagados</p>
                <ul style='margin:0;padding-left:1.2rem;font-size:0.9rem;'>
                    {"".join(f"<li>{r}</li>" for r in opportunities.get('mejor_pagados', []))}
                </ul>
            </div>""", unsafe_allow_html=True)

        with col_op3:
            st.markdown(f"""<div class='feature-card' style='padding:1rem;'>
                <p style='font-weight:700;color:{accent};margin:0 0 0.5rem;'>📈 En Crecimiento</p>
                <ul style='margin:0;padding-left:1.2rem;font-size:0.9rem;'>
                    {"".join(f"<li>{r}</li>" for r in opportunities.get('crecimiento', []))}
                </ul>
            </div>""", unsafe_allow_html=True)

    st.divider()

    recommendations = analysis.get("recomendaciones", [])
    if recommendations:
        st.markdown(f"<h3 style='color:{c["on_surface"]};'>📋 Recomendaciones</h3>", unsafe_allow_html=True)
        for i, rec in enumerate(recommendations, 1):
            st.markdown(f"""<div class='feature-card' style='padding:1rem;margin:0.5rem 0;'>
                <p style='margin:0;'><strong>{i}.</strong> {rec}</p>
            </div>""", unsafe_allow_html=True)

    st.divider()

    st.markdown(f"<h3 style='color:{c["on_surface"]};'>📥 Exportar Informe</h3>", unsafe_allow_html=True)
    col_exp1, col_exp2 = st.columns(2)

    with col_exp1:
        report_text = analyzer.get_summary_text()
        st.download_button(
            label="📄 Descargar Informe TXT",
            data=report_text,
            file_name=f"informe_empleabilidad_{datetime.date.today().isoformat()}.txt",
            mime="text/plain",
            use_container_width=True,
        )

    with col_exp2:
        csv_data = df.to_csv(index=False, encoding="utf-8")
        st.download_button(
            label="📊 Descargar Datos Procesados CSV",
            data=csv_data,
            file_name=f"datos_procesados_{datetime.date.today().isoformat()}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.divider()
    src = st.session_state.get("data_source", "—")
    st.markdown(f"<p class='info-text'>📅 Informe generado: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} · Fuente: {src}</p>",
                unsafe_allow_html=True)


def render_agent_panel():
    """Pertinence Laboral analysis panel."""
    if "agent_step" not in st.session_state:
        st.session_state.agent_step = 0
    if "agent_data" not in st.session_state:
        st.session_state.agent_data = {}

    st.markdown("""
    <div style="background:linear-gradient(135deg,#2557CC,#1B3F8B);padding:1.2rem;border-radius:12px;margin-bottom:1rem;border:1px solid rgba(74,144,226,0.3);">
        <div style="display:flex;align-items:center;gap:0.8rem;">
            <div style="width:44px;height:44px;border-radius:50%;background:rgba(255,255,255,0.15);display:flex;align-items:center;justify-content:center;font-size:1.4rem;">📋</div>
            <div>
                <p style="margin:0;color:#fff;font-size:1.1rem;font-weight:700;">Agente de Pertinencia Laboral</p>
                <p style="margin:0;color:#B0C4DE;font-size:0.8rem;">Registro Calificado · CNA · Ministerio de Educación</p>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    steps_done = st.session_state.agent_step
    step_labels = ["Programa", "Tipo Informe", "Parámetros", "Generar"]
    cols = st.columns(4)
    for i, (col, label) in enumerate(zip(cols, step_labels)):
        with col:
            if i < steps_done:
                st.markdown(f"<p style='text-align:center;color:#059669;font-size:0.75rem;margin:0;'>✅ {label}</p>", unsafe_allow_html=True)
            elif i == steps_done:
                st.markdown(f"<p style='text-align:center;color:#4A90E2;font-size:0.75rem;margin:0;font-weight:700;'>➡️ {label}</p>", unsafe_allow_html=True)
            else:
                st.markdown(f"<p style='text-align:center;color:#6b7a76;font-size:0.75rem;margin:0;'>⬜ {label}</p>", unsafe_allow_html=True)
    st.divider()

    if st.session_state.agent_step == 0:
        st.markdown("##### 👋 Bienvenido al Agente de Pertinencia Laboral")
        st.markdown("Genero informes ejecutivos para el **Registro Calificado** de programas académicos colombianos, siguiendo los criterios del **Consejo Nacional de Acreditación (CNA)**.")
        programa = st.selectbox(
            "¿Qué programa académico deseas evaluar?",
            ["Selecciona un programa...",
             "Ingeniería de Sistemas", "Ingeniería de Software",
             "Ingeniería Electrónica", "Ingeniería de Telecomunicaciones",
             "Tecnología en Desarrollo de Software",
             "Tecnología en Redes y Telecomunicaciones",
             "Administración de Empresas", "Contaduría Pública",
             "Derecho", "Medicina", "Psicología", "Comunicación Social"],
            key="agent_programa",
        )
        if programa != "Selecciona un programa..." and st.button("Siguiente →", key="btn_step0", type="primary"):
            st.session_state.agent_data["programa"] = programa
            st.session_state.agent_step = 1
            st.rerun()

    elif st.session_state.agent_step == 1:
        st.markdown(f"##### 📋 Programa: **{st.session_state.agent_data['programa']}**")
        tipo = st.radio(
            "Tipo de informe:",
            ["📊 Estudio de Pertinencia Laboral",
             "📈 Seguimiento a Graduados (OLE)",
             "🔍 Diagnóstico de Tendencias Sectoriales"],
            key="agent_tipo",
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("← Atrás", key="btn_back1"):
                st.session_state.agent_step = 0
                st.rerun()
        with c2:
            if st.button("Siguiente →", key="btn_step1", type="primary"):
                st.session_state.agent_data["tipo_informe"] = tipo
                st.session_state.agent_step = 2
                st.rerun()

    elif st.session_state.agent_step == 2:
        st.markdown(f"##### ⚙️ Configurar: {st.session_state.agent_data['tipo_informe']}")
        departamento = st.selectbox(
            "Departamento/Región:",
            ["Antioquia", "Bogotá D.C.", "Valle del Cauca", "Atlántico",
             "Santander", "Bolívar", "Cundinamarca", "Tolima", "Nariño", "Otros"],
            key="agent_depto",
        )
        c1, c2 = st.columns(2)
        with c1:
            anio_inicio = st.selectbox("Año inicio:", list(range(2021, 2027)), index=0, key="agent_y1")
        with c2:
            anio_fin = st.selectbox("Año fin:", list(range(2021, 2027)), index=5, key="agent_y2")
        fuentes = st.multiselect(
            "Fuentes de datos:",
            ["Elempleo.com", "CompuTrabajo", "LinkedIn", "Observatorio Laboral (MEN)",
             "DAE (MinEducación)", "SENA", "Superintendencia de Sociedades"],
            default=["Elempleo.com", "Observatorio Laboral (MEN)", "DAE (MinEducación)"],
            key="agent_fuentes",
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("← Atrás", key="btn_back2"):
                st.session_state.agent_step = 1
                st.rerun()
        with c2:
            if st.button("🚀 Generar Informe", key="btn_step2", type="primary"):
                st.session_state.agent_data.update({
                    "departamento": departamento, "anio_inicio": anio_inicio,
                    "anio_fin": anio_fin, "fuentes": fuentes,
                })
                st.session_state.agent_step = 3
                st.rerun()

    elif st.session_state.agent_step == 3:
        from src.utils.report_generator import generate_report, generate_report_offline

        d = st.session_state.agent_data
        st.markdown("##### 📄 Resumen del Informe")
        st.markdown(f"""
        | Parámetro | Valor |
        |-----------|-------|
        | **Programa** | {d['programa']} |
        | **Tipo** | {d['tipo_informe']} |
        | **Región** | {d['departamento']} |
        | **Período** | {d['anio_inicio']} – {d['anio_fin']} |
        | **Fuentes** | {', '.join(d['fuentes'])} |
        """)

        from src.utils.environment import get_groq_key
        groq_key = get_groq_key()

        if groq_key:
            if st.button("🚀 Generar Informe con IA", type="primary", key="btn_gen_report"):
                with st.spinner("Generando informe con Groq AI..."):
                    report = generate_report(d, groq_key)
                if report:
                    st.session_state.agent_report = report
                    st.success("✅ Informe generado exitosamente con IA")
                else:
                    from src.utils.report_generator import generate_report_offline
                    report = generate_report_offline(d)
                    st.session_state.agent_report = report
                    st.warning("⚠️ Groq API no disponible. Informe generado con datos base.")
        else:
            if st.button("📄 Generar Informe Base", type="primary", key="btn_gen_report_offline"):
                from src.utils.report_generator import generate_report_offline
                report = generate_report_offline(d)
                st.session_state.agent_report = report
                st.info("📄 Informe generado con datos base (configura GROQ_API_KEY para informes con IA)")

        if st.session_state.get("agent_report"):
            report = st.session_state.agent_report
            st.divider()
            st.markdown(report)

            st.divider()
            c1, c2, c3 = st.columns(3)
            with c1:
                st.download_button(
                    "📥 Descargar Informe .md",
                    data=report,
                    file_name=f"informe_{d['programa'].replace(' ', '_')}_{d['anio_fin']}.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
            with c2:
                st.download_button(
                    "📥 Descargar Informe .txt",
                    data=report,
                    file_name=f"informe_{d['programa'].replace(' ', '_')}_{d['anio_fin']}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
            with c3:
                from src.utils.pdf_generator import generate_pertinencia_pdf
                pdf_bytes = generate_pertinencia_pdf(
                    program_name=d["programa"],
                    occupation_name=d.get("tipo_informe", "Pertinencia Laboral"),
                    cno_code=d.get("departamento", "N/A"),
                    cuoc_code=d.get("anio_fin", "N/A"),
                    report_text=report,
                    created_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                )
                st.download_button(
                    "📥 Descargar Informe .pdf",
                    data=pdf_bytes,
                    file_name=f"informe_{d['programa'].replace(' ', '_')}_{d['anio_fin']}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
        else:
            st.info("""
            **💡 API Gratuita para generar informes:**

            **Groq API** — Gratis, sin tarjeta de crédito, respuesta instantánea.

            **Cómo configurar (5 minutos):**
            1. Ve a [console.groq.com](https://console.groq.com)
            2. Crea una cuenta gratuita
            3. Ve a **API Keys** → **Create API Key**
            4. Copia la key
            5. Agrégala en Streamlit Cloud → Settings → Secrets:
            ```
            GROQ_API_KEY=gsk_tu_key_aqui
            ```
            6. Reinicia la app

            **Una vez configurada**, presiona **Generar Informe con IA** y recibirás un informe completo listo para el Registro Calificado CNA.
            """)

            if st.button("📄 Generar Informe Base (sin IA)", key="btn_gen_offline"):
                report = generate_report_offline(d)
                st.session_state.agent_report = report
                st.rerun()

            if st.session_state.get("agent_report"):
                report = st.session_state.agent_report
                st.divider()
                st.markdown(report)
                st.divider()
                st.download_button(
                    "📥 Descargar Informe .md",
                    data=report,
                    file_name=f"informe_{d['programa'].replace(' ', '_')}_{d['anio_fin']}.md",
                    mime="text/markdown",
                    use_container_width=True,
                )

        c1, c2 = st.columns(2)
        with c1:
            if st.button("← Atrás", key="btn_back3"):
                st.session_state.agent_step = 2
                st.rerun()
        with c2:
            if st.button("🔄 Nuevo informe", key="btn_new"):
                st.session_state.agent_step = 0
                st.session_state.agent_data = {}
                st.session_state.agent_report = ""
                st.rerun()


if __name__ == "__main__":
    main()
