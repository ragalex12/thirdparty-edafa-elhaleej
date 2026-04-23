#!/bin/bash
# Complete diagnostic and fix for OpenProject + Cloudflare tunnel

echo "=============================================================="
echo "OpenProject + Cloudflare Tunnel Diagnostic & Fix"
echo "=============================================================="
date
echo ""

# Step 1: Check if Cloudflare tunnel is running
echo "### STEP 1: Checking Cloudflare Tunnel ###"
TUNNEL_COUNT=$(pgrep -fl cloudflared | wc -l)
if [ "$TUNNEL_COUNT" -eq 0 ]; then
    echo "❌ Cloudflare tunnel is NOT running!"
    echo "   Starting Cloudflare tunnel..."
    nohup cloudflared tunnel --url http://127.0.0.1:8090 --no-autoupdate > /var/log/cloudflared.log 2>&1 &
    echo "   Tunnel started. Waiting 10 seconds..."
    sleep 10
    echo "   Checking for tunnel URL..."
    grep "trycloudflare.com" /var/log/cloudflared.log | tail -n 3
else
    echo "✓ Cloudflare tunnel is running (${TUNNEL_COUNT} process(es))"
    pgrep -fl cloudflared
fi
echo ""

# Step 2: Fix HTTPS configuration properly
echo "### STEP 2: Fixing HTTPS Configuration ###"
echo "Current HTTPS value:"
CURRENT=$(openproject config:get OPENPROJECT_HTTPS 2>&1)
echo "  $CURRENT"

echo ""
echo "Setting OPENPROJECT_HTTPS=true (without quotes)..."
openproject config:set OPENPROJECT_HTTPS=true

echo ""
echo "Also setting via environment file..."
mkdir -p /etc/openproject/conf.d
cat > /etc/openproject/conf.d/https << 'EOF'
OPENPROJECT_HTTPS=true
EOF

echo ""
echo "Verifying new value:"
NEW_VALUE=$(openproject config:get OPENPROJECT_HTTPS 2>&1)
echo "  $NEW_VALUE"

if [ "$NEW_VALUE" = "true" ]; then
    echo "✓ HTTPS is now set to: true"
else
    echo "⚠️  WARNING: HTTPS is: $NEW_VALUE"
fi
echo ""

# Step 3: Check OpenProject web service
echo "### STEP 3: Checking OpenProject Web Service ###"
PUMA_COUNT=$(pgrep -fl puma | wc -l)
if [ "$PUMA_COUNT" -eq 0 ]; then
    echo "❌ Puma is NOT running!"
    echo "   Starting OpenProject web service..."
    nohup openproject run web > /tmp/openproject_web.log 2>&1 &
    sleep 15
else
    echo "✓ Puma is running (${PUMA_COUNT} process(es))"
    pgrep -fl puma
fi
echo ""

# Step 4: Test local connection
echo "### STEP 4: Testing Local Connection ###"
echo "Testing http://127.0.0.1:8090 ..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8090 2>&1 || echo "FAILED")
echo "Response code: $HTTP_CODE"

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
    echo "✓ OpenProject is responding locally"
else
    echo "⚠️  OpenProject may not be ready yet (code: $HTTP_CODE)"
fi
echo ""

# Step 5: Check OpenProject logs for errors
echo "### STEP 5: Checking Recent OpenProject Logs ###"
if [ -f /tmp/openproject_web.log ]; then
    echo "Last 20 lines of /tmp/openproject_web.log:"
    tail -n 20 /tmp/openproject_web.log
else
    echo "No web log found at /tmp/openproject_web.log"
fi
echo ""

# Step 6: Check Cloudflare tunnel logs
echo "### STEP 6: Checking Cloudflare Tunnel Logs ###"
if [ -f /var/log/cloudflared.log ]; then
    echo "Last 15 lines of cloudflare log:"
    tail -n 15 /var/log/cloudflared.log
else
    echo "No cloudflare log found"
fi
echo ""

# Step 7: Test the public URL
echo "### STEP 7: Testing Public URL ###"
echo "Waiting 5 seconds for tunnel to stabilize..."
sleep 5

TUNNEL_URL="https://generated-complexity-ireland-fully.trycloudflare.com"
echo "Testing: $TUNNEL_URL"
PUBLIC_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$TUNNEL_URL" 2>&1 || echo "FAILED")
echo "Response code: $PUBLIC_CODE"

if [ "$PUBLIC_CODE" = "200" ] || [ "$PUBLIC_CODE" = "302" ]; then
    echo "✓ Public URL is working!"
elif [ "$PUBLIC_CODE" = "502" ]; then
    echo "❌ Still getting 502 - tunnel or backend issue"
else
    echo "⚠️  Got response code: $PUBLIC_CODE"
fi
echo ""

# Summary
echo "=============================================================="
echo "SUMMARY"
echo "=============================================================="
echo "Cloudflare Tunnel: $([ "$TUNNEL_COUNT" -gt 0 ] && echo 'RUNNING' || echo 'STOPPED')"
echo "Puma Web Service:  $([ "$PUMA_COUNT" -gt 0 ] && echo 'RUNNING' || echo 'STOPPED')"
echo "OPENPROJECT_HTTPS: $NEW_VALUE"
echo "Local Test:        $HTTP_CODE"
echo "Public URL Test:   $PUBLIC_CODE"
echo ""

if [ "$PUBLIC_CODE" = "200" ] || [ "$PUBLIC_CODE" = "302" ]; then
    echo "✅ SUCCESS! OpenProject is accessible at:"
    echo "   $TUNNEL_URL"
    echo ""
    echo "Next steps:"
    echo "  1. Open the URL above in your browser"
    echo "  2. Login to OpenProject"
    echo "  3. Go to: Projects → 'Odoo 19 HR Security Fix'"
    echo "  4. Click 'Work packages' → Show closed filter"
    echo "  5. Click '...' → Export → PDF"
else
    echo "⚠️  Still having issues. Check logs above for errors."
    echo ""
    echo "Try restarting everything:"
    echo "  pkill -9 cloudflared puma"
    echo "  nohup cloudflared tunnel --url http://127.0.0.1:8090 > /var/log/cloudflared.log 2>&1 &"
    echo "  nohup openproject run web > /tmp/openproject_web.log 2>&1 &"
fi
echo "=============================================================="
