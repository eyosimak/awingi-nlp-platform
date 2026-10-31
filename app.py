"""
Awingi NLP Platform — Root Serverless & Application Entrypoint
Exposes the top-level application instance for Vercel Python runtime.
Includes a standard-library WSGI fallback if module loading fails.
"""

import os
import sys
import traceback

# Ensure project root is on sys.path
_root = os.path.dirname(os.path.abspath(__file__))
if _root not in sys.path:
    sys.path.insert(0, _root)

_init_error = None

try:
    from src.platform.app import app
except Exception:
    _init_error = traceback.format_exc()
    print(f"[CRITICAL STARTUP ERROR]\n{_init_error}", file=sys.stderr)

    # Standard-library WSGI fallback: zero external dependencies, cannot fail
    def app(environ, start_response):
        status = "200 OK"
        body = f"""<!DOCTYPE html>
<html>
<head><title>Startup Error — Awingi Platform</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace; background: #0f172a; color: #f8fafc; padding: 2rem; margin: 0; }}
.card {{ background: #1e293b; border: 1px solid #ef4444; border-radius: 8px; padding: 1.5rem; max-width: 900px; margin: 1rem auto; }}
pre {{ background: #020617; color: #fca5a5; padding: 1.25rem; border-radius: 6px; overflow-x: auto; white-space: pre-wrap; word-break: break-all; border: 1px solid #334155; font-size: 0.875rem; line-height: 1.5; }}
h1 {{ color: #ef4444; font-size: 1.4rem; margin-top: 0; }}
</style>
</head>
<body>
<div class="card">
    <h1>Awingi Platform — Cold Start Traceback</h1>
    <p>The FastAPI platform encountered an exception during module initialization:</p>
    <pre>{_init_error}</pre>
    <p style="color:#94a3b8;font-size:0.8rem;">Python: {sys.version} | CWD: {os.getcwd()}</p>
</div>
</body>
</html>""".encode("utf-8")
        headers = [
            ("Content-Type", "text/html; charset=utf-8"),
            ("Content-Length", str(len(body))),
        ]
        start_response(status, headers)
        return [body]
