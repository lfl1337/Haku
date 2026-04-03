from PIL import Image


def resize_with_padding(img: Image.Image, target: int = 256) -> Image.Image:
    """Proportional resize, centered on transparent canvas."""
    ratio = min(target / img.width, target / img.height)
    new_w = int(img.width * ratio)
    new_h = int(img.height * ratio)
    resized = img.resize((new_w, new_h), Image.LANCZOS)

    canvas = Image.new("RGBA", (target, target), (0, 0, 0, 0))
    offset_x = (target - new_w) // 2
    offset_y = (target - new_h) // 2
    canvas.paste(resized, (offset_x, offset_y), resized)
    return canvas
