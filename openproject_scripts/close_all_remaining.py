#!/usr/bin/env python3
"""
Close ALL remaining work packages including phases
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
print("CLOSING ALL REMAINING WORK PACKAGES")
print("="*80)

# Get closed status
resp = requests.get(f"{OP_URL}/api/v3/statuses", auth=AUTH, headers=HEADERS, timeout=10)
statuses = resp.json()
closed_status_id = None

for status in statuses.get("_embedded", {}).get("elements", []):
    if status.get("isClosed", False) or "closed" in status.get("name", "").lower():
        closed_status_id = status["id"]
        print(f"\n✓ Using closed status: {status['name']} (ID: {closed_status_id})")
        break

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
    
    data = resp.json()
    wps = data.get("_embedded", {}).get("elements", [])
    
    if not wps:
        break
    
    all_wps.extend(wps)
    offset += len(wps)
    
    if len(wps) < page_size:
        break

print(f"\n✓ Found {len(all_wps)} total work packages")
print(f"\nClosing work packages...\n")

updated_count = 0
already_closed = 0
failed_count = 0

for wp in all_wps:
    wp_id = wp["id"]
    subject = wp["subject"]
    current_status_href = wp.get("_links", {}).get("status", {}).get("href", "")
    
    # Check if already closed
    if current_status_href.endswith(f"/{closed_status_id}"):
        print(f"  ✓ [{wp_id}] Already closed: {subject[:60]}")
        already_closed += 1
        continue
    
    # Get current work package for lockVersion
    try:
        get_resp = requests.get(
            f"{OP_URL}/api/v3/work_packages/{wp_id}",
            auth=AUTH,
            headers=HEADERS,
            timeout=10
        )
        
        if not get_resp.ok:
            print(f"  ✗ [{wp_id}] Failed to get: {get_resp.status_code}")
            failed_count += 1
            continue
            
        wp_details = get_resp.json()
        lock_version = wp_details.get("lockVersion", 0)
        
        # Close it
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
            print(f"  ✓ [{wp_id}] CLOSED: {subject[:60]}")
            updated_count += 1
        else:
            print(f"  ✗ [{wp_id}] Failed ({update_resp.status_code}): {subject[:60]}")
            failed_count += 1
            
    except Exception as e:
        print(f"  ✗ [{wp_id}] Error: {str(e)[:50]}")
        failed_count += 1
    
    time.sleep(0.3)

print(f"\n{'='*80}")
print(f"FINAL SUMMARY:")
print(f"  Total work packages: {len(all_wps)}")
print(f"  Newly closed: {updated_count}")
print(f"  Already closed: {already_closed}")
print(f"  Failed: {failed_count}")
print(f"  Total now closed: {updated_count + already_closed}/{len(all_wps)}")
print(f"{'='*80}")

if updated_count + already_closed == len(all_wps):
    print(f"\n✓ SUCCESS: ALL work packages are now CLOSED!")
else:
    print(f"\n⚠ {len(all_wps) - updated_count - already_closed} work packages still open")

print(f"\nView completed project:")
print(f"https://generated-complexity-ireland-fully.trycloudflare.com/projects/odoo19-hr-security-fix")
