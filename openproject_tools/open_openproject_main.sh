#!/bin/bash
# Open OpenProject public URL (root — login / home), not a specific project.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/openproject_public_url.env"
if [[ -f "$ENV_FILE" ]]; then
    # shellcheck source=/dev/null
    source "$ENV_FILE"
fi
BASE="${OPENPROJECT_PUBLIC_BASE_URL:-https://generated-complexity-ireland-fully.trycloudflare.com}"
URL="${BASE%/}/"

echo "Opening OpenProject (main URL):"
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
