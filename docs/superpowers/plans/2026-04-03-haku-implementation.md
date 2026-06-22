# Haku (白) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a desktop tool that removes image backgrounds, resizes to 256×256 with transparent padding, and exports DDS BC3 textures — with single-image, batch, and online-search input modes.

**Architecture:** Tauri v2 desktop shell launches a FastAPI Python backend as sidecar. React (Vite) frontend communicates with the backend via HTTP on `127.0.0.1:23431`. Processing pipeline: rembg → Pillow resize → texconv DDS conversion.

**Tech Stack:** Tauri v2 (Rust), FastAPI (Python 3.11+), React 18 (Vite 5), rembg, Pillow, texconv.exe, duckduckgo_search

---

## File Structure

```
<repo-root>/
├── src-tauri/
│   ├── src/main.rs                   # Tauri entry, sidecar launch
│   ├── icons/icon.png                # App icon (placeholder)
│   ├── Cargo.toml                    # Rust dependencies
│   └── tauri.conf.json               # Window, plugins, bundle config
│
├── backend/
│   ├── main.py                       # FastAPI app, CORS, uvicorn
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── process.py                # /process/single, /process/batch, /process/from-url
│   │   └── search.py                 # /search/images
│   ├── services/
│   │   ├── __init__.py
│   │   ├── background_remover.py     # rembg wrapper
│   │   ├── image_processor.py        # Resize + padding
│   │   ├── dds_converter.py          # texconv wrapper
│   │   └── image_search.py           # DuckDuckGo search
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py                # Pydantic models
│   ├── requirements.txt
│   └── tools/                        # texconv.exe goes here (not committed)
│       └── .gitkeep
│
├── src/
│   ├── main.jsx                      # React entry
│   ├── App.jsx                       # Root, mode routing
│   ├── index.css                     # CSS variables, dark theme, globals
│   ├── components/
│   │   ├── Layout.jsx                # App shell — header + content
│   │   ├── ModeSwitch.jsx            # Toggle: Single / Batch / Search
│   │   ├── SingleMode.jsx            # Single image select + process
│   │   ├── BatchMode.jsx             # Folder select + batch process
│   │   ├── SearchMode.jsx            # Online search, grid, selection
│   │   ├── Preview.jsx               # Before/after side-by-side
│   │   ├── FolderPicker.jsx          # Input/output folder selection
│   │   ├── ProgressBar.jsx           # Batch progress
│   │   └── ImageGrid.jsx             # Thumbnail grid (search + batch)
│   └── hooks/
│       ├── useProcess.js             # API calls for processing
│       └── useSearch.js              # API call for image search
│
├── package.json
├── vite.config.js
├── .gitignore
├── .github/
│   └── workflows/
│       └── release.yml               # GitHub Actions → .exe build
└── README.md
```

---

## Phase 1: Project Scaffolding

### Task 1: Initialize Git and base files

**Files:**
- Create: `.gitignore`
- Create: `README.md`

- [ ] **Step 1: Initialize git repo**

Run:
```bash
cd <repo-root>
git init
```

- [ ] **Step 2: Create .gitignore**

Create `.gitignore`:
```gitignore
# Dependencies
node_modules/
__pycache__/
*.pyc
.venv/
venv/

# Build output
dist/
target/

# Tauri
src-tauri/target/

# Backend tools (downloaded separately)
backend/tools/texconv.exe

# IDE
.vscode/
.idea/

# OS
Thumbs.db
.DS_Store

# Temp files
_temp_*

# Environment
.env
```

- [ ] **Step 3: Create README.md**

Create `README.md`:
```markdown
# Haku 白

Desktop tool for game asset preparation: background removal, 256×256 resize with transparent padding, DDS BC3 export with mipmaps.

## Stack

- **Desktop:** Tauri v2 (Rust)
- **Backend:** FastAPI (Python 3.11+)
- **Frontend:** React 18 + Vite 5

## Setup

```bash
# Frontend dependencies
npm install

# Backend dependencies
cd backend
pip install -r requirements.txt
cd ..

# Download texconv.exe → backend/tools/
# https://github.com/microsoft/DirectXTex/releases

# Start development
npm run tauri dev
```
```

- [ ] **Step 4: Commit**

```bash
git add .gitignore README.md Prompts/
git commit -m "chore: init repo with gitignore, readme, and spec"
```

---

### Task 2: Scaffold Vite + React frontend

**Files:**
- Create: `package.json`
- Create: `vite.config.js`
- Create: `src/main.jsx`
- Create: `src/App.jsx`
- Create: `src/index.css`
- Create: `index.html`

- [ ] **Step 1: Create package.json**

