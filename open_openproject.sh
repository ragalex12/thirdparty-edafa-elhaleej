#!/bin/bash
################################################################################
# OpenProject Quick Launcher
# Opens the OpenProject HR Security Fix project directly in browser
################################################################################

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration — public URL lives in one place (Cloudflare tunnel → localhost:8090)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/openproject_tools/openproject_public_url.env"
if [[ -f "$ENV_FILE" ]]; then
    # shellcheck source=/dev/null
    source "$ENV_FILE"
fi
OPENPROJECT_PUBLIC_BASE_URL="${OPENPROJECT_PUBLIC_BASE_URL:-https://generated-complexity-ireland-fully.trycloudflare.com}"
OPENPROJECT_DEFAULT_PROJECT="${OPENPROJECT_DEFAULT_PROJECT:-odoo19-finance-acct-master-2026}"
PROJECT_URL="${OPENPROJECT_PUBLIC_BASE_URL}/projects/${OPENPROJECT_DEFAULT_PROJECT}"
OPENPROJECT_PORT=8090

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  OpenProject Quick Launcher"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if Cloudflare tunnel is running
TUNNEL_PID=$(pgrep -f "cloudflared tunnel")
if [ -n "$TUNNEL_PID" ]; then
    echo -e "${GREEN}✓${NC} Cloudflare tunnel is running (PID: $TUNNEL_PID)"
else
    echo -e "${RED}✗${NC} Cloudflare tunnel is NOT running"
    echo -e "${YELLOW}⚠${NC} Starting Cloudflare tunnel..."
    # Uncomment the line below if you want to auto-start the tunnel
    # nohup cloudflared tunnel --url http://localhost:8090 > /tmp/cloudflared.log 2>&1 &
    echo -e "${YELLOW}⚠${NC} Please start Cloudflare tunnel manually or uncomment auto-start in script"
fi

# Check if OpenProject Puma is running
PUMA_PID=$(pgrep -f "puma.*8090")
if [ -n "$PUMA_PID" ]; then
    echo -e "${GREEN}✓${NC} OpenProject Puma web service is running (PID: $PUMA_PID)"
else
    echo -e "${RED}✗${NC} OpenProject Puma web service is NOT running"
    echo -e "${YELLOW}⚠${NC} Starting Puma web service..."
    # Uncomment the line below if you want to auto-start Puma
    # nohup openproject run web > /tmp/openproject_web.log 2>&1 &
    echo -e "${YELLOW}⚠${NC} Please start Puma manually or uncomment auto-start in script"
fi

# Check if local OpenProject is responding
echo ""
echo "Checking OpenProject local service..."
if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:${OPENPROJECT_PORT} | grep -q "302\|200"; then
    echo -e "${GREEN}✓${NC} OpenProject local service is responding"
else
    echo -e "${YELLOW}⚠${NC} OpenProject local service check inconclusive"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}Opening OpenProject in browser...${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Project URL: $PROJECT_URL"
echo "Login: admin / admin"
echo ""

# Open browser
if command -v xdg-open &> /dev/null; then
    xdg-open "$PROJECT_URL" 2>/dev/null
    echo -e "${GREEN}✓${NC} Browser opened successfully"
elif command -v firefox &> /dev/null; then
    firefox "$PROJECT_URL" &
    echo -e "${GREEN}✓${NC} Firefox opened"
elif command -v google-chrome &> /dev/null; then
    google-chrome "$PROJECT_URL" &
    echo -e "${GREEN}✓${NC} Chrome opened"
elif command -v chromium &> /dev/null; then
    chromium "$PROJECT_URL" &
    echo -e "${GREEN}✓${NC} Chromium opened"
else
    echo -e "${YELLOW}⚠${NC} No browser command found. Please open manually:"
    echo "    $PROJECT_URL"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}Done!${NC} OpenProject should now be open in your browser."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
