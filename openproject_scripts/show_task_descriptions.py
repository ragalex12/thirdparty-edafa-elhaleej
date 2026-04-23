#!/usr/bin/env python3
"""Show sample task descriptions from OpenProject to verify full content"""
import requests
from requests.auth import HTTPBasicAuth

OP_URL = "http://127.0.0.1:8090"
API_TOKEN = "f1336582f568d3dc0c27a938d711c10c5f3cb81366aed6ad27b663dc2a7034b3"
AUTH = HTTPBasicAuth("apikey", API_TOKEN)
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Host": "generated-complexity-ireland-fully.trycloudflare.com",
}

# Get work packages for the project
resp = requests.get(
    f"{OP_URL}/api/v3/projects/odoo19-hr-security-fix/work_packages",
    auth=AUTH,
    headers=HEADERS,
    timeout=10
)

if resp.ok:
    wps = resp.json()
    work_packages = wps.get("_embedded", {}).get("elements", [])
    
    print("="*80)
    print("SAMPLE TASK DESCRIPTIONS - Verifying Full Content")
    print("="*80)
    
    # Show first 3 tasks with descriptions
    tasks = [wp for wp in work_packages if "Phase" not in wp.get("subject", "")][:3]
    
    for i, task in enumerate(tasks, 1):
        print(f"\n{'─'*80}")
        print(f"TASK {i}: {task['subject']}")
        print(f"ID: {task['id']}")
        print(f"{'─'*80}")
        
        desc = task.get("description", {}).get("raw", "")
        if desc:
            print(f"\nDESCRIPTION ({len(desc)} characters):")
            print(desc)
        else:
            print("\n⚠️  NO DESCRIPTION FOUND!")
    
    print(f"\n{'='*80}")
    print(f"Total work packages: {len(work_packages)}")
    print(f"Tasks checked: {len(tasks)}")
    print(f"\nFull project at:")
    print(f"https://generated-complexity-ireland-fully.trycloudflare.com/projects/odoo19-hr-security-fix")
    print("="*80)
else:
    print(f"Error: {resp.status_code}")
