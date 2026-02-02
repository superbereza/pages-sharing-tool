---
name: pages-sharing
description: Publish static pages via pst CLI with optional password protection
---

# Pages Sharing Tool

Publish static HTML pages with optional password protection.

## Quick Start

```bash
# Start server (once)
pst start

# Publish a page (public by default)
pst add ./report.html
# → http://192.168.1.50:8080/p/abc123

# Publish with password
pst add ./secret.html --password
# → http://192.168.1.50:8080/p/def456
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
| `pst add <path>` | Publish file/folder (public by default) |
| `pst list` | List all published pages with URLs |
| `pst remove <id>` | Remove published page |

## Flags for `pst add`

- `--password` — protect with auto-generated password
- `--password <pass>` — protect with custom password
- (no flag) — public access

## Flags for `pst start`

- `--port <N>` — server port (default: 8080)
- `--host <ip>` — override detected IP

## Examples

```bash
# Public page (default)
pst add ./report.html

# Auto-generated password
pst add ./secret.html --password

# Custom password
pst add ./secret.html --password mysecret

# Publish folder (serves index.html)
pst add ./dist/

# Start on different port
pst start --port 9000
```

## Tips

- Server auto-detects external IP for shareable URLs
- Page IDs support partial matching: `pst remove abc` works for `abc123`
- Files are served from original location — updates appear immediately
- Rate limiting: 3 password attempts per minute per IP
