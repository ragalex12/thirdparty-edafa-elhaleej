#!/bin/bash
# Simple HTTPS fix for OpenProject

# Create the HTTPS configuration file
echo "OPENPROJECT_HTTPS=true" | tee /etc/openproject/conf.d/https

# Set via openproject command
openproject config:set OPENPROJECT_HTTPS=true

# Restart web service
openproject restart web

echo "HTTPS configuration applied. Waiting for service to restart..."
sleep 10

echo "Done! OpenProject should now work with HTTPS requests from Cloudflare tunnel"
