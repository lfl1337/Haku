"""Auto-setup: install Python deps and download texconv on first run."""

import subprocess
import sys
import os

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.join(BACKEND_DIR, "tools")
TEXCONV_PATH = os.path.join(TOOLS_DIR, "texconv.exe")
REQUIREMENTS_PATH = os.path.join(BACKEND_DIR, "requirements.txt")

TEXCONV_API_URL = "https://api.github.com/repos/microsoft/DirectXTex/releases/latest"


def ensure_pip_deps():
    """Install missing Python dependencies from requirements.txt."""
    # Quick check: try importing the heaviest/most-likely-missing packages
    missing = False
    for module in ["fastapi", "rembg", "PIL", "duckduckgo_search", "httpx"]:
        try:
            __import__(module)
        except ImportError:
            missing = True
            break

    if not missing:
        return

    print("[Haku] Installing Python dependencies...")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-r", REQUIREMENTS_PATH, "-q"],
        stdout=subprocess.DEVNULL,
    )
    print("[Haku] Python dependencies installed.")


def ensure_texconv():
    """Download texconv.exe if not present."""
    if os.path.isfile(TEXCONV_PATH):
        return

    print("[Haku] Downloading texconv.exe...")
    os.makedirs(TOOLS_DIR, exist_ok=True)

    import urllib.request
    import json

    # Find the x64 Texconv.exe asset from latest release
    resp = urllib.request.urlopen(TEXCONV_API_URL)
    release = json.loads(resp.read())
    download_url = None
    for asset in release.get("assets", []):
        if asset["name"] == "Texconv.exe":
            download_url = asset["browser_download_url"]
            break

    if not download_url:
        print("[Haku] WARNING: Could not find Texconv.exe in latest release.")
        return

    resp = urllib.request.urlopen(download_url)
    with open(TEXCONV_PATH, "wb") as f:
        f.write(resp.read())

    print("[Haku] texconv.exe ready.")


def run():
    """Run all bootstrap checks."""
    ensure_pip_deps()
    ensure_texconv()
