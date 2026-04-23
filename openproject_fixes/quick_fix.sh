#!/bin/bash
# Quick Fix Script - Run this manually

echo "=== FIX STEP 1: Set HTTPS without quotes ==="
openproject config:set OPENPROJECT_HTTPS=true
echo "Verify:"
openproject config:get OPENPROJECT_HTTPS
echo ""

echo "=== FIX STEP 2: Check if Cloudflare tunnel is running ==="
pgrep -fl cloudflared || echo "Tunnel NOT running - starting it..."
echo ""

echo "=== FIX STEP 3: Start Cloudflare tunnel if needed ==="
if ! pgrep -f cloudflared > /dev/null; then
    nohup cloudflared tunnel --url http://127.0.0.1:8090 --no-autoupdate > /var/log/cloudflared.log 2>&1 &
    echo "Tunnel started. Waiting 10 seconds..."
    sleep 10
    tail -n 5 /var/log/cloudflared.log | grep -i trycloudflare || tail -n 10 /var/log/cloudflared.log
fi
echo ""

echo "=== FIX STEP 4: Test local OpenProject ==="
curl -I http://127.0.0.1:8090 2>&1 | head -n 3
echo ""

echo "=== FIX STEP 5: Test public URL ==="
sleep 5
curl -I https://generated-complexity-ireland-fully.trycloudflare.com 2>&1 | head -n 3
echo ""

echo "DONE! If you still see 502, check the logs:"
echo "  tail -f /var/log/cloudflared.log"
echo "  tail -f /tmp/openproject_web.log"
