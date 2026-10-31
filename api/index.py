"""
Vercel Serverless Deployment Entrypoint
Routes all incoming HTTP requests to the FastAPI platform application.
"""

import sys
import traceback
from pathlib import Path

# Ensure project root directory is on sys.path so 'src' is always importable on Vercel
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from src.platform.app import app  # noqa: E402
except Exception as exc:
    tb = traceback.format_exc()
    print(f"[Awingi Platform Startup Error]\n{tb}", file=sys.stderr)

    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse

    error_app = FastAPI()

    @error_app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"], response_class=HTMLResponse)
    async def startup_error_fallback(path: str = ""):
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Startup Diagnostic — Awingi Platform</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding: 2rem; background: #0f172a; color: #f8fafc; margin: 0; }}
        .card {{ background: #1e293b; border: 1px solid #ef4444; border-radius: 8px; padding: 1.5rem; max-width: 900px; margin: 2rem auto; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5); }}
        h1 {{ color: #ef4444; font-size: 1.5rem; margin-top: 0; }}
        pre {{ background: #020617; color: #fca5a5; padding: 1.25rem; border-radius: 6px; overflow-x: auto; font-size: 0.875rem; line-height: 1.6; border: 1px solid #334155; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>Serverless Initialization Diagnostic</h1>
        <p>A Python startup error occurred before the FastAPI application could mount:</p>
        <pre>{tb}</pre>
    </div>
</body>
</html>"""

    app = error_app

# Vercel ASGI handler
app = app
