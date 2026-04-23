#!/bin/bash
# Fix OpenProject HTTPS configuration

echo "=========================================="
echo "Fixing OpenProject HTTPS Configuration"
echo "=========================================="

# Check current configuration
echo -e "\n1. Checking current HTTPS setting..."
openproject config:get OPENPROJECT_HTTPS || echo "Not set"

# Set HTTPS mode to true
echo -e "\n2. Setting OPENPROJECT_HTTPS=true..."
openproject config:set OPENPROJECT_HTTPS=true

# Also update the configuration file directly
echo -e "\n3. Updating configuration file..."
if [ ! -f /etc/openproject/conf.d/https ]; then
    echo "Creating /etc/openproject/conf.d/https"
    echo 'OPENPROJECT_HTTPS=true' > /etc/openproject/conf.d/https
else
    echo "Updating /etc/openproject/conf.d/https"
    sed -i 's/OPENPROJECT_HTTPS=.*/OPENPROJECT_HTTPS=true/' /etc/openproject/conf.d/https
fi

# Verify the change
echo -e "\n4. Verifying configuration..."
openproject config:get OPENPROJECT_HTTPS

# Restart OpenProject web service
echo -e "\n5. Restarting OpenProject Puma web service..."
openproject restart web

echo -e "\n=========================================="
echo "Configuration complete!"
echo "OpenProject is now configured for HTTPS"
echo "=========================================="

# Check status
sleep 5
echo -e "\n6. Checking service status..."
openproject run check

echo -e "\nYou can now export work packages as PDF"
echo "Access your project at:"
echo "https://generated-complexity-ireland-fully.trycloudflare.com/projects/odoo19-hr-security-fix"
