"""
Vercel Serverless Function Handler
Re-exports the root application FastAPI instance.
"""

import os
import sys

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

# Standard Library 'platform' Unshadowing
if "platform" in sys.modules and not hasattr(sys.modules["platform"], "system"):
    del sys.modules["platform"]

try:
    import platform as _std_platform

    if not hasattr(_std_platform, "system"):
        _orig_path = sys.path[:]
        sys.path = [p for p in sys.path if "_vendor" not in p]
        if "platform" in sys.modules:
            del sys.modules["platform"]
        import platform as _std_platform

        sys.modules["platform"] = _std_platform
        sys.path = _orig_path
except Exception:
    pass

from app import app  # noqa: F401
