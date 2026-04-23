#!/bin/bash
# Complete fix - remove duplicate lines and restart properly

echo "=== STEP 1: Remove ALL HTTPS lines from server config ==="
sed -i '/^OPENPROJECT_HTTPS/d' /etc/openproject/conf.d/server
echo "Old HTTPS lines removed"

echo ""
echo "=== STEP 2: Add ONE correct HTTPS line ==="
echo 'OPENPROJECT_HTTPS=true' >> /etc/openproject/conf.d/server
echo "Added: OPENPROJECT_HTTPS=true"

echo ""
echo "=== STEP 3: Update https config file ==="
echo 'OPENPROJECT_HTTPS=true' > /etc/openproject/conf.d/https
echo "Created /etc/openproject/conf.d/https"

echo ""
echo "=== STEP 4: Verify config files ==="
echo "Server file HTTPS lines:"
grep OPENPROJECT_HTTPS /etc/openproject/conf.d/server
echo ""
echo "HTTPS file contents:"
cat /etc/openproject/conf.d/https
echo ""
echo "openproject config:get OPENPROJECT_HTTPS:"
openproject config:get OPENPROJECT_HTTPS

echo ""
echo "=== STEP 5: Kill all old processes ==="
pkill -9 -f puma
pkill -9 -f rails
sleep 3
echo "Old processes killed"

echo ""
echo "=== STEP 6: Start fresh OpenProject web service ==="
nohup openproject run web > /tmp/openproject_web_final.log 2>&1 &
WEB_PID=$!
echo "Started new web service with PID: $WEB_PID"
echo "Waiting 20 seconds for full startup..."
sleep 20

echo ""
echo "=== STEP 7: Verify processes are running ==="
pgrep -fl puma || echo "WARNING: Puma not running!"

echo ""
echo "=== STEP 8: Test connectivity ==="
echo "Testing local (http://127.0.0.1:8090)..."
LOCAL_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8090)
echo "Local HTTP Code: $LOCAL_CODE"

sleep 5

echo ""
echo "Testing public (https://generated-complexity-ireland-fully.trycloudflare.com)..."
PUBLIC_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://generated-complexity-ireland-fully.trycloudflare.com)
echo "Public HTTP Code: $PUBLIC_CODE"

echo ""
echo "=== STEP 9: Check logs if there are errors ==="
if [ "$LOCAL_CODE" != "200" ] && [ "$LOCAL_CODE" != "302" ]; then
    echo "Local test failed. Last 20 lines of log:"
    tail -n 20 /tmp/openproject_web_final.log
fi

echo ""
echo "================================================================"
echo "FINAL STATUS"
echo "================================================================"
echo "OPENPROJECT_HTTPS = $(openproject config:get OPENPROJECT_HTTPS)"
echo "Local HTTP Code   = $LOCAL_CODE"
echo "Public HTTP Code  = $PUBLIC_CODE"
echo ""

if [ "$PUBLIC_CODE" = "200" ] || [ "$PUBLIC_CODE" = "302" ]; then
    echo "✅ SUCCESS! OpenProject is working!"
    echo ""
    echo "You can now access it at:"
    echo "https://generated-complexity-ireland-fully.trycloudflare.com"
    echo ""
    echo "To export work packages as PDF:"
    echo "1. Login to OpenProject"
    echo "2. Go to Projects → 'Odoo 19 HR Security Fix'"
    echo "3. Click 'Work packages'"
    echo "4. Enable filter 'Show closed' to see all 32 work packages"
    echo "5. Click '...' menu → Export → PDF"
    echo "6. PDF downloads to your browser's Downloads folder"
else
    echo "⚠️  Still having issues"
    echo "Check the log: tail -f /tmp/openproject_web_final.log"
fi
echo "================================================================"
