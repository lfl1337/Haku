from PIL import Image


def resize_stretch(img: Image.Image, target: int = 256) -> Image.Image:
    """Stretch to target×target, filling the entire canvas (no aspect-ratio preservation)."""
    return img.resize((target, target), Image.LANCZOS)
