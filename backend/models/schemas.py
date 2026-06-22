from pydantic import BaseModel, field_validator

from security import PathValidationError, safe_filename


def _reject_nul(value: str) -> str:
    if "\x00" in value:
        raise ValueError("must not contain a NUL byte")
    return value


class BatchRequest(BaseModel):
    input_dir: str
    output_dir: str

    @field_validator("input_dir", "output_dir")
    @classmethod
    def _no_nul(cls, value: str) -> str:
        return _reject_nul(value)


class FromUrlRequest(BaseModel):
    image_url: str
    output_dir: str
    filename: str = "image"

    @field_validator("output_dir")
    @classmethod
    def _no_nul(cls, value: str) -> str:
        return _reject_nul(value)

    @field_validator("filename")
    @classmethod
    def _safe_filename(cls, value: str) -> str:
        # Reject path separators / traversal at the schema boundary so a
        # malicious body is rejected before any filesystem access.
        try:
            return safe_filename(value)
        except PathValidationError as exc:
            raise ValueError(str(exc))


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
