"""Flask server for drop."""

import mimetypes
import time
from collections import defaultdict
from pathlib import Path

from flask import Flask, request, make_response, send_file, Response

from .storage import get_page, load_pages
from .utils import verify_password, safe_path, load_manifest


app = Flask(__name__)

# Rate limiting: {ip: {page_id: [(timestamp, ...)]}}
_attempts: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
RATE_LIMIT = 3  # attempts
RATE_WINDOW = 60  # seconds
COOKIE_TTL = 15 * 60  # 15 minutes


def _check_rate_limit(ip: str, page_id: str) -> bool:
    """Check if IP is rate limited. Returns True if allowed."""
    now = time.time()
    attempts = _attempts[ip][page_id]

    # Clean old attempts
    _attempts[ip][page_id] = [t for t in attempts if now - t < RATE_WINDOW]

    return len(_attempts[ip][page_id]) < RATE_LIMIT


def _record_attempt(ip: str, page_id: str) -> None:
    """Record a failed attempt."""
    _attempts[ip][page_id].append(time.time())


def _login_form(error: str = "") -> str:
    """Generate login form HTML."""
    error_html = f'<p style="color:red">{error}</p>' if error else ""
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Protected Page</title>
    <style>
        body {{ font-family: system-ui, sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; background: #f5f5f5; }}
        form {{ background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        input {{ padding: 0.5rem; font-size: 1rem; border: 1px solid #ddd; border-radius: 4px; margin-right: 0.5rem; }}
        button {{ padding: 0.5rem 1rem; font-size: 1rem; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }}
        button:hover {{ background: #0056b3; }}
    </style>
</head>
<body>
    <form method="POST">
        {error_html}
        <input type="password" name="password" placeholder="Password" autofocus>
        <button type="submit">View</button>
    </form>
</body>
</html>"""


@app.route("/p/<page_id>/", defaults={"filepath": ""})
@app.route("/p/<page_id>/<path:filepath>")
def serve_page(page_id: str, filepath: str) -> Response:
    """Serve a published page."""
    page = get_page(page_id)
    if not page:
        return make_response("Not found", 404)

    # Check authentication
    cookie_name = f"drop_auth_{page_id}"
    if page["password_hash"]:
        auth_cookie = request.cookies.get(cookie_name)
        if auth_cookie != page["password_hash"]:
            return make_response(_login_form(), 200)

    # Resolve file path
    source = Path(page["source"])

    # Strip name prefix from filepath if present
    page_name = page.get("name", "")
    if page_name and filepath.startswith(page_name + "/"):
        filepath = filepath[len(page_name) + 1:]
    elif page_name and filepath == page_name:
        filepath = ""

    if page["is_dir"]:
        # Directory: serve requested file or index.html
        if not filepath:
            filepath = "index.html"
        # Load manifest for directory
        manifest = load_manifest(source)
        target = safe_path(source, filepath, manifest)
    else:
        # Single file: ignore filepath, no manifest needed
        target = safe_path(source.parent, source.name) if source.exists() else None

    if not target or not target.exists():
        return make_response("Not found", 404)

    if target.is_dir():
        # Try index.html in directory
        index = target / "index.html"
        if index.exists():
            target = index
        else:
            return make_response("Forbidden", 403)

    # Serve file
    mimetype, _ = mimetypes.guess_type(str(target))
    return send_file(target, mimetype=mimetype)


@app.route("/p/<page_id>/", methods=["POST"], defaults={"filepath": ""})
@app.route("/p/<page_id>/<path:filepath>", methods=["POST"])
def auth_page(page_id: str, filepath: str) -> Response:
    """Handle password submission."""
    page = get_page(page_id)
    if not page:
        return make_response("Not found", 404)

    ip = request.remote_addr or "unknown"

    # Check rate limit
    if not _check_rate_limit(ip, page_id):
        return make_response(_login_form("Too many attempts. Try again later."), 429)

    password = request.form.get("password", "")

    if verify_password(password, page["password_hash"]):
        # Success - set cookie and redirect
        response = make_response(_login_form())  # Will be replaced by redirect
        response.status_code = 303
        response.headers["Location"] = request.path
        response.set_cookie(
            f"drop_auth_{page_id}",
            page["password_hash"],
            max_age=COOKIE_TTL,
            httponly=True,
            samesite="Lax",
        )
        return response
    else:
        _record_attempt(ip, page_id)
        return make_response(_login_form("Invalid password"), 401)


@app.route("/")
def index() -> Response:
    """Index page."""
    pages = load_pages()
    if not pages:
        return make_response("No pages published", 200)

    html = "<h1>Published Pages</h1><ul>"
    for page_id in pages:
        html += f'<li><a href="/p/{page_id}/">{page_id}</a></li>'
    html += "</ul>"
    return make_response(html, 200)


def run_server(port: int = 8080, host: str = "0.0.0.0") -> None:
    """Run the Flask server."""
    app.run(host=host, port=port, threaded=True)
