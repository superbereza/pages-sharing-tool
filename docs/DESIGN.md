# Pages Sharing Tool — Design

## Problem

Need a secure way for AI agents to publish static web pages without accidentally exposing the entire filesystem (like `python -m http.server` does).

## Solution

CLI tool `pst` that:
- Publishes specific files/folders (not everything)
- Password-protects each publication
- Returns full URL with server IP (ready to share)
- Validates paths to prevent directory traversal

## CLI Interface

```bash
pst start [--port 8080]      # Start server
pst stop                      # Stop server
pst status                    # Show server URL + published pages

pst add ./report.html         # Publish file → URL + password
pst add ./dist/               # Publish folder
pst list                      # List all publications
pst remove <id>               # Remove publication
```

### Flags

- `--password <pass>` — custom password (default: auto-generated 6 chars)
- `--no-password` — public access
- `--port <N>` — server port (default: 8080)
- `--host <ip>` — override auto-detected IP

### Output Example

```bash
$ pst start
Server started: http://192.168.1.50:8080

$ pst add ./report.html
Published: http://192.168.1.50:8080/p/abc123
Password: xK9mP2

$ pst status
Server: http://192.168.1.50:8080 (running)

Pages:
  abc123  ./report.html      2 min ago
  def456  ./dist/            1 hour ago
```

## Architecture

### Storage

```
~/.pst/
├── server.pid       # PID of running server
├── port             # Current port number
├── pages.json       # Page registry
└── host             # Cached/configured host IP
```

### pages.json

```json
{
  "abc123": {
    "source": "/home/user/report.html",
    "is_dir": false,
    "password_hash": "sha256:...",
    "created_at": "2026-02-02T10:00:00Z"
  }
}
```

### URL Structure

```
http://<ip>:<port>/p/<page_id>/[filepath]

Examples:
  /p/abc123              → single file or index.html
  /p/abc123/             → directory listing or index.html
  /p/abc123/css/style.css → file within published folder
```

## Authentication Flow

1. User opens `http://ip:8080/p/abc123`
2. Server checks cookie `pst_auth_abc123`
3. No valid cookie → show password form
4. User enters password
5. Correct → set cookie (15 min TTL), show content
6. Wrong → "Invalid password" + rate limit (3 attempts/min/IP)

### Password Form (minimal)

```html
<form method="POST">
  <input type="password" name="password" placeholder="Password">
  <button>View</button>
</form>
```

## Security

### Path Traversal Protection

```python
def safe_path(base: Path, requested: str) -> Path:
    """Resolve path and ensure it's within base directory."""
    full_path = (base / requested).resolve()

    if not full_path.is_relative_to(base.resolve()):
        raise Forbidden("Path traversal attempt")

    # Also check symlinks don't escape
    if full_path.is_symlink():
        target = full_path.resolve()
        if not target.is_relative_to(base.resolve()):
            raise Forbidden("Symlink escapes base directory")

    return full_path
```

### Rate Limiting

- 3 password attempts per minute per IP per page
- Store attempts in memory (resets on server restart)

### No Directory Listing

- If folder has no index.html → 403 (not directory listing)
- Prevents enumeration of files

## IP Detection

Priority:
1. `--host` flag or `~/.pst/host` file
2. External IP via `curl -s ifconfig.me` (with 2s timeout)
3. Local network IP (first non-127.0.0.1 interface)
4. Fallback: `127.0.0.1`

## Project Structure

```
pages-sharing-tool/
├── README.md
├── pyproject.toml
├── docs/
│   └── DESIGN.md
├── skills/
│   └── pages-sharing.md
└── src/
    └── pst/
        ├── __init__.py
        ├── cli.py          # argparse entry point
        ├── server.py       # Flask app + auth
        ├── storage.py      # pages.json CRUD
        └── utils.py        # IP detection, password gen, path validation
```

## Dependencies

- `flask>=3.0` — web server
- Standard library only for everything else

## Skill File

See `skills/pages-sharing.md` — instructions for AI agents on how to use the tool.
