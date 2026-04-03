# Haku (白) — Background Removal & DDS Texture Converter

> **Repo:** `lfl1337/Haku`  
> **Pfad:** `F:\Projekte\Haku`  
> **Stack:** Tauri v2 + FastAPI + React (Vite)  
> **Zweck:** Bilder suchen/laden → Hintergrund entfernen → 256×256 (proportional mit Transparenz-Padding) → DDS BC3 mit Mipmaps exportieren

---

## Übersicht

Haku ist ein schlankes Desktop-Tool für Game-Asset-Vorbereitung. Drei Eingabewege: Einzelbild, Batch-Ordner oder Online-Bildersuche (DuckDuckGo, kein API-Key nötig). Ausgabe sind fertige `.dds`-Dateien im BC3-Format (DXT5) mit Mipmaps — ready to use.

---

## Features

- **Drei Eingabemodi:** Einzelbild, Batch (ganzer Ordner), Online-Suche (DuckDuckGo)
- **Background Removal:** Automatisch via `rembg` (U2Net)
- **Proportionales Resize:** 256×256 ohne Stretching — Bild wird zentriert, Rest mit Transparenz aufgefüllt
- **DDS Export:** BC3 (DXT5) mit Mipmaps via Microsoft `texconv`
- **Live-Vorschau:** Vorher/Nachher Side-by-Side im UI
- **Input/Output-Ordner:** Frei wählbar über nativen Datei-Dialog
- **Dark Theme:** Durchgehend dunkles UI

---

## Projektstruktur

```
F:\Projekte\Haku\
├── src-tauri/                        # Tauri v2 (Rust)
│   ├── src/
│   │   └── main.rs                   # Entry, Kommandos, Window-Config
│   ├── icons/                        # App Icons
│   ├── Cargo.toml
│   └── tauri.conf.json               # Window, Bundle, Identifier
│
├── backend/                          # FastAPI (Python)
│   ├── main.py                       # App-Init, CORS, Startup/Shutdown
│   ├── routers/
│   │   ├── process.py                # POST /process/single & /process/batch
│   │   └── search.py                 # GET /search/images?q=...
│   ├── services/
│   │   ├── background_remover.py     # rembg Wrapper
│   │   ├── image_processor.py        # Resize + Padding (Pillow)
│   │   ├── dds_converter.py          # texconv CLI Wrapper
│   │   └── image_search.py           # DuckDuckGo Search (duckduckgo_search)
│   ├── models/
│   │   └── schemas.py                # Pydantic Models
│   ├── requirements.txt
│   └── tools/
│       └── texconv.exe               # Microsoft texconv (mitgeliefert)
│
├── src/                              # React Frontend (Vite)
│   ├── main.jsx                      # Entry
│   ├── App.jsx                       # Root, Mode-Routing
│   ├── index.css                     # CSS Variables, Dark Theme, Globals
│   ├── components/
│   │   ├── Layout.jsx                # App Shell — Header + Content Area
│   │   ├── ModeSwitch.jsx            # Toggle: Einzel / Batch / Suche
│   │   ├── SingleMode.jsx            # Einzelbild wählen + verarbeiten
│   │   ├── BatchMode.jsx             # Ordner wählen + Batch verarbeiten
│   │   ├── SearchMode.jsx            # Online-Suche, Grid, Auswahl
│   │   ├── Preview.jsx               # Vorher/Nachher Side-by-Side
│   │   ├── FolderPicker.jsx          # Input/Output Ordner Auswahl
│   │   ├── ProgressBar.jsx           # Batch-Fortschritt
│   │   └── ImageGrid.jsx             # Thumbnail-Grid (Suche + Batch)
│   └── hooks/
│       ├── useProcess.js             # API Calls für Verarbeitung
│       └── useSearch.js              # API Call für Bildersuche
│
├── package.json
├── vite.config.js
├── .github/
│   └── workflows/
│       └── release.yml               # GitHub Actions → .exe Build
├── .gitignore
└── README.md
```

---

## Stack & Dependencies

### Frontend (React + Vite)
```json
{
  "dependencies": {
    "react": "^18",
    "react-dom": "^18",
    "@tauri-apps/api": "^2",
    "@tauri-apps/plugin-dialog": "^2",
    "@tauri-apps/plugin-fs": "^2"
  },
  "devDependencies": {
    "vite": "^5",
    "@vitejs/plugin-react": "^4",
    "@tauri-apps/cli": "^2"
  }
}
```

