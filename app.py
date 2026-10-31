"""
Awingi NLP Platform — Root Serverless & Application Entrypoint
Exposes the FastAPI application instance for Vercel zero-config deployment.
"""

from src.platform.app import app

# Root application handler
app = app
