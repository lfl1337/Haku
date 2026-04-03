from duckduckgo_search import DDGS


async def search_images(query: str, max_results: int = 20) -> list:
    """Search images via DuckDuckGo — no API key needed."""
    with DDGS() as ddgs:
        results = list(ddgs.images(query, max_results=max_results))
    return [
        {
            "title": r.get("title", ""),
            "url": r.get("image", ""),
            "thumbnail": r.get("thumbnail", ""),
            "source": r.get("source", ""),
        }
        for r in results
    ]
