#!/usr/bin/env python3
"""
Final comprehensive verification of all work packages
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

print("="*80)
print("FINAL VERIFICATION - ALL WORK PACKAGES STATUS")
print("="*80)

# Try multiple page sizes to ensure we get everything
for page_size in [100, 50, 200]:
    resp = requests.get(
        f"{OP_URL}/api/v3/projects/odoo19-hr-security-fix/work_packages?pageSize={page_size}",
        auth=AUTH,
        headers=HEADERS,
        timeout=10
    )
    
    if resp.ok:
        data = resp.json()
        total = data.get("total", 0)
        wps = data.get("_embedded", {}).get("elements", [])
        
        print(f"\n✓ API Response (pageSize={page_size}):")
        print(f"  Total reported: {total}")
        print(f"  Elements returned: {len(wps)}")
        
        if wps:
            phases = [w for w in wps if "Phase" in w.get("subject", "")]
            tasks = [w for w in wps if "Phase" not in w.get("subject", "")]
            
            print(f"\n  PHASES ({len(phases)}):")
            for p in sorted(phases, key=lambda x: x.get("id", 0)):
                status = p.get("_links", {}).get("status", {}).get("title", "Unknown")
                is_closed = "✓" if "closed" in status.lower() else "✗"
                print(f"    {is_closed} [{p['id']}] {p['subject']} - {status}")
            
            print(f"\n  TASKS ({len(tasks)}):")
            closed_tasks = 0
            for t in sorted(tasks, key=lambda x: x.get("id", 0)):
                status = t.get("_links", {}).get("status", {}).get("title", "Unknown")
                if "closed" in status.lower():
                    closed_tasks += 1
            print(f"    Closed: {closed_tasks}/{len(tasks)}")
            
            # Summary
            total_closed = sum(1 for w in wps if "closed" in w.get("_links", {}).get("status", {}).get("title", "").lower())
            
            print(f"\n  {'='*76}")
            print(f"  SUMMARY:")
            print(f"    Total work packages: {len(wps)}")
            print(f"    Total CLOSED: {total_closed}/{len(wps)}")
            print(f"    Phases closed: {sum(1 for p in phases if 'closed' in p.get('_links', {}).get('status', {}).get('title', '').lower())}/{len(phases)}")
            print(f"    Tasks closed: {closed_tasks}/{len(tasks)}")
            print(f"  {'='*76}")
            
            if total_closed == len(wps):
                print(f"\n  ✓ ✓ ✓ ALL WORK PACKAGES ARE CLOSED! ✓ ✓ ✓")
            else:
                print(f"\n  ⚠ {len(wps) - total_closed} work packages still open")
            
            break
        else:
            print(f"  No work packages returned!")
    else:
        print(f"✗ Error: {resp.status_code}")

print(f"\n{'='*80}")
print(f"Access full project:")
print(f"https://generated-complexity-ireland-fully.trycloudflare.com/projects/odoo19-hr-security-fix")
print("="*80)