Create `package.json`:
```json
{
  "name": "haku",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "tauri": "tauri",
    "tauri:dev": "tauri dev",
    "tauri:build": "tauri build"
  },
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

- [ ] **Step 2: Create vite.config.js**

Create `vite.config.js`:
```js
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  clearScreen: false,
  server: {
    port: 5173,
    strictPort: true,
  },
  envPrefix: ["VITE_", "TAURI_"],
  build: {
    target: ["es2021", "chrome100", "safari13"],
    minify: !process.env.TAURI_DEBUG ? "esbuild" : false,
    sourcemap: !!process.env.TAURI_DEBUG,
  },
});
```

- [ ] **Step 3: Create index.html**

Create `index.html`:
```html
<!DOCTYPE html>
<html lang="de">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Haku 白</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

- [ ] **Step 4: Create src/index.css**

Create `src/index.css`:
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

*,
*::before,
*::after {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #root {
  height: 100%;
  width: 100%;
  overflow: hidden;
}

body {
  font-family: var(--font-main);
  background: var(--bg-primary);
  color: var(--text-primary);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

button {
  font-family: var(--font-main);
  cursor: pointer;
  border: none;
  outline: none;
}

input {
  font-family: var(--font-main);
  outline: none;
}

::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: var(--bg-primary);
}

::-webkit-scrollbar-thumb {
  background: var(--border);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--border-active);
}
```

- [ ] **Step 5: Create src/main.jsx**

Create `src/main.jsx`:
```jsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

- [ ] **Step 6: Create src/App.jsx (placeholder)**

Create `src/App.jsx`:
```jsx
import { useState } from "react";
import Layout from "./components/Layout";
import SingleMode from "./components/SingleMode";
import BatchMode from "./components/BatchMode";
import SearchMode from "./components/SearchMode";

export default function App() {
  const [mode, setMode] = useState("single");

  return (
    <Layout mode={mode} onModeChange={setMode}>
      {mode === "single" && <SingleMode />}
      {mode === "batch" && <BatchMode />}
      {mode === "search" && <SearchMode />}
    </Layout>
  );
}
```

- [ ] **Step 7: Install dependencies**

Run:
```bash
npm install
```
Expected: `node_modules/` created, no errors.

- [ ] **Step 8: Verify Vite starts**

Run:
```bash
npm run dev
```
Expected: Vite dev server starts on `http://localhost:5173` (will show errors since components don't exist yet — that's fine).

Kill the dev server after confirming it starts.

- [ ] **Step 9: Commit**

```bash
git add package.json vite.config.js index.html src/main.jsx src/App.jsx src/index.css
git commit -m "chore: scaffold Vite + React frontend with dark theme CSS"
```

---

### Task 3: Scaffold Tauri v2 shell

**Files:**
- Create: `src-tauri/Cargo.toml`
- Create: `src-tauri/tauri.conf.json`
- Create: `src-tauri/src/main.rs`
- Create: `src-tauri/icons/icon.png`

- [ ] **Step 1: Initialize Tauri via CLI**

Run:
```bash
npx tauri init
```

Follow prompts:
- App name: `Haku`
- Window title: `Haku 白`
- Frontend dev URL: `http://localhost:5173`
- Frontend dist: `../dist`
- Frontend dev command: `npm run dev`
- Frontend build command: `npm run build`

- [ ] **Step 2: Install Tauri plugins**

Run:
```bash
cd src-tauri
cargo add tauri-plugin-dialog tauri-plugin-fs tauri-plugin-shell
cd ..
```

- [ ] **Step 3: Update tauri.conf.json**

Replace `src-tauri/tauri.conf.json` with:
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

- [ ] **Step 4: Update main.rs with sidecar launch**

Replace `src-tauri/src/main.rs` with:
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

- [ ] **Step 5: Create a placeholder icon**

Create a simple 32×32 PNG placeholder at `src-tauri/icons/icon.png`. (Can be generated with any tool or use a placeholder — Tauri requires at least one icon.)

- [ ] **Step 6: Verify Tauri compiles**

Run:
```bash
npm run tauri dev
```
Expected: Rust compiles, window opens (frontend may show errors since components are incomplete). Backend won't start yet — that's expected.

Kill after confirming it compiles.

- [ ] **Step 7: Commit**

```bash
git add src-tauri/
git commit -m "chore: scaffold Tauri v2 shell with dialog, fs, shell plugins"
```

---

## Phase 2: Backend — Services

