#!/usr/bin/env python3
"""
Direct project check and work package listing with all filters
"""
import requests
from requests.auth import HTTPBasicAuth
import json

OP_URL = "http://127.0.0.1:8090"
API_TOKEN = "f1336582f568d3dc0c27a938d711c10c5f3cb81366aed6ad27b663dc2a7034b3"
AUTH = HTTPBasicAuth("apikey", API_TOKEN)
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Host": "generated-complexity-ireland-fully.trycloudflare.com",
}

print("="*80)
print("DIRECT PROJECT AND WORK PACKAGE CHECK")
print("="*80)

# Check if project exists
print("\n1. Checking if project exists...")
resp = requests.get(
    f"{OP_URL}/api/v3/projects/odoo19-hr-security-fix",
    auth=AUTH,
    headers=HEADERS,
    timeout=10
)

if resp.ok:
    project = resp.json()
    print(f"   ✓ Project exists: {project['name']} (ID: {project['id']})")
else:
    print(f"   ✗ Project not found: {resp.status_code}")
    exit(1)

# Try different ways to get work packages
print("\n2. Trying different API endpoints...")

endpoints = [
    f"/projects/{project['id']}/work_packages",
    f"/projects/{project['id']}/work_packages?pageSize=1000",
    f"/projects/odoo19-hr-security-fix/work_packages",
]

for endpoint in endpoints:
    print(f"\n   Trying: {endpoint[:80]}...")
    resp = requests.get(
        f"{OP_URL}/api/v3{endpoint}",
        auth=AUTH,
        headers=HEADERS,
        timeout=10
    )
    
    if resp.ok:
        data = resp.json()
        total = data.get("total", 0)
        count = data.get("count", 0)
        elements = data.get("_embedded", {}).get("elements", [])
        
        print(f"   ✓ Success:")
        print(f"     Total: {total}")
        print(f"     Count: {count}")
        print(f"     Elements: {len(elements)}")
        
        if elements:
            print(f"\n   Work Packages found:")
            for wp in elements[:5]:  # Show first 5
                status = wp.get("_links", {}).get("status", {}).get("title", "Unknown")
                print(f"     - [{wp['id']}] {wp['subject'][:50]} - {status}")
            
            if len(elements) > 5:
                print(f"     ... and {len(elements) - 5} more")
            
            # Count closed
            closed_count = sum(1 for w in elements if "closed" in w.get("_links", {}).get("status", {}).get("title", "").lower())
            print(f"\n   Status summary:")
            print(f"     Total: {len(elements)}")
            print(f"     Closed: {closed_count}")
            print(f"     Open: {len(elements) - closed_count}")
            
            if closed_count == len(elements):
                print(f"\n   ✓ ✓ ✓ ALL WORK PACKAGES ARE CLOSED! ✓ ✓ ✓")
            break
    else:
        print(f"   ✗ Failed: {resp.status_code}")
        print(f"     {resp.text[:200]}")

print(f"\n{'='*80}")
print(f"Access project:")
print(f"https://generated-complexity-ireland-fully.trycloudflare.com/projects/odoo19-hr-security-fix")
print("="*80)
