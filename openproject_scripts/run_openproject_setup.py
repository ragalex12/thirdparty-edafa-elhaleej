#!/usr/bin/env python3
"""
Get Cloudflare Tunnel URL and Run OpenProject Creation Script
"""
import os
import sys
import subprocess

# First, get the tunnel URL
tunnel_url = None
try:
    with open('/var/log/cloudflared.log', 'r') as f:
        for line in f:
            if 'trycloudflare.com' in line:
                # Extract URL using simple string parsing
                parts = line.split()
                for part in parts:
                    if 'https://' in part and 'trycloudflare.com' in part:
                        tunnel_url = part.strip()
except FileNotFoundError:
    print("ERROR: /var/log/cloudflared.log not found")
    print("Cloudflare tunnel may not be running.")
    sys.exit(1)

if not tunnel_url:
    print("ERROR: No tunnel URL found in log file")
    print("Start the tunnel with:")
    print("  nohup cloudflared tunnel --url http://127.0.0.1:8088 --no-autoupdate > /var/log/cloudflared.log 2>&1 &")
    sys.exit(1)

print("=" * 60)
print("CLOUDFLARE TUNNEL URL FOUND:")
print(f"  {tunnel_url}")
print("=" * 60)
print()
print("OpenProject Links:")
print(f"  All Projects: {tunnel_url}/projects")
print(f"  HR Security:  {tunnel_url}/projects/odoo19-hr-security-fix")
print()
print("=" * 60)
print()

# Now run the OpenProject creation script
print("Running OpenProject creation script...")
print()

result = subprocess.run(
    [sys.executable, '/opt/localaddons/create_hr_security_project.py'],
    capture_output=True,
    text=True
)

print("STDOUT:")
print(result.stdout)
print()
print("STDERR:")
print(result.stderr)
print()
print(f"Exit Code: {result.returncode}")
print()

if result.returncode == 0:
    print("✓ SUCCESS: OpenProject project created!")
    print(f"✓ Access it at: {tunnel_url}/projects/odoo19-hr-security-fix")
else:
    print("✗ FAILED: Check errors above")

# Write to file as well
with open('/opt/localaddons/openproject_setup_complete.txt', 'w') as f:
    f.write(f"Tunnel URL: {tunnel_url}\n")
    f.write(f"Project URL: {tunnel_url}/projects/odoo19-hr-security-fix\n")
    f.write(f"Exit Code: {result.returncode}\n")
    f.write("\nSTDOUT:\n")
    f.write(result.stdout)
    f.write("\nSTDERR:\n")
    f.write(result.stderr)

print()
print("Results also saved to: /opt/localaddons/openproject_setup_complete.txt")
