# Agent Instant Drop - Human Documentation

A simple file sharing tool designed for AI agents to share files with humans.

## Why This Exists

When an AI agent builds something (HTML page, prototype, report), it needs a way to share it. Running `python -m http.server` exposes your entire directory and requires manual IP configuration. This tool:

- Publishes only specific files/folders (manifest-based security)
- Optional password protection
- Returns ready-to-share URLs with external IP
- Prevents directory traversal attacks

## Installation

```bash
git clone https://github.com/superbereza/agent-instant-drop
cd agent-instant-drop
./install.sh
```

This creates an isolated Python venv and symlinks `drop` to `~/.local/bin/`.

To uninstall:
```bash
./uninstall.sh
```

## Commands Reference

### Server Management

```bash
drop start              # Start server (default port 8080)
drop start --port 9000  # Start on custom port
drop start --host IP    # Override auto-detected IP
drop stop               # Stop server
drop status             # Show server status and all pages
```

### Publishing

```bash
# Publish a single file (no manifest needed)
drop add ./report.html
drop add ./report.html --password           # With auto-generated password
drop add ./report.html --password secret    # With custom password

# Publish a directory (requires .drop-publish manifest)
drop add ./dist/
drop add ./dist/ --name my-feature          # Human-readable URL slug
drop add ./dist/ --desc "Feature prototype" # Description for listing
```

### Listing and Removing

```bash
drop list         # List pages from current directory
drop list --all   # List all published pages
drop remove abc   # Remove page (partial ID match works)
```

## Directory Publishing

To publish a directory, you must create a `.drop-publish` manifest file:

```bash
# Example manifest
cat > ./project/.drop-publish << 'EOF'
index.html
assets/**
config/**
EOF
```

**Why?** Prevents accidental exposure of `.env`, credentials, and other sensitive files.

**Manifest syntax:**
- `index.html` — exact file
- `assets/**` — directory and all contents
- `*.html` — glob pattern

**Security:** `.env` files are always blocked, even if in manifest (except `.env.example`).

## URL Format

```
http://<host>:<port>/p/<16-char-secret>/<optional-name>/
```

Examples:
- `http://94.131.101.149:8080/p/abc123xyz456mnop/`
- `http://94.131.101.149:8080/p/abc123xyz456mnop/my-feature/`

## Security Features

- Path traversal protection via strict path validation
- Password hashing with SHA-256
- Rate limiting: 3 password attempts per minute per IP
- No directory listing
- Symlink escape prevention
- Manifest-based whitelist for directories
- `.env` files always blocked

## For AI Agents

The main README is designed for AI agents. Install the skill:

```bash
# Creates ~/.claude/skills/drop/SKILL.md
./install.sh
```

Or add to your project's `CLAUDE.md`:

```
This project uses `drop` for secure file sharing. Run `drop --help` for usage.
```

## Configuration

Data stored in `~/.drop/`:
- `pages.json` — published pages registry
- `server.pid` — running server PID
- `port` — configured port
- `host` — configured host override

## License

MIT
