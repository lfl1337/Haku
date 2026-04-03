import subprocess
import os

TEXCONV_PATH = os.path.join(os.path.dirname(__file__), "..", "tools", "texconv.exe")


def convert_to_dds(input_png: str, output_dir: str) -> str:
    """Convert PNG to DDS BC3 (DXT5) with all mipmap levels."""
    cmd = [
        TEXCONV_PATH,
        "-f", "BC3_UNORM",
        "-m", "0",
        "-y",
        "-o", output_dir,
        input_png
    ]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return result.stdout
