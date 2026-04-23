#!/bin/bash
################################################################################
# One-Time Setup Script
# Run this once to set up workspace and create permanent aliases
################################################################################

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  OpenProject Workspace - One-Time Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 1: Organize workspace
echo "[1/3] Organizing workspace files..."
bash /opt/localaddons/openproject_tools/organize_workspace.sh

# Step 2: Clean temporary files
echo ""
echo "[2/3] Cleaning temporary files..."
bash /opt/localaddons/openproject_tools/cleanup_temp_files.sh

# Step 3: Add aliases to bashrc
echo ""
echo "[3/3] Setting up permanent aliases..."

BASHRC="$HOME/.bashrc"
ALIAS_LINE="source /opt/localaddons/openproject_tools/openproject_aliases.sh"

if grep -q "openproject_aliases.sh" "$BASHRC" 2>/dev/null; then
    sed -i 's|source /opt/localaddons/openproject_aliases.sh|source /opt/localaddons/openproject_tools/openproject_aliases.sh|g' "$BASHRC"
    sed -i 's|source /opt/localaddons/openproject_tools/openproject_aliases.sh|source /opt/localaddons/openproject_tools/openproject_aliases.sh|g' "$BASHRC"
    echo "✓ Aliases path verified in ~/.bashrc"
else
    echo "" >> "$BASHRC"
    echo "# OpenProject quick commands" >> "$BASHRC"
    echo "$ALIAS_LINE" >> "$BASHRC"
    echo "✓ Added aliases to ~/.bashrc"
fi

# Load aliases now
source /opt/localaddons/openproject_tools/openproject_aliases.sh

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Setup Complete! 🎉"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Quick Commands Available:"
echo "  openproject         - Open OpenProject in browser"
echo "  op                  - Short alias for openproject"
echo "  op-status           - Check service status"
echo "  op-help             - View workspace guide"
echo ""
echo "To use the aliases now in THIS terminal, run:"
echo "  source ~/.bashrc"
echo ""
echo "Next time you open a terminal, they'll work automatically!"
echo ""
echo "To open OpenProject now, run:"
echo "  bash /opt/localaddons/open_openproject.sh"
echo ""
