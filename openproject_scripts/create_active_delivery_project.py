#!/usr/bin/env python3
"""
OpenProject Active Delivery Project Creator
============================================
Step 1: Update old reference project (ID=7) description
Step 2: Create new active delivery project
Step 3: Create 8 milestones + all child work packages

Run: python3 create_active_delivery_project.py
"""

import sys
import requests
from requests.auth import HTTPBasicAuth

# ─── Config ──────────────────────────────────────────────────────────────────
TOKEN  = "f1336582f568d3dc0c27a938d711c10c5f3cb81366aed6ad27b663dc2a7034b3"
BASE   = "https://generated-complexity-ireland-fully.trycloudflare.com"
AUTH   = HTTPBasicAuth("apikey", TOKEN)
HEADS  = {"Accept": "application/json", "Content-Type": "application/json"}

OLD_PROJECT_ID = 7
OLD_PROJECT_IDENTIFIER = "odoo-fin-cust-p1"

NEW_PROJECT_NAME       = "Odoo Finance Customization Phase 1 - Active Delivery"
NEW_PROJECT_IDENTIFIER = "odoo-fin-p1-delivery"
NEW_PROJECT_DESC       = (
    "This project is dedicated to the active delivery of Phase 1 Odoo finance customizations, "
    "including journal entry enhancements, OCA reporting fixes, analytic project statement reporting, "
    "timesheet-based labor accrual, stock-to-project material reclassification, "
    "and invoice approval workflow with ZATCA gating."
)

# Type IDs from OpenProject
TYPE_MILESTONE   = 2   # isMilestone=True
TYPE_TASK        = 1   # Task
TYPE_SUMMARY     = 3   # Summary task (used for milestone parent WPs)

# Status / Priority
STATUS_NEW       = 1   # New (default)
PRIORITY_HIGH    = 9   # High
PRIORITY_NORMAL  = 8   # Normal (default)

# ─── Results tracking ────────────────────────────────────────────────────────
results = {
    "old_project": {},
    "new_project": {},
    "milestones": [],
    "child_counts": {},
    "errors": [],
    "workarounds": [],
}


def api(method, endpoint, data=None):
    url = f"{BASE}/api/v3{endpoint}"
    try:
        if method == "GET":
            r = requests.get(url, auth=AUTH, headers=HEADS, timeout=30)
        elif method == "POST":
            r = requests.post(url, json=data, auth=AUTH, headers=HEADS, timeout=30)
        elif method == "PATCH":
            r = requests.patch(url, json=data, auth=AUTH, headers=HEADS, timeout=30)
        return r
    except Exception as e:
        print(f"  [NET ERROR] {method} {endpoint}: {e}")
        return None


def get_wp_version(wp_id):
    """Get the current lockVersion of a work package (required for PATCH)."""
    r = api("GET", f"/work_packages/{wp_id}")
    if r and r.status_code == 200:
        return r.json().get("lockVersion", 0)
    return 0


