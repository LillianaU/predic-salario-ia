"""
Configuración centralizada del sistema PredicSalario IA.

Implementa el patrón Singleton para garantizar una única instancia de
configuración en toda la aplicación. Contiene rutas, parámetros ML,
fuentes de datos, queries de scraping y configuración de logging.

Author: Lilliana Uribe González
Version: 2.0
"""

import os  # Acceso a variables de entorno del sistema
from pathlib import Path  # Manejo de rutas de archivos de forma multiplataforma
from dotenv import load_dotenv  # Carga variables de archivo .env al entorno


def _get_logger(name: str = "config"):
    """Obtiene un logger configurado para el módulo."""
    import logging  # Módulo estándar de logging de Python
    return logging.getLogger(name)  # Retorna un logger con el nombre dado


logger = _get_logger()  # Crea logger global para este módulo


class Config:
    """Configuración centralizada Singleton para PredicSalario IA.

    Gestiona rutas del proyecto, parámetros del modelo ML, fuentes de
    datos, queries de scraping (97 búsquedas) y configuración de logging.
    La instancia se crea una sola vez y se reutiliza en toda la app.

    Attributes:
        BASE_DIR: Directorio raíz del proyecto.
        MODEL_PATH: Ruta al modelo entrenado (.pkl).
        MODEL_PARAMS: Hiperparámetros del RandomForest.
        SEARCH_QUERIES: Lista de 97 queries de scraping para sector TI.
        DATA_SOURCES: Información de las 5 fuentes de datos configuradas.
    """
    _instance = None  # Variable de clase que almacena la única instancia Singleton

    def __new__(cls):
        """Implementa Singleton — retorna la misma instancia si ya existe."""
        if cls._instance is None:  # Si no existe instancia previa
            cls._instance = super().__new__(cls)  # Crea nueva instancia de la clase
            cls._instance._initialized = False  # Marca como no inicializada aún
        return cls._instance  # Retorna la instancia existente o la nueva

    def __init__(self):
        """Inicializa la configuración solo la primera vez."""
        if self._initialized:  # Si ya fue inicializada, no hace nada (evita re-init)
            return  # Sale sin hacer cambios
        self._initialized = True  # Marca como inicializada
        load_dotenv()  # Carga variables del archivo .env al entorno del sistema
        self.BASE_DIR = Path(__file__).resolve().parent  # Obtiene directorio raíz del proyecto (donde está config.py)
        self._load_paths()  # Carga y crea rutas de directorios (data/raw, data/processed, models, logs)
        self._load_ml_config()  # Carga parámetros del modelo de Machine Learning
        self._load_sources_config()  # Carga información de las 5 fuentes de datos
        self._load_scraping_config()  # Carga las 15 queries de scraping para elempleo.com
        self._load_logging_config()  # Carga configuración de logging con rotación
        try:
            logger.info("Config initialized")  # Registra que la configuración se cargó correctamente
        except Exception:
            pass  # Si hay error con logging, lo ignora silenciosamente

    def _load_paths(self):
        """Crea y configura las rutas de directorios del proyecto."""
        self.RAW_DATA_DIR = self.BASE_DIR / "data" / "raw"  # Ruta a datos crudos del scraping
        self.PROCESSED_DATA_DIR = self.BASE_DIR / "data" / "processed"  # Ruta a datos limpiados
        self.MODELS_DIR = self.BASE_DIR / "models"  # Ruta a modelos entrenados (.pkl)
        self.LOGS_DIR = self.BASE_DIR / "logs"  # Ruta a archivos de log
        for d in [self.RAW_DATA_DIR, self.PROCESSED_DATA_DIR, self.MODELS_DIR, self.LOGS_DIR]:  # Itera cada directorio
            try:
                d.mkdir(parents=True, exist_ok=True)  # Crea directorio si no existe (incluyendo padres)
            except (OSError, PermissionError):
                pass  # Si no puede crear (permisos), lo ignora silenciosamente
        self.MODEL_PATH = self.MODELS_DIR / "salary_predictor.pkl"  # Ruta completa al modelo RandomForest entrenado
        self.MODEL_HASH_PATH = self.MODELS_DIR / "salary_predictor.hash"  # Ruta al hash del modelo (para detectar cambios)

    def _load_ml_config(self):
        """Carga los parámetros del modelo de Machine Learning."""
        self.MODEL_TYPE = "RandomForest"  # Tipo de modelo: RandomForest de scikit-learn
        self.MODEL_PARAMS = {
            "n_estimators": 100,  # Número de árboles en el bosque (100 árboles)
            "max_depth": 10,  # Profundidad máxima de cada árbol (evita overfitting)
            "random_state": 42,  # Semilla para reproducibilidad de resultados
            "n_jobs": 1,  # Número de hilos de CPU (1 para evitar deadlocks en Windows/Streamlit)
        }
        self.TEST_SIZE = 0.2  # 20% de datos para testing, 80% para entrenamiento
        self.RANDOM_STATE = 42  # Semilla para split train/test y reproducibilidad
        self.MIN_SALARY_COP = 1_000_000  # Salario mínimo aceptado: $1,000,000 COP (filtro de datos)
        self.MAX_SALARY_COP = 30_000_000  # Salario máximo aceptado: $30,000,000 COP (filtro de datos)
        self.CONFIDENCE_INTERVAL = 0.20  # Intervalo de confianza del 20% para predicciones

    def _load_sources_config(self):
        """Carga la información de las 5 fuentes de datos configuradas.

        Incluye portales de empleo (elempleo, computrabajo, indeed),
        red profesional (LinkedIn) y portal colombiano (El Empleo).
        """
        self.DATA_SOURCES = [  # Lista de diccionarios con información de cada fuente
            {
                "name": "elempleo.com",  # Nombre del portal
                "icon": "🌐",  # Emoji para mostrar en la interfaz
                "url": "https://www.elempleo.com",  # URL del portal
                "description": "Portal #1 de empleo en Colombia con más de 50.000 ofertas activas. Fuente principal del scraping.",  # Descripción de la fuente
                "tipo": "Portal de empleo",  # Tipo de fuente
                "cobertura": "Nacional (Colombia)",  # Cobertura geográfica
                "actualizacion": "Tiempo real",  # Frecuencia de actualización
                "formato": "Web scraping vía Playwright/HTTP",  # Método de obtención de datos
            },
            {
                "name": "LinkedIn Colombia",  # Red profesional más grande del mundo
                "icon": "💼",  # Emoji de maletín
                "url": "https://www.linkedin.com/jobs/",  # URL de sección de empleos
                "description": "Red profesional con millones de ofertas TI. Segmentación por skills, conexiones y empresas.",  # Descripción
                "tipo": "Red profesional",  # Tipo: red social
                "cobertura": "Global con filtro Colombia",  # Cobertura mundial con filtro local
                "actualizacion": "Diaria",  # Se actualiza cada día
                "formato": "API / RSS",  # Métodos de acceso
            },
            {
                "name": "Computrabajo Colombia",  # Portal líder en Latinoamérica
                "icon": "💻",  # Emoji de computadora
                "url": "https://www.computrabajo.com.co",  # URL Colombia
                "description": "Portal líder en Latinoamérica con más de 10.000 ofertas TI activas en Colombia.",  # Descripción
                "tipo": "Portal de empleo",  # Tipo de fuente
                "cobertura": "Latinoamérica",  # Cobertura regional
                "actualizacion": "Diaria",  # Actualización diaria
                "formato": "Web scraping",  # Método de extracción
            },
            {
                "name": "Indeed Colombia",  # Agregador global de ofertas
                "icon": "🔍",  # Emoji de búsqueda
                "url": "https://co.indeed.com",  # URL Colombia
                "description": "Agregador global de ofertas laborales. Indexa múltiples fuentes en un solo lugar.",  # Descripción
                "tipo": "Agregador",  # Tipo: agrega de múltiples fuentes
                "cobertura": "Global",  # Cobertura mundial
                "actualizacion": "Tiempo real",  # Actualización continua
                "formato": "API / RSS",  # Métodos de acceso
            },
            {
                "name": "El Empleo",  # Portal colombiano especializado
                "icon": "📋",  # Emoji de clipboard
                "url": "https://www.elempleo.com/co",  # URL Colombia
                "description": "Portal colombiano especializado con filtros por ciudad, salario y área profesional. Ideal para el mercado local.",  # Descripción
                "tipo": "Portal de empleo",  # Tipo de fuente
                "cobertura": "Colombia",  # Cobertura nacional
                "actualizacion": "Diaria",  # Actualización diaria
                "formato": "Web scraping",  # Método de extracción
            },
        ]

    def _load_scraping_config(self):
        """Carga las 15 queries de scraping para el sector TI.

        Las queries están enfocadas en: Desarrollo de Software (5),
        Analítica y Ciencia de Datos (3), Cloud y DevOps (2),
        QA y Testing (1), Gestión y Liderazgo (2), Soporte (1),
        Especializados (1). Todas en Medellín, Colombia.
        """
        self.SEARCH_QUERIES = [  # Lista de strings con las búsquedas a realizar
            # 15 queries de alto impacto para scraping rápido de elempleo.com
            # Cada query retorna ~20 ofertas × 5 páginas = ~100 registros
            # Total estimado: 500-1000 registros reales en ~2 minutos
            "desarrollador Medellín Colombia",  # Desarrollador general - ~80 ofertas
            "ingeniero de software Medellín Colombia",  # Ingeniero software - ~60 ofertas
            "desarrollador web Medellín Colombia",  # Desarrollador web - ~70 ofertas
            "desarrollador frontend Medellín Colombia",  # Frontend React/Angular/Vue - ~50 ofertas
            "desarrollador backend Medellín Colombia",  # Backend Python/Java/Node - ~50 ofertas
            "analista de datos Medellín Colombia",  # Analista datos SQL/BI - ~40 ofertas
            "data scientist Medellín Colombia",  # Científico datos - ~30 ofertas
            "machine learning engineer Medellín Colombia",  # Ingeniero ML - ~25 ofertas
            "ingeniero DevOps Medellín Colombia",  # DevOps CI/CD/Cloud - ~35 ofertas
            "ingeniero cloud Medellín Colombia",  # Cloud AWS/Azure/GCP - ~30 ofertas
            "QA engineer Medellín Colombia",  # QA/Testing - ~25 ofertas
            "líder técnico Medellín Colombia",  # Tech Lead - ~20 ofertas
            "scrum master Medellín Colombia",  # Scrum Master/Agile - ~20 ofertas
            "técnico de soporte TI Medellín Colombia",  # Soporte TI - ~40 ofertas
            "arquitecto de software Medellín Colombia",  # Arquitecto software - ~15 ofertas
        ]
        self.SEARCH_LOCATION = "Medellín, Colombia"  # Ubicación base para todas las búsquedas

    def _load_logging_config(self):
        """Carga la configuración de logging con rotación de archivos."""
        self.LOG_FILE = self.LOGS_DIR / "app.log"  # Ruta al archivo de log principal
        self.LOG_MAX_BYTES = 1_048_576  # Tamaño máximo de cada archivo de log: 1 MB
        self.LOG_BACKUP_COUNT = 5  # Número de archivos de respaldo a mantener (rotación)
