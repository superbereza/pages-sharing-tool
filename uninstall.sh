#!/bin/bash
# Pages Sharing Tool - Uninstall Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
LOCAL_BIN="$HOME/.local/bin"
CLAUDE_COMMANDS="$HOME/.claude/commands"

echo "📄 Uninstalling Pages Sharing Tool..."

# Stop server if running
if [ -f "$HOME/.pst/server.pid" ]; then
    pid=$(cat "$HOME/.pst/server.pid")
    if kill -0 "$pid" 2>/dev/null; then
        echo "Stopping server..."
        kill "$pid" 2>/dev/null || true
    fi
    rm -f "$HOME/.pst/server.pid"
fi

# Remove command symlink
if [ -L "$LOCAL_BIN/pst" ]; then
    rm "$LOCAL_BIN/pst"
    echo "  ✓ Removed pst command"
fi

# Remove skill symlinks
for skill in "$SCRIPT_DIR/skills/"*.md; do
    if [ -f "$skill" ]; then
        name=$(basename "$skill")
        if [ -L "$CLAUDE_COMMANDS/$name" ]; then
            rm "$CLAUDE_COMMANDS/$name"
            echo "  ✓ Removed $name skill"
        fi
    fi
done

# Remove venv
if [ -d "$VENV_DIR" ]; then
    rm -rf "$VENV_DIR"
    echo "  ✓ Removed venv"
fi

echo ""
echo "📄 Pages Sharing Tool uninstalled!"
echo ""
echo "Note: ~/.pst/ directory preserved (contains your pages config)"
echo "To remove completely: rm -rf ~/.pst"