def create_wp(project_id, subject, description="", parent_id=None,
              wp_type=TYPE_TASK, priority=PRIORITY_NORMAL):
    data = {
        "subject": subject,
        "description": {"format": "plain", "raw": description},
        "type": {"href": f"/api/v3/types/{wp_type}"},
        "priority": {"href": f"/api/v3/priorities/{priority}"},
        "status": {"href": f"/api/v3/statuses/{STATUS_NEW}"},
    }
    if parent_id:
        data["parent"] = {"href": f"/api/v3/work_packages/{parent_id}"}

    r = api("POST", f"/projects/{project_id}/work_packages", data)
    if r and r.status_code in (200, 201):
        wp = r.json()
        wp_id = wp.get("id")
        return wp_id
    else:
        err = r.text[:200] if r else "no response"
        print(f"  [ERROR] Failed to create '{subject}': {err}")
        results["errors"].append(f"Failed: '{subject}' — {err}")
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Update old project to mark as reference
# ═══════════════════════════════════════════════════════════════════════════════
def step1_update_old_project():
    print("\n" + "="*70)
    print("STEP 1: Marking old project as reference-only")
    print("="*70)

    # Fetch current project
    r = api("GET", f"/projects/{OLD_PROJECT_ID}")
    if not r or r.status_code != 200:
        msg = f"Could not fetch old project (ID={OLD_PROJECT_ID})"
        print(f"  [WARN] {msg}")
        results["old_project"] = {"status": "fetch_failed", "note": msg}
        results["workarounds"].append(msg)
        return

    old = r.json()
    current_desc = old.get("description", {}).get("raw", "")
    ref_note = (
        "\n\n---\n"
        "NOTE: This project is retained for REFERENCE ONLY. "
        "Active execution continues in: Odoo Finance Customization Phase 1 - Active Delivery "
        f"(identifier: {NEW_PROJECT_IDENTIFIER})"
    )

    if "REFERENCE ONLY" in current_desc:
        print("  ✓ Reference note already present — skipping update")
        results["old_project"] = {
            "id": OLD_PROJECT_ID,
            "identifier": OLD_PROJECT_IDENTIFIER,
            "name": old.get("name"),
            "action": "already_marked_reference",
        }
        return

    new_desc = current_desc + ref_note

    patch_data = {
        "description": {"format": "plain", "raw": new_desc}
    }
    rp = api("PATCH", f"/projects/{OLD_PROJECT_ID}", patch_data)
    if rp and rp.status_code in (200, 201):
        print(f"  ✓ Old project (ID={OLD_PROJECT_ID}) description updated with reference note")
        results["old_project"] = {
            "id": OLD_PROJECT_ID,
            "identifier": OLD_PROJECT_IDENTIFIER,
            "name": old.get("name"),
            "action": "description_updated_with_reference_note",
            "status_change": "none — no archive/on-hold setting applied to avoid visibility loss",
        }
    else:
        err = rp.text[:300] if rp else "no response"
        print(f"  [WARN] Could not update description: {err}")
        results["old_project"] = {
            "id": OLD_PROJECT_ID,
            "name": old.get("name"),
            "action": "description_update_failed",
            "reason": err,
        }
        results["workarounds"].append(
            "Old project description could not be patched. "
            "Manually add reference note in OpenProject UI."
        )


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Create new active delivery project
# ═══════════════════════════════════════════════════════════════════════════════
def step2_create_project():
    print("\n" + "="*70)
    print("STEP 2: Creating new active delivery project")
    print("="*70)

    # Check if name already exists
    r = api("GET", "/projects")
    existing = {p.get("name"): p for p in r.json().get("_embedded", {}).get("elements", [])} if r else {}
    existing_ids = {p.get("identifier"): p for p in existing.values()}

    name = NEW_PROJECT_NAME
    identifier = NEW_PROJECT_IDENTIFIER

    if name in existing:
        name = "Odoo Finance Customization Phase 1 - Execution 2"
        identifier = "odoo-fin-p1-exec2"
        results["workarounds"].append(
            f"Primary name '{NEW_PROJECT_NAME}' already existed. "
            f"Used fallback: '{name}' / '{identifier}'"
        )
        print(f"  [WARN] Name conflict — using fallback: {name}")

    if identifier in existing_ids:
        identifier = identifier + "-a"
        results["workarounds"].append(f"Identifier conflict — appended suffix: {identifier}")

    data = {
        "name": name,
        "identifier": identifier,
        "description": {"format": "plain", "raw": NEW_PROJECT_DESC},
        "public": True,
    }

    r = api("POST", "/projects", data)
    if r and r.status_code in (200, 201):
        proj = r.json()
        pid = proj.get("id")
        print(f"  ✓ Project created: '{name}' (ID={pid}, identifier={identifier})")
        results["new_project"] = {
            "id": pid,
            "name": name,
            "identifier": identifier,
        }
        return pid
    else:
        err = r.text[:400] if r else "no response"
        print(f"  [FATAL] Could not create project: {err}")
        sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Create milestones + all child work packages
