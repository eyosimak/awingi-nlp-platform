"""
Vercel Serverless Deployment Entrypoint
Routes all incoming HTTP requests to the FastAPI platform application.
"""

from src.platform.app import app

# Vercel WSGI/ASGI handler
app = app
