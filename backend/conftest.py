"""Pytest bootstrap for the Haku backend.

The backend uses flat imports (`from routers import ...`), so the backend
directory must be on sys.path when tests run from the repo root. We also set
HAKU_SKIP_BOOTSTRAP before main.py is imported so importing the app never
triggers pip installs or the texconv download.
"""

import os
import sys

os.environ.setdefault("HAKU_SKIP_BOOTSTRAP", "1")

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
