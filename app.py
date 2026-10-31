"""
Awingi NLP Platform — Root Serverless & Application Entrypoint
Exposes the top-level application instance for Vercel Python runtime.
Includes deep diagnostic reporting if module loading fails.
"""

import os
import sys
import traceback

# Ensure project root is on sys.path
_root = os.path.dirname(os.path.abspath(__file__))
if _root not in sys.path:
    sys.path.insert(0, _root)

_diag = []


def _log(msg: str):
    _diag.append(msg)
    print(f"[Awingi DIAG] {msg}", file=sys.stderr)


# Step 1: Diagnose Pydantic Core
try:
    import pydantic_core

    _log(f"pydantic_core loaded: {getattr(pydantic_core, '__file__', 'no-file')}")
    _log(f"pydantic_core version: {getattr(pydantic_core, '__version__', 'unknown')}")
except Exception as e:
    _log(f"FAIL import pydantic_core: {type(e).__name__}: {e}\n{traceback.format_exc()}")

# Step 2: Diagnose Pydantic
try:
    import pydantic

    _log(f"pydantic loaded: {getattr(pydantic, '__file__', 'no-file')}")
    _log(f"pydantic version: {getattr(pydantic, '__version__', 'unknown')}")
    _log(f"pydantic has BaseModel: {hasattr(pydantic, 'BaseModel')}")
except Exception as e:
    _log(f"FAIL import pydantic: {type(e).__name__}: {e}\n{traceback.format_exc()}")

# Step 3: Diagnose Pydantic Main
try:
    import pydantic.main as _pm

    _log(f"pydantic.main loaded: {_pm.__file__}")
    _log(f"BaseModel in pydantic.main: {hasattr(_pm, 'BaseModel')}")
    # Force attach to pydantic module
    import pydantic as _p

    _p.BaseModel = _pm.BaseModel
    _p.create_model = _pm.create_model
    _log("Successfully attached BaseModel and create_model to pydantic module")
except Exception as e:
    _log(f"FAIL import pydantic.main: {type(e).__name__}: {e}\n{traceback.format_exc()}")

# Step 4: Test from pydantic import BaseModel
try:
    from pydantic import BaseModel, create_model

    _log(f"TEST from pydantic import BaseModel: SUCCESS ({BaseModel})")
except Exception as e:
    _log(f"FAIL from pydantic import BaseModel: {type(e).__name__}: {e}\n{traceback.format_exc()}")

# Step 5: Vendor filesystem inspection
_vendor_dir = "/var/task/_vendor"
if os.path.isdir(_vendor_dir):
    try:
        entries = sorted(os.listdir(_vendor_dir))
        _log(f"_vendor contents ({len(entries)} items): {', '.join(entries[:30])}")
    except Exception as e:
        _log(f"Could not list _vendor: {e}")

_pydantic_core_dir = "/var/task/_vendor/pydantic_core"
if os.path.isdir(_pydantic_core_dir):
    try:
        core_files = sorted(os.listdir(_pydantic_core_dir))
        _log(f"_vendor/pydantic_core contents: {', '.join(core_files)}")
    except Exception as e:
        _log(f"Could not list pydantic_core dir: {e}")

# Step 6: Try importing the real FastAPI app
_init_error = None
try:
    from src.platform.app import app
except Exception:
    _init_error = traceback.format_exc()
    _log(f"FAIL import src.platform.app:\n{_init_error}")

    # Standard-library WSGI fallback: zero external dependencies, cannot fail
    def app(environ, start_response):
        status = "200 OK"
        diag_html = "".join(f"<pre>{item}</pre>" for item in _diag)
        body = f"""<!DOCTYPE html>
<html>
<head><title>Diagnostic — Awingi Platform</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace; background: #0f172a; color: #f8fafc; padding: 2rem; margin: 0; }}
.card {{ background: #1e293b; border: 1px solid #ef4444; border-radius: 8px; padding: 1.5rem; max-width: 900px; margin: 1rem auto; }}
pre {{ background: #020617; color: #fca5a5; padding: 1rem; border-radius: 6px; overflow-x: auto; white-space: pre-wrap; word-break: break-all; border: 1px solid #334155; font-size: 0.825rem; line-height: 1.4; margin-bottom: 0.5rem; }}
h1 {{ color: #ef4444; font-size: 1.4rem; margin-top: 0; }}
h2 {{ color: #38bdf8; font-size: 1.1rem; margin-top: 1.5rem; }}
</style>
</head>
<body>
<div class="card">
    <h1>Awingi Platform — Diagnostic Investigation</h1>
    <h2>Step-by-Step Diagnostic Probe Log:</h2>
    {diag_html}
    <h2>Full Startup Traceback:</h2>
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
