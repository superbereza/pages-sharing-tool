---
name: pages-sharing
description: Securely publish static pages with password protection using pst CLI
---

# Pages Sharing Tool

Publish static HTML pages with password protection.

## Quick Start

```bash
# Start server (once)
pst start

# Publish a page
pst add ./report.html
# → http://192.168.1.50:8080/p/abc123
# → Password: xK9mP2

# Check status
pst status

# Remove when done
pst remove abc123

# Stop server
pst stop
```

## Commands

| Command | Description |
|---------|-------------|
| `pst start [--port N]` | Start server (default: 8080) |
| `pst stop` | Stop server |
| `pst status` | Show server URL and published pages |
| `pst add <path>` | Publish file/folder, returns URL + password |
| `pst list` | List all published pages with URLs |
| `pst remove <id>` | Remove published page |

## Flags

- `--password <pass>` — set custom password
- `--no-password` — public access (no password)
- `--port <N>` — server port (default: 8080)
- `--host <ip>` — override detected IP

## Workflow

1. `pst start` — start server (if not running)
2. `pst add ./file.html` — publish, get URL + password
3. Share URL and password with recipient
4. `pst remove <id>` — cleanup when done

## Examples

```bash
# Publish single file
pst add ./report.html

# Publish folder (serves index.html)
pst add ./dist/

# Public page (no password)
pst add ./public-info.html --no-password

# Custom password
pst add ./secret.html --password mysecret

# Start on different port
pst start --port 9000

# Override IP for URL
pst start --host example.com
```

## Tips

- Server auto-detects external IP for shareable URLs
- Page IDs support partial matching: `pst remove abc` works for `abc123`
- Files are served from original location — updates appear immediately
- Rate limiting: 3 password attempts per minute per IP
