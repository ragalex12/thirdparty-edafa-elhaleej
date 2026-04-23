#!/bin/bash
# Find and fix all HTTPS configuration issues

echo "=== Checking ALL OpenProject config files ==="
echo ""

echo "File: /etc/openproject/conf.d/server"
grep -i https /etc/openproject/conf.d/server 2>&1 || echo "No HTTPS setting found"

echo ""
echo "File: /etc/openproject/conf.d/https"
cat /etc/openproject/conf.d/https 2>&1 || echo "File doesn't exist"

echo ""
echo "All files in /etc/openproject/conf.d/:"
ls -la /etc/openproject/conf.d/ 2>&1

echo ""
echo "=== FIXING HTTPS Configuration ==="
echo ""

# Update server file to include HTTPS=true
echo "1. Updating /etc/openproject/conf.d/server..."
if grep -q "OPENPROJECT_HTTPS" /etc/openproject/conf.d/server; then
    # Replace existing line
    sed -i 's/^OPENPROJECT_HTTPS=.*/OPENPROJECT_HTTPS=true/' /etc/openproject/conf.d/server
    echo "   Updated existing HTTPS line"
else
    # Add new line
    echo 'OPENPROJECT_HTTPS=true' >> /etc/openproject/conf.d/server
    echo "   Added new HTTPS line"
fi

# Also create dedicated https file
echo ""
echo "2. Creating /etc/openproject/conf.d/https..."
cat > /etc/openproject/conf.d/https << 'EOF'
OPENPROJECT_HTTPS=true
EOF
echo "   Created https config file"

# Set via openproject command
echo ""
echo "3. Setting via openproject config command..."
openproject config:set OPENPROJECT_HTTPS=true

echo ""
echo "=== Verification ==="
echo ""
echo "openproject config:get OPENPROJECT_HTTPS:"
openproject config:get OPENPROJECT_HTTPS

echo ""
echo "Contents of /etc/openproject/conf.d/server:"
grep -i https /etc/openproject/conf.d/server

echo ""
echo "Contents of /etc/openproject/conf.d/https:"
cat /etc/openproject/conf.d/https

echo ""
echo "=== Restarting Puma ==="
pkill -9 -f puma
sleep 2
nohup openproject run web > /tmp/openproject_web_new.log 2>&1 &
echo "Puma restarted. Waiting 15 seconds..."
sleep 15

echo ""
echo "=== Testing ==="
echo "Local test:"
curl -s -o /dev/null -w "HTTP Code: %{http_code}\n" http://127.0.0.1:8090

echo ""
echo "Public test:"
sleep 5
curl -s -o /dev/null -w "HTTP Code: %{http_code}\n" https://generated-complexity-ireland-fully.trycloudflare.com

echo ""
echo "=== DONE ==="
echo "Final HTTPS value: $(openproject config:get OPENPROJECT_HTTPS)"
