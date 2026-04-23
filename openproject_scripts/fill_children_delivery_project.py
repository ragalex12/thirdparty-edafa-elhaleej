#!/usr/bin/env python3
"""
Fill all child work packages into the new active delivery project (ID=8).
Steps:
  1. Patch milestone WPs 345-352 from Milestone → Task type (allows children)
  2. Create all 151 child tasks with retry + delay
"""

import time
import requests
from requests.auth import HTTPBasicAuth

TOKEN  = "f1336582f568d3dc0c27a938d711c10c5f3cb81366aed6ad27b663dc2a7034b3"
BASE   = "https://generated-complexity-ireland-fully.trycloudflare.com"
AUTH   = HTTPBasicAuth("apikey", TOKEN)
J      = {"Accept": "application/json", "Content-Type": "application/json"}
G      = {"Accept": "application/json"}

PROJECT_ID = 8
DELAY = 1.2    # seconds between POST calls (avoid rate-limit)
TIMEOUT = 60   # seconds per request


# ── Milestone parents already created ────────────────────────────────────────
# IDs returned from the previous run
MILESTONES = [
    {"code": "M0", "id": 345, "children": [
        "Confirm target Odoo version and installed OCA branches",
        "Confirm module naming convention and repository structure",
        "Create technical design note per module",
        "Define security groups matrix",
        "Prepare staging database for testing",
        "Prepare sample finance test cases and expected outputs",
        "Define journals to be used for R4 and R5",
        "Freeze phase 1 scope versus later enhancements",
    ]},
    {"code": "M2", "id": 346, "children": [
        "Identify exact OCA report module and version",
        "Reproduce issue in staging",
        "Build controlled chart-of-accounts sample",
        "Test with custom overrides enabled and disabled",
        "Document current defect behavior across screen, PDF, and XLSX",
        "Inspect wizard range domain logic",
        "Inspect account ordering and comparison logic",
        "Check export path data source parity",
        "Choose minimal override point",
        "Decide whether local patch or upstream cherry-pick is possible",
        "Implement minimal fix",
        "Add regression test for blank range",
        "Add regression test for same from/to",
        "Add regression test for inclusive boundaries",
        "Add regression test for leading-zero codes",
        "Add regression test for multi-company",
        "Add regression test for export parity",
        "Validate no side effects on other filters",
    ]},
    {"code": "M1", "id": 347, "children": [
        "Add fields on account.move.line",
        "Add tracking and audit support",
        "Add posted-entry correction security",
        "Define correction action and audit note requirement",
        "Add fields to journal item tree and form views",
        "Default line_tax_number from partner VAT if empty",
        "Keep fields editable in draft only",
        "Lock fields after posting for normal users",
        "Add manager-only correction action on posted entries",
        "Add search/filter/group support if needed",
        "Validate export visibility",
        "Test draft edit",
        "Test partner default",
        "Test post-lock behavior",
        "Test manager correction logging",
    ]},
    {"code": "M6", "id": 348, "children": [
        "Add approval fields on account.move",
        "Add approval states",
        "Create or adjust security groups",
        "Map allowed actions per group",
        "Add workflow buttons",
        "Add chatter and audit fields",
        "Add list filters by approval state",
        "Implement rejection reason capture",
        "Enforce reset to review on material changes",
        "Exclude non-material admin notes from reset logic",
        "Log reset reason in chatter",
        "Allow posting only after approval",
        "Allow Send to ZATCA only after approved and posted",
        "Reuse existing ZATCA integration call path",
        "Add retry and failure handling",
        "Log who sent and when",
        "Migrate existing posted invoices to Approved",
        "Migrate draft invoices to Draft Entry",
        "Validate state consistency",
        "Test normal flow",
        "Test reject and resubmit",
        "Test unauthorized action",
        "Test material edit reset",
        "Test ZATCA failure and retry",
    ]},
    {"code": "M3", "id": 349, "children": [
        "Confirm exact report layout with finance",
        "Confirm project subtotal and debit-account grouping logic",
        "Confirm whether only posted entries are included by default",
        "Validate analytic distribution handling on current database",
        "Create report wizard model",
        "Add report filters",
        "Build reporting service and query layer",
        "Implement allocation-slice logic per move line",
        "Build on-screen report with approved column order",
        "Add grouping by project",
        "Add grouped debit-account totals per project",
        "Add totals and subtotals",
        "Add access control by company and analytic visibility",
        "Implement XLSX export with approved layout",
        "Ensure totals match screen output exactly",
        "Add audit columns like move line ID and source debit/credit",
        "Validate export labels if bilingual output is needed",
        "Test single allocation",
        "Test multi-allocation",
        "Test rounding",
        "Test multi-company isolation",
        "Test large dataset sanity",
        "Optimize query if required",
        "Prepare finance reconciliation examples",
    ]},
    {"code": "M4", "id": 350, "children": [
        "Add configuration fields for direct wages and WIP accounts",
        "Confirm exact configuration location on project or analytic context",
        "Confirm employee cost source fields",
        "Build exception handling for missing employee or category cost",
        "Create labor posting batch model",
        "Add timesheet linkage fields",
        "Add batch states",
        "Add audit history view",
        "Select only approved unposted lines for target month",
        "Compute hourly cost from employee monthly cost and standard monthly hours",
        "Apply fallback to employee category cost",
        "Block lines with no cost source and include them in exception report",
        "Generate draft journal entry grouped by company and project",
        "Post only via authorized accounting role",
        "Exclude already posted lines",
        "Make batch posting idempotent",
        "Prevent rerun duplication",
        "Handle edited timesheet after posting through exception or reversal policy",
        "Add reversal path for generated entries",
        "Test approved versus unapproved inclusion",
        "Test rerun behavior",
        "Test missing cost fallback or blocking",
        "Test multi-project month-end batch",
        "Test accounting trace back to source timesheets",
    ]},
    {"code": "M5", "id": 351, "children": [
        "Add analytic/project field on stock.move",
        "Expose field on delivery operation lines where needed",
        "Define defaulting strategy from source document if available",
        "Ensure field is stored and auditable",
        "Read valuation-based amounts from completed stock moves",
        "Identify eligible moves not yet reclassified",
        "Build monthly grouping logic",
        "Link stock moves to generated reclass entry",
        "Create reclassification journal entry",
        "Use valuation-derived cost only",
        "Mark moves as reclassified",
        "Put generated entries in dedicated journal if approved",
        "Prevent duplicate reclassification",
        "Add reclassification batch/log model if needed",
        "Add reversal option for generated batches",
        "Handle partial deliveries and backorders correctly",
        "Validate FIFO and AVCO compatibility",
        "Test single project",
        "Test multiple project lines",
        "Test partial delivery",
        "Test backorder",
        "Test FIFO",
        "Test AVCO",
        "Test rerun prevention",
        "Reconcile reclass totals against stock valuation basis",
        "Validate project reporting visibility",
    ]},
    {"code": "M7", "id": 352, "children": [
        "Standardize audit message style",
        "Standardize manager override pattern",
        "Standardize batch reversal approach for R4 and R5",
        "Validate no permission conflicts across accounting, inventory, and timesheet roles",
        "Add unit and integration tests per module",
        "Add reconciliation tests for R3, R4, and R5",
        "Add workflow permission tests for R6",
        "Prepare finance walkthrough by module",
        "Execute UAT in sequence",
        "Freeze defects",
        "Approve production deployment plan",
        "Prepare rollback plan for R4, R5, and R6",
    ]},
]