# ═══════════════════════════════════════════════════════════════════════════════

# ── Child tasks per milestone ──────────────────────────────────────────────────
MILESTONES = [
    {
        "code": "M0",
        "title": "M0 - Project Setup",
        "description": (
            "Phase 0: Environment validation and scope finalization before development starts.\n"
            "Related request: Pre-requisite for all modules.\n"
            "Must be completed before M1 through M7 begin."
        ),
        "priority": PRIORITY_HIGH,
        "children": [
            "Confirm target Odoo version and installed OCA branches",
            "Confirm module naming convention and repository structure",
            "Create technical design note per module",
            "Define security groups matrix",
            "Prepare staging database for testing",
            "Prepare sample finance test cases and expected outputs",
            "Define journals to be used for R4 and R5",
            "Freeze phase 1 scope versus later enhancements",
        ],
    },
    {
        "code": "M2",
        "title": "M2 - OCA General Ledger Range Fix",
        "description": (
            "R2: Diagnose and fix OCA General Ledger account from/to range filter bug.\n"
            "Approach: Controlled diagnosis → minimal patch → regression tests.\n"
            "Dependency: Staging database from M0."
        ),
        "priority": PRIORITY_HIGH,
        "children": [
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
        ],
    },
    {
        "code": "M1",
        "title": "M1 - Journal Line Reference Extension",
        "description": (
            "R1: Add line_reference, line_reference_number, line_tax_number to account.move.line.\n"
            "Fields are transactional snapshots with partner VAT defaulting.\n"
            "Draft-only edit, post-lock, manager correction action with audit trail."
        ),
        "priority": PRIORITY_HIGH,
        "children": [
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
        ],
    },
    {
        "code": "M6",
        "title": "M6 - Invoice Approval and ZATCA Gate",
        "description": (
            "R6: 3-stage invoice approval: Draft Entry → Under Review → Approved → Sent to ZATCA.\n"
            "Post gated by approval. Send to ZATCA manual button after approved+posted.\n"
            "Material edit reset triggers return to Under Review. Full chatter audit trail."
        ),
        "priority": PRIORITY_NORMAL,
        "children": [
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
        ],
    },
    {
        "code": "M3",
        "title": "M3 - Analytic Project Statement Report",
        "description": (
            "R3: New project-centric analytic statement report.\n"
            "Wizard + on-screen report + XLSX with identical totals.\n"
            "Allocation-aware: one row per move line per analytic allocation slice.\n"
            "Grouped debit-account totals per project."
        ),
        "priority": PRIORITY_NORMAL,
        "children": [
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
        ],
    },
    {
        "code": "M4",
        "title": "M4 - Timesheet Labor Accrual",
        "description": (
            "R4: Monthly labor cost journal posting from approved timesheets.\n"
            "Costing: Employee monthly cost ÷ standard hours → fallback category cost.\n"
            "Dr Direct Wages / Cr WIP. Batch-based, idempotent, duplicate-safe."
        ),
        "priority": PRIORITY_NORMAL,
        "children": [
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
        ],
    },
    {
        "code": "M5",
        "title": "M5 - Stock Project Material Reclassification",
        "description": (
            "R5: Monthly reclassification of material costs to projects at valuation cost.\n"
            "Analytic account captured at stock.move level. Standard valuation engine untouched.\n"
            "Secondary reclassification entry: Dr Direct Materials / Cr Inventory.\n"
            "Fixed monthly grouping: company + period + project + accounts."
        ),
        "priority": PRIORITY_HIGH,
        "children": [
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
        ],
    },
    {
        "code": "M7",
        "title": "M7 - Cross Module Hardening and Delivery",
        "description": (
            "Final integration, cross-module hardening, UAT, and production go-live.\n"
            "Verify no permission conflicts. Finance walkthrough per module.\n"
            "UAT sequence: R2 → R1 → R6 → R3 → R4 → R5. Rollback plans for R4/R5/R6."
        ),
        "priority": PRIORITY_HIGH,
        "children": [
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
        ],
    },
]


