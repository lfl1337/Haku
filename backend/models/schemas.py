from pydantic import BaseModel


class BatchRequest(BaseModel):
    input_dir: str
    output_dir: str


class FromUrlRequest(BaseModel):
    image_url: str
    output_dir: str
    filename: str = "image"


class ProcessResult(BaseModel):
    original_preview: str
    processed_preview: str
    output_path: str
    success: bool


class SearchResult(BaseModel):
    title: str
    url: str
    thumbnail: str
    source: str


class SearchResponse(BaseModel):
    results: list[SearchResult]
