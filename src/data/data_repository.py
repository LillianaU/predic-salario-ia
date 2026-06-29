"""Repositorio de datos para gestión de archivos raw y procesados."""
import json  # Exportación a formato JSON
import pandas as pd  # Manejo de DataFrames
from pathlib import Path  # Manejo de rutas de archivos
from typing import Optional, List, Dict, Any  # Type hints
from src.utils.loggers import get_logger  # Logger configurado
from src.utils.security import compute_file_hash  # Hash SHA-256 de archivos

logger = get_logger("data.repository")  # Logger para este módulo


class DataRepository:
    """Repositorio para guardar y cargar datos raw y procesados."""

    def __init__(self, raw_dir: Path, processed_dir: Path):
        """Inicializa el repositorio con las rutas de directorios.

        Args:
            raw_dir: Directorio para datos crudos del scraping.
            processed_dir: Directorio para datos limpiados.
        """
        self.raw_dir = raw_dir  # Ruta a data/raw/
        self.processed_dir = processed_dir  # Ruta a data/processed/

    def save_raw(self, data: List[Dict[str, Any]], filename: Optional[str] = None) -> Path:
        """Guarda datos crudos del scraping en CSV.

        Args:
            data: Lista de diccionarios con ofertas de empleo.
            filename: Nombre del archivo (default: raw_data_YYYY-MM-DD.csv).

        Returns:
            Path del archivo guardado.
        """
        if filename is None:  # Si no se especificó nombre
            import datetime  # Importa datetime para fecha
            filename = f"raw_data_{datetime.date.today().isoformat()}.csv"  # Nombre con fecha: raw_data_2026-06-28.csv
        path = self.raw_dir / filename  # Ruta completa del archivo
        df = pd.DataFrame(data)  # Convierte lista de dicts a DataFrame
        df.to_csv(path, index=False, encoding="utf-8")  # Guarda CSV sin índice
        logger.info(f"Raw data saved: {path} ({len(df)} records)")
        return path  # Retorna path del archivo guardado

    def save_processed(self, df: pd.DataFrame, filename: Optional[str] = None) -> Path:
        """Guarda datos procesados en CSV y JSON.

        Args:
            df: DataFrame limpio listo para entrenamiento.
            filename: Nombre del archivo (default: dataset_limpio.csv).

        Returns:
            Path del archivo CSV guardado.
        """
        if filename is None:  # Si no se especificó nombre
            filename = "dataset_limpio.csv"  # Nombre por defecto
        path = self.processed_dir / filename  # Ruta completa
        df.to_csv(path, index=False, encoding="utf-8")  # Guarda CSV
        logger.info(f"Processed data saved: {path} ({len(df)} records)")
        json_path = path.with_suffix(".json")  # Cambia extensión .csv → .json
        df.to_json(json_path, orient="records", force_ascii=False)  # Guarda JSON (orientación: lista de registros)
        logger.info(f"JSON export saved: {json_path}")
        return path  # Retorna path del CSV

    def load_raw(self, filename: str = "raw_data.csv") -> Optional[pd.DataFrame]:
        """Carga datos crudos desde CSV.

        Args:
            filename: Nombre del archivo a cargar.

        Returns:
            DataFrame o None si no existe el archivo.
        """
        path = self.raw_dir / filename  # Ruta completa
        if not path.exists():  # Si el archivo no existe
            return None  # Retorna None
        return pd.read_csv(path, encoding="utf-8")  # Lee CSV y retorna DataFrame

    def load_processed(self, filename: str = "dataset_limpio.csv") -> Optional[pd.DataFrame]:
        """Carga datos procesados desde CSV.

        Args:
            filename: Nombre del archivo a cargar.

        Returns:
            DataFrame o None si no existe el archivo.
        """
        path = self.processed_dir / filename  # Ruta completa
        if not path.exists():  # Si el archivo no existe
            return None  # Retorna None
        return pd.read_csv(path, encoding="utf-8")  # Lee CSV y retorna DataFrame

    def list_raw_files(self) -> List[Path]:
        """Lista todos los archivos CSV en el directorio raw."""
        return sorted(self.raw_dir.glob("*.csv"))  # Retorna lista ordenada de archivos .csv
