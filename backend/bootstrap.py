"""Auto-setup: install Python deps and download texconv on first run."""

import hashlib
import subprocess
import sys
import os

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.join(BACKEND_DIR, "tools")
TEXCONV_PATH = os.path.join(TOOLS_DIR, "texconv.exe")
REQUIREMENTS_PATH = os.path.join(BACKEND_DIR, "requirements.txt")

TEXCONV_API_URL = "https://api.github.com/repos/microsoft/DirectXTex/releases/latest"

# Known-good SHA256 for the texconv.exe shipped with the DirectXTex "may2026"
# release, recorded out-of-band. If the GitHub release API still advertises a
# per-asset digest (it currently does, as "sha256:..."), we verify against that
# authoritative value; this constant is a secondary anchor / audit trail.
# TODO: refresh when bumping the pinned release.
TEXCONV_KNOWN_SHA256 = (
    "dcfdec10244e02cf5037fba089c55fb7e1326b1c8181742d77d15fa5cb5eef06"
)


def ensure_pip_deps():
    """Install missing Python dependencies from requirements.txt."""
    # Quick check: try importing the heaviest/most-likely-missing packages
    missing = False
    for module in ["fastapi", "rembg", "PIL", "ddgs", "httpx"]:
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


def _parse_sha256_digest(asset: dict) -> str | None:
    """Return the lowercase SHA256 hex from a release asset's `digest` field.

    GitHub advertises asset digests as e.g. "sha256:abcd...". Anything that is
    not an sha256 digest is ignored (returns None) so we fall back to the
    known-good constant instead of trusting an unverified download.
    """
    digest = (asset.get("digest") or "").strip().lower()
    if digest.startswith("sha256:"):
        value = digest.split(":", 1)[1]
        if len(value) == 64 and all(c in "0123456789abcdef" for c in value):
            return value
    return None


def ensure_texconv():
    """Download texconv.exe if not present, verifying its SHA256 before use.

    The previous implementation trusted the download blindly (TOFU). We now
    verify the bytes against the digest GitHub publishes for the asset (an
    authoritative, out-of-band value) and fall back to a pinned known-good
    hash if the API stops advertising one. On any mismatch the temp file is
    deleted and we abort rather than install an unverified binary.
    """
    if os.path.isfile(TEXCONV_PATH):
        return

    print("[Haku] Downloading texconv.exe...")
    os.makedirs(TOOLS_DIR, exist_ok=True)

    import urllib.request
    import json

    # Find the x64 texconv.exe asset from the latest release. Match case-
    # insensitively: the asset has been published as both "Texconv.exe" and
    # "texconv.exe" across releases.
    resp = urllib.request.urlopen(TEXCONV_API_URL)
    release = json.loads(resp.read())
    asset = None
    for candidate in release.get("assets", []):
        if candidate.get("name", "").lower() == "texconv.exe":
            asset = candidate
            break

    if not asset:
        raise RuntimeError(
            "[Haku] Could not find texconv.exe in the latest DirectXTex release."
        )

    download_url = asset["browser_download_url"]
    expected = _parse_sha256_digest(asset) or TEXCONV_KNOWN_SHA256

    resp = urllib.request.urlopen(download_url)
    data = resp.read()
    actual = hashlib.sha256(data).hexdigest()

    if actual != expected:
        raise RuntimeError(
            "[Haku] texconv.exe SHA256 mismatch — refusing to install. "
            f"expected {expected}, got {actual}. The download may be corrupt "
            "or tampered with."
        )

    # Write to a temp file first, then atomically move into place so a partial
    # or rejected download never leaves a usable texconv.exe behind.
    tmp_path = TEXCONV_PATH + ".tmp"
    try:
        with open(tmp_path, "wb") as f:
            f.write(data)
        os.replace(tmp_path, TEXCONV_PATH)
    except BaseException:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise

    print("[Haku] texconv.exe ready (SHA256 verified).")


def run():
    """Run all bootstrap checks."""
    ensure_pip_deps()
    ensure_texconv()
