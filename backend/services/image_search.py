from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import RatelimitException


async def search_images(query: str, max_results: int = 20) -> list:
    """Search images via DuckDuckGo — no API key needed."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.images(query, max_results=max_results))
    except RatelimitException:
        raise Exception("DuckDuckGo Ratelimit — bitte kurz warten und erneut versuchen.")
    except Exception as e:
        raise Exception(f"Suche fehlgeschlagen: {e}")

    return [
        {
            "title": r.get("title", ""),
            "url": r.get("image", ""),
            "thumbnail": r.get("thumbnail", ""),
            "source": r.get("source", ""),
        }
        for r in results
    ]
