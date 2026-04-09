# Haku — Fix: Backend-Bundling & Production Build

> **Bezieht sich auf:** `Haku.md` (Hauptspezifikation)  
> **Problem:** Im gebauten `.exe`-Release kommt `failed to fetch` — Backend startet nicht oder wird nicht gefunden  
> **Ursachen:** Python nicht auf Zielrechner, falscher Pfad zu `main.py`, Race Condition beim Startup

---

## Was sich ändert

| Bereich | Vorher (kaputt) | Nachher (fix) |
|---|---|---|
| Backend in Prod | `Command::new("python")` → braucht Python im PATH | PyInstaller `.exe` als Tauri Sidecar → standalone |
| App-Start | Frontend sofort interaktiv | Health-Gate wartet bis Backend `/health` antwortet |
| texconv Pfad | Relativer Pfad `backend/tools/` | Dynamisch: `sys._MEIPASS` (PyInstaller) oder relativ (Dev) |
| Shutdown | Backend-Prozess bleibt als Zombie | Tauri killt Backend-Prozess bei App-Close |

---

## 1. PyInstaller Backend-Bundle

### `backend/backend.spec`
```python
# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# rembg + onnxruntime brauchen extra Data-Files
datas = collect_data_files('rembg')
datas += collect_data_files('onnxruntime')
datas += [('tools/texconv.exe', 'tools')]

hiddenimports = collect_submodules('rembg') + collect_submodules('onnxruntime')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports + [
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,    # console=True damit stdout/stderr sichtbar für Debugging
    icon=None,
)
```

### `scripts/build_backend.py`
```python
"""Baut das Backend als standalone .exe und kopiert es in src-tauri/binaries/"""
import subprocess
import shutil
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(ROOT, "backend")
BINARIES_DIR = os.path.join(ROOT, "src-tauri", "binaries")

# Tauri Sidecar Naming-Convention: name-target_triple
SIDECAR_NAME = "backend-x86_64-pc-windows-msvc.exe"

def build():
    print(">>> Building backend with PyInstaller...")
    subprocess.run(
        ["pyinstaller", "--clean", "--noconfirm", "backend.spec"],
        cwd=BACKEND_DIR,
        check=True
    )

    # Output: backend/dist/backend.exe
    built_exe = os.path.join(BACKEND_DIR, "dist", "backend.exe")

    os.makedirs(BINARIES_DIR, exist_ok=True)
    dest = os.path.join(BINARIES_DIR, SIDECAR_NAME)
    shutil.copy2(built_exe, dest)
    print(f">>> Copied to {dest}")

if __name__ == "__main__":
    build()
```

### Build ausführen
```bash
cd F:\Projekte\Haku

# Einmalig PyInstaller installieren
pip install pyinstaller

# Backend bauen
python scripts/build_backend.py

# Ergebnis: src-tauri/binaries/backend-x86_64-pc-windows-msvc.exe
```

---

## 2. Tauri Sidecar-Konfiguration

### `tauri.conf.json` — Änderungen
```jsonc
{
  // ... bestehende Config bleibt ...

  "plugins": {
    "dialog": { "all": true },
    "fs": {
      "scope": ["**"]
    },
    "shell": {
      "scope": [
        {
          "name": "backend",
          "sidecar": true          // ← NEU: als Sidecar markiert
          // Kein "cmd" nötig — Tauri sucht automatisch in binaries/
        }
      ]
    }
  },
  "bundle": {
    "active": true,
    "targets": ["nsis"],
    "icon": ["icons/icon.png"],
    "externalBin": ["binaries/backend"]   // ← NEU: Sidecar bundlen
    // "resources" für backend/ entfällt — alles ist in der .exe
  }
}
```

