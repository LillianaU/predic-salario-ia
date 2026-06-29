"""
Predictor salarial basado en Random Forest para el sector TI.

Utiliza TF-IDF para vectorizar habilidades técnicas y features numéricas
para predecir el salario promedio en COP. Incluye cross-validation,
feature importance y guardado con hash SHA-256 para integridad.

Author: Lilliana Uribe González
Version: 2.0
"""

from pathlib import Path  # Manejo de rutas de archivos multiplataforma
import joblib  # Serialización de objetos Python (modelos ML)
import pandas as pd  # Manejo de DataFrames
import numpy as np  # Operaciones numéricas matriciales
from typing import Dict, Any, Tuple, Optional, List  # Type hints para tipado
from sklearn.ensemble import RandomForestRegressor  # Modelo de regresión Random Forest
from sklearn.model_selection import train_test_split, cross_val_score  # División train/test y validación cruzada
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score  # Métricas de evaluación
from sklearn.feature_extraction.text import TfidfVectorizer  # Vectorización TF-IDF para skills
from sklearn.preprocessing import LabelEncoder  # Codificación de categorías a números
from scipy.sparse import hstack, csr_matrix  # Matrices dispersas para eficiencia de memoria
from src.interfaces.model_interface import ModelInterface  # Interfaz abstracta del modelo
from src.utils.loggers import get_logger  # Logger configurado
from src.utils.security import save_hash, verify_hash  # Hash SHA-256 para integridad del modelo
from config import Config  # Configuración centralizada

logger = get_logger("models.predictor")  # Logger para este módulo


