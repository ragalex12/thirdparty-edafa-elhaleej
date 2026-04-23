#!/usr/bin/env python3
"""
Check all work packages including phases
"""
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

# Get ALL work packages with pagination
all_wps = []
offset = 0
page_size = 100

while True:
    resp = requests.get(
        f"{OP_URL}/api/v3/projects/odoo19-hr-security-fix/work_packages?offset={offset}&pageSize={page_size}",
        auth=AUTH,
        headers=HEADERS,
        timeout=10
    )
    
    if not resp.ok:
        print(f"Error: {resp.status_code}")
        break
    
    data = resp.json()
    wps = data.get("_embedded", {}).get("elements", [])
    
    if not wps:
        break
    
    all_wps.extend(wps)
    offset += len(wps)
    
    if len(wps) < page_size:
        break

print("="*80)
print(f"TOTAL WORK PACKAGES: {len(all_wps)}")
print("="*80)

# Separate phases and tasks
phases = []
tasks = []

for wp in all_wps:
    if "Phase" in wp.get("subject", ""):
        phases.append(wp)
    else:
        tasks.append(wp)

print(f"\nPHASES: {len(phases)}")
for phase in sorted(phases, key=lambda x: x.get("id", 0)):
    status = phase.get("_links", {}).get("status", {}).get("title", "Unknown")
    is_closed = "✓" if status.lower() in ["closed", "done"] else "✗"
    print(f"  {is_closed} [{phase['id']}] {phase['subject']} - Status: {status}")

print(f"\nTASKS: {len(tasks)}")
closed_tasks = sum(1 for t in tasks if t.get("_links", {}).get("status", {}).get("title", "").lower() in ["closed", "done"])
print(f"  Closed: {closed_tasks}/{len(tasks)}")

print(f"\n{'='*80}")
print(f"SUMMARY:")
print(f"  Total: {len(all_wps)}")
print(f"  Phases: {len(phases)}")
print(f"  Tasks: {len(tasks)}")
print(f"  Closed phases: {sum(1 for p in phases if p.get('_links', {}).get('status', {}).get('title', '').lower() in ['closed', 'done'])}/{len(phases)}")
print(f"  Closed tasks: {closed_tasks}/{len(tasks)}")
print("="*80)
