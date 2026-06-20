# Haku 白

Desktop tool for game asset preparation: background removal, 256×256 resize (stretch to fill), DDS BC3 export with mipmaps.

## Stack

- **Desktop:** Tauri v2 (Rust)
- **Backend:** FastAPI (Python 3.11+)
- **Frontend:** React 18 + Vite 8

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