### Task 4: Create backend scaffolding and services

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/tools/.gitkeep`
- Create: `backend/models/__init__.py`
- Create: `backend/models/schemas.py`
- Create: `backend/services/__init__.py`
- Create: `backend/services/background_remover.py`
- Create: `backend/services/image_processor.py`
- Create: `backend/services/dds_converter.py`
- Create: `backend/services/image_search.py`
- Create: `backend/routers/__init__.py`

- [ ] **Step 1: Create directory structure**

Run:
```bash
mkdir -p backend/routers backend/services backend/models backend/tools
```

- [ ] **Step 2: Create requirements.txt**

Create `backend/requirements.txt`:
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

- [ ] **Step 3: Create __init__.py files and .gitkeep**

Create empty files:
- `backend/routers/__init__.py` (empty)
- `backend/services/__init__.py` (empty)
- `backend/models/__init__.py` (empty)
- `backend/tools/.gitkeep` (empty)

- [ ] **Step 4: Create models/schemas.py**

Create `backend/models/schemas.py`:
```python
from pydantic import BaseModel


class BatchRequest(BaseModel):
    input_dir: str
    output_dir: str


class FromUrlRequest(BaseModel):
    image_url: str
    output_dir: str
    filename: str = "image"


class ProcessResult(BaseModel):
    original_preview: str
    processed_preview: str
    output_path: str
    success: bool


class SearchResult(BaseModel):
    title: str
    url: str
    thumbnail: str
    source: str


class SearchResponse(BaseModel):
    results: list[SearchResult]
```

- [ ] **Step 5: Create services/image_processor.py**

Create `backend/services/image_processor.py`:
```python
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
```

- [ ] **Step 6: Create services/background_remover.py**

Create `backend/services/background_remover.py`:
```python
from rembg import remove
from PIL import Image
import io


def remove_background(img_bytes: bytes) -> Image.Image:
    """Remove background and return RGBA Image."""
    result_bytes = remove(img_bytes)
    return Image.open(io.BytesIO(result_bytes)).convert("RGBA")
```

- [ ] **Step 7: Create services/dds_converter.py**

Create `backend/services/dds_converter.py`:
```python
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
```

- [ ] **Step 8: Create services/image_search.py**

Create `backend/services/image_search.py`:
```python
from duckduckgo_search import DDGS


async def search_images(query: str, max_results: int = 20) -> list:
    """Search images via DuckDuckGo — no API key needed."""
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

- [ ] **Step 9: Install Python dependencies**

Run:
```bash
cd backend
pip install -r requirements.txt
cd ..
```
Expected: All packages install successfully.

- [ ] **Step 10: Commit**

```bash
git add backend/
git commit -m "feat(backend): add services — bg removal, resize, DDS converter, image search"
```

---

### Task 5: Create backend routers and main.py

**Files:**
- Create: `backend/main.py`
- Create: `backend/routers/search.py`
- Create: `backend/routers/process.py`

- [ ] **Step 1: Create routers/search.py**

Create `backend/routers/search.py`:
```python
from fastapi import APIRouter, Query
from services.image_search import search_images

router = APIRouter()


@router.get("/images")
async def search(q: str = Query(...), max_results: int = Query(20)):
    results = await search_images(q, max_results)
    return {"results": results}
```

- [ ] **Step 2: Create routers/process.py**

Create `backend/routers/process.py`:
```python
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from services.background_remover import remove_background
from services.image_processor import resize_with_padding
from services.dds_converter import convert_to_dds
from models.schemas import BatchRequest, FromUrlRequest
from PIL import Image
import io
import base64
import os
import json

router = APIRouter()


@router.post("/single")
async def process_single(file: UploadFile = File(...), output_dir: str = Form(...)):
    img_bytes = await file.read()
    original = Image.open(io.BytesIO(img_bytes)).convert("RGBA")

    # Original preview
    buf = io.BytesIO()
    original.save(buf, "PNG")
    original_b64 = base64.b64encode(buf.getvalue()).decode()

    # Pipeline: BG Remove → Resize → DDS
    no_bg = remove_background(img_bytes)
    padded = resize_with_padding(no_bg)

    # Processed preview
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
        "success": True,
    }


@router.post("/batch")
async def process_batch(body: BatchRequest):
    input_dir = body.input_dir
    output_dir = body.output_dir
    supported = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tga")
    files = [f for f in os.listdir(input_dir) if f.lower().endswith(supported)]

    async def stream():
        for i, fname in enumerate(files):
            yield json.dumps({
                "file": fname,
                "status": "processing",
                "progress": i + 1,
                "total": len(files),
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
                    "file": fname,
                    "status": "done",
                    "preview": preview,
                }) + "\n"
            except Exception as e:
                yield json.dumps({
                    "file": fname,
                    "status": "error",
                    "error": str(e),
                }) + "\n"

        yield json.dumps({
            "status": "complete",
            "processed": len(files),
        }) + "\n"

    return StreamingResponse(stream(), media_type="application/x-ndjson")


@router.post("/from-url")
async def process_from_url(body: FromUrlRequest):
    import httpx

    async with httpx.AsyncClient() as client:
        resp = await client.get(body.image_url)
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

    temp_png = os.path.join(body.output_dir, f"_temp_{body.filename}.png")
    padded.save(temp_png, "PNG")
    convert_to_dds(temp_png, body.output_dir)
    os.remove(temp_png)

    return {
        "original_preview": original_b64,
        "processed_preview": processed_b64,
        "output_path": os.path.join(body.output_dir, f"{body.filename}.dds"),
        "success": True,
    }
```

