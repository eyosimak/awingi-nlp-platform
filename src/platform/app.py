"""
Awingi NLP Platform — Main Application Factory
"""

import os
import sys
import traceback
from pathlib import Path

# Ensure standard library 'platform' is not shadowed by local package in serverless runtimes
if "platform" in sys.modules and not hasattr(sys.modules["platform"], "system"):
    del sys.modules["platform"]

try:
    import platform as _std_platform

    if not hasattr(_std_platform, "system"):
        _orig_path = sys.path[:]
        sys.path = [p for p in sys.path if "_vendor" not in p]
        if "platform" in sys.modules:
            del sys.modules["platform"]
        import platform as _std_platform

        sys.modules["platform"] = _std_platform
        sys.path = _orig_path
except Exception:
    pass
# Self-healing bridge for Pydantic lazy imports in serverless runtimes
try:
    import pydantic
    if not hasattr(pydantic, "BaseModel"):
        try:
            import pydantic.main as _pm
            pydantic.BaseModel = getattr(_pm, "BaseModel", None)
            pydantic.create_model = getattr(_pm, "create_model", None)
        except Exception:
            pass
except Exception:
    pass

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

# These imports might fail on Vercel — catch them
_import_error = None
try:
    from fastapi.staticfiles import StaticFiles
    from src.platform.database import init_db
    from src.platform.auth.routes import router as auth_router
    from src.platform.routes.dashboard import router as dashboard_router
    from src.platform.routes.ingest import router as ingest_router
    from src.platform.routes.review import router as review_router
    from src.platform.routes.export import router as export_router
    from src.platform.templates import templates  # noqa: F401
except Exception:
    _import_error = traceback.format_exc()
    print(f"[Awingi Platform] IMPORT ERROR:\n{_import_error}", file=sys.stderr)

STATIC_DIR = Path(__file__).resolve().parent / "static"


def create_app() -> FastAPI:
    """FastAPI application factory for Awingi NLP Platform."""

    # If imports failed, return a diagnostic app
    if _import_error:
        _app = FastAPI(title="Awingi NLP Platform — Error")

        @_app.get("/{path:path}")
        async def _diagnostic(path: str = ""):
            return HTMLResponse(
                content=f"""<!DOCTYPE html>
<html>
<head><title>Import Error — Awingi Platform</title>
<style>
body {{ font-family: monospace; background: #0f172a; color: #f8fafc; padding: 2rem; }}
pre {{ background: #1e293b; color: #fca5a5; padding: 1.5rem; border-radius: 8px; overflow-x: auto; white-space: pre-wrap; word-wrap: break-word; border: 1px solid #ef4444; }}
h1 {{ color: #ef4444; }}
</style>
</head>
<body>
<h1>Application Import Failed</h1>
<p>Python {sys.version}</p>
<p>CWD: {os.getcwd()}</p>
<pre>{_import_error}</pre>
</body>
</html>""",
                status_code=500,
            )
        return _app

    # Normal app creation
    _app = FastAPI(
        title="Awingi NLP Platform",
        description="Corpus curation, human-in-the-loop review, and dataset export platform for Awingi (Awngi) language data.",
        version="0.1.0",
        lifespan=_lifespan,
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
        _app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @_app.get("/healthz", tags=["health"])
    async def health_check():
        return {"status": "healthy", "service": "awingi-nlp-platform"}

    @_app.get("/api/index", include_in_schema=False)
    async def api_index_redirect():
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)

    @_app.exception_handler(Exception)
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
    _app.include_router(auth_router)
    _app.include_router(dashboard_router)
    _app.include_router(ingest_router)
    _app.include_router(review_router)
    _app.include_router(export_router)

    return _app


# Lifespan must be defined before create_app references it
from contextlib import asynccontextmanager  # noqa: E402


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle management."""
    if not os.getenv("VERCEL"):
        try:
            init_db()
        except Exception as exc:
            print(f"[Awingi Platform] Lifespan database initialization notice: {exc}")
    yield


app = create_app()
