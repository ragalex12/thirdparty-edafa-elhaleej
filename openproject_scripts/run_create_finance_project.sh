#!/bin/bash
#──────────────────────────────────────────────────────────────────────────────
# OpenProject Finance Customization Phase 1 Project Creator
# Manages execution when Cloudflare tunnel is ready
#──────────────────────────────────────────────────────────────────────────────

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
FINANCE_SCRIPT="$SCRIPT_DIR/create_odoo_finance_phase1_project.py"
TUNNEL_URL="https://generated-complexity-ireland-fully.trycloudflare.com"

echo "═══════════════════════════════════════════════════════════════════════════════"
echo "  OpenProject Finance Customization Phase 1 - Project Creator"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""

# Check if tunnel is ready
echo "⏳ Checking Cloudflare tunnel connectivity..."
if python3 - <<PYEOF 2>/dev/null
import requests
from requests.auth import HTTPBasicAuth
from pathlib import Path
import re
import sys

cfg=Path("$SCRIPT_DIR/create_simple_project.py").read_text()
token=re.search(r'API_TOKEN\s*=\s*"([^"]+)"',cfg).group(1)
try:
    r=requests.get("$TUNNEL_URL/api/v3/projects",auth=HTTPBasicAuth('apikey',token),timeout=10)
    sys.exit(0 if r.status_code in [200,401,403] else 1)
except:
    sys.exit(1)
PYEOF
then
    echo "✓ Cloudflare tunnel is reachable"
    echo ""
    echo "Launching project creation..."
    python3 "$FINANCE_SCRIPT"
    exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo ""
        echo "✓ Project created successfully!"
        echo ""
        echo "Next steps:"
        echo "  1. Open OpenProject: $TUNNEL_URL"
        echo "  2. Login with: admin / admin"
        echo "  3. Navigate to: Projects > Odoo Finance Customization Phase 1"
        echo "  4. Review milestones and work packages"
        echo ""
    fi
    exit $exit_code
else
    echo "✗ Cloudflare tunnel is not responding"
    echo ""
    echo "Status: OpenProject service is currently not accessible"
    echo "URL: $TUNNEL_URL"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check if OpenProject service is running on localhost:8090"
    echo "  2. Verify Cloudflare tunnel is active"
    echo "  3. Check tunnel logs for errors"
    echo ""
    echo "When tunnel is ready, run this script again:"
    echo "  bash $0"
    echo ""
    exit 1
fi