- [ ] **Step 3: Create main.py**

Create `backend/main.py`:
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

- [ ] **Step 4: Test backend starts**

Run:
```bash
cd backend
python main.py
```
Expected: Uvicorn starts on `http://127.0.0.1:23431`. Visit `http://127.0.0.1:23431/health` — should return `{"status":"ok"}`.

Kill the server.

- [ ] **Step 5: Commit**

```bash
git add backend/main.py backend/routers/
git commit -m "feat(backend): add FastAPI routers — process single/batch/url + image search"
```

---

## Phase 3: Frontend — Components

### Task 6: Create Layout and ModeSwitch components

**Files:**
- Create: `src/components/Layout.jsx`
- Create: `src/components/ModeSwitch.jsx`

- [ ] **Step 1: Create src/components/ModeSwitch.jsx**

Create `src/components/ModeSwitch.jsx`:
```jsx
const modes = [
  { key: "single", label: "Einzel" },
  { key: "batch", label: "Batch" },
  { key: "search", label: "Suche" },
];

export default function ModeSwitch({ mode, onModeChange }) {
  return (
    <div className="mode-switch">
      {modes.map((m) => (
        <button
          key={m.key}
          className={`mode-switch__btn ${mode === m.key ? "mode-switch__btn--active" : ""}`}
          onClick={() => onModeChange(m.key)}
        >
          {m.label}
        </button>
      ))}
    </div>
  );
}
```

- [ ] **Step 2: Create src/components/Layout.jsx**

Create `src/components/Layout.jsx`:
```jsx
import ModeSwitch from "./ModeSwitch";

export default function Layout({ mode, onModeChange, children }) {
  return (
    <div className="layout">
      <header className="layout__header">
        <h1 className="layout__title">Haku <span className="layout__kanji">白</span></h1>
        <ModeSwitch mode={mode} onModeChange={onModeChange} />
      </header>
      <main className="layout__content">{children}</main>
    </div>
  );
}
```

- [ ] **Step 3: Add Layout and ModeSwitch styles to index.css**

Append to `src/index.css`:
```css
/* Layout */
.layout {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.layout__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border);
  -webkit-app-region: drag;
}

.layout__title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
  -webkit-app-region: drag;
}

.layout__kanji {
  color: var(--accent);
  font-weight: 400;
}

.layout__content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

/* ModeSwitch */
.mode-switch {
  display: flex;
  gap: 2px;
  background: var(--bg-primary);
  border-radius: var(--radius);
  padding: 2px;
  -webkit-app-region: no-drag;
}

.mode-switch__btn {
  padding: 6px 16px;
  border-radius: calc(var(--radius) - 2px);
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--text-secondary);
  background: transparent;
  transition: all 0.15s ease;
}

.mode-switch__btn:hover {
  color: var(--text-primary);
  background: var(--bg-hover);
}

.mode-switch__btn--active {
  color: var(--text-primary);
  background: var(--bg-elevated);
}
```

- [ ] **Step 4: Commit**

```bash
git add src/components/Layout.jsx src/components/ModeSwitch.jsx src/index.css
git commit -m "feat(ui): add Layout shell and ModeSwitch component"
```

---

### Task 7: Create FolderPicker and Preview components

**Files:**
- Create: `src/components/FolderPicker.jsx`
- Create: `src/components/Preview.jsx`

- [ ] **Step 1: Create src/components/FolderPicker.jsx**

Create `src/components/FolderPicker.jsx`:
```jsx
import { open } from "@tauri-apps/plugin-dialog";

export default function FolderPicker({ label, value, onChange }) {
  const handlePick = async () => {
    const selected = await open({ directory: true, multiple: false });
    if (selected) {
      onChange(selected);
    }
  };

  return (
    <div className="folder-picker">
      <span className="folder-picker__label">{label}</span>
      <button className="folder-picker__btn" onClick={handlePick}>
        <span className="folder-picker__icon">📂</span>
        <span className="folder-picker__path">
          {value || "Ordner wählen..."}
        </span>
      </button>
    </div>
  );
}
```

- [ ] **Step 2: Create src/components/Preview.jsx**

