"""
Stillwater Pose Hub
-------------------
Single unified entry point for all Stillwater yoga pose-detection modules.

Adding a new module:
    1. Edit app/modules.json — append a new module object.
    2. Commit & push. Render auto-deploys.
    3. The new card appears on the homepage automatically.

The detector applications themselves live in their own repositories and
deploy independently. This hub only routes traffic to them.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "app" / "modules.json"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"


# --------------------------------------------------------------------------
# Config loading (re-read on each request in dev, cached in prod)
# --------------------------------------------------------------------------
_CONFIG_CACHE: dict[str, Any] | None = None


def load_config() -> dict[str, Any]:
    """Load the modules configuration from JSON.

    In development we re-read every call so edits show up instantly.
    In production (RENDER env set) we cache after first read.
    """
    global _CONFIG_CACHE

    is_prod = os.getenv("RENDER") == "true" or os.getenv("ENV") == "production"
    if is_prod and _CONFIG_CACHE is not None:
        return _CONFIG_CACHE

    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Module config not found at {CONFIG_PATH}")

    with CONFIG_PATH.open("r", encoding="utf-8") as fh:
        config = json.load(fh)

    if is_prod:
        _CONFIG_CACHE = config
    return config


# --------------------------------------------------------------------------
# FastAPI app
# --------------------------------------------------------------------------
app = FastAPI(
    title="Stillwater Pose Hub",
    description="Unified gateway for Stillwater Yoga's AI pose-detection modules.",
    version="1.1.0",
    docs_url="/api/docs",
    redoc_url=None,
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def find_module(module_id: str) -> dict[str, Any] | None:
    """Look up a single module by id."""
    config = load_config()
    for module in config.get("modules", []):
        if module.get("id") == module_id:
            return module
    return None


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request) -> HTMLResponse:
    """Landing page — shows all modules as cards."""
    config = load_config()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "site": config["site"],
            "modules": config["modules"],
        },
    )


@app.get("/launch/{module_id}")
async def launch_module(request: Request, module_id: str):
    """Module launch — either embedded iframe view, or 302 redirect to external app.

    The mode is controlled per-module by the `embed_mode` field in modules.json:
      - "iframe" (default): renders launch.html with an embedded iframe
      - "new_tab": defensively redirects to the external URL. This is for
        modules that can't be safely iframed (WebRTC, cross-origin webcam,
        Twilio TURN handshakes, etc.). The homepage card for these already
        opens directly in a new tab; this redirect catches stale bookmarks.
    """
    module = find_module(module_id)
    if module is None:
        raise HTTPException(status_code=404, detail=f"Module '{module_id}' not found.")

    embed_mode = module.get("embed_mode", "iframe")
    if embed_mode == "new_tab":
        return RedirectResponse(url=module["url"], status_code=302)

    config = load_config()
    return templates.TemplateResponse(
        "launch.html",
        {
            "request": request,
            "site": config["site"],
            "module": module,
        },
    )


@app.get("/go/{module_id}")
async def redirect_to_module(module_id: str) -> RedirectResponse:
    """Direct redirect — opens the underlying app in the current tab."""
    module = find_module(module_id)
    if module is None:
        raise HTTPException(status_code=404, detail=f"Module '{module_id}' not found.")
    return RedirectResponse(url=module["url"], status_code=302)


@app.get("/api/modules")
async def list_modules() -> JSONResponse:
    """JSON list of all modules — useful for embedding or external integrations."""
    config = load_config()
    return JSONResponse(content=config)


@app.get("/healthz")
async def health_check() -> dict[str, str]:
    """Render health-check endpoint."""
    return {"status": "ok", "service": "stillwater-pose-hub"}


# --------------------------------------------------------------------------
# Local dev entry point
# --------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
