"""
Awingi NLP Platform — Database Engine and Session Management
"""

import os
import ssl
from pathlib import Path
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Import settings with graceful fallback
try:
    from src.common.config import settings
    _default_db_url = settings.DATABASE_URL
except Exception:
    _default_db_url = "sqlite:////tmp/app.db"

# Allow DATABASE_URL or POSTGRES_URL (Vercel Neon integration standard) override from environment
DATABASE_URL = (
    os.getenv("DATABASE_URL")
    or os.getenv("POSTGRES_URL")
    or os.getenv("POSTGRES_PRISMA_URL")
    or _default_db_url
)

# Normalize legacy postgres:// URI scheme provided by some cloud hosts (Neon, Supabase, Heroku)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# If running in serverless Vercel environment with SQLite, route to /tmp
if os.getenv("VERCEL") and "sqlite" in DATABASE_URL:
    DATABASE_URL = "sqlite:////tmp/app.db"

engine_kwargs = {}

if "sqlite" in DATABASE_URL:
    db_path = DATABASE_URL.replace("sqlite:///", "")
    if db_path and not db_path.startswith(":memory:"):
        try:
            Path(db_path).resolve().parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
    engine_kwargs["connect_args"] = {"check_same_thread": False}
elif "postgresql" in DATABASE_URL:
    # Serverless-friendly settings for Postgres (Neon / Supabase)
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 300

    # Parse the URL to clean up parameters incompatible with pg8000
    parsed = urlparse(DATABASE_URL)
    query_params = parse_qs(parsed.query, keep_blank_values=True)

    # Remove parameters that pg8000 doesn't support
    for param in ["channel_binding", "sslmode"]:
        query_params.pop(param, None)

    # Rebuild clean URL with pg8000 driver
    clean_query = urlencode(query_params, doseq=True)
    clean_parsed = parsed._replace(
        scheme="postgresql+pg8000",
        query=clean_query,
    )
    DATABASE_URL = urlunparse(clean_parsed)

    # pg8000 needs ssl_context for Neon/cloud connections
    if "neon.tech" in (parsed.hostname or "") or "supabase.co" in (parsed.hostname or ""):
        engine_kwargs["connect_args"] = {"ssl_context": ssl.create_default_context()}

try:
    engine = create_engine(DATABASE_URL, **engine_kwargs)
except Exception as exc:
    print(f"[Awingi Platform] Notice: Could not initialize engine for {DATABASE_URL}: {exc}. Falling back to SQLite in /tmp.")
    DATABASE_URL = "sqlite:////tmp/app.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """
    FastAPI dependency yielding a transactional database session per request.
    Closes the session automatically upon completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database schema by creating all tables defined on Base metadata.
    Ensures storage directories exist.
    """
    try:
        from src.common.config import settings as _s
        _s.DATA_DIR.mkdir(parents=True, exist_ok=True)
        _s.RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
        _s.PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    
    # Import models here so Base knows about all tables before create_all
    from src.platform import models  # noqa: F401
    
    Base.metadata.create_all(bind=engine)

    # Ensure initial admin exists
    try:
        from src.platform.auth.dependencies import bootstrap_default_admin
        db = SessionLocal()
        try:
            bootstrap_default_admin(db)
        finally:
            db.close()
    except Exception:
        pass
