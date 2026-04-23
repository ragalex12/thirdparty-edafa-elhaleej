#!/bin/bash
# Get Cloudflare Tunnel URL from log file

LOG_FILE="/var/log/cloudflared.log"

if [ ! -f "$LOG_FILE" ]; then
    echo "ERROR: Cloudflared log file not found at $LOG_FILE"
    echo "Tunnel may not be running. Start it with:"
    echo "  nohup cloudflared tunnel --url http://127.0.0.1:8088 --no-autoupdate > /var/log/cloudflared.log 2>&1 &"
    exit 1
fi

# Extract the tunnel URL
TUNNEL_URL=$(grep -oP 'https://[a-z0-9-]+\.trycloudflare\.com' "$LOG_FILE" | tail -1)

if [ -z "$TUNNEL_URL" ]; then
    echo "ERROR: No tunnel URL found in log file"
    echo "Check if cloudflared is running:"
    echo "  pgrep -a cloudflared"
    exit 1
fi

echo "============================================"
echo "OpenProject is accessible at:"
echo ""
echo "  $TUNNEL_URL"
echo ""
echo "Your HR Security project:"
echo "  $TUNNEL_URL/projects/odoo19-hr-security-fix"
echo ""
echo "All projects:"
echo "  $TUNNEL_URL/projects"
echo "============================================"
