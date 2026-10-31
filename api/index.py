"""
Vercel Serverless Deployment Entrypoint
Routes all incoming HTTP requests to the FastAPI platform application.
"""

import sys
from pathlib import Path

# Ensure project root directory is on sys.path so 'src' is always importable on Vercel
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.platform.app import app  # noqa: E402

# Vercel ASGI handler
app = app
