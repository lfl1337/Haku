import sys
import os

# When frozen (PyInstaller), skip pip bootstrap — deps are bundled.
# HAKU_SKIP_BOOTSTRAP lets tests import the app without triggering pip/network.
if getattr(sys, 'frozen', False):
    os.chdir(sys._MEIPASS)
elif not os.environ.get("HAKU_SKIP_BOOTSTRAP"):
    import bootstrap
    bootstrap.run()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from routers import process, search

app = FastAPI(title="Haku Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "tauri://localhost",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(process.router, prefix="/process")
app.include_router(search.router, prefix="/search")


@app.get("/health")
async def health():
    return {"status": "ok"}


def kill_old_backend(port=24100):
    """Kill any existing process on our port before starting."""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", port))
        sock.close()
    except OSError:
        import subprocess
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True, text=True,
        )
        for line in result.stdout.splitlines():
            if f"127.0.0.1:{port}" in line and "LISTENING" in line:
                pid = line.strip().split()[-1]
                subprocess.run(["taskkill", "/F", "/PID", pid],
                               capture_output=True)
                break
        sock.close()
        import time
        time.sleep(0.5)


if __name__ == "__main__":
    print("[haku-backend] Starting on 127.0.0.1:24100", flush=True)
    print(f"[haku-backend] Frozen: {getattr(sys, 'frozen', False)}", flush=True)
    kill_old_backend()
    uvicorn.run(app, host="127.0.0.1", port=24100)
