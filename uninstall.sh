#!/bin/bash
# Pages Sharing Tool - Uninstall Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
LOCAL_BIN="$HOME/.local/bin"
DEFAULT_SKILLS_ROOT="$(dirname "$SCRIPT_DIR")"
SKILLS_ROOT="${PST_SKILLS_ROOT:-$DEFAULT_SKILLS_ROOT}"

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

# Remove skill
SKILL_DIR="$SKILLS_ROOT/.claude/skills/pages-sharing"
if [ -d "$SKILL_DIR" ]; then
    rm -rf "$SKILL_DIR"
    echo "  ✓ Removed pages-sharing skill"
fi

# Also remove from old location (~/.claude/commands/) if exists
if [ -L "$HOME/.claude/commands/pages-sharing.md" ]; then
    rm "$HOME/.claude/commands/pages-sharing.md"
    echo "  ✓ Removed old command symlink"
fi

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
