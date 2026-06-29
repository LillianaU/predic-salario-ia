"""
Utilidad de detección de entorno para local vs Streamlit Cloud.

Detecta automáticamente si la app se ejecuta en Streamlit Cloud
o en local, y configura las opciones de scraping, API keys y
estrategia de fallback accordingly.

Author: Lilliana Uribe González
Version: 2.0
"""
import os
import sys


def is_streamlit_cloud() -> bool:
    """Detect if running on Streamlit Cloud."""
    # Streamlit Cloud sets these environment variables
    if os.getenv("STREAMLIT_SERVER_HEADLESS") == "true":
        return True
    if os.getenv("STREAMLIT_CLOUD") == "true":
        return True
    # Check for Streamlit Cloud's specific user agent or server
    if os.getenv("STREAMLIT_SERVER_ADDRESS"):
        return True
    # Check if running in a container (common in Streamlit Cloud)
    if os.path.exists("/.dockerenv"):
        return True
    # Check for common Streamlit Cloud paths
    if os.path.exists("/app"):
        return True
    return False


def is_local() -> bool:
    """Detect if running locally."""
    return not is_streamlit_cloud()


def get_playwright_available() -> bool:
    """Check if Playwright is available and can run."""
    if is_streamlit_cloud():
        return False  # Streamlit Cloud doesn't have Chromium
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
        return True
    except Exception:
        return False


def get_zenrows_key() -> str:
    """Get ZenRows API key from environment or Streamlit secrets."""
    key = os.getenv("ZENROWS_API_KEY", "")
    if key:
        return key
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            key = st.secrets.get("ZENROWS_API_KEY", "")
            if key:
                return key
    except Exception:
        pass
    return ""


def get_scraper_strategy() -> str:
    """Get the best scraper strategy for the current environment."""
    if is_local():
        # Try Playwright first on local
        if get_playwright_available():
            return "playwright"
        # Fallback to HTTP on local
        return "http"
    else:
        # On Streamlit Cloud: ZenRows > HTTP
        if get_zenrows_key():
            return "zenrows"
        return "http"


def get_groq_key() -> str:
    """Get Groq API key from environment or Streamlit secrets."""
    # Try environment variable first (local .env)
    key = os.getenv("GROQ_API_KEY", "")
    if key:
        return key
    
    # Try Streamlit secrets (Streamlit Cloud)
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            key = st.secrets.get("GROQ_API_KEY", "")
            if key:
                return key
    except Exception:
        pass
    
    return ""


def get_environment_info() -> dict:
    """Get detailed environment information."""
    env = "Streamlit Cloud" if is_streamlit_cloud() else "Local"
    playwright = get_playwright_available()
    scraper = get_scraper_strategy()
    groq_key = bool(get_groq_key())
    
    return {
        "environment": env,
        "playwright_available": playwright,
        "scraper_strategy": scraper,
        "groq_configured": groq_key,
        "python_version": sys.version,
        "platform": sys.platform,
    }