### `main.rs` — Sidecar Start + Shutdown
```rust
use tauri::Manager;
use tauri_plugin_shell::ShellExt;
use std::sync::Mutex;

struct BackendProcess(Mutex<Option<tauri_plugin_shell::process::CommandChild>>);

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_shell::init())
        .manage(BackendProcess(Mutex::new(None)))
        .setup(|app| {
            // Backend Sidecar starten
            let sidecar = app.shell()
                .sidecar("backend")
                .expect("failed to create sidecar command");

            let (mut rx, child) = sidecar.spawn()
                .expect("failed to spawn backend sidecar");

            // Backend stdout/stderr loggen (optional, hilft beim Debugging)
            tauri::async_runtime::spawn(async move {
                use tauri_plugin_shell::process::CommandEvent;
                while let Some(event) = rx.recv().await {
                    match event {
                        CommandEvent::Stdout(line) => {
                            println!("[backend] {}", String::from_utf8_lossy(&line));
                        }
                        CommandEvent::Stderr(line) => {
                            eprintln!("[backend:err] {}", String::from_utf8_lossy(&line));
                        }
                        _ => {}
                    }
                }
            });

            // Child-Process speichern für Cleanup
            let state = app.state::<BackendProcess>();
            *state.0.lock().unwrap() = Some(child);

            Ok(())
        })
        .on_window_event(|window, event| {
            // Backend killen wenn App geschlossen wird
            if let tauri::WindowEvent::Destroyed = event {
                let state = window.state::<BackendProcess>();
                if let Some(child) = state.0.lock().unwrap().take() {
                    let _ = child.kill();
                    println!("[haku] Backend process killed");
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running Haku");
}
```

### `Cargo.toml` — Dependencies
```toml
[dependencies]
tauri = { version = "2", features = [] }
tauri-plugin-dialog = "2"
tauri-plugin-fs = "2"
tauri-plugin-shell = "2"
serde = { version = "1", features = ["derive"] }
serde_json = "1"
```

---

## 3. Backend — Dynamische Pfade für PyInstaller

### `services/dds_converter.py` — Fix
```python
import subprocess
import os
import sys

def _get_base_path() -> str:
    """PyInstaller packt Files nach sys._MEIPASS, im Dev ist es relativ."""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.join(os.path.dirname(__file__), "..")

TEXCONV_PATH = os.path.join(_get_base_path(), "tools", "texconv.exe")

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

### `main.py` — Startup-Log
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sys
import os

# PyInstaller Workaround: CWD auf MEIPASS setzen
if getattr(sys, 'frozen', False):
    os.chdir(sys._MEIPASS)

from routers import process, search

app = FastAPI(title="Haku Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["tauri://localhost", "https://tauri.localhost", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(process.router, prefix="/process")
app.include_router(search.router, prefix="/search")

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    print(f"[haku-backend] Starting on 127.0.0.1:23431")
    print(f"[haku-backend] Frozen: {getattr(sys, 'frozen', False)}")
    if getattr(sys, 'frozen', False):
        print(f"[haku-backend] MEIPASS: {sys._MEIPASS}")
    uvicorn.run(app, host="127.0.0.1", port=23431)
```

---

## 4. Frontend — Health-Check Gate

### `src/hooks/useBackendHealth.js`
```javascript
import { useState, useEffect } from 'react';

const API = 'http://127.0.0.1:23431';
const MAX_RETRIES = 30;       // 30 Versuche
const RETRY_INTERVAL = 1000;  // 1 Sekunde

export function useBackendHealth() {
  const [ready, setReady] = useState(false);
  const [error, setError] = useState(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let cancelled = false;
    let retries = 0;

    async function check() {
      while (retries < MAX_RETRIES && !cancelled) {
        try {
          const res = await fetch(`${API}/health`);
          if (res.ok) {
            if (!cancelled) setReady(true);
            return;
          }
        } catch {
          // Backend noch nicht bereit — weiter versuchen
        }

        retries++;
        if (!cancelled) setAttempt(retries);
        await new Promise(r => setTimeout(r, RETRY_INTERVAL));
      }

      if (!cancelled) {
        setError('Backend konnte nicht gestartet werden.');
      }
    }

    check();
    return () => { cancelled = true; };
  }, []);

  return { ready, error, attempt, maxRetries: MAX_RETRIES };
}
```

