#!/bin/bash
# Agent Instant Drop - Install Script
# Creates isolated venv and installs skill

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
LOCAL_BIN="$HOME/.local/bin"

# Default skills location - user home directory
SKILLS_ROOT="${DROP_SKILLS_ROOT:-$HOME}"

echo "Installing Agent Instant Drop..."

# Create venv
echo "Creating venv in $VENV_DIR..."
python3 -m venv "$VENV_DIR"

# Install package
echo "Installing package..."
"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install -e "$SCRIPT_DIR" -q

# Create ~/.local/bin if needed
mkdir -p "$LOCAL_BIN"

# Symlink drop command
echo "Creating command symlink in $LOCAL_BIN..."
ln -sf "$VENV_DIR/bin/drop" "$LOCAL_BIN/drop"
echo "  ✓ drop"

# Create skill in .claude/skills/ structure
SKILL_DIR="$SKILLS_ROOT/.claude/skills/drop"
mkdir -p "$SKILL_DIR"

echo "Creating skill in $SKILL_DIR..."
ln -sf "$SCRIPT_DIR/skills/drop.md" "$SKILL_DIR/SKILL.md"
echo "  ✓ drop"

echo ""
echo "Agent Instant Drop installed!"
echo ""
echo "Usage:"
echo "  drop start              # Start server"
echo "  drop add ./file.html    # Publish file"
echo "  drop stop               # Stop server"
echo ""
echo "Skill available for all projects under: $SKILLS_ROOT"
echo ""
echo "To change skill location, set DROP_SKILLS_ROOT before install:"
echo "  DROP_SKILLS_ROOT=/path/to/projects ./install.sh"
echo ""
echo "To uninstall: ./uninstall.sh"
