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
pst add ./report.html --desc "Weekly report"
# → http://192.168.1.50:8080/p/abc123

# Publish with password
pst add ./secret.html --password --desc "Confidential"
# → http://192.168.1.50:8080/p/def456
# → Password: xK9mP2

# List pages from current directory
pst list

# List all pages
pst list --all

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
| `pst status` | Show server URL and all pages |
| `pst add <path>` | Publish file/folder (public by default) |
| `pst list` | List pages from current directory |
| `pst list --all` | List all pages |
| `pst remove <id>` | Remove published page |

## Flags for `pst add`

- `--desc "text"` / `-d "text"` — description (saved in config)
- `--password` / `-p` — protect with auto-generated password
- `--password <pass>` — protect with custom password
- (no flags) — public access

## Flags for `pst start`

- `--port <N>` — server port (default: 8080)
- `--host <ip>` — override detected IP

## Examples

```bash
# Public page with description
pst add ./report.html --desc "Q1 Report"

# Auto-generated password
pst add ./secret.html --password --desc "Internal docs"

# Custom password
pst add ./secret.html --password mysecret

# Publish folder (serves index.html)
pst add ./dist/ --desc "Build output"

# Start on different port
pst start --port 9000
```

## Important: HTML with Assets

If your HTML references relative paths (`./assets/`, `./css/`, `./js/`), **publish the directory, not the file**:

```bash
# ❌ Wrong — CSS/JS won't load
pst add ./index.html

# ✅ Correct — serves index.html with all assets
pst add ./project-folder/
```

Single HTML files only work for standalone pages with inline styles or external CDN links.

## Tips

- `pst list` filters by current directory — use in project folder to see only that project's pages
- Server auto-detects external IP for shareable URLs
- Page IDs support partial matching: `pst remove abc` works for `abc123`
- Files are served from original location — updates appear immediately
- Rate limiting: 3 password attempts per minute per IP
