#!/usr/bin/env python3
"""
Close M2 — OCA General Ledger Range Fix milestone and all its children.
Posts a structured closure comment on the M2 parent WP.

M2 Parent WP ID: 346 (as created by create_odoo_finance_phase1_project.py)
"""
import json
import time
import requests
from requests.auth import HTTPBasicAuth

TOKEN  = "f1336582f568d3dc0c27a938d711c10c5f3cb81366aed6ad27b663dc2a7034b3"
BASE   = "https://generated-complexity-ireland-fully.trycloudflare.com"
AUTH   = HTTPBasicAuth("apikey", TOKEN)
HEADS  = {"Accept": "application/json", "Content-Type": "application/json"}
G      = {"Accept": "application/json"}

M2_WP_ID = 346   # parent WP for M2

CLOSURE_COMMENT = """\
**M2 — OCA General Ledger Range Fix: Investigation & Test Patch Complete**

**Status:** Test/training environment only | **Date:** April 9, 2026

---

### Root Cause Confirmed

`on_change_account_range()` in the OCA `account_financial_report` module used `int()` type casting for domain bounds:

- **`isdigit()` gate** — silently blocked the filter for any non-numeric account code
- **`int()` cast** — forced integer comparison on `code_store` (Odoo 19 JSONB string field), producing incorrect lexical vs numeric ordering

**Database verified (trgulf_Mrp):** 470 accounts, 469 unique codes, all 6-7 digit numeric — confirming medium real-world impact. No dotted codes found. Two alphanumeric test codes (TCWIP01, TCCLR01) and one duplicate (105001) discovered and resolved.

---

### Files Patched (test/training environment)

| File | Change |
|------|--------|
| `wizard/general_ledger_wizard.py` | Removed `isdigit()` gate; replaced `int()` bounds with string bounds |
| `wizard/aged_partner_balance_wizard.py` | Same fix |
| `wizard/open_items_wizard.py` | Same fix |
| `wizard/trial_balance_wizard.py` | **No change** — already used string bounds correctly |

---

### Validation Completed

- No `TypeError` on range onchange
- `account_ids` populated correctly for numeric and alphanumeric code ranges
- SQL domain and ORM domain results consistent
- Automated regression test added for GL onchange
- Duplicate code `105001` resolved in test DB
- Test accounts `TCCLR01` / `TCWIP01` deactivated

---

### Out of Scope

Lexical vs numeric code ordering semantics (6-digit vs 7-digit accounts, e.g. `999999` vs `TCWIP01` in string sort). Separate product consideration — not a blocker.

---

### Next Step

Production rollout planning and approval required before deploying patch to Gulf_Cons / production instances.
"""

# ─────────────────────────────────────────────────────────────────────────────

def get_statuses():
    r = requests.get(f"{BASE}/api/v3/statuses", auth=AUTH, headers=G, timeout=15)
    r.raise_for_status()
    elements = r.json()["_embedded"]["elements"]
    closed_id = None
    for s in elements:
        if s.get("isClosed", False) or "closed" in s.get("name", "").lower():
            closed_id = s["id"]
            print(f"  [status] Using closed status: '{s['name']}' (id={closed_id})")
            break
    if not closed_id:
        closed_id = elements[-1]["id"]
        print(f"  [status] Fallback closed status id={closed_id}")
    return closed_id


def get_wp(wp_id):
    r = requests.get(f"{BASE}/api/v3/work_packages/{wp_id}", auth=AUTH, headers=G, timeout=15)
    r.raise_for_status()
    return r.json()


def get_children(parent_id):
    """Fetch all children of a WP by filtering on parentId."""
    import urllib.parse
    filters = json.dumps([{"parent": {"operator": "=", "values": [str(parent_id)]}}])
    params = f"?filters={urllib.parse.quote(filters)}&pageSize=100"
    url = f"{BASE}/api/v3/work_packages{params}"
    r = requests.get(url, auth=AUTH, headers=G, timeout=15)
    r.raise_for_status()
    data = r.json()
    return data.get("_embedded", {}).get("elements", [])


def close_wp(wp_id, subject, closed_status_id):
    wp = get_wp(wp_id)
    lock_version = wp.get("lockVersion", 0)
    current_status = wp.get("_links", {}).get("status", {}).get("title", "?")

    if wp.get("_links", {}).get("status", {}).get("id") == closed_status_id:
        print(f"  [skip]  #{wp_id} '{subject[:55]}' — already closed")
        return True

    payload = {
        "lockVersion": lock_version,
        "_links": {
            "status": {"href": f"/api/v3/statuses/{closed_status_id}"}
        }
    }
    r = requests.patch(
        f"{BASE}/api/v3/work_packages/{wp_id}",
        auth=AUTH, headers=HEADS, json=payload, timeout=15
    )
    if r.status_code in (200, 201):
        print(f"  [ok]    #{wp_id} '{subject[:55]}' closed  ({current_status} → closed)")
        return True
    else:
        print(f"  [FAIL]  #{wp_id} '{subject[:55]}' — HTTP {r.status_code}: {r.text[:200]}")
        return False


def post_comment(wp_id, text):
    payload = {
        "comment": {"raw": text}
    }
    r = requests.post(
        f"{BASE}/api/v3/work_packages/{wp_id}/activities",
        auth=AUTH, headers=HEADS, json=payload, timeout=15
    )
    if r.status_code in (200, 201):
        print(f"  [ok]    Comment posted on WP #{wp_id}")
        return True
    else:
        print(f"  [FAIL]  Comment on WP #{wp_id} — HTTP {r.status_code}: {r.text[:300]}")
        return False


# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("CLOSE M2 — OCA GENERAL LEDGER RANGE FIX")
    print("=" * 70)

    # 1. Resolve closed status ID
    print("\n[1/4] Fetching available statuses...")
    closed_status_id = get_statuses()

    # 2. Fetch M2 parent WP
    print(f"\n[2/4] Fetching M2 parent WP #{M2_WP_ID}...")
    parent = get_wp(M2_WP_ID)
    print(f"      Subject : {parent.get('subject', '?')}")
    print(f"      Type    : {parent.get('_links', {}).get('type', {}).get('title', '?')}")
    print(f"      Status  : {parent.get('_links', {}).get('status', {}).get('title', '?')}")

    # 3. Fetch children
    print(f"\n[3/4] Fetching children of WP #{M2_WP_ID}...")
    children = get_children(M2_WP_ID)
    print(f"      Found {len(children)} child work package(s)")

    # Close children first
    closed_ok = 0
    failed = 0
    for child in children:
        cid = child["id"]
        subject = child.get("subject", "?")
        ok = close_wp(cid, subject, closed_status_id)
        if ok:
            closed_ok += 1
        else:
            failed += 1
        time.sleep(0.6)

    # Close parent M2 WP
    print(f"\n  Closing parent M2 WP #{M2_WP_ID}...")
    ok = close_wp(M2_WP_ID, parent.get("subject", "M2 OCA GL Range Fix"), closed_status_id)
    if ok:
        closed_ok += 1
    else:
        failed += 1

    # 4. Post closure comment
    print(f"\n[4/4] Posting closure comment on WP #{M2_WP_ID}...")
    post_comment(M2_WP_ID, CLOSURE_COMMENT)

    print("\n" + "=" * 70)
    print(f"DONE — closed {closed_ok} WP(s), failed {failed}")
    print("=" * 70)


if __name__ == "__main__":
    main()
