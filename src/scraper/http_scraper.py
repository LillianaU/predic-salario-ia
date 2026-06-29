"""Scraper HTTP para elempleo.com usando cloudscraper con anti-detection."""

import re  # Expresiones regulares para parseo de HTML y salarios
import json  # Decodificación de JSON embebido en HTML
import time  # Pausas entre requests para evitar rate limiting
import random  # Selección aleatoria de User-Agents y delays
import datetime  # Fechas para registros
from typing import List, Dict, Any, Callable, Optional  # Type hints
from urllib.parse import quote  # Codificación URL para queries de búsqueda
from src.interfaces.scraper_strategy import ScraperStrategy  # Interfaz abstracta del scraper
from src.utils.loggers import get_logger  # Logger configurado

logger = get_logger("scraper.http")  # Logger para este módulo

USER_AGENTS = [  # Lista de User-Agents realistas para rotación
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",  # Chrome Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",  # Chrome Windows (versión anterior)
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",  # Chrome Mac
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",  # Firefox Windows
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",  # Safari Mac
]


class HttpScraper(ScraperStrategy):
    """HTTP-based scraper using cloudscraper with enhanced anti-detection.
    Works on Streamlit Cloud where Playwright is unavailable."""

    def __init__(self, timeout: int = 45, max_retries: int = 3, **kwargs):
        """Inicializa el scraper con configuración de timeout y reintentos.

        Args:
            timeout: Tiempo máximo de espera por request (segundos).
            max_retries: Número máximo de reintentos por query.
        """
        self.timeout = timeout  # Timeout HTTP en segundos
        self.max_retries = max_retries  # Máximo de reintentos
        self.session = None  # Sesión HTTP (se crea bajo demanda)

    def _get_session(self):
        """Crea o retorna la sesión HTTP con anti-detection."""
        if self.session is None:  # Si no hay sesión creada
            try:
                import cloudscraper  # Intenta importar cloudscraper (bypass Cloudflare)
                self.session = cloudscraper.create_scraper(
                    browser={
                        "browser": "chrome",  # Simula Chrome
                        "platform": "windows",  # Simula Windows
                        "desktop": True,  # Simula escritorio (no móvil)
                    },
                    delay=5,  # Delay inicial de 5 segundos
                )
                logger.info("Using cloudscraper (Cloudflare bypass)")
            except ImportError:  # Si cloudscraper no está instalado
                import requests  # Usa requests normal
                self.session = requests.Session()  # Crea sesión simple
                logger.info("Using requests (no cloudscraper)")

            # Realistic headers  # Headers realistas para parecer un navegador
            ua = random.choice(USER_AGENTS)  # Selecciona User-Agent aleatorio
            self.session.headers.update({
                "User-Agent": ua,  # User-Agent del navegador
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",  # Tipos de contenido aceptados
                "Accept-Language": "es-CO,es;q=0.9,en-US;q=0.8,en;q=0.7",  # Idioma: español Colombia
                "Accept-Encoding": "gzip, deflate, br",  # Compresión aceptada
                "Connection": "keep-alive",  # Conexión persistente
                "Upgrade-Insecure-Requests": "1",  # Solicita HTTPS
                "Sec-Fetch-Dest": "document",  # Destino: documento HTML
                "Sec-Fetch-Mode": "navigate",  # Modo: navegación
                "Sec-Fetch-Site": "none",  # Origen: directo (no referrer)
                "Sec-Fetch-User": "?1",  # Usuario interactuando
                "Cache-Control": "max-age=0",  # No usar caché
                "DNT": "1",  # Do Not Track activado
            })
        return self.session  # Retorna sesión configurada

    def _rotate_ua(self):
        """Rotate User-Agent for each request."""
        if self.session:  # Si hay sesión activa
            ua = random.choice(USER_AGENTS)  # Selecciona nuevo User-Agent aleatorio
            self.session.headers["User-Agent"] = ua  # Actualiza header

    def fetch_data(self, search_queries: List[str], progress_callback: Optional[Callable] = None) -> List[Dict[str, Any]]:
        """Ejecuta scraping para todas las queries de búsqueda.

        Args:
            search_queries: Lista de strings con las búsquedas a realizar.
            progress_callback: Función para reportar progreso a Streamlit.

        Returns:
            Lista de diccionarios con ofertas de empleo scrapeadas.
        """
        session = self._get_session()  # Obtiene sesión HTTP configurada
        all_results = []  # Lista acumuladora de todos los resultados
        global_seen = set()  # Set para deduplicar ofertas entre queries
        total_queries = len(search_queries)  # Total de queries a procesar

        for i, query in enumerate(search_queries):  # Itera cada query con índice
            # Report progress  # Reporta progreso a la UI
            if progress_callback:  # Si hay callback de progreso
                progress_callback(
                    current=i + 1,  # Query actual (1-indexed)
                    total=total_queries,  # Total de queries
                    query=query,  # Texto de la query
                    records=len(all_results),  # Ofertas encontradas hasta ahora
                    status="scraping"  # Estado: scrapeando
                )

            try:
                # Rotate UA every 5 queries  # Rota User-Agent cada 5 queries
                if i % 5 == 0:  # Si es múltiplo de 5
                    self._rotate_ua()  # Cambia User-Agent

                results = self._scrape_query_with_retry(session, query, global_seen)  # Scrapea con reintentos
                all_results.extend(results)  # Agrega resultados a la lista total
                logger.info(f"[HTTP] {len(results)} records for '{query}' (total: {len(all_results)})")
            except Exception as e:
                logger.error(f"[HTTP] Failed for '{query}': {e}")

            # Random delay between queries (2-5 seconds)  # Pausa aleatoria entre queries
            time.sleep(random.uniform(2.0, 5.0))  # Espera 2-5 segundos

        # Final progress  # Progreso final
        if progress_callback:  # Si hay callback
            progress_callback(
                current=total_queries,  # Todas las queries procesadas
                total=total_queries,
                query="Completado",  # Mensaje de completado
                records=len(all_results),  # Total de ofertas
                status="done"  # Estado: terminado
            )

        logger.info(f"[HTTP] Total: {len(all_results)} records")
        return all_results  # Retorna todas las ofertas encontradas

    def _scrape_query_with_retry(self, session, query: str, global_seen: set) -> List[Dict[str, Any]]:
        """Scrape with retry logic and exponential backoff."""
        for attempt in range(self.max_retries):  # Intenta hasta max_retries veces
            try:
                results = self._scrape_query(session, query, global_seen)  # Scrapea la query
                if results:  # Si obtuvo resultados
                    return results  # Retorna inmediatamente
                logger.warning(f"[HTTP] No results for '{query}' (attempt {attempt + 1})")
            except Exception as e:
                logger.warning(f"[HTTP] Attempt {attempt + 1} failed for '{query}': {e}")

            # Exponential backoff with jitter  # Espera exponencial con variación
            if attempt < self.max_retries - 1:  # Si no es el último intento
                wait = (2 ** attempt) * random.uniform(1.0, 2.0)  # 1-2s, 2-4s, 4-8s...
                time.sleep(wait)  # Espera antes de reintentar
                self._rotate_ua()  # Rotate UA on retry  # Rota User-Agent en reintento

        return []  # Si todos los intentos fallaron, retorna lista vacía

    def _scrape_query(self, session, query: str, global_seen: set) -> List[Dict[str, Any]]:
        """Scrapea una query específica en elempleo.com con paginación."""
        search_words = query.lower().replace("medellín", "").replace("colombia", "").strip()  # Limpia query: quita ubicación
        search_words = re.sub(r"\s+", " ", search_words).strip()  # Normaliza espacios múltiples
        search_slug = search_words.replace(" ", "-")  # Convierte espacios a guiones para URL
        search_slug = re.sub(r"[^a-z0-9\-áéíóúñ]", "", search_slug).strip("-")  # Quita caracteres especiales
        base_url = f"https://www.elempleo.com/co/ofertas-empleo/{quote(search_slug)}/medellin"  # Construye URL base

        results = []  # Lista de resultados de esta query
        page_num = 1  # Número de página actual

        while len(results) < 100 and page_num <= 10:  # Máximo 100 ofertas o 10 páginas
            url = f"{base_url}?p={page_num}" if page_num > 1 else base_url  # URL con paginación
            try:
                resp = session.get(url, timeout=self.timeout)  # Realiza request HTTP

                if resp.status_code == 403:  # Cloudflare bloqueó
                    logger.warning(f"[HTTP] Cloudflare 403 for {url}, rotating UA")
                    self._rotate_ua()  # Rota User-Agent
                    break  # Sale del loop de paginación

                if resp.status_code == 503:  # Servicio no disponible
                    logger.warning(f"[HTTP] Service unavailable (503) for {url}")
                    break  # Sale

                if resp.status_code != 200:  # Cualquier otro error HTTP
                    logger.warning(f"[HTTP] Status {resp.status_code} for {url}")
                    break  # Sale

                if "cf-browser-verification" in resp.text or "Just a moment..." in resp.text:  # Cloudflare challenge
                    logger.warning(f"[HTTP] Cloudflare challenge detected for {url}")
                    break  # Sale

                page_offers = self._extract_offers_from_json(resp.text, query, global_seen)  # Extrae ofertas del JSON embebido
                if not page_offers:  # Si no hay ofertas en esta página
                    logger.info(f"[HTTP] No offers found on page {page_num} for '{query}', stopping pagination")
                    break  # Detiene paginación

                results.extend(page_offers)  # Agrega ofertas de esta página
                logger.info(f"[HTTP] Page {page_num}: {len(page_offers)} offers for '{query}' (total: {len(results)})")
                page_num += 1  # Siguiente página
                time.sleep(random.uniform(1.0, 2.5))  # Pausa entre páginas

            except Exception as e:
                logger.error(f"[HTTP] Request error for {url}: {e}")
                break  # Sale si hay error de conexión

        return results  # Retorna ofertas de esta query

    def _extract_offers_from_json(self, html: str, query: str, global_seen: set) -> List[Dict[str, Any]]:
        """Extract job offers from data-ga4-offerdata JSON attributes embedded in HTML."""
        json_pattern = r'data-ga4-offerdata="([^"]+)"'  # Regex para encontrar atributos JSON
        raw_matches = re.findall(json_pattern, html)  # Encuentra todas las ocurrencias

        offers = []  # Lista de ofertas parseadas
        for raw in raw_matches:  # Itera cada match
            decoded = raw.replace("&quot;", '"').replace("&#237;", "í").replace("&#243;", "ó").replace("&#233;", "é").replace("&amp;", "&")  # Decodifica HTML entities
            try:
                data = json.loads(decoded)  # Parsea JSON
            except json.JSONDecodeError:  # Si el JSON es inválido
                continue  # Saltar esta oferta

            title = data.get("title", "").strip()  # Obtiene título
            company = data.get("company", "").strip()  # Obtiene empresa
            location = data.get("location", "Medellín").strip()  # Obtiene ubicación
            salary_text = data.get("salary", "").strip()  # Obtiene salario como texto
            tags = data.get("tags", "").strip()  # Obtiene skills/tags

            if not title:  # Si no hay título
                continue  # Saltar

            sal_min, sal_max = self._parse_salary(salary_text)  # Parsea salario a números

            record_id = f"{title[:50]}_{company[:30]}_{sal_min}"  # ID único para deduplicar
            if record_id in global_seen:  # Si ya vimos esta oferta
                continue  # Saltar duplicado
            global_seen.add(record_id)  # Agrega al set de vistos

            modalidad = "presencial"  # Default: presencial
            combined = f"{title} {tags} {salary_text}".lower()  # Texto combinado para detectar modalidad
            if "remoto" in combined or "virtual" in combined or "teletrabajo" in combined:  # Si contiene palabras de remoto
                modalidad = "remoto"  # Marca como remoto
            elif "híbrido" in combined or "hibrido" in combined or "mixto" in combined:  # Si contiene palabras de híbrido
                modalidad = "hibrido"  # Marca como híbrido

            offers.append({  # Agrega oferta a la lista
                "titulo": title[:200],  # Título (máx 200 chars)
                "empresa": company[:150] if company else "No especificada",  # Empresa (máx 150 chars)
                "salario_minimo": sal_min,  # Salario mínimo en COP
                "salario_maximo": sal_max,  # Salario máximo en COP
                "moneda": "COP",  # Moneda colombiana
                "ubicacion": f"{location}, Colombia" if location and "colombia" not in location.lower() else location or "Medellín, Colombia",  # Ubicación completa
                "experiencia_requerida": "",  # No disponible en JSON
                "tipo_contrato": "",  # No disponible en JSON
                "skills": tags,  # Skills/tags detectados
                "fecha_publicacion": datetime.date.today().isoformat(),  # Fecha de hoy
                "descripcion": "",  # No disponible en JSON
                "modalidad": modalidad,  # presencial/remoto/hibrido
            })

        return offers  # Retorna ofertas parseadas

    def _parse_card(self, card: str, query: str, global_seen: set) -> Dict[str, Any]:
        """Parse a job card from HTML (legacy fallback)."""
        return None  # No usa parseo HTML legacy (usa JSON embebido)

    def _parse_salary(self, text: str):
        """Parse salary from elempleo.com format (e.g. '$1,5 a $2 millones')."""
        if not text or "confidencial" in text.lower():  # Si no hay salario o es confidencial
            return 0.0, 0.0  # Retorna 0,0 (será filtrado por DataCleaner)

        nums = re.findall(r"[\d.,]+", text)  # Extrae todos los números del texto
        sal_nums = []  # Lista de números parseados
        for n in nums:  # Itera cada número encontrado
            try:
                n_clean = n.replace(".", "").replace(",", ".")  # Convierte formato colombiano a float
                sal_nums.append(float(n_clean))  # Agrega a lista
            except ValueError:
                pass  # Si no se puede parsear, lo ignora

        sal_min, sal_max = 0.0, 0.0  # Valores por defecto
        if len(sal_nums) >= 2:  # Si hay 2 o más números
            sal_min, sal_max = min(sal_nums), max(sal_nums)  # Menor = mínimo, mayor = máximo
        elif len(sal_nums) == 1:  # Si hay solo 1 número
            sal_min, sal_max = sal_nums[0] * 0.8, sal_nums[0] * 1.2  # Estima rango ±20%

        if "millon" in text.lower():  # Si menciona "millones"
            if sal_max > 0 and sal_max < 100:  # Si el número es pequeño (<100)
                sal_min *= 1_000_000  # Multiplica por 1 millón
                sal_max *= 1_000_000  # Multiplica por 1 millón

        return sal_min, sal_max  # Retorna salario mínimo y máximo
