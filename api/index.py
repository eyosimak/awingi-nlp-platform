"""
Vercel Serverless Function Entrypoint
Auto-detected by @vercel/python from the api/ directory.
"""

import sys
import os

# Ensure project root is on sys.path so 'src' package is importable
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from src.platform.app import app  # noqa: E402, F401
