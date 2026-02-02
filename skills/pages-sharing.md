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

- `--name "slug"` / `-n "slug"` — human-readable name in URL
- `--desc "text"` / `-d "text"` — description for listing
- `--password` / `-p` — protect with auto-generated password
- `--password <pass>` — protect with custom password
- (no flags) — public access

**URL format:** `http://host:port/p/<secret>/<name>/`

Example:
```bash
pst add ./dist/ --name my-feature --desc "Feature prototype"
# → http://94.131.101.149:8080/p/a8k2m9x4p1n7q3w5/my-feature/
```

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

## Publishing Directories (Manifest Required)

To publish a directory, create `.pst-publish` manifest first:

```bash
# 1. Create manifest with allowed patterns
cat > ./project/.pst-publish << 'EOF'
index.html
assets/**
EOF

# 2. Now publish works
pst add ./project/ --desc "My project"
```

**Why manifest?** Prevents accidental exposure of `.env`, config files, etc. Only files matching manifest patterns are served.

**Manifest syntax:**
- `index.html` — exact file
- `assets/**` — directory and all contents
- `*.html` — glob pattern

**Before creating manifest, check what HTML loads:**
```bash
grep -E "src=|href=" index.html | grep -oE '\./[^"'"'"']*' | sort -u
```
Add ALL referenced directories to manifest (assets/, config/, js/, etc.)

**Security:** `.env` files are always blocked, even if in manifest (except `.env.example`).

**API calls won't work** — pst is a file server only. If HTML uses `fetch('/api/...')`, either embed mock data or use the actual backend server.

**Single files** work without manifest:
```bash
pst add ./report.html  # OK, no manifest needed
```

## Tips

- **Always `cd` to project first, then `pst add .`** — don't use absolute paths, so `pst list` works correctly
- `pst list` filters by current directory — use in project folder to see only that project's pages
- Server auto-detects external IP for shareable URLs
- Page IDs support partial matching: `pst remove abc` works for `abc123`
- Files are served from original location — updates appear immediately
- Rate limiting: 3 password attempts per minute per IP
