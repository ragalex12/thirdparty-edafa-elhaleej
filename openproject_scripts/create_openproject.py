#!/usr/bin/env python3
"""
OpenProject Setup Script
========================
Creates the "Odoo 19 – MRP Timesheet Labor Cost Integration" project
with Work Packages and Tasks via the OpenProject REST API.

Run this script from any machine that can reach the OpenProject server:
    python3 create_openproject.py

Requires: requests  (pip install requests)
"""

import sys
import json
import time
import requests
from requests.auth import HTTPBasicAuth

# ─── Configuration ────────────────────────────────────────────────────────────
OP_URL    = "http://127.0.0.1:8088"
API_TOKEN = "f1336582f568d3dc0c27a938d711c10c5f3cb81366aed6ad27b663dc2a7034b3"
AUTH      = HTTPBasicAuth("apikey", API_TOKEN)
HEADERS   = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Host": "localhost:8088",          # required by OpenProject host validation
}

# ─── Project Definition ───────────────────────────────────────────────────────
PROJECT_NAME       = "Odoo 19 – MRP Timesheet Labor Cost Integration"
PROJECT_IDENTIFIER = "odoo19-mrp-labor-v2"
PROJECT_DESCRIPTION = (
    "Implementation of automatic accounting entries for direct labor cost "
    "from timesheets in Odoo 19 Manufacturing. "
    "Covers WIP/Project Cost Account debit and Labor Clearing/Payroll Accrual "
    "credit entries, fully automated from configuration."
)

