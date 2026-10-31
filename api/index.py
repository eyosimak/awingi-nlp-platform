"""
Vercel API route handler
Re-exports the root application instance.
"""

from app import app

# ASGI handler
app = app
