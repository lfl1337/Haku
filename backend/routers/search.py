from fastapi import APIRouter, Query
from services.image_search import search_images

router = APIRouter()


@router.get("/images")
async def search(q: str = Query(...), max_results: int = Query(20)):
    results = await search_images(q, max_results)
    return {"results": results}
