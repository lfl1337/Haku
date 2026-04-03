from rembg import remove
from PIL import Image
import io


def remove_background(img_bytes: bytes) -> Image.Image:
    """Remove background and return RGBA Image."""
    result_bytes = remove(img_bytes)
    return Image.open(io.BytesIO(result_bytes)).convert("RGBA")