### `src/components/BackendStatus.jsx`
```jsx
export default function BackendStatus({ attempt, maxRetries, error }) {
  if (error) {
    return (
      <div className="backend-status error">
        <span className="icon">✕</span>
        <p>{error}</p>
        <p className="hint">Starte die App neu oder prüfe die Logs.</p>
      </div>
    );
  }

  return (
    <div className="backend-status loading">
      <div className="spinner" />
      <p>Backend wird gestartet...</p>
      <p className="hint">{attempt} / {maxRetries}</p>
    </div>
  );
}
```

### `src/App.jsx` — Gate einbauen
```jsx
import { useBackendHealth } from './hooks/useBackendHealth';
import BackendStatus from './components/BackendStatus';
import Layout from './components/Layout';

export default function App() {
  const { ready, error, attempt, maxRetries } = useBackendHealth();

  if (!ready) {
    return <BackendStatus attempt={attempt} maxRetries={maxRetries} error={error} />;
  }

  return <Layout />;
}
```

### `src/index.css` — BackendStatus Styles
```css
/* Ergänzen zu bestehenden Styles */

.backend-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
  gap: 12px;
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: var(--font-main);
}

.backend-status.error .icon {
  font-size: 48px;
  color: var(--error);
}

.backend-status .hint {
  color: var(--text-muted);
  font-size: 13px;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
```

---

## 5. GitHub Actions — Angepasster Release Build

### `.github/workflows/release.yml` — Änderungen
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
        run: |
          pip install -r backend/requirements.txt
          pip install pyinstaller

      - name: Download texconv
        run: |
          curl -L -o texconv.zip https://github.com/microsoft/DirectXTex/releases/latest/download/texconv.zip
          Expand-Archive texconv.zip -DestinationPath backend/tools/
        shell: pwsh

      - name: Build backend sidecar            # ← NEU
        run: python scripts/build_backend.py

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

## 6. Dev vs Prod — So läuft es jetzt

### Dev-Modus (`npm run tauri dev`)
```
Tauri startet → shell.sidecar("backend") sucht in src-tauri/binaries/
              → backend-x86_64-pc-windows-msvc.exe startet
              → FastAPI auf 127.0.0.1:23431
              → Frontend Health-Check pollt /health
              → Backend antwortet OK → App wird interaktiv
```

> **Hinweis:** Für Dev kannst du auch weiterhin `python backend/main.py` manuell starten
> und die Sidecar-Zeile in `main.rs` auskommentieren. Dann hast du Hot-Reload auf dem Backend.

### Prod-Modus (gebaute `.exe`)
```
User startet Haku.exe
  → Tauri entpackt backend.exe aus Bundle
  → Startet als Sidecar-Child-Process
  → Frontend zeigt "Backend wird gestartet..." mit Spinner
  → Health-Check pollt 127.0.0.1:23431/health (max 30s)
  → Backend meldet OK → App wird interaktiv
  → User schließt App → Tauri killt backend.exe Process
```

---

## Checkliste

- [ ] `pip install pyinstaller` lokal installieren
- [ ] `python scripts/build_backend.py` ausführen
- [ ] Prüfen ob `src-tauri/binaries/backend-x86_64-pc-windows-msvc.exe` existiert
- [ ] `tauri.conf.json` → `externalBin` und `shell.scope` anpassen
- [ ] `main.rs` → Sidecar-Start + Shutdown-Handling einbauen
- [ ] `dds_converter.py` → `sys._MEIPASS` Pfad-Fix
- [ ] `main.py` → `os.chdir(sys._MEIPASS)` für Frozen-Mode
- [ ] `App.jsx` → Health-Gate einbauen
- [ ] `npm run tauri build` testen
- [ ] Release-Tag pushen → GitHub Actions baut `.exe`
