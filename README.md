# Agent Instant Drop

Drop any file, app, or prototype to your human.

## Install

```bash
git clone https://github.com/superbereza/agent-instant-drop
cd agent-instant-drop
./install.sh
```

Creates isolated venv and symlinks `drop` to `~/.local/bin/`.

## Quick Start

```bash
drop start                    # Start server
drop add ./report.html        # Publish file → get URL
drop add ./dist/              # Publish folder
drop list                     # List pages
drop remove abc123            # Remove page
drop stop                     # Stop server
```

## Features

- Manifest-based security for directories (`.drop-publish`)
- Optional password protection
- Human-readable URLs: `/p/<secret>/<name>/`
- External IP detection for shareable URLs
- Rate limiting (3 attempts/min/IP)

## For Humans

See [docs/README-human.md](docs/README-human.md) for detailed documentation.

## License

MIT
