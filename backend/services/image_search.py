from ddgs import DDGS
import time


async def search_images(query: str, max_results: int = 20) -> list:
    """Search images via DuckDuckGo — no API key needed."""
    ddgs = DDGS()

    # Try with different regions as fallback (DDG rate-limits vary by region)
    regions = ["de-de", "wt-wt", "us-en"]
    results = []

    for region in regions:
        try:
            results = ddgs.images(query, region=region, max_results=max_results)
            if results:
                break
        except Exception:
            time.sleep(0.5)
            continue

    return [
        {
            "title": r.get("title", ""),
            "url": r.get("image", ""),
            "thumbnail": r.get("thumbnail", ""),
            "source": r.get("source", ""),
        }
        for r in results
    ]