def get_lv(wp_id):
    r = requests.get(f"{BASE}/api/v3/work_packages/{wp_id}", auth=AUTH, headers=G, timeout=TIMEOUT)
    return r.json().get("lockVersion", 0) if r.status_code == 200 else 0


def patch_to_task(wp_id):
    lv = get_lv(wp_id)
    data = {"lockVersion": lv, "type": {"href": "/api/v3/types/1"}}
    r = requests.patch(f"{BASE}/api/v3/work_packages/{wp_id}", json=data, auth=AUTH, headers=J, timeout=TIMEOUT)
    return r.status_code in (200, 201)


def create_child(subject, parent_id, retries=3):
    data = {
        "subject": subject,
        "description": {"format": "plain", "raw": ""},
        "type": {"href": "/api/v3/types/1"},
        "priority": {"href": "/api/v3/priorities/8"},
        "status": {"href": "/api/v3/statuses/1"},
        "parent": {"href": f"/api/v3/work_packages/{parent_id}"},
    }
    for attempt in range(retries):
        try:
            r = requests.post(
                f"{BASE}/api/v3/projects/{PROJECT_ID}/work_packages",
                json=data, auth=AUTH, headers=J, timeout=TIMEOUT,
            )
            if r.status_code in (200, 201):
                return r.json().get("id")
            else:
                err = r.text[:200]
                print(f"    [WARN] Attempt {attempt+1}/{retries} failed ({r.status_code}): {err}")
                if attempt < retries - 1:
                    time.sleep(3)
        except Exception as e:
            print(f"    [WARN] Attempt {attempt+1}/{retries} exception: {e}")
            if attempt < retries - 1:
                time.sleep(5)
    return None


def main():
    print("\n" + "="*70)
    print("PHASE A — Patching milestone WPs 345-352 to Task type")
    print("="*70)

    # WP 345 was already patched; patch 346-352
    for m in MILESTONES:
        wp_id = m["id"]
        ok = patch_to_task(wp_id)
        print(f"  {m['code']} (WP {wp_id}): {'✓ Task type' if ok else '✗ patch failed'}")
        time.sleep(0.5)

    print("\n" + "="*70)
    print("PHASE B — Creating 151 child work packages")
    print("="*70)

    total_ok = 0
    total_fail = 0
    child_counts = {}

    for m in MILESTONES:
        print(f"\n  ── {m['code']} (parent ID={m['id']}, {len(m['children'])} tasks) ──")
        ok_count = 0

        for task in m["children"]:
            cid = create_child(task, m["id"])
            if cid:
                ok_count += 1
                total_ok += 1
                print(f"    ✓ {task[:65]} (ID={cid})")
            else:
                total_fail += 1
                print(f"    ✗ FAILED: {task[:65]}")
            time.sleep(DELAY)

        child_counts[m["code"]] = ok_count
        print(f"  → {ok_count}/{len(m['children'])} tasks created for {m['code']}")

    print("\n\n" + "="*70)
    print("PHASE B COMPLETE — SUMMARY")
    print("="*70)
    print(f"\nProject: Odoo Finance Customization Phase 1 - Active Delivery (ID=8)")
    print(f"URL: {BASE}/projects/odoo-fin-p1-delivery")
    print()
    for m in MILESTONES:
        cnt = child_counts.get(m["code"], 0)
        print(f"  {m['code']:3} | Parent WP {m['id']:4} | {cnt:2}/{len(m['children'])} children | {m['code']}")
    print()
    print(f"  Total children created : {total_ok}")
    print(f"  Total children failed  : {total_fail}")
    print(f"  Total WPs in project   : 8 milestones + {total_ok} children = {8 + total_ok}")
    print("="*70)


if __name__ == "__main__":
    main()
