from PIL import Image


def resize_with_padding(img: Image.Image, target: int = 256) -> Image.Image:
    """Stretch to target×target. Fills entire canvas."""
    return img.resize((target, target), Image.LANCZOS)