def step3_create_structure(project_id):
    print("\n" + "="*70)
    print("STEP 3: Creating milestone parents and child work packages")
    print("="*70)

    for m in MILESTONES:
        print(f"\n  ── {m['code']} ({len(m['children'])} children) ──")

        # Create Milestone marker (isMilestone type)
        m_id = create_wp(
            project_id,
            m["title"],
            m["description"],
            wp_type=TYPE_MILESTONE,
            priority=m["priority"],
        )
        if not m_id:
            results["errors"].append(f"Milestone parent failed: {m['title']}")
            continue        

        print(f"    ✓ Milestone created: {m['title']} (ID={m_id})")
        results["milestones"].append({
            "code": m["code"],
            "title": m["title"],
            "id": m_id,
        })

        # Create child tasks
        child_count = 0
        for task in m["children"]:
            t_id = create_wp(
                project_id,
                task,
                "",
                parent_id=m_id,
                wp_type=TYPE_TASK,
                priority=PRIORITY_NORMAL,
            )
            if t_id:
                child_count += 1
            else:
                results["errors"].append(f"Child failed under {m['code']}: {task}")

        results["child_counts"][m["code"]] = child_count
        print(f"    ✓ Children created: {child_count}/{len(m['children'])}")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    print("\n" + "="*70)
    print("ODOO FINANCE CUSTOMIZATION – ACTIVE DELIVERY PROJECT SETUP")
    print("="*70)

    step1_update_old_project()
    project_id = step2_create_project()
    step3_create_structure(project_id)

    # ── Final Summary ──────────────────────────────────────────────────────
    print("\n\n" + "="*70)
    print("EXECUTION COMPLETE — FINAL SUMMARY")
    print("="*70)

    print("\n1. OLD PROJECT:")
    op = results["old_project"]
    print(f"   Name          : {op.get('name')}")
    print(f"   ID            : {op.get('id')} | {op.get('identifier')}")
    print(f"   Action taken  : {op.get('action')}")
    if op.get("status_change"):
        print(f"   Status change : {op.get('status_change')}")
    if op.get("reason"):
        print(f"   Note          : {op.get('reason')}")

    print("\n2. NEW PROJECT:")
    np = results["new_project"]
    print(f"   Name          : {np.get('name')}")
    print(f"   ID            : {np.get('id')}")
    print(f"   Identifier    : {np.get('identifier')}")
    print(f"   URL           : {BASE}/projects/{np.get('identifier')}")

    print("\n3. MILESTONES CREATED:")
    total_children = 0
    for m in results["milestones"]:
        count = results["child_counts"].get(m["code"], 0)
        total_children += count
        print(f"   {m['code']} : ID={m['id']} | {m['title']} | {count} children")

    print(f"\n   Total milestones : {len(results['milestones'])}")
    print(f"   Total children   : {total_children}")
    print(f"   Total WPs created: {len(results['milestones']) + total_children}")

    print("\n4. ERRORS / FAILED ITEMS:")
    if results["errors"]:
        for e in results["errors"]:
            print(f"   ✗ {e}")
    else:
        print("   ✓ None — all items created successfully")

    print("\n5. WORKAROUNDS USED:")
    if results["workarounds"]:
        for w in results["workarounds"]:
            print(f"   → {w}")
    else:
        print("   None required")

    print("\n6. RECOMMENDATIONS:")
    print("   → Set due dates on milestones after team kickoff")
    print("   → Assign owners to M0 first before other milestones")
    print("   → Use 'In progress' status when work starts on each child task")
    print("   → Keep old project (ID=7) visible for reference; do not delete")
    print("   → Review M5 FIFO/AVCO test tasks with inventory team before starting")

    print(f"\n   Access new project: {BASE}/projects/{np.get('identifier')}")
    print("   Login: admin / admin")
    print("\n" + "="*70)


if __name__ == "__main__":
    main()
