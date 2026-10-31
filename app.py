"""
Awingi NLP Platform — Root Serverless & Application Entrypoint
Catches import errors and displays them in browser for debugging on Vercel.
"""

import sys
import os
import traceback

# Ensure project root is on sys.path
_root = os.path.dirname(os.path.abspath(__file__))
if _root not in sys.path:
    sys.path.insert(0, _root)

try:
    from src.platform.app import app
except Exception:
    # If the real app fails to import, serve a diagnostic page showing the error
    _tb = traceback.format_exc()
    print(f"[Awingi Platform] FATAL IMPORT ERROR:\n{_tb}", file=sys.stderr)

    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse

    app = FastAPI()

    @app.get("/{path:path}")
    async def _diagnostic(path: str = ""):
        return HTMLResponse(
            content=f"""<!DOCTYPE html>
<html>
<head><title>Import Error — Awingi Platform</title>
<style>
body {{ font-family: monospace; background: #0f172a; color: #f8fafc; padding: 2rem; }}
pre {{ background: #1e293b; color: #fca5a5; padding: 1.5rem; border-radius: 8px; overflow-x: auto; white-space: pre-wrap; word-wrap: break-word; border: 1px solid #ef4444; }}
h1 {{ color: #ef4444; }}
</style>
</head>
<body>
<h1>Application Import Failed</h1>
<p>The FastAPI application could not be loaded. Traceback:</p>
<pre>{_tb}</pre>
<p>Python: {sys.version}</p>
<p>CWD: {os.getcwd()}</p>
<p>sys.path: {sys.path}</p>
</body>
</html>""",
            status_code=500,
        )
