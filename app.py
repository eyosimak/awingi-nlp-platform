"""
Awingi NLP Platform — Root Serverless & Application Entrypoint
Exposes the top-level FastAPI application instance for Vercel Python runtime.
"""

import os
import sys
import traceback

# Ensure project root is on sys.path
_root = os.path.dirname(os.path.abspath(__file__))
if _root not in sys.path:
    sys.path.insert(0, _root)

# Self-healing compatibility bridge for Pydantic lazy imports in serverless runtimes
try:
    import pydantic

    if not hasattr(pydantic, "BaseModel"):
        try:
            import pydantic.main as _pm

            pydantic.BaseModel = getattr(_pm, "BaseModel", None)
            pydantic.create_model = getattr(_pm, "create_model", None)
        except Exception:
            pass
except Exception:
    pass

# Import the core FastAPI platform application
try:
    from src.platform.app import app
except Exception:
    # If anything unexpected fails during import, provide a fallback FastAPI instance
    # that renders the startup traceback with HTTP 200 so Vercel does not intercept with generic 500.
    _startup_err = traceback.format_exc()
    print(f"[Awingi Platform] Startup Import Failure:\n{_startup_err}", file=sys.stderr)

    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse

    app = FastAPI(title="Awingi Platform Diagnostic")

    @app.get("/{full_path:path}")
    async def _diagnostic_fallback(full_path: str = ""):
        return HTMLResponse(
            content=f"""<!DOCTYPE html>
<html>
<head><title>Startup Error — Awingi Platform</title>
<style>
body {{ font-family: monospace; background: #0f172a; color: #f8fafc; padding: 2rem; }}
pre {{ background: #1e293b; color: #fca5a5; padding: 1.5rem; border-radius: 8px; overflow-x: auto; white-space: pre-wrap; word-break: break-all; border: 1px solid #ef4444; }}
h1 {{ color: #ef4444; font-size: 1.5rem; }}
</style>
</head>
<body>
<h1>Awingi NLP Platform — Cold Start Failure</h1>
<p>Python {sys.version}</p>
<p>Working Directory: {os.getcwd()}</p>
<pre>{_startup_err}</pre>
</body>
</html>""",
            status_code=200,
        )
