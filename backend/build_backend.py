"""Build the backend as standalone .exe (onefile) and copy to src-tauri/binaries/.

Self-contained: installs all required Python packages and downloads texconv if needed.
Run with: python backend/build_backend.py
"""

import subprocess
import shutil
import sys
import os

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BACKEND_DIR)
BINARIES_DIR = os.path.join(ROOT_DIR, "src-tauri", "binaries")
REQUIREMENTS = os.path.join(BACKEND_DIR, "requirements.txt")
TEXCONV = os.path.join(BACKEND_DIR, "tools", "texconv.exe")


def pip_install(*packages):
    subprocess.run([sys.executable, "-m", "pip", "install", *packages], check=True)


# 1. Ensure PyInstaller is available
try:
    import PyInstaller
except ImportError:
    print(">>> Installing PyInstaller...")
    pip_install("pyinstaller")

# 2. Ensure backend dependencies are installed
print(">>> Installing backend dependencies...")
pip_install("-r", REQUIREMENTS)

# 3. Ensure texconv.exe is present
if not os.path.isfile(TEXCONV):
    print(">>> texconv.exe not found, downloading...")
    sys.path.insert(0, BACKEND_DIR)
    import bootstrap
    bootstrap.ensure_texconv()

# 4. Build via spec file
print(">>> Building backend with PyInstaller...")
subprocess.run(
    ["pyinstaller", "--clean", "--noconfirm", "backend.spec"],
    cwd=BACKEND_DIR,
    check=True,
)

# 5. Copy to src-tauri/binaries/ (Tauri sidecar naming convention)
built_exe = os.path.join(BACKEND_DIR, "dist", "backend.exe")
os.makedirs(BINARIES_DIR, exist_ok=True)
dest = os.path.join(BINARIES_DIR, "backend-x86_64-pc-windows-msvc.exe")
shutil.copy2(built_exe, dest)
print(f">>> Done: {dest}")
