"""
Awingi NLP Platform — Root Application Entrypoint
Simple top-level app variable for Vercel Python runtime detection.
"""

import sys
import os

# Ensure project root is on sys.path
_root = os.path.dirname(os.path.abspath(__file__))
if _root not in sys.path:
    sys.path.insert(0, _root)

from src.platform.app import app  # noqa: F401, E402

# Vercel Python runtime expects a top-level ASGI app variable — this is it.
