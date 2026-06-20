import subprocess
import sys
import os


def _get_texconv_path():
    """Find texconv.exe — handles both dev and PyInstaller frozen modes."""
    if getattr(sys, 'frozen', False):
        # Frozen: backend.spec bundles texconv under the 'tools' subdir of _MEIPASS
        base = os.path.join(sys._MEIPASS, "tools")
    else:
        # Dev: texconv is in backend/tools/
        base = os.path.join(os.path.dirname(__file__), "..", "tools")
    return os.path.join(base, "texconv.exe")


TEXCONV_PATH = _get_texconv_path()


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