Create `src/components/Preview.jsx`:
```jsx
export default function Preview({ original, processed }) {
  if (!original && !processed) {
    return (
      <div className="preview preview--empty">
        <p className="preview__placeholder">Kein Bild ausgewählt</p>
      </div>
    );
  }

  return (
    <div className="preview">
      <div className="preview__panel">
        <span className="preview__label">Vorher</span>
        {original ? (
          <img
            className="preview__img"
            src={`data:image/png;base64,${original}`}
            alt="Original"
          />
        ) : (
          <div className="preview__placeholder-box" />
        )}
      </div>
      <div className="preview__arrow">→</div>
      <div className="preview__panel">
        <span className="preview__label">Nachher</span>
        {processed ? (
          <img
            className="preview__img"
            src={`data:image/png;base64,${processed}`}
            alt="Processed"
          />
        ) : (
          <div className="preview__placeholder-box" />
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Add FolderPicker and Preview styles to index.css**

Append to `src/index.css`:
```css
/* FolderPicker */
.folder-picker {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.folder-picker__label {
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.folder-picker__btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text-primary);
  font-size: 0.8125rem;
  transition: border-color 0.15s ease;
}

.folder-picker__btn:hover {
  border-color: var(--border-active);
}

.folder-picker__path {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: var(--text-secondary);
}

/* Preview */
.preview {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
  padding: 32px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  min-height: 280px;
}

.preview--empty {
  min-height: 200px;
}

.preview__placeholder {
  color: var(--text-muted);
  font-size: 0.875rem;
}

