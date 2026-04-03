from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from services.image_search import search_images

router = APIRouter()


@router.get("/images")
async def search(q: str = Query(...), max_results: int = Query(20)):
    try:
        results = await search_images(q, max_results)
        return {"results": results}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"error": str(e)},
        )
