from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from services.background_remover import remove_background
from services.image_processor import resize_stretch
from services.dds_converter import convert_to_dds
from models.schemas import BatchRequest, FromUrlRequest
from security import (
    PathValidationError,
    safe_filename,
    safe_output_path,
    validate_dir,
    validate_image_url,
)
from PIL import Image
import io
import base64
import os
import json

router = APIRouter()


@router.post("/single")
async def process_single(file: UploadFile = File(...), output_dir: str = Form(...)):
    try:
        out_dir = validate_dir(output_dir)
        stem = safe_filename(os.path.splitext(os.path.basename(file.filename or ""))[0])
        temp_png = safe_output_path(output_dir, stem, ".png")
        out_dds = safe_output_path(output_dir, stem, ".dds")
    except PathValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    img_bytes = await file.read()
    original = Image.open(io.BytesIO(img_bytes)).convert("RGBA")

    # Original preview
    buf = io.BytesIO()
    original.save(buf, "PNG")
    original_b64 = base64.b64encode(buf.getvalue()).decode()

    # Pipeline: BG Remove → Resize → DDS
    no_bg = remove_background(img_bytes)
    padded = resize_stretch(no_bg)

    # Processed preview
    buf2 = io.BytesIO()
    padded.save(buf2, "PNG")
    processed_b64 = base64.b64encode(buf2.getvalue()).decode()

    # Temp PNG → texconv → DDS (paths validated above)
    padded.save(temp_png, "PNG")
    convert_to_dds(str(temp_png), str(out_dir))
    os.remove(temp_png)

    return {
        "original_preview": original_b64,
        "processed_preview": processed_b64,
        "output_path": str(out_dds),
        "success": True,
    }


@router.post("/batch")
async def process_batch(body: BatchRequest):
    try:
        in_dir = validate_dir(body.input_dir)
        out_dir = validate_dir(body.output_dir)
    except PathValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    supported = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tga")
    files = [f for f in os.listdir(in_dir) if f.lower().endswith(supported)]

    async def stream():
        for i, fname in enumerate(files):
            yield json.dumps({
                "file": fname,
                "status": "processing",
                "progress": i + 1,
                "total": len(files),
            }) + "\n"

            try:
                # os.listdir yields bare names, but route them through the
                # same validation so the read/write paths stay contained.
                src = safe_output_path(str(in_dir), fname)
                stem = safe_filename(os.path.splitext(fname)[0])
                temp_png = safe_output_path(str(out_dir), stem, ".png")

                with open(src, "rb") as f:
                    img_bytes = f.read()
                no_bg = remove_background(img_bytes)
                padded = resize_stretch(no_bg)

                padded.save(temp_png, "PNG")
                convert_to_dds(str(temp_png), str(out_dir))
                os.remove(temp_png)

                buf = io.BytesIO()
                padded.save(buf, "PNG")
                preview = base64.b64encode(buf.getvalue()).decode()

                yield json.dumps({
                    "file": fname,
                    "status": "done",
                    "preview": preview,
                }) + "\n"
            except Exception as e:
                yield json.dumps({
                    "file": fname,
                    "status": "error",
                    "error": str(e),
                }) + "\n"

        yield json.dumps({
            "status": "complete",
            "processed": len(files),
        }) + "\n"

    return StreamingResponse(stream(), media_type="application/x-ndjson")


@router.post("/from-url")
async def process_from_url(body: FromUrlRequest):
    import httpx

    try:
        url = validate_image_url(body.image_url)
        out_dir = validate_dir(body.output_dir)
        temp_png = safe_output_path(body.output_dir, body.filename, ".png")
        out_dds = safe_output_path(body.output_dir, body.filename, ".dds")
    except PathValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # follow_redirects stays False so a 3xx cannot bounce us past the SSRF
    # check to an internal host; a timeout caps the request.
    try:
        async with httpx.AsyncClient(
            follow_redirects=False, timeout=httpx.Timeout(15.0)
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            img_bytes = resp.content
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"failed to fetch image: {exc}")

    original = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
    buf = io.BytesIO()
    original.save(buf, "PNG")
    original_b64 = base64.b64encode(buf.getvalue()).decode()

    no_bg = remove_background(img_bytes)
    padded = resize_stretch(no_bg)

    buf2 = io.BytesIO()
    padded.save(buf2, "PNG")
    processed_b64 = base64.b64encode(buf2.getvalue()).decode()

    padded.save(temp_png, "PNG")
    convert_to_dds(str(temp_png), str(out_dir))
    os.remove(temp_png)

    return {
        "original_preview": original_b64,
        "processed_preview": processed_b64,
        "output_path": str(out_dds),
        "success": True,
    }
