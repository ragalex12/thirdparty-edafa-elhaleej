#!/bin/bash
# Open Odoo testing database in browser (URL from openproject_public_url.env).

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/openproject_public_url.env"
if [[ -f "$ENV_FILE" ]]; then
    # shellcheck source=/dev/null
    source "$ENV_FILE"
fi
URL="${ODOO_TESTING_WEB_URL:-https://gpc.odoo.com.se/web/login?redirect=%2Fodoo%3Fdb%3Dtrgulf_Mrp}"

echo "Opening Odoo testing database (trgulf_Mrp):"
echo "  $URL"
echo ""

if command -v xdg-open &> /dev/null; then
    xdg-open "$URL" 2>/dev/null && echo "✓ Browser opened."
elif command -v firefox &> /dev/null; then
    firefox "$URL" &
elif command -v google-chrome &> /dev/null; then
    google-chrome "$URL" &
elif command -v chromium &> /dev/null; then
    chromium "$URL" &
else
    echo "No xdg-open/browser found; open this URL manually:"
    echo "  $URL"
    exit 1
fi