### Backend (Python — `requirements.txt`)
```
fastapi==0.115.*
uvicorn==0.34.*
rembg==2.0.*
onnxruntime==1.19.*
Pillow==11.*
duckduckgo_search==7.*
python-multipart==0.0.*
httpx==0.28.*
```

### Tauri (Rust — `Cargo.toml`)
- `tauri` v2 mit Plugins: `dialog`, `fs`, `shell`

### Externes Tool
- **texconv.exe** — Microsoft DirectXTex Kommandozeilen-Tool. Wird im Repo unter `backend/tools/` mitgeliefert. Download: [GitHub DirectXTex Releases](https://github.com/microsoft/DirectXTex/releases)

---

## Backend-Architektur (FastAPI)

### Startup
- FastAPI läuft auf `127.0.0.1:23431` (nur lokal)
- Tauri startet den Python-Prozess als Sidecar beim App-Start
- CORS erlaubt nur `tauri://localhost` und `http://localhost:*`

### Endpoints

#### `POST /process/single`
```
Request (multipart/form-data):
  - file: UploadFile (Bild)
  - output_dir: str (Ausgabe-Ordner)

Response:
  {
    "original_preview": "base64 PNG",
    "processed_preview": "base64 PNG (transparent, 256x256)",
    "output_path": "F:\\Output\\image.dds",
    "success": true
  }
```

#### `POST /process/batch`
```
Request (JSON):
  {
    "input_dir": "F:\\Input",
    "output_dir": "F:\\Output"
  }

Response (SSE Stream — NDJSON):
  {"file": "img1.png", "status": "processing", "progress": 1, "total": 10}
  {"file": "img1.png", "status": "done", "preview": "base64..."}
  {"file": "img2.png", "status": "processing", "progress": 2, "total": 10}
  ...
  {"status": "complete", "processed": 10, "failed": 0}
```

#### `GET /search/images`
```
Query Params:
  - q: str (Suchbegriff)
  - max_results: int (default 20)

Response:
  {
    "results": [
      {
        "title": "...",
        "url": "https://...",
        "thumbnail": "https://...",
        "source": "example.com"
      }
    ]
  }
```

#### `POST /process/from-url`
```
Request (JSON):
  {
    "image_url": "https://...",
    "output_dir": "F:\\Output",
    "filename": "selected_image"
  }

Response: (wie /process/single)
```

---

## Verarbeitungs-Pipeline

```
Eingabe (PNG/JPG/WEBP/etc.)
    │
    ▼
┌─────────────────────────┐
│  1. Background Removal  │  rembg (U2Net Modell)
│     → RGBA PNG          │  Transparenter Hintergrund
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│  2. Resize & Padding    │  Pillow
│     → 256×256 RGBA      │  Proportional skalieren
│                         │  Zentrieren auf 256×256 Canvas
│                         │  Rest = Transparenz (Alpha 0)
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│  3. DDS Konvertierung   │  texconv.exe
│     → .dds BC3          │  Format: BC3_UNORM (DXT5)
│     → mit Mipmaps       │  Flag: -m 0 (alle Mip-Levels)
└─────────────────────────┘
```

### Resize-Logik (kein Stretching)
```python
def resize_with_padding(img: Image.Image, target: int = 256) -> Image.Image:
    """Proportional skalieren, zentriert auf transparentem 256x256 Canvas."""
    ratio = min(target / img.width, target / img.height)
    new_w = int(img.width * ratio)
    new_h = int(img.height * ratio)
    resized = img.resize((new_w, new_h), Image.LANCZOS)

    canvas = Image.new("RGBA", (target, target), (0, 0, 0, 0))
    offset_x = (target - new_w) // 2
    offset_y = (target - new_h) // 2
    canvas.paste(resized, (offset_x, offset_y), resized)
    return canvas
```

### texconv Aufruf
```python
import subprocess
import os

TEXCONV_PATH = os.path.join(os.path.dirname(__file__), "..", "tools", "texconv.exe")

def convert_to_dds(input_png: str, output_dir: str):
    """PNG → DDS BC3 (DXT5) mit allen Mipmap-Levels."""
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
```

---

## Frontend-Design

### Dark Theme — CSS Variables
```css
:root {
  --bg-primary: #0a0a0c;
  --bg-secondary: #131318;
  --bg-elevated: #1a1a22;
  --bg-hover: #222230;
  --border: #2a2a3a;
  --border-active: #4a4a6a;
  --text-primary: #e8e8f0;
  --text-secondary: #8888a0;
  --text-muted: #555568;
  --accent: #6c8aff;
  --accent-hover: #8aa4ff;
  --accent-dim: rgba(108, 138, 255, 0.12);
  --success: #4ade80;
  --error: #f87171;
  --radius: 8px;
  --radius-lg: 12px;
  --font-main: 'DM Sans', sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
}
```

### Layout
```
┌──────────────────────────────────────────────────┐
│  Haku 白                    [Einzel|Batch|Suche] │  ← Header
├──────────────────────────────────────────────────┤
│                                                  │
│  ┌─── Input ──────────┐  ┌─── Output ─────────┐ │
│  │ 📂 F:\Input        │  │ 📂 F:\Output       │ │  ← Ordner-Picker
│  └────────────────────┘  └─────────────────────┘ │
│                                                  │
│  ┌──────────────────────────────────────────────┐│
│  │                                              ││
│  │   Vorher              Nachher                ││  ← Preview Area
│  │   ┌──────────┐       ┌──────────┐            ││
│  │   │ Original │  →→→  │ 256×256  │            ││
│  │   │          │       │ DDS-Ready│            ││
│  │   └──────────┘       └──────────┘            ││
│  │                                              ││
│  └──────────────────────────────────────────────┘│
│                                                  │
│  [ ▶ Verarbeiten ]              Status: Bereit   │  ← Action Bar
└──────────────────────────────────────────────────┘
```

### Such-Modus Layout
```
┌──────────────────────────────────────────────────┐
│  🔍 [Suchbegriff eingeben...]          [Suchen]  │
├──────────────────────────────────────────────────┤
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐  │
│  │ img1 │ │ img2 │ │ img3 │ │ img4 │ │ img5 │  │
│  │      │ │  ✓   │ │      │ │      │ │      │  │  ← Auswählbar
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘  │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐            │
│  │ img6 │ │ img7 │ │ img8 │ │ img9 │            │
│  └──────┘ └──────┘ └──────┘ └──────┘            │
├──────────────────────────────────────────────────┤
│  2 ausgewählt          [ ▶ Auswahl verarbeiten ] │
└──────────────────────────────────────────────────┘
```

---

## Tauri-Konfiguration

### `tauri.conf.json` (Kernfelder)
```json
{
  "productName": "Haku",
  "version": "1.0.0",
  "identifier": "com.lfl1337.haku",
  "build": {
    "frontendDist": "../dist",
    "devUrl": "http://localhost:5173",
    "beforeDevCommand": "npm run dev",
    "beforeBuildCommand": "npm run build"
  },
  "app": {
    "title": "Haku 白",
    "windows": [
      {
        "label": "main",
        "width": 960,
        "height": 640,
        "resizable": true,
        "decorations": true,
        "center": true
      }
    ]
  },
  "plugins": {
    "dialog": { "all": true },
    "fs": {
      "scope": ["**"]
    },
    "shell": {
      "scope": [
        {
          "name": "python-backend",
          "cmd": "python",
          "args": ["-u", "backend/main.py"]
        }
      ]
    }
  },
  "bundle": {
    "active": true,
    "targets": ["nsis"],
    "icon": ["icons/icon.png"],
    "resources": ["backend/**/*"]
  }
}
```

### `main.rs` — Backend Sidecar Start
```rust
use tauri::Manager;
use std::process::Command;

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            let resource_path = app.path().resource_dir()
                .expect("failed to resolve resource dir");

            std::thread::spawn(move || {
                Command::new("python")
                    .args(["-u", "backend/main.py"])
                    .current_dir(&resource_path)
                    .spawn()
                    .expect("Failed to start backend");
            });

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running Haku");
}
```

---

## FastAPI Backend

### `main.py`
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from routers import process, search

app = FastAPI(title="Haku Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["tauri://localhost", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(process.router, prefix="/process")
app.include_router(search.router, prefix="/search")

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=23431)
```

### `routers/search.py`
```python
from fastapi import APIRouter, Query
from services.image_search import search_images

router = APIRouter()

@router.get("/images")
async def search(q: str = Query(...), max_results: int = Query(20)):
    results = await search_images(q, max_results)
    return {"results": results}
```

### `routers/process.py`
```python
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from services.background_remover import remove_background
from services.image_processor import resize_with_padding
from services.dds_converter import convert_to_dds
from PIL import Image
import io, base64, os, json

router = APIRouter()

@router.post("/single")
async def process_single(file: UploadFile = File(...), output_dir: str = Form(...)):
    img_bytes = await file.read()
    original = Image.open(io.BytesIO(img_bytes)).convert("RGBA")

    # Original Preview
    buf = io.BytesIO()
    original.save(buf, "PNG")
    original_b64 = base64.b64encode(buf.getvalue()).decode()

    # Pipeline: BG Remove → Resize → DDS
    no_bg = remove_background(img_bytes)
    padded = resize_with_padding(no_bg)

    # Processed Preview
    buf2 = io.BytesIO()
    padded.save(buf2, "PNG")
    processed_b64 = base64.b64encode(buf2.getvalue()).decode()

    # Temp PNG → texconv → DDS
    stem = os.path.splitext(file.filename)[0]
    temp_png = os.path.join(output_dir, f"_temp_{stem}.png")
    padded.save(temp_png, "PNG")
    convert_to_dds(temp_png, output_dir)
    os.remove(temp_png)

    return {
        "original_preview": original_b64,
        "processed_preview": processed_b64,
        "output_path": os.path.join(output_dir, f"{stem}.dds"),
        "success": True
    }

@router.post("/batch")
async def process_batch(body: dict):
    input_dir = body["input_dir"]
    output_dir = body["output_dir"]
    supported = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tga")
    files = [f for f in os.listdir(input_dir) if f.lower().endswith(supported)]

    async def stream():
        for i, fname in enumerate(files):
            yield json.dumps({
                "file": fname, "status": "processing",
                "progress": i + 1, "total": len(files)
            }) + "\n"

            path = os.path.join(input_dir, fname)
            try:
                with open(path, "rb") as f:
                    img_bytes = f.read()
                no_bg = remove_background(img_bytes)
                padded = resize_with_padding(no_bg)

                stem = os.path.splitext(fname)[0]
                temp_png = os.path.join(output_dir, f"_temp_{stem}.png")
                padded.save(temp_png, "PNG")
                convert_to_dds(temp_png, output_dir)
                os.remove(temp_png)

                buf = io.BytesIO()
                padded.save(buf, "PNG")
                preview = base64.b64encode(buf.getvalue()).decode()

                yield json.dumps({
                    "file": fname, "status": "done", "preview": preview
                }) + "\n"
            except Exception as e:
                yield json.dumps({
                    "file": fname, "status": "error", "error": str(e)
                }) + "\n"

        yield json.dumps({"status": "complete", "processed": len(files)}) + "\n"

    return StreamingResponse(stream(), media_type="application/x-ndjson")

@router.post("/from-url")
async def process_from_url(body: dict):
    import httpx
    async with httpx.AsyncClient() as client:
        resp = await client.get(body["image_url"])
        img_bytes = resp.content

    original = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
    buf = io.BytesIO()
    original.save(buf, "PNG")
    original_b64 = base64.b64encode(buf.getvalue()).decode()

    no_bg = remove_background(img_bytes)
    padded = resize_with_padding(no_bg)

    buf2 = io.BytesIO()
    padded.save(buf2, "PNG")
    processed_b64 = base64.b64encode(buf2.getvalue()).decode()

    filename = body.get("filename", "image")
    temp_png = os.path.join(body["output_dir"], f"_temp_{filename}.png")
    padded.save(temp_png, "PNG")
    convert_to_dds(temp_png, body["output_dir"])
    os.remove(temp_png)

    return {
        "original_preview": original_b64,
        "processed_preview": processed_b64,
        "output_path": os.path.join(body["output_dir"], f"{filename}.dds"),
        "success": True
    }
```

### `services/background_remover.py`
```python
from rembg import remove
from PIL import Image
import io

def remove_background(img_bytes: bytes) -> Image.Image:
    """Entfernt den Hintergrund und gibt RGBA Image zurück."""
    result_bytes = remove(img_bytes)
    return Image.open(io.BytesIO(result_bytes)).convert("RGBA")
```

### `services/image_processor.py`
```python
from PIL import Image

def resize_with_padding(img: Image.Image, target: int = 256) -> Image.Image:
    """Proportional skalieren, zentriert auf transparentem Canvas."""
    ratio = min(target / img.width, target / img.height)
    new_w = int(img.width * ratio)
    new_h = int(img.height * ratio)
    resized = img.resize((new_w, new_h), Image.LANCZOS)

    canvas = Image.new("RGBA", (target, target), (0, 0, 0, 0))
    offset_x = (target - new_w) // 2
    offset_y = (target - new_h) // 2
    canvas.paste(resized, (offset_x, offset_y), resized)
    return canvas
```

### `services/dds_converter.py`
```python
import subprocess
import os

TEXCONV_PATH = os.path.join(os.path.dirname(__file__), "..", "tools", "texconv.exe")

def convert_to_dds(input_png: str, output_dir: str):
    """Konvertiert PNG → DDS BC3 (DXT5) mit allen Mipmap-Levels."""
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
```

### `services/image_search.py`
```python
from duckduckgo_search import DDGS

async def search_images(query: str, max_results: int = 20) -> list:
    """Sucht Bilder via DuckDuckGo — kein API Key nötig."""
    with DDGS() as ddgs:
        results = list(ddgs.images(query, max_results=max_results))
    return [
        {
            "title": r.get("title", ""),
            "url": r.get("image", ""),
            "thumbnail": r.get("thumbnail", ""),
            "source": r.get("source", ""),
        }
        for r in results
    ]
```

---

## GitHub Actions — Release Build (`.exe`)

### `.github/workflows/release.yml`
```yaml
name: Build & Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: windows-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Rust
        uses: dtolnay/rust-toolchain@stable

      - name: Install frontend deps
        run: npm ci

      - name: Install Python deps
        run: pip install -r backend/requirements.txt

      - name: Download texconv
        run: |
          curl -L -o texconv.zip https://github.com/microsoft/DirectXTex/releases/latest/download/texconv.zip
          Expand-Archive texconv.zip -DestinationPath backend/tools/
        shell: pwsh

      - name: Build Tauri
        uses: tauri-apps/tauri-action@v0
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tagName: ${{ github.ref_name }}
          releaseName: 'Haku ${{ github.ref_name }}'
          releaseBody: 'Haku Release ${{ github.ref_name }}'
          releaseDraft: false
          prerelease: false
```

---

## Setup & Development

### Voraussetzungen
- Node.js 20+
- Python 3.11+
- Rust (latest stable)
- npm

### Lokales Setup
```bash
# Repo klonen
git clone https://github.com/lfl1337/Haku.git
cd Haku

# Frontend Deps
npm install

# Backend Deps
cd backend
pip install -r requirements.txt
cd ..

# texconv.exe herunterladen → backend/tools/ entpacken
# Download: https://github.com/microsoft/DirectXTex/releases

# Dev starten
npm run tauri dev
```

### Package Scripts (`package.json`)
```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "tauri": "tauri",
    "tauri:dev": "tauri dev",
    "tauri:build": "tauri build"
  }
}
```

---

## Notizen

- **texconv.exe** muss im Repo unter `backend/tools/` liegen oder wird im CI automatisch heruntergeladen. Lizenz: MIT (Microsoft DirectXTex).
- **rembg** lädt beim ersten Start das U2Net-Modell herunter (~170MB). Danach gecached in `~/.u2net/`.
- **Port 23431** für den lokalen FastAPI-Server — nicht-standard, vermeidet Konflikte.
- **Batch-Modus** nutzt NDJSON Streaming für Live-Fortschritt im UI.
- **DuckDuckGo Search** braucht keinen API-Key. Bei extremer Nutzung können Requests temporär geblockt werden — für normalen Gebrauch kein Problem.
- **Unterstützte Eingabeformate:** PNG, JPG, JPEG, WEBP, BMP, TGA.
