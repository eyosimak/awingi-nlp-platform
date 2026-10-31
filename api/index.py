"""
Vercel API route handler — Re-exports the root application instance.
"""

import sys
import os

# Ensure project root is on sys.path for Vercel Lambda
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from app import app

# ASGI handler
app = app
