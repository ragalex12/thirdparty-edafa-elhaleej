#!/bin/bash
################################################################################
# OpenProject Quick Commands
# Source this file to get quick aliases: source /opt/localaddons/openproject_tools/openproject_aliases.sh
# Or add to ~/.bashrc: echo "source /opt/localaddons/openproject_tools/openproject_aliases.sh" >> ~/.bashrc
################################################################################

# OpenProject launcher aliases
alias openproject='bash /opt/localaddons/open_openproject.sh'
alias op='bash /opt/localaddons/open_openproject.sh'
alias open-op='bash /opt/localaddons/open_openproject.sh'
# OpenProject public root (login / home), not the default project
alias op-main='bash /opt/localaddons/openproject_tools/open_openproject_main.sh'
# Odoo GPC testing database (trgulf_Mrp) — URL in openproject_public_url.env
alias op-odoo='bash /opt/localaddons/openproject_tools/open_odoo_testing.sh'
alias odoo-test='bash /opt/localaddons/openproject_tools/open_odoo_testing.sh'

# Workspace organization
alias op-organize='bash /opt/localaddons/openproject_tools/organize_workspace.sh'
alias op-cleanup='bash /opt/localaddons/openproject_tools/cleanup_temp_files.sh'
alias op-setup='bash /opt/localaddons/openproject_tools/setup_workspace.sh'

# Quick navigation
alias cdop='cd /opt/localaddons'
alias op-tools='cd /opt/localaddons/openproject_tools 2>/dev/null || cd /opt/localaddons'
alias op-docs='cd /opt/localaddons/openproject_docs 2>/dev/null || cd /opt/localaddons'
alias op-scripts='cd /opt/localaddons/openproject_scripts 2>/dev/null || cd /opt/localaddons'

# Service status checks
alias op-status='pgrep -f "cloudflared|puma" && echo "Services running" || echo "Services need attention"'
alias op-tunnel='pgrep -f cloudflared && echo "Tunnel: Running" || echo "Tunnel: NOT running"'
alias op-puma='pgrep -f puma && echo "Puma: Running" || echo "Puma: NOT running"'

# Documentation quick access
alias op-help='cat /opt/localaddons/WORKSPACE_GUIDE.md | less'
alias op-guide='cat /opt/localaddons/WORKSPACE_GUIDE.md | less'

# Avoid duplicate banners if this file is sourced more than once (e.g. .bashrc + manual source).
if [[ -z "${OPENPROJECT_ALIASES_LOADED:-}" ]]; then
    export OPENPROJECT_ALIASES_LOADED=1
    echo "✓ OpenProject aliases loaded!"
    echo ""
    echo "Available commands (type the name exactly; do not include commas):"
    echo "  openproject           - Open OpenProject (default finance project) in browser"
    echo "  op                    - same as openproject"
    echo "  op-main               - Open OpenProject main URL (login / home)"
    echo "  op-odoo               - Open Odoo testing DB (gpc.odoo.com.se, trgulf_Mrp)"
    echo "  odoo-test             - same as op-odoo"
    echo "  op-organize           - Organize workspace files"
    echo "  op-cleanup            - Clean temporary files"
    echo "  op-setup              - Run one-time workspace setup"
    echo "  op-status             - Check service status"
    echo "  op-help               - View workspace guide"
    echo ""
    echo "To make these permanent, add this to ~/.bashrc:"
    echo "  echo 'source /opt/localaddons/openproject_tools/openproject_aliases.sh' >> ~/.bashrc"
    echo ""
fi