.preview__panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.preview__label {
  font-size: 0.6875rem;
  font-weight: 500;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.preview__img {
  max-width: 256px;
  max-height: 256px;
  border-radius: var(--radius);
  background: repeating-conic-gradient(var(--bg-elevated) 0% 25%, var(--bg-primary) 0% 50%) 50% / 16px 16px;
}

.preview__placeholder-box {
  width: 256px;
  height: 256px;
  border-radius: var(--radius);
  background: var(--bg-elevated);
  border: 1px dashed var(--border);
}

.preview__arrow {
  font-size: 1.5rem;
  color: var(--text-muted);
}
```

- [ ] **Step 4: Commit**

```bash
git add src/components/FolderPicker.jsx src/components/Preview.jsx src/index.css
git commit -m "feat(ui): add FolderPicker and Preview components"
```

---

### Task 8: Create ProgressBar and ImageGrid components

**Files:**
- Create: `src/components/ProgressBar.jsx`
- Create: `src/components/ImageGrid.jsx`

- [ ] **Step 1: Create src/components/ProgressBar.jsx**

Create `src/components/ProgressBar.jsx`:
```jsx
export default function ProgressBar({ current, total, label }) {
  const percent = total > 0 ? Math.round((current / total) * 100) : 0;

  return (
    <div className="progress-bar">
      <div className="progress-bar__header">
        <span className="progress-bar__label">{label || "Fortschritt"}</span>
        <span className="progress-bar__count">
          {current}/{total} ({percent}%)
        </span>
      </div>
      <div className="progress-bar__track">
        <div
          className="progress-bar__fill"
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create src/components/ImageGrid.jsx**

Create `src/components/ImageGrid.jsx`:
```jsx
export default function ImageGrid({ images, selected, onToggle, renderImage }) {
  return (
    <div className="image-grid">
      {images.map((img, i) => {
        const isSelected = selected?.includes(i);
        return (
          <button
            key={i}
            className={`image-grid__item ${isSelected ? "image-grid__item--selected" : ""}`}
            onClick={() => onToggle?.(i)}
          >
            {renderImage ? (
              renderImage(img, i)
            ) : (
              <img
                className="image-grid__img"
                src={img.thumbnail || img.src}
                alt={img.title || `Image ${i + 1}`}
                loading="lazy"
              />
            )}
            {isSelected && <div className="image-grid__check">✓</div>}
          </button>
        );
      })}
    </div>
  );
}
```

- [ ] **Step 3: Add ProgressBar and ImageGrid styles to index.css**

Append to `src/index.css`:
```css
/* ProgressBar */
.progress-bar {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.progress-bar__header {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
}

.progress-bar__label {
  color: var(--text-secondary);
}

.progress-bar__count {
  font-family: var(--font-mono);
  color: var(--text-muted);
}

.progress-bar__track {
  height: 4px;
  background: var(--bg-elevated);
  border-radius: 2px;
  overflow: hidden;
}

.progress-bar__fill {
  height: 100%;
  background: var(--accent);
  border-radius: 2px;
  transition: width 0.3s ease-out;
}

/* ImageGrid */
.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 8px;
}

.image-grid__item {
  position: relative;
  aspect-ratio: 1;
  overflow: hidden;
  border-radius: var(--radius);
  border: 2px solid transparent;
  background: var(--bg-elevated);
  padding: 0;
  transition: border-color 0.15s ease;
}

.image-grid__item:hover {
  border-color: var(--border-active);
}

.image-grid__item--selected {
  border-color: var(--accent);
}

.image-grid__img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-grid__check {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent);
  color: white;
  border-radius: 50%;
  font-size: 0.75rem;
  font-weight: 700;
}
```

- [ ] **Step 4: Commit**

```bash
git add src/components/ProgressBar.jsx src/components/ImageGrid.jsx src/index.css
git commit -m "feat(ui): add ProgressBar and ImageGrid components"
```

---

### Task 9: Create API hooks (useProcess, useSearch)

**Files:**
- Create: `src/hooks/useProcess.js`
- Create: `src/hooks/useSearch.js`

- [ ] **Step 1: Create src/hooks/useProcess.js**

Create `src/hooks/useProcess.js`:
```js
import { useState } from "react";

const API = "http://127.0.0.1:23431";

export function useProcess() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const processSingle = async (file, outputDir) => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("output_dir", outputDir);

      const res = await fetch(`${API}/process/single`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setResult(data);
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const processFromUrl = async (imageUrl, outputDir, filename) => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`${API}/process/from-url`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          image_url: imageUrl,
          output_dir: outputDir,
          filename,
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setResult(data);
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const processBatch = async (inputDir, outputDir, onProgress) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API}/process/batch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ input_dir: inputDir, output_dir: outputDir }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop();

        for (const line of lines) {
          if (line.trim()) {
            const event = JSON.parse(line);
            onProgress?.(event);
            if (event.status === "complete") {
              setResult(event);
            }
          }
        }
      }
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { processSingle, processFromUrl, processBatch, loading, result, error };
}
```

- [ ] **Step 2: Create src/hooks/useSearch.js**

Create `src/hooks/useSearch.js`:
```js
import { useState } from "react";

const API = "http://127.0.0.1:23431";

export function useSearch() {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [error, setError] = useState(null);

  const searchImages = async (query, maxResults = 20) => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ q: query, max_results: maxResults });
      const res = await fetch(`${API}/search/images?${params}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setResults(data.results);
      return data.results;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { searchImages, results, loading, error };
}
```

- [ ] **Step 3: Commit**

```bash
git add src/hooks/
git commit -m "feat(ui): add useProcess and useSearch API hooks"
```

---

### Task 10: Create SingleMode component

**Files:**
- Create: `src/components/SingleMode.jsx`

- [ ] **Step 1: Create src/components/SingleMode.jsx**

Create `src/components/SingleMode.jsx`:
```jsx
import { useState, useRef } from "react";
import FolderPicker from "./FolderPicker";
import Preview from "./Preview";
import { useProcess } from "../hooks/useProcess";

export default function SingleMode() {
  const [outputDir, setOutputDir] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileName, setFileName] = useState("");
  const fileInputRef = useRef(null);
  const { processSingle, loading, result, error } = useProcess();

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      setFileName(file.name);
    }
  };

  const handleProcess = async () => {
    if (!selectedFile || !outputDir) return;
    await processSingle(selectedFile, outputDir);
  };

  return (
    <div className="single-mode">
      <div className="single-mode__controls">
        <div className="single-mode__file-row">
          <div className="single-mode__file-picker">
            <span className="folder-picker__label">Bild</span>
            <button
              className="folder-picker__btn"
              onClick={() => fileInputRef.current?.click()}
            >
              <span className="folder-picker__icon">🖼️</span>
              <span className="folder-picker__path">
                {fileName || "Bild wählen..."}
              </span>
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/png,image/jpeg,image/webp,image/bmp"
              onChange={handleFileSelect}
              style={{ display: "none" }}
            />
          </div>
          <FolderPicker
            label="Ausgabe"
            value={outputDir}
            onChange={setOutputDir}
          />
        </div>

        <button
          className="btn btn--primary"
          onClick={handleProcess}
          disabled={!selectedFile || !outputDir || loading}
        >
          {loading ? "Verarbeite..." : "▶ Verarbeiten"}
        </button>
      </div>

      {error && <p className="error-msg">{error}</p>}

      <Preview
        original={result?.original_preview}
        processed={result?.processed_preview}
      />

      {result?.success && (
        <p className="success-msg">
          Gespeichert: <code>{result.output_path}</code>
        </p>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Add SingleMode and shared button/message styles to index.css**

Append to `src/index.css`:
```css
/* Shared button styles */
.btn {
  padding: 10px 24px;
  border-radius: var(--radius);
  font-size: 0.875rem;
  font-weight: 600;
  transition: all 0.15s ease;
}

.btn--primary {
  background: var(--accent);
  color: white;
}

.btn--primary:hover:not(:disabled) {
  background: var(--accent-hover);
}

.btn--primary:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.error-msg {
  color: var(--error);
  font-size: 0.8125rem;
  padding: 8px 12px;
  background: rgba(248, 113, 113, 0.08);
  border-radius: var(--radius);
}

.success-msg {
  color: var(--success);
  font-size: 0.8125rem;
  padding: 8px 12px;
  background: rgba(74, 222, 128, 0.08);
  border-radius: var(--radius);
}

.success-msg code {
  font-family: var(--font-mono);
  font-size: 0.75rem;
}

/* SingleMode */
.single-mode {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.single-mode__controls {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.single-mode__file-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
```

- [ ] **Step 3: Commit**

```bash
git add src/components/SingleMode.jsx src/index.css
git commit -m "feat(ui): add SingleMode component with file picker and processing"
```

---

### Task 11: Create BatchMode component

**Files:**
- Create: `src/components/BatchMode.jsx`

- [ ] **Step 1: Create src/components/BatchMode.jsx**

Create `src/components/BatchMode.jsx`:
```jsx
import { useState } from "react";
import FolderPicker from "./FolderPicker";
import ProgressBar from "./ProgressBar";
import ImageGrid from "./ImageGrid";
import { useProcess } from "../hooks/useProcess";

export default function BatchMode() {
  const [inputDir, setInputDir] = useState("");
  const [outputDir, setOutputDir] = useState("");
  const [progress, setProgress] = useState({ current: 0, total: 0 });
  const [previews, setPreviews] = useState([]);
  const [status, setStatus] = useState("idle");
  const { processBatch, loading, error } = useProcess();

  const handleBatch = async () => {
    if (!inputDir || !outputDir) return;
    setPreviews([]);
    setProgress({ current: 0, total: 0 });
    setStatus("processing");

    await processBatch(inputDir, outputDir, (event) => {
      if (event.status === "processing") {
        setProgress({ current: event.progress, total: event.total });
      } else if (event.status === "done") {
        setPreviews((prev) => [
          ...prev,
          { src: `data:image/png;base64,${event.preview}`, title: event.file },
        ]);
      } else if (event.status === "complete") {
        setStatus("complete");
      } else if (event.status === "error") {
        setPreviews((prev) => [
          ...prev,
          { src: null, title: `❌ ${event.file}` },
        ]);
      }
    });
  };

  return (
    <div className="batch-mode">
      <div className="batch-mode__controls">
        <div className="batch-mode__folders">
          <FolderPicker label="Eingabe" value={inputDir} onChange={setInputDir} />
          <FolderPicker label="Ausgabe" value={outputDir} onChange={setOutputDir} />
        </div>

        <button
          className="btn btn--primary"
          onClick={handleBatch}
          disabled={!inputDir || !outputDir || loading}
        >
          {loading ? "Verarbeite..." : "▶ Batch verarbeiten"}
        </button>
      </div>

      {error && <p className="error-msg">{error}</p>}

      {(loading || status === "complete") && (
        <ProgressBar
          current={progress.current}
          total={progress.total}
          label={status === "complete" ? "Fertig!" : "Verarbeite..."}
        />
      )}

      {previews.length > 0 && (
        <ImageGrid images={previews} />
      )}

      {status === "complete" && (
        <p className="success-msg">
          Alle Bilder verarbeitet — Ausgabe in <code>{outputDir}</code>
        </p>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Add BatchMode styles to index.css**

Append to `src/index.css`:
```css
/* BatchMode */
.batch-mode {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.batch-mode__controls {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.batch-mode__folders {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
```

- [ ] **Step 3: Commit**

```bash
git add src/components/BatchMode.jsx src/index.css
git commit -m "feat(ui): add BatchMode component with streaming progress"
```

---

### Task 12: Create SearchMode component

**Files:**
- Create: `src/components/SearchMode.jsx`

- [ ] **Step 1: Create src/components/SearchMode.jsx**

Create `src/components/SearchMode.jsx`:
```jsx
import { useState } from "react";
import FolderPicker from "./FolderPicker";
import ImageGrid from "./ImageGrid";
import Preview from "./Preview";
import { useSearch } from "../hooks/useSearch";
import { useProcess } from "../hooks/useProcess";

export default function SearchMode() {
  const [query, setQuery] = useState("");
  const [outputDir, setOutputDir] = useState("");
  const [selected, setSelected] = useState([]);
  const { searchImages, results, loading: searching, error: searchError } = useSearch();
  const { processFromUrl, loading: processing, result, error: processError } = useProcess();

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    setSelected([]);
    await searchImages(query.trim());
  };

  const toggleSelect = (index) => {
    setSelected((prev) =>
      prev.includes(index)
        ? prev.filter((i) => i !== index)
        : [...prev, index]
    );
  };

  const handleProcessSelected = async () => {
    if (selected.length === 0 || !outputDir) return;
    for (const idx of selected) {
      const img = results[idx];
      const filename = img.title?.replace(/[^a-zA-Z0-9_-]/g, "_").slice(0, 50) || `image_${idx}`;
      await processFromUrl(img.url, outputDir, filename);
    }
  };

  return (
    <div className="search-mode">
      <form className="search-mode__bar" onSubmit={handleSearch}>
        <input
          className="search-mode__input"
          type="text"
          placeholder="Suchbegriff eingeben..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button
          className="btn btn--primary"
          type="submit"
          disabled={searching || !query.trim()}
        >
          {searching ? "Suche..." : "Suchen"}
        </button>
      </form>

      {searchError && <p className="error-msg">{searchError}</p>}
      {processError && <p className="error-msg">{processError}</p>}

      {results.length > 0 && (
        <>
          <ImageGrid
            images={results}
            selected={selected}
            onToggle={toggleSelect}
          />

          <div className="search-mode__actions">
            <FolderPicker label="Ausgabe" value={outputDir} onChange={setOutputDir} />
            <div className="search-mode__action-row">
              <span className="search-mode__count">
                {selected.length} ausgewählt
              </span>
              <button
                className="btn btn--primary"
                onClick={handleProcessSelected}
                disabled={selected.length === 0 || !outputDir || processing}
              >
                {processing ? "Verarbeite..." : "▶ Auswahl verarbeiten"}
              </button>
            </div>
          </div>
        </>
      )}

      {result && (
        <Preview
          original={result.original_preview}
          processed={result.processed_preview}
        />
      )}

      {result?.success && (
        <p className="success-msg">
          Gespeichert: <code>{result.output_path}</code>
        </p>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Add SearchMode styles to index.css**

Append to `src/index.css`:
```css
/* SearchMode */
.search-mode {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.search-mode__bar {
  display: flex;
  gap: 8px;
}

.search-mode__input {
  flex: 1;
  padding: 10px 14px;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text-primary);
  font-size: 0.875rem;
  transition: border-color 0.15s ease;
}

.search-mode__input:focus {
  border-color: var(--accent);
}

.search-mode__input::placeholder {
  color: var(--text-muted);
}

.search-mode__actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.search-mode__action-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.search-mode__count {
  font-size: 0.8125rem;
  color: var(--text-secondary);
}
```

- [ ] **Step 3: Commit**

```bash
git add src/components/SearchMode.jsx src/index.css
git commit -m "feat(ui): add SearchMode component with DuckDuckGo search and selection"
```

---

## Phase 4: Integration & CI/CD

### Task 13: Verify full Tauri + Backend integration

**Files:**
- No new files — integration test of existing code

- [ ] **Step 1: Download texconv.exe**

Download from https://github.com/microsoft/DirectXTex/releases and extract `texconv.exe` to `backend/tools/texconv.exe`.

Run:
```bash
ls backend/tools/texconv.exe
```
Expected: File exists.

- [ ] **Step 2: Start backend manually and test health**

Run:
```bash
cd backend
python main.py &
```

Then test:
```bash
curl http://127.0.0.1:23431/health
```
Expected: `{"status":"ok"}`

- [ ] **Step 3: Test search endpoint**

Run:
```bash
curl "http://127.0.0.1:23431/search/images?q=cat&max_results=3"
```
Expected: JSON with `results` array containing image objects.

- [ ] **Step 4: Start full Tauri dev**

Kill the standalone backend, then:
```bash
npm run tauri dev
```
Expected: Window opens with dark UI, mode switch visible, backend starts automatically.

- [ ] **Step 5: Manual smoke test**

In the running app:
1. Switch between Einzel/Batch/Suche modes — all render
2. In Einzel mode: select a test image and output folder, click Verarbeiten — preview shows, DDS file appears in output folder
3. In Suche mode: search "cat", thumbnails appear, select one, process — DDS output created

- [ ] **Step 6: Commit any fixes from integration testing**

```bash
git add -A
git commit -m "fix: integration fixes from smoke testing"
```

(Only if changes were needed.)

---

### Task 14: Add GitHub Actions release workflow

**Files:**
- Create: `.github/workflows/release.yml`

- [ ] **Step 1: Create .github/workflows directory**

Run:
```bash
mkdir -p .github/workflows
```

- [ ] **Step 2: Create release.yml**

Create `.github/workflows/release.yml`:
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

- [ ] **Step 3: Commit**

```bash
git add .github/
git commit -m "ci: add GitHub Actions release workflow for Windows .exe build"
```

---

## Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| 1 — Scaffolding | Tasks 1–3 | Git init, Vite+React, Tauri v2 shell |
| 2 — Backend | Tasks 4–5 | Python services + FastAPI routers |
| 3 — Frontend | Tasks 6–12 | All React components and hooks |
| 4 — Integration | Tasks 13–14 | Smoke test + CI/CD |

**Total tasks:** 14
**Estimated steps:** ~65
