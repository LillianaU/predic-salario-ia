"""
Analizador de empleabilidad basado en red neuronal MLPRegressor.

Entrena una red neuronal de 3 capas (128/64/32) para análisis
de tendencias del mercado laboral TI: distribución municipal,
análisis salarial, demanda de roles, habilidades y oportunidades.

Author: Lilliana Uribe González
Version: 2.0
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List
from src.utils.loggers import get_logger

logger = get_logger("models.neural_network")


class EmployabilityAnalyzer:
    """Analizador de empleabilidad con red neuronal MLPRegressor.

    Arquitectura: 3 capas ocultas (128 → 64 → 32 neuronas)
    Activación: ReLU | Optimizador: Adam | Early stopping: True

    Genera análisis de:
    - Resumen general del mercado
    - Distribución por municipio del AMVA
    - Análisis salarial por categoría
    - Demanda de roles y tendencias
    - Habilidades más demandadas
    - Oportunidades de empleabilidad
    - Recomendaciones

    Attributes:
        model: MLPRegressor entrenado.
        scaler: StandardScaler para normalizar features.
        is_trained: Flag de entrenamiento.
        feature_columns: Columnas usadas en entrenamiento.
        analysis_results: Resultados del último análisis.
    """

    def __init__(self):
        """Inicializa el analizador sin modelo."""
        self.model = None
        self.scaler = None
        self.is_trained = False
        self.feature_columns = []
        self.analysis_results = {}

    def _build_model(self, input_dim: int):
        """Construye la red neuronal MLPRegressor.

        Args:
            input_dim: Número de features de entrada.
        """
        try:
            from sklearn.neural_network import MLPRegressor
            self.model = MLPRegressor(
                hidden_layer_sizes=(128, 64, 32),
                activation='relu',
                solver='adam',
                max_iter=500,
                random_state=42,
                early_stopping=True,
                validation_fraction=0.2,
            )
            from sklearn.preprocessing import StandardScaler
            self.scaler = StandardScaler()
            logger.info("Built MLPRegressor model (scikit-learn)")
            return True
        except ImportError:
            logger.warning("scikit-learn not available, using simple statistics")
            return False

    def train(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Entrena la red neuronal con datos del mercado laboral.

        Args:
            df: DataFrame con features y target (salario_promedio).

        Returns:
            Dict con métricas de entrenamiento o error.
        """
        logger.info(f"Training neural network on {len(df)} records")

        features = self._prepare_features(df)
        if features is None or len(features) < 10:
            logger.warning("Insufficient data for training")
            return {"error": "Datos insuficientes para entrenar (mínimo 10 registros)"}

        X = features.values
        y_min = df["salario_minimo"].values
        y_max = df["salario_maximo"].values
        y_avg = (y_min + y_max) / 2

        if self._build_model(X.shape[1]):
            X_scaled = self.scaler.fit_transform(X)
            self.model.fit(X_scaled, y_avg)
            self.is_trained = True

            train_score = self.model.score(X_scaled, y_avg)
            logger.info(f"Model trained. R² = {train_score:.4f}")

            return {
                "status": "trained",
                "r2_score": float(train_score),
                "samples": len(df),
                "features": len(self.feature_columns),
            }
        else:
            self.is_trained = False
            return {"error": "No se pudo crear el modelo"}

    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Genera análisis completo de empleabilidad.

        Ejecuta 8 análisis: resumen general, distribución municipal,
        análisis salarial, demanda de roles, tendencias modalidad,
        niveles de cargo, skills demandadas y oportunidades.

        Args:
            df: DataFrame con datos procesados del mercado laboral.

        Returns:
            Dict con todos los análisis y recomendaciones.
        """
        if df is None or df.empty:
            return {"error": "No hay datos para analizar"}

        results = {
            "resumen_general": self._general_summary(df),
            "distribucion_municipios": self._municipality_distribution(df),
            "analisis_salarial": self._salary_analysis(df),
            "roles_demanda": self._role_demand(df),
            "modalidad_tendencias": self._modality_trends(df),
            "nivel_cargos": self._cargo_levels(df),
            "habilidades_demandadas": self._skills_demand(df),
            "oportunidades_empleabilidad": self._employability_opportunities(df),
            "recomendaciones": self._generate_recommendations(df),
        }

        self.analysis_results = results
        return results

    def _prepare_features(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        try:
            features = pd.DataFrame()

            if "experiencia_requerida" in df.columns:
                features["experiencia"] = pd.to_numeric(df["experiencia_requerida"], errors="coerce").fillna(0)
            else:
                features["experiencia"] = 0

            if "cargo_nivel_cod" in df.columns:
                features["nivel_cargo"] = df["cargo_nivel_cod"]
            elif "cargo_nivel" in df.columns:
                level_map = {"tecnico": 0, "tecnologo": 1, "ingeniero": 2, "senior": 3}
                features["nivel_cargo"] = df["cargo_nivel"].map(level_map).fillna(2)
            else:
                features["nivel_cargo"] = 2

            if "modalidad_cod" in df.columns:
                features["modalidad"] = df["modalidad_cod"]
            elif "modalidad_clean" in df.columns:
                modal_map = {"presencial": 0, "hibrido": 1, "remoto": 2}
                features["modalidad"] = df["modalidad_clean"].map(modal_map).fillna(0)
            else:
                features["modalidad"] = 0

            if "num_skills" in df.columns:
                features["num_skills"] = df["num_skills"]
            elif "skills_str" in df.columns:
                features["num_skills"] = df["skills_str"].apply(lambda x: len(str(x).split(",")) if x else 0)
            else:
                features["num_skills"] = 0

            if "role_categoria" in df.columns:
                role_dummies = pd.get_dummies(df["role_categoria"], prefix="role")
                features = pd.concat([features, role_dummies], axis=1)

            self.feature_columns = list(features.columns)
            return features
        except Exception as e:
            logger.error(f"Error preparing features: {e}")
            return None

    def _general_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        total = len(df)
        salaries = pd.to_numeric(df.get("salario_promedio", pd.Series()), errors="coerce").dropna()

        return {
            "total_ofertas": total,
            "salario_promedio": float(salaries.mean()) if len(salaries) > 0 else 0,
            "salario_minimo": float(salaries.min()) if len(salaries) > 0 else 0,
            "salario_maximo": float(salaries.max()) if len(salaries) > 0 else 0,
            "mediana_salario": float(salaries.median()) if len(salaries) > 0 else 0,
            "desviacion_salario": float(salaries.std()) if len(salaries) > 1 else 0,
        }

    def _municipality_distribution(self, df: pd.DataFrame) -> Dict[str, Any]:
        if "ciudad" not in df.columns:
            return {}

        dist = df["ciudad"].value_counts()
        total = len(df)

        result = {}
        for city, count in dist.items():
            result[city] = {
                "cantidad": int(count),
                "porcentaje": round(count / total * 100, 1),
            }

        return result

    def _salary_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        if "salario_promedio" not in df.columns or "ciudad" not in df.columns:
            return {}

        count_col = "titulo" if "titulo" in df.columns else df.columns[0]
        by_city = df.groupby("ciudad").agg(
            promedio=("salario_promedio", "mean"),
            minimo=("salario_minimo", "min"),
            maximo=("salario_maximo", "max"),
            mediana=("salario_promedio", "median"),
            count=(count_col, "count"),
        ).to_dict("index")

        return by_city

    def _role_demand(self, df: pd.DataFrame) -> Dict[str, Any]:
        if "role_categoria" not in df.columns:
            return {}

        roles = df["role_categoria"].value_counts()
        total = len(df)

        result = {}
        for role, count in roles.items():
            role_df = df[df["role_categoria"] == role]
            sal = pd.to_numeric(role_df.get("salario_promedio", pd.Series()), errors="coerce").dropna()

            result[role] = {
                "cantidad": int(count),
                "porcentaje": round(count / total * 100, 1),
                "salario_promedio": float(sal.mean()) if len(sal) > 0 else 0,
            }

        return result

    def _modality_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        modal_col = "modalidad_clean" if "modalidad_clean" in df.columns else "modalidad"
        if modal_col not in df.columns:
            return {}

        modals = df[modal_col].value_counts()
        total = len(df)

        result = {}
        for mod, count in modals.items():
            result[mod] = {
                "cantidad": int(count),
                "porcentaje": round(count / total * 100, 1),
            }

        return result

    def _cargo_levels(self, df: pd.DataFrame) -> Dict[str, Any]:
        if "cargo_nivel" not in df.columns:
            return {}

        levels = df["cargo_nivel"].value_counts()
        total = len(df)

        result = {}
        for level, count in levels.items():
            level_df = df[df["cargo_nivel"] == level]
            sal = pd.to_numeric(level_df.get("salario_promedio", pd.Series()), errors="coerce").dropna()

            result[level] = {
                "cantidad": int(count),
                "porcentaje": round(count / total * 100, 1),
                "salario_promedio": float(sal.mean()) if len(sal) > 0 else 0,
            }

        return result

    def _skills_demand(self, df: pd.DataFrame) -> Dict[str, Any]:
        if "skills_str" not in df.columns:
            return {}

        all_skills = []
        for skills in df["skills_str"].dropna():
            if skills:
                all_skills.extend([s.strip() for s in str(skills).split(",") if s.strip()])

        if not all_skills:
            return {}

        skill_counts = pd.Series(all_skills).value_counts()
        total_skills = len(all_skills)

        result = {}
        for skill, count in skill_counts.head(15).items():
            result[skill] = {
                "cantidad": int(count),
                "porcentaje": round(count / total_skills * 100, 1),
            }

        return result

    def _employability_opportunities(self, df: pd.DataFrame) -> Dict[str, Any]:
        opportunities = {
            "alta_demanda": [],
            "mejor_pagados": [],
            "crecimiento": [],
        }

        if "role_categoria" in df.columns:
            role_counts = df["role_categoria"].value_counts()
            for role in role_counts.head(5).index:
                count = role_counts[role]
                pct = round(count / len(df) * 100, 1)
                opportunities["alta_demanda"].append(f"{role} ({count} ofertas, {pct}%)")

        if "salario_promedio" in df.columns and "role_categoria" in df.columns:
            sal_by_role = df.groupby("role_categoria")["salario_promedio"].mean().sort_values(ascending=False)
            for role in sal_by_role.head(5).index:
                sal = sal_by_role[role]
                if sal > 0:
                    opportunities["mejor_pagados"].append(f"{role} (${sal/1e6:.2f}M promedio)")

        if "salario_promedio" in df.columns and "ciudad" in df.columns:
            sal_by_city = df.groupby("ciudad")["salario_promedio"].mean().sort_values(ascending=False)
            for city in sal_by_city.head(3).index:
                sal = sal_by_city[city]
                if sal > 0:
                    opportunities["crecimiento"].append(f"{city}: ${sal/1e6:.2f}M promedio")

        if "modalidad_clean" in df.columns:
            mod_counts = df["modalidad_clean"].value_counts()
            for mod, count in mod_counts.items():
                if mod != "presencial" and count > 0:
                    pct = round(count / len(df) * 100, 1)
                    opportunities["crecimiento"].append(f"Modalidad '{mod}': {count} ofertas ({pct}%)")

        if "cargo_nivel" in df.columns:
            cargo_counts = df["cargo_nivel"].value_counts()
            for cargo, count in cargo_counts.items():
                if count > 0:
                    pct = round(count / len(df) * 100, 1)
                    opportunities["crecimiento"].append(f"Nivel '{cargo}': {count} ofertas ({pct}%)")

        if not opportunities["alta_demanda"]:
            opportunities["alta_demanda"].append("Análisis basado en datos del archivo subido")
        if not opportunities["mejor_pagados"]:
            opportunities["mejor_pagados"].append("Sin datos salariales para analizar")
        if not opportunities["crecimiento"]:
            opportunities["crecimiento"].append("Sin tendencias detectadas")

        return opportunities

    def _generate_recommendations(self, df: pd.DataFrame) -> List[str]:
        recommendations = []

        if "salario_promedio" in df.columns:
            avg_sal = df["salario_promedio"].mean()
            if avg_sal > 5_000_000:
                recommendations.append("Los salarios promedio son competitivos (+$5M COP). El sector TI en Medellín ofrece buenas remuneraciones.")
            elif avg_sal > 3_000_000:
                recommendations.append("Los salarios son moderados ($3M-$5M COP). Hay oportunidad de crecimiento con experiencia adicional.")
            else:
                recommendations.append("Los salarios están por debajo del promedio del sector. Considera especializarte en áreas de alta demanda.")

        if "modalidad_clean" in df.columns:
            remote_pct = len(df[df["modalidad_clean"] == "remoto"]) / len(df) * 100
            if remote_pct > 30:
                recommendations.append(f"El {remote_pct:.0f}% de las ofertas son remotas. Excelente oportunidad para trabajar desde casa.")

        if "cargo_nivel" in df.columns:
            senior_pct = len(df[df["cargo_nivel"] == "senior"]) / len(df) * 100
            if senior_pct > 40:
                recommendations.append("Alta demanda de perfiles senior. Considera obtener certificaciones y experiencia de liderazgo.")

        if "role_categoria" in df.columns:
            top_role = df["role_categoria"].value_counts().index[0]
            recommendations.append(f"El rol más demandado es '{top_role}'. Enfócate en habilidades relacionadas.")

        if not recommendations:
            recommendations.append("Se recomienda diversificar habilidades y mantenerse actualizado con las tendencias del mercado TI.")

        return recommendations

    def get_summary_text(self) -> str:
        if not self.analysis_results:
            return "No hay análisis disponible"

        res = self.analysis_results
        gen = res.get("resumen_general", {})

        text = f"""
