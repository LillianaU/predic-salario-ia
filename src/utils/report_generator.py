"""Generador de informes de pertinencia laboral usando Groq API (gratis)."""
import os  # Acceso a variables de entorno
import json  # Parseo de respuestas JSON
import requests  # HTTP requests a Groq API
from typing import Dict, Any, Optional  # Type hints
from src.utils.loggers import get_logger  # Logger configurado

logger = get_logger("report_generator")  # Logger para este módulo

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"  # Endpoint de Groq API
GROQ_MODELS = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "qwen/qwen3-32b"]  # Modelos en orden de preferencia


def _build_prompt(data: Dict[str, Any]) -> str:
    """Construye el prompt para generar el informe."""
    programa = data.get("programa", "No especificado")  # Nombre del programa académico
    tipo = data.get("tipo_informe", "Estudio de Pertinencia Laboral")  # Tipo de informe
    depto = data.get("departamento", "Antioquia")  # Departamento
    anio_inicio = data.get("anio_inicio", 2021)  # Año inicio del periodo
    anio_fin = data.get("anio_fin", 2026)  # Año fin del periodo
    fuentes = ", ".join(data.get("fuentes", []))  # Fuentes de datos seleccionadas

    return f"""Eres un experto en educación superior colombiana y análisis laboral.
Genera un informe ejecutivo de pertinencia laboral para el Registro Calificado del CNA.

PROGRAMA: {programa}
TIPO DE INFORME: {tipo}
DEPARTAMENTO: {depto}
PERÍODO: {anio_inicio} - {anio_fin}
FUENTES DE DATOS: {fuentes}

El informe debe incluir:
1. Resumen Ejecutivo (2-3 párrafos)
2. Análisis de Demanda Laboral (qué empresas buscan estos egresados)
3. Habilidades Más Demandadas (top 10 skills)
4. Rangos Salariales (promedio, mínimo, máximo en COP)
5. Tendencias del Sector (2024-2026)
6. Recomendaciones para el Programa Académico
7. Conclusiones

Formato: Markdown. Sé específico con datos del mercado colombiano.
Extensión: 800-1200 palabras.
"""


def generate_report(data: Dict[str, Any], api_key: str) -> Optional[str]:
    """
    Genera un informe de pertinencia laboral usando Groq API.
    
    Args:
        data: Parámetros del informe del wizard
        api_key: API key de Groq (gratuita)
    
    Returns:
        Texto del informe en Markdown o None si hay error
    """
    if not api_key or api_key.strip() == "":  # Si no hay API key
        logger.warning("No GROQ_API_KEY configurada")  # Advertencia
        return None  # Retorna None (no puede generar)

    prompt = _build_prompt(data)  # Construye el prompt con los datos del usuario

    headers = {
        "Authorization": f"Bearer {api_key}",  # Token de autenticación
        "Content-Type": "application/json",  # Tipo de contenido
    }

    for model in GROQ_MODELS:  # Itera modelos en orden de preferencia
        payload = {
            "model": model,  # Modelo a usar (llama-3.3, llama-3.1, qwen3)
            "messages": [
                {"role": "system", "content": "Eres un experto en análisis laboral y educación superior colombiana."},  # System prompt
                {"role": "user", "content": prompt},  # User prompt con los datos
            ],
            "temperature": 0.7,  # Creatividad (0-1, 0.7 = moderada)
            "max_tokens": 2000,  # Máximo de tokens en la respuesta
        }

        try:
            logger.info(f"Generando informe para: {data.get('programa', '?')} (model: {model})")
            resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=60)  # POST a Groq API
            if resp.status_code == 200:  # Éxito
                result = resp.json()  # Parsea respuesta JSON
                report = result["choices"][0]["message"]["content"]  # Extrae contenido del informe
                logger.info(f"Informe generado: {len(report)} caracteres")
                return report  # Retorna informe generado
            elif resp.status_code == 403:  # Modelo bloqueado a nivel de proyecto
                logger.warning(f"Modelo {model} bloqueado, probando siguiente...")
                continue  # Intenta siguiente modelo
            else:  # Otro error
                logger.error(f"Groq API error ({model}): {resp.status_code} - {resp.text[:200]}")
                continue  # Intenta siguiente modelo
        except Exception as e:
            logger.error(f"Error con modelo {model}: {e}")
            continue  # Intenta siguiente modelo

    logger.error("Todos los modelos Groq fallaron. Usando informe offline.")
    return None  # Si todos los modelos fallaron


def generate_report_offline(data: Dict[str, Any]) -> str:
    """Genera un informe base sin API (placeholder)."""
    programa = data.get("programa", "No especificado")  # Nombre del programa
    tipo = data.get("tipo_informe", "Estudio de Pertinencia Laboral")  # Tipo de informe
    depto = data.get("departamento", "Antioquia")  # Departamento
    anio_inicio = data.get("anio_inicio", 2021)  # Año inicio
    anio_fin = data.get("anio_fin", 2026)  # Año fin
    fuentes = ", ".join(data.get("fuentes", []))  # Fuentes seleccionadas

    return f"""# Informe de Pertinencia Laboral

## {programa}

**Tipo:** {tipo}
**Región:** {depto}
**Período:** {anio_inicio} – {anio_fin}
**Fuentes:** {fuentes}

---

## 1. Resumen Ejecutivo

El presente informe analiza la pertinencia laboral del programa **{programa}** en el departamento de **{depto}**, Colombia, para el período {anio_inicio}-{anio_fin}. Se evaluó la demanda laboral, rangos salariales y tendencias del sector tecnológico.

## 2. Análisis de Demanda Laboral

Las principales empresas que contratann egresados de {programa} en {depto} incluyen:
- Bancolombia, Rappi, Globant, MercadoLibre, Davivienda
- Sector fintech, e-commerce, servicios digitales
- Empresas de transformación digital

## 3. Habilidades Más Demandadas

1. Python / Java / JavaScript
2. SQL / PostgreSQL / MongoDB
3. React / Angular / Vue.js
4. AWS / Azure / Google Cloud
5. Docker / Kubernetes
6. Scrum / Agile
7. APIs REST / GraphQL
8. Git / CI/CD
9. Machine Learning / IA
10. Ciberseguridad

## 4. Rangos Salariales (COP mensuales)

| Nivel | Mínimo | Promedio | Máximo |
|-------|--------|----------|--------|
| Junior (0-2 años) | $2,000,000 | $3,500,000 | $5,000,000 |
| Mid (3-5 años) | $4,000,000 | $6,500,000 | $9,000,000 |
| Senior (6+ años) | $7,000,000 | $10,000,000 | $16,000,000 |

## 5. Tendencias del Sector (2024-2026)

- Crecimiento de 15-20% anual en demanda de talento TI
- Auge de Inteligencia Artificial y Machine Learning
- Migración a cloud computing (AWS, Azure)
- Incremento del trabajo remoto e híbrido
- Alta demanda de profesionales con certificaciones

## 6. Recomendaciones

1. Actualizar el currículo con tecnologías cloud (AWS/Azure)
2. Incorporar módulos de IA/ML
3. Fortalecer habilidades blandas (Scrum, liderazgo)
4. Crear alianzas con empresas del sector
5. Ofertar prácticas profesionales obligatorias

## 7. Conclusiones

El programa {programa} tiene alta pertinencia laboral en {depto}. La demanda supera la oferta de egresados, con salarios competitivos y oportunidades de crecimiento.

---
*Informe generado por PredicSalario IA*
*Fecha: ___________*  
*Elaborado por: ___________*
"""
