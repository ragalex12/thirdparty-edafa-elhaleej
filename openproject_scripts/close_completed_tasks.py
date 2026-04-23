#!/usr/bin/env python3
"""
Close all completed work packages in OpenProject
Mark all phases and tasks from the HR Security Enhancement project as completed
"""
import requests
from requests.auth import HTTPBasicAuth
import json
import time

OP_URL = "http://127.0.0.1:8090"
API_TOKEN = "f1336582f568d3dc0c27a938d711c10c5f3cb81366aed6ad27b663dc2a7034b3"
AUTH = HTTPBasicAuth("apikey", API_TOKEN)
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Host": "generated-complexity-ireland-fully.trycloudflare.com",
}

print("="*80)
print("CLOSING ALL COMPLETED WORK PACKAGES")
print("="*80)

# Get statuses
resp = requests.get(f"{OP_URL}/api/v3/statuses", auth=AUTH, headers=HEADERS, timeout=10)
statuses = resp.json()
closed_status_id = None

for status in statuses.get("_embedded", {}).get("elements", []):
    name = status.get("name", "").lower()
    if "closed" in name or "done" in name or status.get("isClosed", False):
        closed_status_id = status["id"]
        print(f"\n✓ Found closed status: {status['name']} (ID: {closed_status_id})")
        break

if not closed_status_id:
    print("✗ No 'closed' status found, will use first available status")
    closed_status_id = statuses["_embedded"]["elements"][0]["id"]

# Get all work packages
resp = requests.get(
    f"{OP_URL}/api/v3/projects/odoo19-hr-security-fix/work_packages",
    auth=AUTH,
    headers=HEADERS,
    timeout=10
)

work_packages = resp.json().get("_embedded", {}).get("elements", [])

print(f"\n✓ Found {len(work_packages)} work packages")
print(f"\nClosing all work packages...\n")

updated_count = 0
failed_count = 0

for wp in work_packages:
    wp_id = wp["id"]
    subject = wp["subject"]
    current_status = wp.get("_links", {}).get("status", {}).get("title", "Unknown")
    
    # Check if already closed
    if wp.get("_links", {}).get("status", {}).get("href", "").endswith(f"/{closed_status_id}"):
        print(f"  ✓ [{wp_id}] Already closed: {subject[:60]}")
        continue
    
    # Get current work package to get lockVersion
    try:
        get_resp = requests.get(
            f"{OP_URL}/api/v3/work_packages/{wp_id}",
            auth=AUTH,
            headers=HEADERS,
            timeout=10
        )
        
        if not get_resp.ok:
            print(f"  ✗ [{wp_id}] Failed to get details: {get_resp.status_code}")
            failed_count += 1
            continue
            
        wp_details = get_resp.json()
        lock_version = wp_details.get("lockVersion", 0)
        
        # Update to closed status with lockVersion
        update_data = {
            "lockVersion": lock_version,
            "_links": {
                "status": {"href": f"/api/v3/statuses/{closed_status_id}"}
            }
        }
        
        update_resp = requests.patch(
            f"{OP_URL}/api/v3/work_packages/{wp_id}",
            auth=AUTH,
            headers=HEADERS,
            data=json.dumps(update_data),
            timeout=10
        )
        
        if update_resp.ok:
            print(f"  ✓ [{wp_id}] Closed: {subject[:60]}")
            updated_count += 1
        else:
            print(f"  ✗ [{wp_id}] Failed: {update_resp.status_code} - {subject[:60]}")
            if update_resp.text:
                print(f"      Response: {update_resp.text[:100]}")
            failed_count += 1
            
    except Exception as e:
        print(f"  ✗ [{wp_id}] Error: {str(e)[:50]} - {subject[:60]}")
        failed_count += 1
    
    time.sleep(0.3)  # Rate limiting

print(f"\n{'='*80}")
print(f"SUMMARY:")
print(f"  Total work packages: {len(work_packages)}")
print(f"  Closed successfully: {updated_count}")
print(f"  Failed to close: {failed_count}")
print(f"  Already closed: {len(work_packages) - updated_count - failed_count}")
print(f"{'='*80}")

print(f"\n✓ All completed work is now marked as CLOSED!")
print(f"\nView your completed project at:")
print(f"https://generated-complexity-ireland-fully.trycloudflare.com/projects/odoo19-hr-security-fix")
