"""
Awingi NLP Platform — Main Application Factory
"""

from contextlib import asynccontextmanager
import os
import sys
import traceback
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from src.platform.database import init_db
from src.platform.auth.routes import router as auth_router
from src.platform.routes.dashboard import router as dashboard_router
from src.platform.routes.ingest import router as ingest_router
from src.platform.routes.review import router as review_router
from src.platform.routes.export import router as export_router

STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown lifecycle management.
    Initializes database schema and bootstraps default administrator.
    """
    # In local development, eagerly initialize schema.
    # In serverless environments, schema initialization is performed lazily on demand to avoid cold-start timeouts.
    if not os.getenv("VERCEL"):
        try:
            init_db()
        except Exception as exc:
            print(f"[Awingi Platform] Lifespan database initialization notice: {exc}")

    yield


def create_app() -> FastAPI:
    """FastAPI application factory for Awingi NLP Platform."""
    app = FastAPI(
        title="Awingi NLP Platform",
        description="Corpus curation, human-in-the-loop review, and dataset export platform for Awingi (Awngi) language data.",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Ensure static directories exist if writable
    try:
        STATIC_DIR.mkdir(parents=True, exist_ok=True)
        (STATIC_DIR / "css").mkdir(parents=True, exist_ok=True)
        (STATIC_DIR / "js").mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    # Mount static assets if directory exists
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/healthz", tags=["health"])
    async def health_check():
        return {"status": "healthy", "service": "awingi-nlp-platform"}

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        tb = traceback.format_exc()
        print(f"[Awingi Platform Request Exception]\n{tb}", file=sys.stderr)
        return HTMLResponse(
            content=f"""<!DOCTYPE html>
<html>
<head>
    <title>Runtime Error — Awingi Platform</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding: 2rem; background: #0f172a; color: #f8fafc; margin: 0; }}
        .card {{ background: #1e293b; border: 1px solid #ef4444; border-radius: 8px; padding: 1.5rem; max-width: 900px; margin: 2rem auto; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5); }}
        h1 {{ color: #ef4444; font-size: 1.5rem; margin-top: 0; }}
        pre {{ background: #020617; color: #fca5a5; padding: 1.25rem; border-radius: 6px; overflow-x: auto; font-size: 0.875rem; line-height: 1.6; border: 1px solid #334155; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>Serverless Runtime Exception</h1>
        <p>An uncaught error occurred while handling request {request.url.path}:</p>
        <pre>{tb}</pre>
    </div>
</body>
</html>""",
            status_code=500,
        )

    # Include route modules
    app.include_router(auth_router)
    app.include_router(dashboard_router)
    app.include_router(ingest_router)
    app.include_router(review_router)
    app.include_router(export_router)

    return app


app = create_app()
