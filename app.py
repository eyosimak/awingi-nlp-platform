"""
Awingi NLP Platform — Root Application & Serverless Entrypoint
Designed for high reliability across standard servers and serverless runtimes (Vercel Lambda).
"""

import os
import sys
import traceback

# Ensure project root is at the front of sys.path
_root = os.path.dirname(os.path.abspath(__file__))
if _root not in sys.path:
    sys.path.insert(0, _root)

# Diagnostic log accumulator for debugging runtime issues
_diag_messages = []


def _diag_log(msg: str):
    _diag_messages.append(msg)
    print(f"[Awingi Boot] {msg}", file=sys.stderr)


_diag_log(f"Python {sys.version}")
_diag_log(f"CWD: {os.getcwd()}")
_diag_log(f"sys.path: {sys.path[:5]}...")

# --- Self-Healing Bridge for Pydantic / Vercel Lambda ---
# Under certain Vercel packagers or runtime caching conditions, lazy-loaded
# attributes like BaseModel may raise an unhandled exception inside __getattr__.
# We explicitly ensure BaseModel and create_model are bound to the pydantic module.
try:
    import pydantic

    if not hasattr(pydantic, "BaseModel"):
        _diag_log("pydantic missing BaseModel attribute; applying compatibility bridge...")
        try:
            import pydantic.main as _pm

            pydantic.BaseModel = getattr(_pm, "BaseModel", None)
            pydantic.create_model = getattr(_pm, "create_model", None)
            _diag_log("Successfully attached BaseModel from pydantic.main")
        except Exception as _e_pm:
            _diag_log(f"Notice: pydantic.main import failed: {_e_pm}")
except Exception as _p_err:
    _diag_log(f"Notice: Early pydantic inspection error: {_p_err}")

# --- Application Loader ---
_real_app = None
_load_error = None

try:
    from src.platform.app import app as _imported_app

    _real_app = _imported_app
    _diag_log("src.platform.app imported successfully!")
except Exception:
    _load_error = traceback.format_exc()
    _diag_log(f"FATAL: Failed to import src.platform.app:\n{_load_error}")


async def app(scope, receive, send):
    """
    Root ASGI application entrypoint.
    Delegates to the full FastAPI platform if initialized, or renders an
    in-browser diagnostic report with HTTP 200 to prevent generic cloud 500 errors.
    """
    if _real_app is not None:
        await _real_app(scope, receive, send)
        return

    # Handle ASGI lifespan events gracefully when in diagnostic mode
    if scope["type"] == "lifespan":
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                await send({"type": "lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                await send({"type": "lifespan.shutdown.complete"})
                return

    # Handle HTTP requests by returning diagnostic information
    if scope["type"] == "http":
        logs_html = "".join(f"<li>{msg}</li>" for msg in _diag_messages)
        content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Platform Diagnostic — Awingi NLP</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace;
            background: #0f172a;
            color: #f8fafc;
            padding: 2rem;
            margin: 0;
            line-height: 1.5;
        }}
        .card {{
            background: #1e293b;
            border: 1px solid #ef4444;
            border-radius: 8px;
            padding: 1.5rem;
            max-width: 900px;
            margin: 1rem auto;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
        }}
        h1 {{ color: #ef4444; font-size: 1.5rem; margin-top: 0; }}
        h2 {{ color: #94a3b8; font-size: 1.1rem; margin-top: 1.5rem; }}
        pre {{
            background: #020617;
            color: #fca5a5;
            padding: 1rem;
            border-radius: 6px;
            overflow-x: auto;
            font-size: 0.875rem;
            border: 1px solid #334155;
            white-space: pre-wrap;
            word-break: break-all;
        }}
        ul {{ background: #020617; padding: 1rem 1.5rem; border-radius: 6px; border: 1px solid #334155; }}
        li {{ color: #38bdf8; font-size: 0.875rem; margin-bottom: 0.25rem; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>Awingi NLP Platform — Initialization Diagnostic</h1>
        <p>The application could not complete cold-start initialization on this serverless instance.</p>
        
        <h2>Startup Traceback</h2>
        <pre>{_load_error or "No traceback available."}</pre>

        <h2>Boot Activity Log</h2>
        <ul>{logs_html}</ul>

        <h2>Environment Details</h2>
        <pre>Python: {sys.version}
CWD: {os.getcwd()}
sys.path:
{chr(10).join(sys.path)}</pre>
    </div>
</body>
</html>"""
        body_bytes = content.encode("utf-8")
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [
                [b"content-type", b"text/html; charset=utf-8"],
                [b"content-length", str(len(body_bytes)).encode("ascii")],
            ],
        })
        await send({
            "type": "http.response.body",
            "body": body_bytes,
        })
