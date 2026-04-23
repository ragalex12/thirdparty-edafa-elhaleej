#!/bin/bash
# Container-friendly OpenProject web service restart
# (systemctl doesn't work in containers)

echo "==========================================================="
echo "Restarting OpenProject Web Service (Container Method)"
echo "==========================================================="
echo ""

echo "Step 1: Stopping existing Puma processes..."
pkill -9 -u openproject 2>/dev/null || true
pkill -9 -f "rails|puma" 2>/dev/null || true
sleep 2

echo "Step 2: Starting web service..."
nohup openproject run web > /tmp/openproject_web.log 2>&1 &
WEB_PID=$!
echo "Web service started with PID: $WEB_PID"

echo ""
echo "Step 3: Waiting 15 seconds for startup..."
sleep 15

echo ""
echo "Step 4: Checking if Puma is running..."
ps aux | grep -E "puma|openproject" | grep -v grep

echo ""
echo "==========================================================="
echo "✓ Restart complete!"
echo "==========================================================="
echo ""
echo "Verification:"
echo "  OPENPROJECT_HTTPS = $(openproject config:get OPENPROJECT_HTTPS 2>&1)"
echo ""
echo "Next steps:"
echo "  1. Open: https://generated-complexity-ireland-fully.trycloudflare.com"
echo "  2. Login to OpenProject"
echo "  3. Navigate to your project → Work packages"
echo "  4. Enable 'Show closed' filter to see all 32 work packages"
echo "  5. Click '...' menu → Export → PDF"
echo ""
echo "The PDF will download to your browser's Downloads folder"
echo "==========================================================="
