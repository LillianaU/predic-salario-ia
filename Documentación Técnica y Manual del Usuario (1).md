# Documentación Técnica y Manual del Usuario

## 1. Información general del sistema

| Campo | Valor |
|-------|-------|
| **Nombre del modelo** | PredicSalario IA — Estudio Laboral de Pertinencia de Programas en TICs |
| **Tipo de modelo** | Regresión supervisada (Random Forest) + Red Neuronal (MLPRegressor) |
| **Autor(es)** | Lilliana Uribe González |
| **Fecha** | Junio 2025 |
| **Versión** | v2.0 — Análisis SENA + Neural Network |
| **Dataset utilizado** | 500 registros embebidos (generados con rangos salariales reales) + scraping en tiempo real de elempleo.com (~500 registros) |
| **Variable objetivo** | `salario_promedio` — Salario promedio mensual en COP (rango: $500,000 – $50,000,000) |
| **URL / Demo** | https://predic-salario-ia.streamlit.app/ |

---

## 2. Resumen ejecutivo

PredicSalario IA es un sistema de predicción salarial del sector tecnológico en Medellín, Colombia. Utiliza web scraping ético de elempleo.com (15 queries de alto impacto) para obtener ofertas reales, las procesa con un pipeline ETL y entrena un modelo de Machine Learning (Random Forest) que predice el salario esperado de un perfil profesional TIC. El sistema incluye una red neuronal (MLPRegressor) para análisis de empleabilidad y un agente de pertinencia laboral con IA generativa (Groq API) para generar informes del Registro Calificado CNA. Está dirigido a instituciones académicas, profesionales del sector TI y tomadores de decisiones laborales.

---

## 3. Problema y contexto

### 3.1 Problema identificado

Los profesionales del sector TI en Colombia carecen de información objetiva y actualizada sobre los salarios reales del mercado. Las instituciones académicas no disponen de datos para evaluar la pertinencia laboral de sus programas de formación. Los procesos de búsqueda de empleo dependen de información dispersa en múltiples portales, sin una visión integrada del mercado.

### 3.2 Justificación del uso de IA

El problema depende de múltiples variables no lineales (experiencia, habilidades técnicas, modalidad laboral, cargo, ubicación, empresa) que un modelo de Machine Learning puede aprender mejor que reglas manuales. El scraping automatizado permite obtener datos reales de múltiples fuentes, y los modelos de regresión y red neuronal pueden capturar patrones complejos del mercado laboral TIC.

---

## 4. Arquitectura del modelo

**Flujo del sistema:**

```
elempleo.com (15 queries de scraping)
    ↓ Scraping (HTTP cloudscraper con bypass Cloudflare)
Datos crudos (título, empresa, salario, ubicación, skills, modalidad)
    ↓ Limpieza ETL (DataCleaner)
Datos procesados (salario COP, experiencia años, skills detectados, categorías)
    ↓ Codificación (TF-IDF skills + LabelEncoder categorías + features numéricas)
Matriz de features (9 base + 80 TF-IDF = 89 columnas)
    ↓ Entrenamiento (Random Forest Regressor)
Modelo entrenado (salary_predictor.pkl)
    ↓ Predicción
Salario estimado + rango de confianza ±15%
```

**Flujo paralelo (Análisis de empleabilidad):**

```
Datos procesados → MLPRegressor (128/64/32 neuronas) → Análisis de empleabilidad
```

---

## 5. Datos y variables

- **Fuente del dataset:** Datos embebidos (500+ registros generados con plantillas reales del mercado TI de Medellín) + scraping en tiempo real de 5 portales de empleo
- **Número de registros:** 500 registros embebidos (carga instantánea) + scraping dinámico (variable)
- **Variables utilizadas:**

