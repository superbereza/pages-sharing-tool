#!/bin/bash
# Pages Sharing Tool - Install Script
# Creates isolated venv and installs skill

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
LOCAL_BIN="$HOME/.local/bin"

# Default skills location - parent of script dir (e.g., /home/user/dev/)
DEFAULT_SKILLS_ROOT="$(dirname "$SCRIPT_DIR")"
SKILLS_ROOT="${PST_SKILLS_ROOT:-$DEFAULT_SKILLS_ROOT}"

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

# Create skill in .claude/skills/ structure
SKILL_DIR="$SKILLS_ROOT/.claude/skills/pages-sharing"
mkdir -p "$SKILL_DIR"

echo "Creating skill in $SKILL_DIR..."
ln -sf "$SCRIPT_DIR/skills/pages-sharing.md" "$SKILL_DIR/SKILL.md"
echo "  ✓ pages-sharing"

echo ""
echo "📄 Pages Sharing Tool installed!"
echo ""
echo "Usage:"
echo "  pst start              # Start server"
echo "  pst add ./file.html    # Publish file"
echo "  pst stop               # Stop server"
echo ""
echo "Skill available for all projects under: $SKILLS_ROOT"
echo ""
echo "To change skill location, set PST_SKILLS_ROOT before install:"
echo "  PST_SKILLS_ROOT=/path/to/projects ./install.sh"
echo ""
echo "To uninstall: ./uninstall.sh"