class SalaryPredictor(ModelInterface):
    """Predictor salarial usando Random Forest Regressor.

    Combina features numéricas (experiencia, nivel cargo, modalidad),
    features derivadas (interacción, cuadrático, remoto), categoría de
    rol (LabelEncoder) y habilidades técnicas (TF-IDF, 80 features)
    para predecir el salario promedio mensual en COP.

    Attributes:
        model: Modelo RandomForestRegressor entrenado.
        vectorizer: TF-IDF vectorizer para skills.
        role_encoder: LabelEncoder para categorías de rol.
        metrics: Métricas de evaluación (MAE, RMSE, R2).
        cv_scores: Resultados de validación cruzada.
        feature_columns: Nombres de las 89 columnas de features.
        feature_importances: Importancia de cada feature.
    """

    @staticmethod
    def _split_skills(text: str) -> list:
        """Divide el texto de skills por coma para TF-IDF tokenizer."""
        return text.split(", ")  # "Python, Java" → ["Python", "Java"]

    def __init__(self, model_type: str = "RandomForest", params: Optional[Dict] = None):
        """Inicializa el predictor con el tipo de modelo y parámetros.

        Args:
            model_type: Tipo de modelo (default: "RandomForest").
            params: Hiperparámetros personalizados. Si es None, usa Config.MODEL_PARAMS.
        """
        self.config = Config()  # Carga configuración centralizada
        self.model_type = model_type  # Tipo de modelo (RandomForest)
        self.params = params or self.config.MODEL_PARAMS  # Hiperparámetros o los por defecto
        self.model = None  # Modelo ML (se crea en train())
        self.vectorizer: Optional[TfidfVectorizer] = None  # Vectorizador TF-IDF para skills
        self.role_encoder: Optional[LabelEncoder] = None  # Codificador de categorías de rol
        self.metrics: Dict[str, float] = {}  # Métricas de evaluación (MAE, RMSE, R2)
        self.cv_scores: Dict[str, float] = {}  # Resultados de validación cruzada
        self.feature_columns: list = []  # Nombres de las columnas de features
        self.feature_importances: Dict[str, float] = {}  # Importancia de cada feature
        self._trained = False  # Flag de entrenamiento

    def train(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Entrena el modelo RandomForest con features engineeradas.

        Ejecuta el pipeline completo: preparación de features (TF-IDF +
        numéricas + derivadas), split 80/20, entrenamiento, evaluación
        con MAE/RMSE/R2, y validación cruzada (3-5 folds).

        Args:
            X: DataFrame con las features de entrada.
            y: Serie con el target (salario_promedio).
        """
        logger.info("Training model with enhanced features...")  # Inicia entrenamiento
        self._prepare_features(X)  # Prepara matriz de features (TF-IDF + numéricas + derivadas)

        # Divide datos: 80% entrenamiento, 20% prueba
        X_train, X_test, y_train, y_test = train_test_split(
            self._feature_matrix, y, test_size=self.config.TEST_SIZE,  # 20% para test
            random_state=self.config.RANDOM_STATE,  # Semilla 42 para reproducibilidad
        )

        # Crea y entrena el modelo RandomForest
        self.model = RandomForestRegressor(**self.params)  # Crea modelo con hiperparámetros
        self.model.fit(X_train, y_train)  # Entrena con datos de entrenamiento
        y_pred = self.model.predict(X_test)  # Predice con datos de prueba

        # Calcula métricas de evaluación
        self.metrics = {
            "MAE": float(mean_absolute_error(y_test, y_pred)),  # Error absoluto promedio en COP
            "RMSE": float(np.sqrt(mean_squared_error(y_test, y_pred))),  # Raíz del error cuadrático medio
            "R2": float(r2_score(y_test, y_pred)),  # Coeficiente de determinación (0-1, mayor es mejor)
        }

        # Cross-validation (min 3 folds for small datasets)  # Validación cruzada
        n_samples = self._feature_matrix.shape[0]  # Número total de muestras
        n_folds = min(5, max(3, n_samples // 5))  # Calcula folds: entre 3 y 5
        try:
            import platform  # Detecta sistema operativo
            n_jobs_cv = 1 if platform.system() == "Windows" else -1  # Windows: 1 hilo, otros: todos los cores
            cv_scores = cross_val_score(  # Ejecuta validación cruzada
                self.model, self._feature_matrix, y,  # Modelo, features, target
                cv=n_folds, scoring="r2", n_jobs=n_jobs_cv  # Folds, métrica R², paralelismo
            )
            self.cv_scores = {
                "R2_mean": float(cv_scores.mean()),  # Promedio de R² en cross-validation
                "R2_std": float(cv_scores.std()),  # Desviación estándar del R²
                "n_folds": n_folds,  # Número de folds utilizados
            }
            logger.info(f"CV R² = {cv_scores.mean():.4f} ± {cv_scores.std():.4f} ({n_folds} folds)")
        except Exception as e:
            logger.warning(f"Cross-validation failed: {e}")  # Si falla CV, usa métrica del test
            self.cv_scores = {"R2_mean": self.metrics["R2"], "R2_std": 0.0, "n_folds": 0}

        # Feature importances  # Importancia de features
        if hasattr(self.model, "feature_importances_"):  # Si el modelo tiene importancias
            importances = self.model.feature_importances_  # Obtiene array de importancias
            self.feature_importances = dict(zip(self.feature_columns, importances.tolist()))  # Crea diccionario feature→importancia
            top_5 = sorted(self.feature_importances.items(), key=lambda x: -x[1])[:5]  # Top 5 features más importantes
            logger.info(f"Top 5 features: {top_5}")  # Muestra top 5

        self._trained = True  # Marca modelo como entrenado
        logger.info(f"Model trained. R² = {self.metrics['R2']:.4f}, MAE = ${self.metrics['MAE']:,.0f}")

    def _prepare_features(self, df: pd.DataFrame) -> None:
        """Prepara la matriz de features para entrenamiento.

        Pipeline:
        1. TF-IDF vectorizer para skills (80 features, sublinear_tf)
        2. LabelEncoder para categoría de rol
        3. Features numéricas base (5 columnas)
        4. Features derivadas: exp×nivel, exp², is_remote
        5. Stack con scipy.sparse.hstack → matriz dispersa
        """
        # TF-IDF for skills (better than CountVectorizer for rare high-value skills)
        if self.vectorizer is None:  # Si el vectorizador no existe aún
            self.vectorizer = TfidfVectorizer(
                max_features=80,  # Máximo 80 features (skills más frecuentes)
                tokenizer=self._split_skills,  # Tokeniza por coma+espacio
                token_pattern=None,  # Desactiva patrón por defecto (usa tokenizer custom)
                sublinear_tf=True,  # Aplica log(1 + tf) para suavizar frecuencias
                min_df=1,  # Aparece en al menos 1 documento
            )
        skills_vectors = self.vectorizer.fit_transform(df["skills_str"].fillna(""))  # Vectoriza skills a matriz dispersa 80 cols

        # Role category encoding  # Codificación de categoría de rol
        if self.role_encoder is None:  # Si el codificador no existe aún
            self.role_encoder = LabelEncoder()  # Crea codificador
            role_cats = df["role_categoria"].fillna("Otros").astype(str) if "role_categoria" in df.columns else pd.Series(["Otros"] * len(df))  # Obtiene categorías
            self.role_encoder.fit(role_cats)  # Aprende categorías únicas
        role_col = pd.Series(["Otros"] * len(df))  # Serie por defecto "Otros"
        if "role_categoria" in df.columns:  # Si existe columna de categoría
            role_col = df["role_categoria"].fillna("Otros").astype(str)  # Usa esa columna
        role_encoded = self.role_encoder.transform(role_col)  # Convierte categorías a números
        role_sparse = csr_matrix(role_encoded.reshape(-1, 1))  # Convierte a matriz dispersa columna

        # Numeric features (with fallbacks for missing columns)  # Features numéricas
        base_features = ["experiencia_requerida", "cargo_nivel_cod", "modalidad_cod"]  # Columnas base
        for opt_col in ["num_skills", "tipo_contrato_cod"]:  # Columnas opcionales
            if opt_col not in df.columns:  # Si no existe
                df[opt_col] = 0  # Crea con valor 0
            base_features.append(opt_col)  # Agrega a lista de features

        numeric_values = df[base_features].fillna(0).values  # Convierte a array numpy, NaN → 0

        # Derived features  # Features derivadas (crean relaciones no lineales)
        exp = df["experiencia_requerida"].fillna(0).values  # Array de experiencia
        nivel = df["cargo_nivel_cod"].fillna(2).values  # Array de nivel (default: 2=ingeniero)
        exp_x_nivel = (exp * nivel).reshape(-1, 1)  # Interacción: experiencia × nivel (captura seniority)
        exp_squared = (exp ** 2).reshape(-1, 1)  # Experiencia al cuadrado (captura no linealidad)
        is_remote = (df["modalidad_cod"].fillna(0) == 2).astype(int).values.reshape(-1, 1)  # Binario: 1 si es remoto

        # Stack all features  # Apila todas las features en una matriz
        derived = np.hstack([exp_x_nivel, exp_squared, is_remote])  # Features derivadas
        self._feature_matrix = hstack([  # Combina todas las features en matriz dispersa
            csr_matrix(numeric_values),  # Features numéricas (5 columnas)
            derived,  # Features derivadas (3 columnas)
            role_sparse,  # Categoría de rol (1 columna)
            skills_vectors,  # Skills TF-IDF (80 columnas)
        ])

        self.feature_columns = (  # Nombres de las 89 columnas de features
            base_features  # 5 features numéricas base
            + ["exp_x_nivel", "exp_squared", "is_remote"]  # 3 features derivadas
            + ["role_categoria"]  # 1 categoría de rol
            + [f"skill_{s}" for s in self.vectorizer.get_feature_names_out()]  # 80 skills TF-IDF
        )

    def predict(self, features: pd.DataFrame) -> Dict[str, Any]:
        """Predice el salario estimado con rango de confianza.

        Args:
            features: DataFrame con una fila de features del usuario.

        Returns:
            Dict con salario_estimado, rango_inferior, rango_superior
            y confianza (±15%).
        """
        if not self._trained or self.model is None:  # Si el modelo no está entrenado
            raise ValueError("Model not trained. Call train() first.")  # Error: debe entrenar primero
        feats = self._prepare_prediction_features(features)  # Prepara features para predicción
        pred = self.model.predict(feats)[0]  # Predice salario (primer resultado)
        pred = float(np.clip(pred, self.config.MIN_SALARY_COP, self.config.MAX_SALARY_COP))  # Recorta a rango válido
        interval = pred * self.config.CONFIDENCE_INTERVAL  # Intervalo de confianza (20%)
        lower = max(self.config.MIN_SALARY_COP, pred - interval)  # Límite inferior (mínimo 1M)
        upper = min(self.config.MAX_SALARY_COP, pred + interval)  # Límite superior (máximo 30M)
        return {
            "salario_estimado": round(pred, -3),  # Redondeado a miles
            "rango_inferior": round(lower, -3),  # Redondeado a miles
            "rango_superior": round(upper, -3),  # Redondeado a miles
            "confianza": f"±{self.config.CONFIDENCE_INTERVAL * 100:.0f}%",  # Ej: "±20%"
        }

    def _prepare_prediction_features(self, df: pd.DataFrame) -> csr_matrix:
        """Prepara features para predicción individual.

        Transforma los datos del usuario en la misma representación
        de features usada durante el entrenamiento (TF-IDF + numéricas).
        """
        # Skills TF-IDF  # Vectorización de skills
        skills_str = df["skills_str"].iloc[0] if "skills_str" in df.columns else ""  # Obtiene skills como string
        if self.vectorizer:  # Si el vectorizador existe
            skills_vec = self.vectorizer.transform([skills_str])  # Transforma skills a vector TF-IDF
        else:  # Si no existe vectorizador
            skills_vec = csr_matrix((1, 80))  # Crea vector vacío de 80 ceros

        # Role category  # Categoría de rol
        role_cat = df["role_categoria"].iloc[0] if "role_categoria" in df.columns else "Otros"  # Obtiene categoría
        if self.role_encoder:  # Si el codificador existe
            try:
                role_enc = self.role_encoder.transform([str(role_cat)])[0]  # Convierte a número
            except ValueError:  # Si la categoría no fue vista en entrenamiento
                role_enc = self.role_encoder.transform(["Otros"])[0]  # Usa "Otros" como fallback
        else:  # Si no existe codificador
            role_enc = 0  # Valor por defecto
        role_sparse = csr_matrix([[role_enc]])  # Convierte a matriz dispersa

        # Numeric features  # Features numéricas
        exp = float(df["experiencia_requerida"].iloc[0]) if "experiencia_requerida" in df.columns else 0.0  # Experiencia
        nivel = int(df["cargo_nivel_cod"].iloc[0]) if "cargo_nivel_cod" in df.columns else 2  # Nivel (default: 2)
        modalidad = int(df["modalidad_cod"].iloc[0]) if "modalidad_cod" in df.columns else 0  # Modalidad (default: 0)
        num_skills = int(df["num_skills"].iloc[0]) if "num_skills" in df.columns else 0  # Número de skills
        tipo_contrato = int(df["tipo_contrato_cod"].iloc[0]) if "tipo_contrato_cod" in df.columns else 1  # Tipo contrato (default: 1)

        # Derived  # Features derivadas
        exp_x_nivel = exp * nivel  # Interacción experiencia × nivel
        exp_squared = exp ** 2  # Experiencia al cuadrado
        is_remote = 1 if modalidad == 2 else 0  # Binario: ¿es remoto?

        num_feats = csr_matrix([[exp, nivel, modalidad, num_skills, tipo_contrato]])  # Features numéricas
        derived = csr_matrix([[exp_x_nivel, exp_squared, is_remote]])  # Features derivadas

        return hstack([num_feats, derived, role_sparse, skills_vec])  # Combina todo en una matriz

    def save(self, path: str) -> None:
        """Guarda el modelo entrenado y genera hash SHA-256.

        Args:
            path: Ruta donde guardar el modelo (.pkl).
        """
        if not self._trained:  # Si no está entrenado
            raise ValueError("Cannot save untrained model.")  # Error: no se puede guardar

        # Serializa LabelEncoder como dict para compatibilidad entre Python versions
        role_enc_dict = None  # Por defecto None
        if self.role_encoder is not None:  # Si existe codificador de roles
            role_enc_dict = {
                "classes_": self.role_encoder.classes_.tolist(),  # Guarda clases como lista Python
            }

        save_data = {
            "model": self.model,  # Modelo RandomForest entrenado
            "vectorizer": self.vectorizer,  # Vectorizador TF-IDF entrenado
            "role_encoder_dict": role_enc_dict,  # Codificador de roles serializado
            "metrics": self.metrics,  # Métricas de evaluación
            "cv_scores": self.cv_scores,  # Resultados de validación cruzada
            "feature_columns": self.feature_columns,  # Nombres de features
            "feature_importances": self.feature_importances,  # Importancia de cada feature
            "model_type": self.model_type,  # Tipo de modelo
            "params": self.params,  # Hiperparámetros usados
        }
        joblib.dump(save_data, path)  # Serializa todo a archivo .pkl
        hash_path = self.config.MODEL_HASH_PATH  # Ruta del archivo de hash
        save_hash(Path(path), hash_path)  # Genera hash SHA-256 para integridad
        logger.info(f"Model saved to {path}")

    def load(self, path: str) -> None:
        """Carga un modelo entrenado y verifica integridad con hash.

        Args:
            path: Ruta del modelo (.pkl) a cargar.

        Raises:
            FileNotFoundError: Si el archivo no existe.
            ValueError: Si el hash no coincide (integridad comprometida).
        """
        p = Path(path)  # Convierte a objeto Path
        if not p.exists():  # Si el archivo no existe
            raise FileNotFoundError(f"Model file not found: {path}")  # Error: archivo no encontrado
        if not verify_hash(p, self.config.MODEL_HASH_PATH):  # Si el hash no coincide
            logger.warning("Model hash mismatch. Retraining required.")  # Advertencia
            raise ValueError("Model integrity check failed. Hash mismatch.")  # Error: integridad comprometida
        save_data = joblib.load(path)  # Deserializa el archivo .pkl
        self.model = save_data["model"]  # Carga modelo RandomForest
        self.vectorizer = save_data["vectorizer"]  # Carga vectorizador TF-IDF

        # Carga codificador de roles (compatible con ambos formatos)
        role_enc_dict = save_data.get("role_encoder_dict")  # Intenta obtener formato nuevo (dict)
        if role_enc_dict and "classes_" in role_enc_dict:  # Si existe formato nuevo
            self.role_encoder = LabelEncoder()  # Crea codificador
            self.role_encoder.classes_ = np.array(role_enc_dict["classes_"])  # Restaura clases
        else:  # Si no, intenta formato antiguo (LabelEncoder directo)
            self.role_encoder = save_data.get("role_encoder")  # Carga directamente

        self.metrics = save_data["metrics"]  # Carga métricas
        self.cv_scores = save_data.get("cv_scores", {})  # Carga CV scores (default: vacío)
        self.feature_columns = save_data["feature_columns"]  # Carga nombres de features
        self.feature_importances = save_data.get("feature_importances", {})  # Carga importancias
        self.model_type = save_data.get("model_type", self.model_type)  # Carga tipo de modelo
        self.params = save_data.get("params", self.params)  # Carga hiperparámetros
        self._trained = True  # Marca como entrenado
        logger.info(f"Model loaded from {path}")

    def get_metrics(self) -> Dict[str, float]:
        """Retorna las métricas de evaluación (MAE, RMSE, R2)."""
        return self.metrics.copy()  # Retorna copia para evitar modificaciones accidentales

    def get_cv_scores(self) -> Dict[str, float]:
        """Retorna los resultados de validación cruzada."""
        return self.cv_scores.copy()  # Retorna copia

    def get_top_features(self, n: int = 10) -> List[Tuple[str, float]]:
        """Retorna las N features más importantes según el modelo.

        Args:
            n: Número de features a retornar (default: 10).
        """
        if not self.feature_importances:  # Si no hay importancias calculadas
            return []  # Retorna lista vacía
        sorted_feats = sorted(self.feature_importances.items(), key=lambda x: -x[1])  # Ordena de mayor a menor importancia
        return sorted_feats[:n]  # Retorna top N

    @property
    def is_trained(self) -> bool:
        """Retorna True si el modelo ha sido entrenado."""
        return self._trained