INFORME DE EMPLEABILIDAD - AREA METROPOLITANA DE MEDELLIN
==========================================================

RESUMEN EJECUTIVO
-----------------
Total de ofertas analizadas: {gen.get('total_ofertas', 0)}
Salario promedio: ${gen.get('salario_promedio', 0)/1e6:.2f}M COP
Rango salarial: ${gen.get('salario_minimo', 0)/1e6:.2f}M - ${gen.get('salario_maximo', 0)/1e6:.2f}M COP
Mediana salarial: ${gen.get('mediana_salario', 0)/1e6:.2f}M COP

DISTRIBUCION POR MUNICIPIO
---------------------------
"""
        for city, data in res.get("distribucion_municipios", {}).items():
            text += f"  {city}: {data['cantidad']} ofertas ({data['porcentaje']}%)\n"

        text += "\nROLES MAS DEMANDADOS\n---------------------\n"
        for role, data in res.get("roles_demanda", {}).items():
            text += f"  {role}: {data['cantidad']} ofertas ({data['porcentaje']}%) - Prom: ${data['salario_promedio']/1e6:.2f}M\n"

        text += "\nMODALIDAD LABORAL\n-----------------\n"
        for mod, data in res.get("modalidad_tendencias", {}).items():
            text += f"  {mod}: {data['cantidad']} ofertas ({data['porcentaje']}%)\n"

        text += "\nRECOMENDACIONES\n---------------\n"
        for rec in res.get("recomendaciones", []):
            text += f"  * {rec}\n"

        return text
