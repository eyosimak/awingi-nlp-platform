"""
Awingi NLP Platform — Main Application Factory
"""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from src.platform.database import SessionLocal, init_db
from src.platform.auth.dependencies import bootstrap_default_admin
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
    # 1. Initialize database tables
    init_db()

    # 2. Bootstrap default admin user
    db = SessionLocal()
    try:
        bootstrap_default_admin(db)
    finally:
        db.close()

    yield


def create_app() -> FastAPI:
    """FastAPI application factory for Awingi NLP Platform."""
    app = FastAPI(
        title="Awingi NLP Platform",
        description="Corpus curation, human-in-the-loop review, and dataset export platform for Awingi (Awngi) language data.",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Ensure static directories exist
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    (STATIC_DIR / "css").mkdir(parents=True, exist_ok=True)
    (STATIC_DIR / "js").mkdir(parents=True, exist_ok=True)

    # Mount static assets
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # Include route modules
    app.include_router(auth_router)
    app.include_router(dashboard_router)
    app.include_router(ingest_router)
    app.include_router(review_router)
    app.include_router(export_router)

    return app


app = create_app()
