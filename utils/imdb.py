import requests
from config import Config

OMDB_API_URL = "http://www.omdbapi.com/"
_DEFAULT_HEADERS = {"Accept": "application/json", "User-Agent": "CineVibes/1.0"}
_CACHE: dict[str, tuple[dict, float]] = {}
_TTL_SEARCH = 30.0
_TTL_DETAIL = 60.0
import time

def search_movies(query: str):
    url = f"{OMDB_API_URL}?apikey={Config.OMDB_API_KEY}&s={requests.utils.quote(query)}&language=es"
    # cache simple en memoria
    now = time.time()
    key = f"s::{query}"
    if (cached := _CACHE.get(key)) and now - cached[1] < _TTL_SEARCH:
        return cached[0]
    try:
        resp = requests.get(url, headers=_DEFAULT_HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        _CACHE[key] = (data, now)
        return data
    except requests.exceptions.RequestException:
        return {"errorMessage": "No se pudo conectar con la API de OMDb"}

def get_movie_details(movie_id: str):
    url = f"{OMDB_API_URL}?apikey={Config.OMDB_API_KEY}&i={requests.utils.quote(movie_id)}&plot=full&language=es"
    now = time.time()
    key = f"i::{movie_id}"
    if (cached := _CACHE.get(key)) and now - cached[1] < _TTL_DETAIL:
        return cached[0]
    try:
        resp = requests.get(url, headers=_DEFAULT_HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        _CACHE[key] = (data, now)
        return data
    except requests.exceptions.RequestException:
        return {"errorMessage": "No se pudieron obtener los detalles de la película"}

def get_movie_details_by_title(title: str, year: str | None = None):
    # Fetch by exact title (and optional year) for cases where we don't have IMDb ID
    params = {
        'apikey': Config.OMDB_API_KEY,
        't': title,
        'plot': 'full',
        'language': 'es'
    }
    if year:
        params['y'] = year
    # Build URL manually to keep parity with other helpers
    url = f"{OMDB_API_URL}?" + "&".join(f"{k}={requests.utils.quote(str(v))}" for k, v in params.items())

    now = time.time()
    key = f"t::{title}::{year or ''}"
    if (cached := _CACHE.get(key)) and now - cached[1] < _TTL_DETAIL:
        return cached[0]
    try:
        resp = requests.get(url, headers=_DEFAULT_HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        _CACHE[key] = (data, now)
        return data
    except requests.exceptions.RequestException:
        return {"errorMessage": "No se pudieron obtener los detalles de la película"}