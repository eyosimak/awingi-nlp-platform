"""
Awingi NLP Platform — Database Engine and Session Management
"""

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from src.common.config import settings

# Allow DATABASE_URL override from environment
DATABASE_URL = os.getenv("DATABASE_URL", settings.DATABASE_URL)

# If running in serverless Vercel environment with SQLite, route to /tmp
if os.getenv("VERCEL") and "sqlite" in DATABASE_URL:
    DATABASE_URL = "sqlite:////tmp/app.db"

# Configure SQLite or PostgreSQL connection arguments
if "sqlite" in DATABASE_URL:
    db_path = DATABASE_URL.replace("sqlite:///", "")
    if db_path and not db_path.startswith(":memory:"):
        try:
            Path(db_path).resolve().parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
    connect_args = {"check_same_thread": False}
else:
    connect_args = {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

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
