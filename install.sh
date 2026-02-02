#!/bin/bash
# Pages Sharing Tool - Install Script
# Creates isolated venv and symlinks commands globally

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
LOCAL_BIN="$HOME/.local/bin"
CLAUDE_COMMANDS="$HOME/.claude/commands"

echo "📄 Installing Pages Sharing Tool..."

# Create venv
echo "Creating venv in $VENV_DIR..."
python3 -m venv "$VENV_DIR"

# Install package
echo "Installing package..."
"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install -e "$SCRIPT_DIR" -q

# Create ~/.local/bin if needed
mkdir -p "$LOCAL_BIN"

# Symlink pst command
echo "Creating command symlink in $LOCAL_BIN..."
ln -sf "$VENV_DIR/bin/pst" "$LOCAL_BIN/pst"
echo "  ✓ pst"

# Create ~/.claude/commands if needed
mkdir -p "$CLAUDE_COMMANDS"

# Symlink skills
echo "Creating skill symlinks in $CLAUDE_COMMANDS..."
for skill in "$SCRIPT_DIR/skills/"*.md; do
    if [ -f "$skill" ]; then
        name=$(basename "$skill")
        ln -sf "$skill" "$CLAUDE_COMMANDS/$name"
        echo "  ✓ $name"
    fi
done

echo ""
echo "📄 Pages Sharing Tool installed!"
echo ""
echo "Usage:"
echo "  pst start              # Start server"
echo "  pst add ./file.html    # Publish file"
echo "  pst stop               # Stop server"
echo ""
echo "Skill available in ~/.claude/commands/"
echo ""
echo "To uninstall: ./uninstall.sh"
