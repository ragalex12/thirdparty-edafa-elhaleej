#!/usr/bin/env python3
"""
Verify OpenProject work packages have full descriptions
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

print("="*70)
print("VERIFYING OPENPROJECT WORK PACKAGES")
print("="*70)

# Get project
resp = requests.get(
    f"{OP_URL}/api/v3/projects/odoo19-hr-security-fix",
    auth=AUTH,
    headers=HEADERS,
    timeout=10
)

if not resp.ok:
    print(f"✗ Error getting project: {resp.status_code}")
    exit(1)

project = resp.json()
project_id = project["id"]
print(f"\n✓ Project found: {project['name']} (ID: {project_id})")

# Get all work packages
resp = requests.get(
    f"{OP_URL}/api/v3/projects/{project_id}/work_packages",
    auth=AUTH,
    headers=HEADERS,
    timeout=10
)

if not resp.ok:
    print(f"✗ Error getting work packages: {resp.status_code}")
    exit(1)

wps = resp.json()
work_packages = wps.get("_embedded", {}).get("elements", [])

print(f"\n✓ Found {len(work_packages)} work packages\n")
print("="*70)

# Check each work package
phases = [wp for wp in work_packages if "Phase" in wp.get("subject", "")]
tasks = [wp for wp in work_packages if "Phase" not in wp.get("subject", "")]

print(f"\nPHASES: {len(phases)}")
for phase in sorted(phases, key=lambda x: x.get("id", 0)):
    desc = phase.get("description", {}).get("raw", "")
    desc_length = len(desc)
    has_desc = "✓" if len(desc) > 50 else "✗"
    print(f"  {has_desc} [{phase['id']}] {phase['subject'][:50]}... ({desc_length} chars)")

print(f"\nTASKS: {len(tasks)}")
task_count_with_desc = 0
task_count_without_desc = 0

for task in sorted(tasks, key=lambda x: x.get("id", 0)):
    desc = task.get("description", {}).get("raw", "")
    desc_length = len(desc)
    
    if len(desc) > 50:
        has_desc = "✓"
        task_count_with_desc += 1
    else:
        has_desc = "✗"
        task_count_without_desc += 1
    
    # Show first task in detail as example
    if task["id"] == min(t["id"] for t in tasks):
        print(f"\n  Example Task (first one):")
        print(f"  {has_desc} [{task['id']}] {task['subject']}")
        print(f"  Description length: {desc_length} chars")
        if desc_length > 0:
            print(f"  First 200 chars: {desc[:200]}...")

print(f"\n{'='*70}")
print(f"SUMMARY:")
print(f"  Phases with descriptions: {len([p for p in phases if len(p.get('description', {}).get('raw', '')) > 50])}/{len(phases)}")
print(f"  Tasks with descriptions: {task_count_with_desc}/{len(tasks)}")
print(f"  Tasks WITHOUT descriptions: {task_count_without_desc}/{len(tasks)}")
print(f"{'='*70}")

if task_count_without_desc > 0:
    print(f"\n⚠️  WARNING: {task_count_without_desc} tasks are missing detailed descriptions!")
    print(f"   These should contain findings, code changes, and results.")
else:
    print(f"\n✓ SUCCESS: All work packages have detailed descriptions!")

print(f"\nAccess full project at:")
print(f"https://generated-complexity-ireland-fully.trycloudflare.com/projects/odoo19-hr-security-fix")