| Variable | Tipo | Descripción |
|----------|------|-------------|
| `experiencia_requerida` | Numérica | Años de experiencia (0-50) |
| `cargo_nivel_cod` | Categórica codificada | Nivel: técnico=0, tecnólogo=1, ingeniero=2, senior=3 |
| `modalidad_cod` | Categórica codificada | Presencial=0, híbrido=1, remoto=2 |
| `num_skills` | Numérica | Cantidad de habilidades técnicas detectadas |
| `tipo_contrato_cod` | Categórica codificada | Indefinido=0, servicios=1, obra=2, aprendizaje=3 |
| `exp_x_nivel` | Numérica derivada | Interacción experiencia × nivel de cargo |
| `exp_squared` | Numérica derivada | Experiencia al cuadrado (no linealidad) |
| `is_remote` | Binaria | 1 si es remoto, 0 si no |
| `role_categoria` | Categórica codificada | Categoría del rol (Desarrollo, Datos, IA, etc.) |
| `skills_tfidf` | Texto vectorizado | 80 features TF-IDF de habilidades técnicas |

- **Variables descartadas (y por qué):** `nombre_empresa` (no aporta al modelo), `url_fuente` (metadata), `fecha_publicacion` (temporal, no significativa), `titulo_completo` (redundante con role_categoria)
- **Tipo de datos:** Numéricos (5), categóricos codificados (4), texto vectorizado TF-IDF (80)

---

## 6. Modelo de IA utilizado

- **Algoritmo principal:** Random Forest Regressor (scikit-learn)
- **Algoritmo secundario:** MLPRegressor — Red neuronal para análisis de empleabilidad
- **Librerías:** scikit-learn, pandas, numpy, scipy, joblib, Plotly
- **Hiperparámetros:**
  - Random Forest: `n_estimators=100`, `max_depth=10`, `random_state=42`, `n_jobs=1`
  - MLPRegressor: `hidden_layer_sizes=(128, 64, 32)`, `activation='relu'`, `solver='adam'`, `max_iter=500`, `early_stopping=True`
- **Tipo de aprendizaje:** Supervisado (regresión)
- **Vectorización:** TF-IDF (`max_features=80`, `sublinear_tf=True`, `min_df=1`)

---

## 7. Entrenamiento y evaluación

- **División de datos:** 80% entrenamiento, 20% prueba (`test_size=0.2`, `random_state=42`)
- **Validación cruzada:** 3-5 folds (dinámico: `min(5, max(3, n_samples // 5))`)
- **Métricas utilizadas:**

| Métrica | Valor |
|---------|-------|
| R² (R-cuadrado) | 0.50 |
| MAE (Error absoluto medio) | $938,000 COP |
| RMSE (Error cuadrático medio) | $1,170,000 COP |

- **Resultados obtenidos:** El modelo explica el 50% de la varianza salarial. El error absoluto promedio es de $938,000 COP, lo cual es razonable dado el amplio rango salarial del sector TI ($500K – $50M COP). El rango de confianza es de ±15%. La precisión mejorará con datos reales de scraping (actualmente usa datos embebidos sintéticos).

---

## 8. Interpretabilidad

- **Variables más importantes:** `experiencia_requerida`, `cargo_nivel_cod`, `role_categoria`, `skills_tfidf` (habilidades específicas como Python, AWS, Kubernetes)
- **Método utilizado:** Feature importance del Random Forest + análisis de coeficientes TF-IDF
- **Explicación del modelo:**
  - A mayor experiencia requerida, mayor salario estimado
  - El nivel de cargo (técnico → senior) tiene impacto significativo
  - Ciertas habilidades (cloud, IA/ML, ciberseguridad) aumentan el salario
  - El trabajo remoto tiende a ofrecer salarios competitivos
  - La interacción experiencia × nivel captura el crecimiento no lineal del salario

---

## 9. Uso del modelo

1. El usuario ingresa su perfil en el formulario: experiencia, nivel de cargo, modalidad, tipo de contrato, habilidades técnicas, categoría de rol
2. El sistema procesa la información: codifica variables categóricas, vectoriza skills con TF-IDF, crea features derivadas
3. El modelo genera una predicción: salario estimado en COP + rango de confianza ±15%

---

## 10. Implementación técnica

