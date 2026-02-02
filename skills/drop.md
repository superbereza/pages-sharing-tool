---
name: drop
description: Drop files, apps, or prototypes to your human via drop CLI
---

# Agent Instant Drop

Drop any file, app, or prototype to your human.

## Quick Start

```bash
# Start server (once)
drop start

# Publish a page (public by default)
drop add ./report.html --desc "Weekly report"
# → http://192.168.1.50:8080/p/abc123

# Publish with password
drop add ./secret.html --password --desc "Confidential"
# → http://192.168.1.50:8080/p/def456
# → Password: xK9mP2

# List pages from current directory
drop list

# List all pages
drop list --all

# Remove when done
drop remove abc123

# Stop server
drop stop
```

## Commands

| Command | Description |
|---------|-------------|
| `drop start [--port N]` | Start server (default: 8080) |
| `drop stop` | Stop server |
| `drop status` | Show server URL and all pages |
| `drop add <path>` | Publish file/folder (public by default) |
| `drop list` | List pages from current directory |
| `drop list --all` | List all pages |
| `drop remove <id>` | Remove published page |

## Flags for `drop add`

- `--name "slug"` / `-n "slug"` — human-readable name in URL
- `--desc "text"` / `-d "text"` — description for listing
- `--password` / `-p` — protect with auto-generated password
- `--password <pass>` — protect with custom password
- (no flags) — public access

**URL format:** `http://host:port/p/<secret>/<name>/`

Example:
```bash
drop add ./dist/ --name my-feature --desc "Feature prototype"
# → http://94.131.101.149:8080/p/a8k2m9x4p1n7q3w5/my-feature/
```

## Flags for `drop start`

- `--port <N>` — server port (default: 8080)
- `--host <ip>` — override detected IP

## Examples

```bash
# Public page with description
drop add ./report.html --desc "Q1 Report"

# Auto-generated password
drop add ./secret.html --password --desc "Internal docs"

# Custom password
drop add ./secret.html --password mysecret

# Publish folder (serves index.html)
drop add ./dist/ --desc "Build output"

# Start on different port
drop start --port 9000
```

## Publishing Directories (Manifest Required)

To publish a directory, create `.drop-publish` manifest first:

```bash
# 1. Create manifest with allowed patterns
cat > ./project/.drop-publish << 'EOF'
index.html
assets/**
EOF

# 2. Now publish works
drop add ./project/ --desc "My project"
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

**API calls won't work** — drop is a file server only. If HTML uses `fetch('/api/...')`, either embed mock data or use the actual backend server.

**Single files** work without manifest:
```bash
drop add ./report.html  # OK, no manifest needed
```

## Tips

- **Always `cd` to project first, then `drop add .`** — don't use absolute paths, so `drop list` works correctly
- `drop list` filters by current directory — use in project folder to see only that project's pages
- Server auto-detects external IP for shareable URLs
- Page IDs support partial matching: `drop remove abc` works for `abc123`
- Files are served from original location — updates appear immediately
- Rate limiting: 3 password attempts per minute per IP
