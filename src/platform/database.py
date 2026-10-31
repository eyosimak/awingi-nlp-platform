"""
Awingi NLP Platform — Database Engine and Session Management
"""

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from src.common.config import settings

# Allow DATABASE_URL or POSTGRES_URL (Vercel Neon integration standard) override from environment
DATABASE_URL = (
    os.getenv("DATABASE_URL")
    or os.getenv("POSTGRES_URL")
    or os.getenv("POSTGRES_PRISMA_URL")
    or settings.DATABASE_URL
)

# Normalize legacy postgres:// URI scheme provided by some cloud hosts (Neon, Supabase, Heroku)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Ensure SSL requirement for cloud-hosted Neon/Supabase endpoints
if ("neon.tech" in DATABASE_URL or "supabase.co" in DATABASE_URL) and "sslmode" not in DATABASE_URL:
    delimiter = "&" if "?" in DATABASE_URL else "?"
    DATABASE_URL = f"{DATABASE_URL}{delimiter}sslmode=require"

# If running in serverless Vercel environment with SQLite, route to /tmp
if os.getenv("VERCEL") and "sqlite" in DATABASE_URL:
    DATABASE_URL = "sqlite:////tmp/app.db"

# Configure SQLite or PostgreSQL connection arguments & pooling
engine_kwargs = {}
if "sqlite" in DATABASE_URL:
    db_path = DATABASE_URL.replace("sqlite:///", "")
    if db_path and not db_path.startswith(":memory:"):
        try:
            Path(db_path).resolve().parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Serverless-friendly settings for Postgres (Neon / Supabase)
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 300

engine = create_engine(DATABASE_URL, **engine_kwargs)

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
        settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
        settings.RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
        settings.PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    
    # Import models here so Base knows about all tables before create_all
    from src.platform import models  # noqa: F401
    
    Base.metadata.create_all(bind=engine)
