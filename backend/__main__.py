"""Run the FastAPI app with sensible defaults for local development.

Usage:
  python -m backend

This starts the app on port 8001 by default (can be overridden with
`BACKEND_PORT` env var). This avoids having to pass `--port` to uvicorn.
"""
import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("BACKEND_PORT", "8001"))
    host = os.environ.get("BACKEND_HOST", "127.0.0.1")
    reload_flag = os.environ.get("BACKEND_RELOAD", "true").lower() in ("1", "true", "yes")
    uvicorn.run("backend.main:app", host=host, port=port, reload=reload_flag)
