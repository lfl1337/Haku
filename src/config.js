// Single source of truth for the backend base URL.
// The Python sidecar listens on 127.0.0.1:24100 (see backend/main.py).
// Override the port at build time via VITE_BACKEND_PORT if it ever moves again;
// keep this constant and backend/main.py in sync.
const BACKEND_PORT = import.meta.env.VITE_BACKEND_PORT ?? "24100";

export const API_BASE = `http://127.0.0.1:${BACKEND_PORT}`;