# ─── Work Packages & Sub-tasks ────────────────────────────────────────────────
WORK_PACKAGES = [
    {
        "subject": "Step 1 – Add Configuration Fields",
        "description": (
            "Extend res.company, project.project, and mrp.workcenter with new "
            "account fields for WIP debit, Labor Clearing credit, and dedicated "
            "Labor Cost Journal. Keep existing production_labor_expense_account_id "
            "as backward-compatible fallback."
        ),
        "estimated_hours": 4,
        "tasks": [
            {
                "subject": "Add labor_wip_account_id to res.company",
                "description": "Asset account for WIP debit side of labor JE. "
                               "check_company=True. Add @api.constrains to validate account type is asset.",
            },
            {
                "subject": "Add labor_clearing_account_id to res.company",
                "description": "Liability/clearing account for payroll accrual credit. "
                               "Must be liability type – add validation constraint.",
            },
            {
                "subject": "Add labor_cost_journal_id to res.company",
                "description": "Dedicated journal for labor cost entries, separate from stock journal.",
            },
            {
                "subject": "Add overtime_rate_multiplier & holiday_rate_multiplier to res.company",
                "description": "Float fields, defaults 1.5 and 2.0 respectively.",
            },
            {
                "subject": "Add generate_labor_je + account overrides to project.project",
                "description": "Boolean generate_labor_je, optional labor_wip_account_id and "
                               "labor_clearing_account_id overrides at project level.",
            },
            {
                "subject": "Add labor_account_id to mrp.workcenter (optional)",
                "description": "WIP account override at workcenter level for granular cost center mapping.",
            },
            {
                "subject": "Update res_company_views.xml with Labor Cost Accounting group",
                "description": "Show all 4 new account fields in Settings → Manufacturing section "
                               "restricted to group_account_manager.",
            },
        ],
    },
    {
        "subject": "Step 2 – Cost Calculation Logic",
        "description": (
            "Enhance cost computation on account.analytic.line with priority-chain "
            "rate resolution, overtime/holiday multipliers, stored labor_cost field, "
            "and currency conversion support."
        ),
        "estimated_hours": 4,
        "tasks": [
            {
                "subject": "Refactor _resolve_labor_rate() helper",
                "description": "Priority: employee.hourly_cost → employee.timesheet_cost → "
                               "workcenter.costs_hour → product.standard_price.",
            },
            {
                "subject": "Implement _resolve_labor_multiplier() helper",
                "description": "Returns 1.0 (normal), 1.5 (overtime), 2.0 (holiday) "
                               "based on work_status and company config fields.",
            },
            {
                "subject": "Add stored computed field labor_cost on account.analytic.line",
                "description": "stored=True so it is queryable in reports. "
                               "compute='_compute_labor_cost', depends on unit_amount, employee_id, work_status.",
            },
            {
                "subject": "Add currency conversion logic",
                "description": "If employee company currency differs from record company currency, "
                               "apply currency_id._convert() before storing.",
            },
        ],
    },
    {
        "subject": "Step 3 – Accounting Entry Generator",
        "description": (
            "Create _generate_labor_cost_move() — the core JE builder on "
            "account.analytic.line. Implements cascaded account resolution, "
            "analytic_distribution JSON on both move lines, MO/project reference, "
            "and labor_move_id link field."
        ),
        "estimated_hours": 8,
        "tasks": [
            {
                "subject": "Add labor_move_id field to account.analytic.line",
                "description": "Many2one('account.move'), copy=False, readonly=True. "
                               "Links each timesheet line to its labor cost JE.",
            },
            {
                "subject": "Implement _generate_labor_cost_move()",
                "description": "Resolves debit/credit accounts via cascade, builds move_vals, "
                               "creates and posts account.move. Returns move or False if config missing.",
            },
            {
                "subject": "Set analytic_distribution on both JE move lines",
                "description": "In Odoo 19: analytic_distribution = {str(analytic_account_id): 100.0} "
                               "on both debit and credit account.move.line records.",
            },
            {
                "subject": "Set audit trail ref and narration on JE",
                "description": "ref = 'Labor – {MO.name} – {employee.name} – {date}'. "
                               "narration includes hours and rate for audit.",
            },
            {
                "subject": "Implement _reverse_labor_cost_move() helper",
                "description": "Calls labor_move_id._reverse_moves() and clears labor_move_id. "
                               "Used by write() and unlink() overrides.",
            },
            {
                "subject": "Add skip_labor_je context guard",
                "description": "Allow bypassing JE creation during migration/import via "
                               "context.get('skip_labor_je').",
            },
        ],
    },
    {
        "subject": "Step 4 – MO Linkage & Trigger Integration",
        "description": (
            "Override create/write/unlink on account.analytic.line to auto-generate "
            "and reverse labor JEs in real-time. Update _post_inventory on mrp.production "
            "to reconciliation/fallback mode for pre-upgrade lines."
        ),
        "estimated_hours": 12,
        "tasks": [
            {
                "subject": "Verify _post_inventory() hook in Odoo 19 MRP source",
                "description": "SSH to server and grep mrp_production.py for _post_inventory, "
                               "button_mark_done, action_mark_done to confirm correct hook name.",
            },
            {
                "subject": "Override account.analytic.line.create()",
                "description": "After super().create(), call _generate_labor_cost_move() for each "
                               "line where mrp_production_id is set or project.generate_labor_je=True "
                               "and unit_amount > 0.",
            },
            {
                "subject": "Override account.analytic.line.write()",
                "description": "If unit_amount or employee_id changed and labor_move_id exists: "
                               "call _reverse_labor_cost_move() then _generate_labor_cost_move().",
            },
            {
                "subject": "Override account.analytic.line.unlink()",
                "description": "For lines with labor_move_id: call _reverse_labor_cost_move() "
                               "before super().unlink(). Prevent unlink if reversal fails.",
            },
            {
                "subject": "Update mrp.production._post_timesheet_labor_cost_if_any() to reconciliation mode",
                "description": "Find timesheet lines with no labor_move_id (unposted). "
                               "Batch-create JEs for those lines only. Handles pre-upgrade data.",
            },
            {
                "subject": "Write post_init_hook migration for existing posted MOs",
                "description": "Backfill labor_move_id from existing timesheet_labor_move_id "
                               "on MOs with timesheet_cost_posted=True to prevent double-posting.",
            },
        ],
    },
    {
        "subject": "Step 5 – Clearing Account Logic",
        "description": (
            "Implement proper Labor Clearing Account validation, document payroll "
            "reconciliation two-step flow, and coordinate with hr_payroll_account_community."
        ),
        "estimated_hours": 4,
        "tasks": [
            {
                "subject": "Add @api.constrains on labor_clearing_account_id",
                "description": "Validate account is reconcilable and type is liability_current "
                               "or liability_non_current. Raise clear ValidationError if wrong type.",
            },
            {
                "subject": "Document two-step payroll reconciliation flow",
                "description": "Step 1 (this module): DR WIP / CR Labor Clearing. "
                               "Step 2 (payroll): DR Salary Expense / CR Labor Clearing. "
                               "Add to README.md with diagram.",
            },
            {
                "subject": "Coordinate hr_payroll_account_community salary rule",
                "description": "Configure the Direct Labor salary rule to credit "
                               "company.labor_clearing_account_id. Document in setup guide.",
            },
            {
                "subject": "Add clearing account balance check wizard (optional)",
                "description": "Button on company config to show clearing account balance by period. "
                               "Helps accountants verify labor accrual vs payroll posting.",
            },
        ],
    },
    {
        "subject": "Step 6 – Security & Access Rules",
        "description": (
            "Update ir.model.access.csv, add field-level group restrictions, "
            "use sudo() for JE creation, and ensure multi-company record isolation."
        ),
        "estimated_hours": 4,
        "tasks": [
            {
                "subject": "Restrict new account config fields to group_account_manager",
                "description": "Add groups='account.group_account_manager' on labor_wip_account_id, "
                               "labor_clearing_account_id in company views.",
            },
            {
                "subject": "Use sudo() in _generate_labor_cost_move()",
                "description": "MFG users (no accounting access) must be able to log timesheets "
                               "without permission errors. Use self.sudo().env['account.move'].create(...).",
            },
            {
                "subject": "Add explicit sudo() audit logging",
                "description": "Log _logger.info when JE is created via sudo() to maintain "
                               "audit trail of who triggered the entry.",
            },
            {
                "subject": "Verify multi-company record isolation",
                "description": "Ensure labor JEs are created with correct company_id and "
                               "all account fields have check_company=True.",
            },
        ],
    },
    {
        "subject": "Step 7 – Views, Testing & Documentation",
        "description": (
            "Update all UI views, write 7 test scenarios, and update README "
            "with accounting setup guide."
        ),
        "estimated_hours": 8,
        "tasks": [
            {
                "subject": "Update mrp_production_views.xml – smart button & labor_cost column",
                "description": "Add 'Labor JEs' smart button on MO form. "
                               "Add labor_cost column in Timesheets tab tree view.",
            },
            {
                "subject": "Create account_analytic_line_views.xml",
                "description": "New file. Add labor_move_id and labor_cost columns in timesheet "
                               "list view. Add 'View JE' button on timesheet form view.",
            },
            {
                "subject": "Write TC-01: Basic MO timesheet → correct JE accounts",
                "description": "Verify DR WIP = hours×rate, CR Clearing = same. "
                               "Check analytic_distribution on both lines.",
            },
            {
                "subject": "Write TC-02: Overtime multiplier applied correctly",
                "description": "work_status='overtime', verify amount = hours × rate × 1.5.",
            },
            {
                "subject": "Write TC-03: Timesheet edit → JE reversal + recreate",
                "description": "Edit unit_amount; verify old JE reversed, new JE created, "
                               "labor_move_id updated.",
            },
            {
                "subject": "Write TC-04: Missing account config → no JE, no crash",
                "description": "No labor_wip_account_id set; verify no JE, warning logged, "
                               "no UserError raised.",
            },
            {
                "subject": "Write TC-05: Project-based timesheet JE (no MO)",
                "description": "project.generate_labor_je=True; verify JE uses project analytic account.",
            },
            {
                "subject": "Write TC-06: Multi-company JE in correct company",
                "description": "Two companies; verify JE uses correct company's accounts.",
            },
            {
                "subject": "Write TC-07: Delete timesheet → JE reversed",
                "description": "Unlink timesheet line; verify JE reversed and clearing balance = 0.",
            },
            {
                "subject": "Update README.md with accounting setup section",
                "description": "Account type guide, clearing account reconciliation flow, "
                               "multi-company setup, and test run command.",
            },
        ],
    },
]