- **Backend:** Python 3.12 + Streamlit
- **Frontend:** Streamlit (tema oscuro-only, diseño responsivo, burbujitas animadas)
- **Modelo:** Archivo `.pkl` entrenado (`models/salary_predictor.pkl`) + red neuronal MLPRegressor
- **Base de datos:** No aplica (datos embebidos + scraping en tiempo real)
- **Despliegue:** Streamlit Cloud (https://predic-salario-ia.streamlit.app/)
- **Repositorios:** GitHub (https://github.com/LillianaU/predic-salario-ia) + GitLab (https://gitlab.com/lillyuribegon/predic-salario-ia)

---

## 11. Resultados y valor

- Predicción salarial personalizada del sector TI en Medellín con datos reales del mercado
- Dashboard interactivo con gráficos de salarios, habilidades demandadas, distribución geográfica
- Análisis de empleabilidad con red neuronal para orientar decisiones de carrera
- Agente de pertinencia laboral con IA para informes del Registro Calificado CNA
- Scraping automatizado de 5 portales con 97 queries de búsqueda
- Exportación de informes en MD, TXT y PDF
- Sistema de fallback automático (embebidos → Playwright → HTTP → ZenRows)

---

## 12. Limitaciones

- **Sesgo geográfico:** Solo ofertas en Medellín y área metropolitana del Valle de Aburrá
- **Sesgo temporal:** Datos limitados al periodo disponible del scraping
- **Sesgo de plataforma:** Scraping de 5 portales (elempleo, computrabajo, indeed, glassdoor, dane)
- **Dataset embebido:** 500 registros sintéticos (mejor precisión con datos reales de scraping)
- **Precisión del modelo:** R² = 0.50 (mejorable con más datos reales)
- **Streamlit Cloud:** Playwright no disponible, usa HTTP fallback o datos embebidos
- **Límites de scraping:** ZenRows: 1000 req/mes gratis; rate limits en portales

---

## 13. Ética y seguridad

- El modelo puede generar sesgos si los datos de scraping están desbalanceados geográficamente
- No se almacenan datos personales de usuarios (solo perfil de entrada para predicción)
- API keys en `.env` (nunca en código), no PII almacenado
- Hash SHA-256 del modelo para integridad
- Logging append-only para auditoría
- Scraping ético con identificación de bot y respeto a robots.txt
- Datos obtenidos de fuentes públicas de empleo

---

## 14. Manual de uso

### Paso 1: Ingresar datos

1. Abrir https://predic-salario-ia.streamlit.app/
2. En el menú lateral, seleccionar **"🎯 Predice tu Salario"**
3. Completar el formulario con:
   - Experiencia (años)
   - Nivel de cargo (técnico / tecnólogo / ingeniero / senior)
   - Modalidad (presencial / híbrido / remoto)
   - Tipo de contrato
   - Habilidades técnicas (ej: Python, AWS, React)
   - Categoría de rol

### Paso 2: Ejecutar predicción

4. Hacer clic en **" Predecir Salario"**
5. El sistema procesa la información y muestra el resultado

### Paso 3: Interpretar resultado

6. **Salario estimado:** Valor en COP mensual
7. **Rango de confianza:** ±15% del valor estimado
8. **Análisis de empleabilidad:** Distribución por municipio, tendencias salariales, habilidades más demandadas

### Otras funcionalidades:

- **📊 Análisis del Mercado:** Dashboard interactivo con gráficos de ofertas, salarios, skills
- **📈 Informe Ejecutivo:** Análisis TICs por departamento con upload de archivo SENA
- **📋 Datos Crudos:** Exploración y descarga de datos con filtros
- **📋 Agente de Pertinencia:** Generación de informes CNA con IA (Groq API)

---

## 15. Checklist de entrega

- [x] Este documento diligenciado (Documentación Técnica y Manual del Usuario)
- [x] Repositorio

**Enlace del repositorio (OBLIGATORIO):**

- GitHub: https://github.com/LillianaU/predic-salario-ia
- GitLab: https://gitlab.com/lillyuribegon/predic-salario-ia

**Video de explicación del modelo (OBLIGATORIO):** *[Pendiente — enlace a incluir]*
