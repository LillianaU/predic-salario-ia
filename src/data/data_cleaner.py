"""
Pipeline ETL para limpieza y procesamiento de datos laborales.

Convierte datos crudos del scraping en un DataFrame listo para
entrenamiento del modelo ML. Incluye: filtrado salarial, extracción
de experiencia, detección de skills (120+ keywords), codificación
categórica y deduplicación.

Author: Lilliana Uribe González
Version: 2.0
"""

import re  # Expresiones regulares para patrones de extracción
import pandas as pd  # Manejo de DataFrames (estructura de datos principal)
from typing import List, Dict, Any, Optional  # Type hints para tipado estático
from src.utils.loggers import get_logger  # Función para obtener logger configurado
from src.utils.validators import (  # Funciones de validación y extracción
    extract_experience_years,  # Extrae años de experiencia desde texto ("3+ años" → 3)
    extract_skills,  # Extrae skills técnicas con regex (120+ keywords)
    identify_cargo_level,  # Identifica nivel: tecnico/tecnologo/ingeniero/senior
    identify_modalidad,  # Identifica modalidad: presencial/hibrido/remoto
    identify_role_category,  # Identifica categoría: Desarrollo/Datos/IA/etc
)

logger = get_logger("data.cleaner")  # Logger para registrar eventos de limpieza