# ─── API Helpers ──────────────────────────────────────────────────────────────

def api_get(path):
    r = requests.get(f"{OP_URL}/api/v3{path}", auth=AUTH, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.json()


def api_post(path, payload):
    r = requests.post(
        f"{OP_URL}/api/v3{path}",
        auth=AUTH,
        headers=HEADERS,
        data=json.dumps(payload),
        timeout=15,
    )
    if not r.ok:
        print(f"  ✗ POST {path} failed [{r.status_code}]: {r.text[:300]}")
        return None
    return r.json()


def format_description(text):
    return {
        "format": "markdown",
        "raw": text,
    }


# ─── Step 1: Create Project ───────────────────────────────────────────────────

def create_project():
    print(f"\n{'='*60}")
    print(f"  Creating project: {PROJECT_NAME}")
    print(f"{'='*60}")

    payload = {
        "name": PROJECT_NAME,
        "identifier": PROJECT_IDENTIFIER,
        "description": format_description(PROJECT_DESCRIPTION),
        "public": False,
    }
    result = api_post("/projects", payload)
    if not result:
        print("  ✗ Failed to create project. Check if identifier already exists.")
        sys.exit(1)

    project_id = result["id"]
    project_href = result.get("_links", {}).get("self", {}).get("href", "")
    print(f"  ✓ Project created: ID={project_id}  ({project_href})")
    return project_id


# ─── Step 2: Get WP Types ─────────────────────────────────────────────────────

def get_wp_types(project_id):
    """Return dict of type name → href for the project."""
    data = api_get(f"/projects/{project_id}/types")
    types = {}
    for t in data.get("_embedded", {}).get("elements", []):
        types[t["name"].lower()] = t["_links"]["self"]["href"]
    print(f"\n  Available WP types: {list(types.keys())}")
    return types


def pick_type(types, preferred_names):
    """Return the href of the first matching preferred type, or first available."""
    for name in preferred_names:
        if name in types:
            return types[name]
    # fallback: first type available
    return next(iter(types.values())) if types else None


# ─── Step 3: Create Work Packages ─────────────────────────────────────────────

def create_work_package(project_id, wp_type_href, subject, description, estimated_hours, parent_href=None):
    payload = {
        "subject": subject,
        "description": format_description(description),
        "_links": {
            "type": {"href": wp_type_href},
            "project": {"href": f"/api/v3/projects/{project_id}"},
        },
    }
    if estimated_hours:
        payload["estimatedTime"] = f"PT{int(estimated_hours)}H"
    if parent_href:
        payload["_links"]["parent"] = {"href": parent_href}

    result = api_post(f"/projects/{project_id}/work_packages", payload)
    return result


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "="*60)
    print("  OpenProject Setup — Odoo 19 MRP Labor Cost Integration")
    print("="*60)

    # 1. Test connection
    print("\n[1/3] Testing connection to OpenProject...")
    try:
        me = api_get("/users/me")
        print(f"  ✓ Connected as: {me.get('name', '?')} ({me.get('login', '?')})")
    except Exception as e:
        print(f"  ✗ Cannot reach OpenProject at {OP_URL}: {e}")
        print("     Make sure you are running this script from a machine on the same network.")
        sys.exit(1)

    # 2. Create project
    print("\n[2/3] Creating project...")
    project_id = create_project()

    # 3. Get WP types
    print("\n[3/3] Creating Work Packages and Tasks...")
    types = get_wp_types(project_id)
    # Use "summary task" for parent WPs (can have children), "task" for leaves
    phase_type  = pick_type(types, ["summary task", "epic", "feature", "task"])
    task_type   = pick_type(types, ["task", "user story", "bug", "feature", "summary task"])

    total_wp = 0
    total_tasks = 0

    for i, wp_def in enumerate(WORK_PACKAGES, start=1):
        print(f"\n  → WP {i}/7: {wp_def['subject']}")

        wp = create_work_package(
            project_id=project_id,
            wp_type_href=phase_type,
            subject=wp_def["subject"],
            description=wp_def["description"],
            estimated_hours=wp_def.get("estimated_hours", 0),
        )
        if not wp:
            print(f"    ✗ Failed to create WP {i}")
            continue

        wp_id   = wp["id"]
        wp_href = wp["_links"]["self"]["href"]
        total_wp += 1
        print(f"    ✓ Created WP #{wp_id}")

        for j, task_def in enumerate(wp_def.get("tasks", []), start=1):
            time.sleep(0.3)   # gentle rate limiting
            task = create_work_package(
                project_id=project_id,
                wp_type_href=task_type,
                subject=task_def["subject"],
                description=task_def["description"],
                estimated_hours=task_def.get("estimated_hours", 0),
                parent_href=wp_href,
            )
            if task:
                total_tasks += 1
                print(f"      ✓ Task {j}: {task_def['subject'][:55]}…")
            else:
                print(f"      ✗ Failed: {task_def['subject'][:55]}")

        time.sleep(0.5)

    # ─── Summary ──────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  ✓ Done!")
    print(f"  Project  : {PROJECT_NAME}")
    print(f"  URL      : {OP_URL}/projects/{PROJECT_IDENTIFIER}/work_packages")
    print(f"  Work Pkgs: {total_wp} / {len(WORK_PACKAGES)}")
    print(f"  Tasks    : {total_tasks}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
