"""
Token Usage Monitor — FastAPI entry point.

Run with:
    uvicorn main:app --reload --host 127.0.0.1 --port 8000

Binds to 127.0.0.1 only (never 0.0.0.0).
CORS restricted to Vite dev server origins.
Serves built frontend from backend/dist/ when it exists.
"""
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from db import init_db
from routes.by_category import router as by_category_router
from routes.refresh import router as refresh_router
from routes.summary import router as summary_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)

app = FastAPI(
    title="Token Usage Monitor",
    description="Local dashboard for Claude Code token usage from .jsonl transcripts.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup() -> None:
    init_db()
    logging.getLogger(__name__).info("Database initialised.")


app.include_router(summary_router)
app.include_router(by_category_router)
app.include_router(refresh_router)

_DIST = Path(__file__).parent / "dist"

if _DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(_DIST / "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str) -> FileResponse:
        index = _DIST / "index.html"
        return FileResponse(str(index))