class DataCleaner:
    """Pipeline ETL para limpieza de datos laborales del sector TI.

    Procesa datos crudos del scraping y aplica 10 pasos de limpieza:
    1. Asegurar columnas requeridas
    2. Eliminar registros sin salario
    3. Filtrar salarios inválidos (<500K o >100M COP)
    4. Normalizar salarios a float
    5. Extraer experiencia en años desde texto
    6. Extraer skills con regex (120+ keywords)
    7. Crear target (salario_promedio)
    8. Codificar variables categóricas
    9. Limpiar strings y extraer ciudad
    10. Eliminar duplicados

    Attributes:
        REQUIRED_FIELDS: Lista de 12 columnas requeridas en los datos.
    """
    REQUIRED_FIELDS = [  # Columnas que DEBE tener cada registro para ser válido
        "titulo",  # Título del puesto de trabajo
        "empresa",  # Nombre de la empresa
        "salario_minimo",  # Salario mínimo en COP
        "salario_maximo",  # Salario máximo en COP
        "moneda",  # Moneda (debe ser COP para Colombia)
        "ubicacion",  # Ubicación geográfica del empleo
        "experiencia_requerida",  # Años de experiencia requeridos
        "tipo_contrato",  # Tipo de contrato laboral
        "skills",  # Habilidades técnicas requeridas
        "fecha_publicacion",  # Fecha de publicación de la oferta
        "descripcion",  # Descripción del puesto
        "modalidad",  # Modalidad de trabajo (presencial/hibrido/remoto)
    ]

    def clean(self, raw_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Ejecuta el pipeline completo de limpieza ETL.

        Args:
            raw_data: Lista de diccionarios con datos crudos del scraping.

        Returns:
            DataFrame limpio listo para entrenamiento.
        """
        logger.info(f"Cleaning {len(raw_data)} raw records")  # Registra cuántos registros va a limpiar
        df = pd.DataFrame(raw_data)  # Convierte lista de diccionarios a DataFrame de pandas

        if df.empty:  # Si el DataFrame está vacío (no hay datos)
            logger.warning("Empty dataset — no data to clean")  # Advertencia de dataset vacío
            return df  # Retorna DataFrame vacío sin procesar

        # Ejecuta los 10 pasos de limpieza en orden secuencial
        df = self._ensure_columns(df)  # Paso 1: Asegura que existan todas las columnas requeridas
        df = self._remove_without_salary(df)  # Paso 2: Elimina registros sin salario
        df = self._filter_invalid_salaries(df)  # Paso 3: Filtra salarios fuera de rango
        df = self._normalize_salaries(df)  # Paso 4: Convierte salarios a tipo float
        df = self._extract_experience(df)  # Paso 5: Extrae años de experiencia desde texto
        df = self._extract_skills_column(df)  # Paso 6: Extrae skills técnicas con regex
        df = self._create_target(df)  # Paso 7: Crea variable target (salario_promedio)
        df = self._encode_categorical(df)  # Paso 8: Codifica variables categóricas a números
        df = self._clean_strings(df)  # Paso 9: Limpia strings y extrae ciudad
        df = self._remove_duplicates(df)  # Paso 10: Elimina registros duplicados

        logger.info(f"Cleaned dataset: {len(df)} records")  # Registra cuántos registros quedaron
        return df  # Retorna DataFrame limpio listo para entrenamiento

    def _ensure_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Asegura que todas las columnas requeridas existan en el DataFrame."""
        for col in self.REQUIRED_FIELDS:  # Itera cada columna requerida
            if col not in df.columns:  # Si la columna no existe en el DataFrame
                df[col] = ""  # La crea con valor vacío por defecto
        return df  # Retorna DataFrame con todas las columnas aseguradas

    def _remove_without_salary(self, df: pd.DataFrame) -> pd.DataFrame:
        """Elimina registros que no tienen información de salario válida."""
        before = len(df)  # Guarda cantidad inicial para calcular cuántos se eliminaron
        df["salario_minimo"] = pd.to_numeric(df["salario_minimo"], errors="coerce")  # Convierte salario_minimo a numérico, errores → NaN
        df["salario_maximo"] = pd.to_numeric(df["salario_maximo"], errors="coerce")  # Convierte salario_maximo a numérico, errores → NaN
        df = df.dropna(subset=["salario_minimo", "salario_maximo"])  # Elimina filas donde salario sea NaN
        df = df[(df["salario_minimo"] > 0) & (df["salario_maximo"] > 0)]  # Elimina salarios en 0 o negativos
        removed = before - len(df)  # Calcula cuántos registros se eliminaron
        if removed:  # Si se eliminaron registros
            logger.info(f"Removed {removed} records without salary info")  # Registra la eliminación
        return df  # Retorna DataFrame sin registros sin salario

    def _filter_invalid_salaries(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filtra salarios inválidos: solo COP, rango 500K-100M, min <= max."""
        before = len(df)  # Guarda cantidad inicial
        df["moneda"] = df["moneda"].fillna("COP").astype(str).str.upper().str.strip()  # Normaliza moneda: rellena NaN con COP, convierte a mayúsculas, quita espacios
        cop_mask = df["moneda"].str.contains("COP|COL|PESO", na=False)  # Crea máscara para monedas colombianas
        df = df[cop_mask | (df["moneda"] == "")]  # Filtra solo registros con moneda COP o vacía
        df.loc[df["moneda"] == "", "moneda"] = "COP"  # Rellena monedas vacías con COP
        # Remove unrealistic salaries (> 100M COP or < 500K)  # Elimina salarios poco realistas
        df = df[(df["salario_minimo"] >= 500_000) & (df["salario_maximo"] <= 100_000_000)]  # Filtra rango 500K-100M COP
        df = df[df["salario_minimo"] <= df["salario_maximo"]]  # Asegura que mínimo ≤ máximo
        removed = before - len(df)  # Calcula eliminados
        if removed:  # Si hubo eliminaciones
            logger.info(f"Removed {removed} records with invalid salaries")  # Registra
        return df  # Retorna DataFrame filtrado

    def _normalize_salaries(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normaliza los salarios a tipo float."""
        df["salario_minimo"] = df["salario_minimo"].astype(float)  # Convierte salario_minimo a float
        df["salario_maximo"] = df["salario_maximo"].astype(float)  # Convierte salario_maximo a float
        return df  # Retorna DataFrame con salarios normalizados

    def _extract_experience(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extrae años de experiencia desde texto (regex patterns, clip 0-50)."""
        df["experiencia_requerida_str"] = df["experiencia_requerida"].fillna("").astype(str)  # Guarda texto original como string
        df["experiencia_requerida"] = df["experiencia_requerida_str"].apply(extract_experience_years)  # Aplica función de extracción regex a cada fila
        df["experiencia_requerida"] = df["experiencia_requerida"].fillna(0).astype(float)  # Rellena NaN con 0 y convierte a float
        # Clip to sensible max  # Recorta a máximo razonable
        df["experiencia_requerida"] = df["experiencia_requerida"].clip(0, 50)  # Limita experiencia entre 0 y 50 años
        return df  # Retorna DataFrame con experiencia extraída

    def _extract_skills_column(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extrae skills técnicas con regex (120+ keywords) y crea skills_str."""
        desc_text = df["descripcion"].fillna("") + " " + df["skills"].fillna("") + " " + df["titulo"].fillna("")  # Concatena descripción + skills + título para buscar keywords
        df["skills_list"] = desc_text.apply(extract_skills)  # Aplica extracción de skills a cada fila (retorna lista)
        df["skills_str"] = df["skills_list"].apply(lambda x: ", ".join(x) if x else "")  # Convierte lista a string separado por comas
        df["num_skills"] = df["skills_list"].apply(len)  # Cuenta cuántas skills se detectaron
        return df  # Retorna DataFrame con skills extraídas

    def _create_target(self, df: pd.DataFrame) -> pd.DataFrame:
        """Crea la variable target: salario_promedio = (min + max) / 2."""
        df["salario_promedio"] = (df["salario_minimo"] + df["salario_maximo"]) / 2  # Promedio de min y max es el target del modelo
        return df  # Retorna DataFrame con variable target creada

    def _encode_categorical(self, df: pd.DataFrame) -> pd.DataFrame:
        """Codifica variables categóricas: cargo_nivel, modalidad, role_categoria, contrato."""
        df["cargo_nivel"] = df["titulo"].fillna("").astype(str).apply(identify_cargo_level)  # Identifica nivel del cargo desde título
        df["modalidad_clean"] = (df["modalidad"].fillna("") + " " + df["descripcion"].fillna("")).apply(identify_modalidad)  # Identifica modalidad desde modalidad + descripción
        level_map = {"tecnico": 0, "tecnologo": 1, "ingeniero": 2, "senior": 3}  # Mapa de niveles a números
        modal_map = {"presencial": 0, "hibrido": 1, "remoto": 2}  # Mapa de modalidades a números
        df["cargo_nivel_cod"] = df["cargo_nivel"].map(level_map).fillna(2).astype(int)  # Convierte nivel a código numérico (default: 2=ingeniero)
        df["modalidad_cod"] = df["modalidad_clean"].map(modal_map).fillna(0).astype(int)  # Convierte modalidad a código numérico (default: 0=presencial)
        # Role category  # Categoría del rol
        df["role_categoria"] = df.apply(  # Aplica identificación de categoría a cada fila
            lambda r: identify_role_category(r.get("titulo", ""), r.get("descripcion", "")), axis=1  # Usa título y descripción para identificar categoría
        )
        # Tipo contrato encoding  # Codificación de tipo de contrato
        contrato_map = {"indefinido": 0, "prestación de servicios": 1, "obra y labor": 2, "aprendizaje": 3}  # Mapa de contratos a números
        df["tipo_contrato_clean"] = df["tipo_contrato"].fillna("").str.lower().str.strip()  # Normaliza texto del contrato
        df["tipo_contrato_cod"] = df["tipo_contrato_clean"].map(contrato_map).fillna(1).astype(int)  # Convierte contrato a código numérico (default: 1=servicios)
        # Skill count  # Conteo de skills
        if "num_skills" not in df.columns:  # Si num_skills no fue creado antes
            df["num_skills"] = df["skills_str"].apply(lambda x: len(x.split(",")) if x else 0)  # Cuenta skills dividiendo por comas
        return df  # Retorna DataFrame con variables categóricas codificadas

    def _clean_strings(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia strings (strip whitespace) y extrae ciudad de ubicación."""
        str_cols = df.select_dtypes(include=["object", "string"]).columns  # Selecciona todas las columnas de tipo string
        for col in str_cols:  # Itera cada columna string
            df[col] = df[col].fillna("").astype(str).str.strip()  # Rellena NaN, convierte a string, quita espacios
        # Extract ciudad from ubicacion if not present  # Extrae ciudad si no existe columna ciudad
        if "ciudad" not in df.columns:  # Si no hay columna ciudad
            if "ubicacion" in df.columns:  # Si hay columna ubicación
                df["ciudad"] = df["ubicacion"].apply(  # Extrae ciudad de la ubicación
                    lambda x: x.split(",")[0].strip() if isinstance(x, str) and x else "Medellín"  # Toma texto antes de la primera coma (default: Medellín)
                )
            else:  # Si no hay ubicación
                df["ciudad"] = "Medellín"  # Asigna Medellín por defecto
        return df  # Retorna DataFrame limpio

    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Elimina duplicados por (titulo, empresa, salario_minimo, salario_maximo)."""
        before = len(df)  # Guarda cantidad inicial
        subset = [c for c in ["titulo", "empresa", "salario_minimo", "salario_maximo"] if c in df.columns]  # Columnas para detectar duplicados
        if subset:  # Si hay columnas para comparar
            df = df.drop_duplicates(subset=subset, keep="first")  # Elimina duplicados, mantiene el primero
        removed = before - len(df)  # Calcula cuántos se eliminaron
        if removed:  # Si hubo eliminaciones
            logger.info(f"Removed {removed} duplicate records")  # Registra
        return df  # Retorna DataFrame sin duplicados
