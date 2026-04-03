from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from services.background_remover import remove_background
from services.image_processor import resize_with_padding
from services.dds_converter import convert_to_dds
from models.schemas import BatchRequest, FromUrlRequest
from PIL import Image
import io
import base64
import os
import json

router = APIRouter()


@router.post("/single")
async def process_single(file: UploadFile = File(...), output_dir: str = Form(...)):
    img_bytes = await file.read()
    original = Image.open(io.BytesIO(img_bytes)).convert("RGBA")

    # Original preview
    buf = io.BytesIO()
    original.save(buf, "PNG")
    original_b64 = base64.b64encode(buf.getvalue()).decode()

    # Pipeline: BG Remove → Resize → DDS
    no_bg = remove_background(img_bytes)
    padded = resize_with_padding(no_bg)

    # Processed preview
    buf2 = io.BytesIO()
    padded.save(buf2, "PNG")
    processed_b64 = base64.b64encode(buf2.getvalue()).decode()

    # Temp PNG → texconv → DDS
    stem = os.path.splitext(file.filename)[0]
    temp_png = os.path.join(output_dir, f"_temp_{stem}.png")
    padded.save(temp_png, "PNG")
    convert_to_dds(temp_png, output_dir)
    os.remove(temp_png)

    return {
        "original_preview": original_b64,
        "processed_preview": processed_b64,
        "output_path": os.path.join(output_dir, f"{stem}.dds"),
        "success": True,
    }


@router.post("/batch")
async def process_batch(body: BatchRequest):
    input_dir = body.input_dir
    output_dir = body.output_dir
    supported = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tga")
    files = [f for f in os.listdir(input_dir) if f.lower().endswith(supported)]

    async def stream():
        for i, fname in enumerate(files):
            yield json.dumps({
                "file": fname,
                "status": "processing",
                "progress": i + 1,
                "total": len(files),
            }) + "\n"

            path = os.path.join(input_dir, fname)
            try:
                with open(path, "rb") as f:
                    img_bytes = f.read()
                no_bg = remove_background(img_bytes)
                padded = resize_with_padding(no_bg)

                stem = os.path.splitext(fname)[0]
                temp_png = os.path.join(output_dir, f"_temp_{stem}.png")
                padded.save(temp_png, "PNG")
                convert_to_dds(temp_png, output_dir)
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

    async with httpx.AsyncClient() as client:
        resp = await client.get(body.image_url)
        img_bytes = resp.content

    original = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
    buf = io.BytesIO()
    original.save(buf, "PNG")
    original_b64 = base64.b64encode(buf.getvalue()).decode()

    no_bg = remove_background(img_bytes)
    padded = resize_with_padding(no_bg)

    buf2 = io.BytesIO()
    padded.save(buf2, "PNG")
    processed_b64 = base64.b64encode(buf2.getvalue()).decode()

    temp_png = os.path.join(body.output_dir, f"_temp_{body.filename}.png")
    padded.save(temp_png, "PNG")
    convert_to_dds(temp_png, body.output_dir)
    os.remove(temp_png)

    return {
        "original_preview": original_b64,
        "processed_preview": processed_b64,
        "output_path": os.path.join(body.output_dir, f"{body.filename}.dds"),
        "success": True,
    }
