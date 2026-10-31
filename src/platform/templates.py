"""
Awingi NLP Platform — Centralized Jinja2 Templates Engine
Provides robust absolute-path template rendering across local and serverless environments.
"""

from pathlib import Path
from fastapi.templating import Jinja2Templates

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
