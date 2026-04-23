#!/usr/bin/env python3
"""
OpenProject Project Creator – Odoo Finance Customization Phase 1
=================================================================
Creates comprehensive project tracking Odoo Finance Customization Phase 1 delivery:
- 6 Modules (R1-R6 from approved functional specification)
- 8 Milestones with phase hierarchy
- ~200 Work packages across all modules

Project Structure:
  M0 - Project Setup
  M2 - OCA General Ledger Range Fix
  M1 - Journal Line Reference Extension
  M6 - Invoice Approval and ZATCA Gate
  M3 - Analytic Project Statement Report
  M4 - Timesheet Labor Accrual
  M5 - Stock Project Material Reclassification
  M7 - Cross Module Hardening and Delivery

Run: python3 create_odoo_finance_phase1_project.py
"""

import sys
import json
import re
from pathlib import Path
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta

# ─── Configuration ────────────────────────────────────────────────────────────
# Dynamically detect API token from existing script
CONFIG_FILE = Path(__file__).parent / "create_simple_project.py"
CONFIG_TEXT = CONFIG_FILE.read_text()
API_TOKEN = re.search(r'API_TOKEN\s*=\s*"([^"]+)"', CONFIG_TEXT).group(1)

# Use Cloudflare tunnel URL
OP_URL = "https://generated-complexity-ireland-fully.trycloudflare.com"
AUTH = HTTPBasicAuth("apikey", API_TOKEN)
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}

# ─── Project Definition ───────────────────────────────────────────────────────
PROJECT_NAME = "Odoo Finance Customization Phase 1"
PROJECT_IDENTIFIER = "odoo-fin-cust-p1"
PROJECT_DESCRIPTION = (
    "Phase 1 delivery of 6 approved Odoo functional enhancements:\n"
    "R1: Journal Item Reference Fields\n"
    "R2: OCA General Ledger Range Fix\n"
    "R3: Analytic Project Statement Report\n"
    "R4: Timesheet Labor Accrual\n"
    "R5: Stock Project Material Reclassification\n"
    "R6: Invoice Approval + ZATCA Gate\n\n"
    "Baseline: Approved Functional Specification + Technical Direction (April 9, 2026)"
)

# Default type and priority IDs (will be fetched if needed)
DEFAULT_TYPE_ID = "1"  # Task type, usually 1
DEFAULT_PRIORITY_ID = "2"  # Normal priority


def api_call(method, endpoint, data=None, timeout=30):
    """Make API call to OpenProject."""
    url = f"{OP_URL}/api/v3{endpoint}"
    try:
        if method == "GET":
            resp = requests.get(url, headers=HEADERS, auth=AUTH, timeout=timeout)
        elif method == "POST":
            resp = requests.post(url, json=data, headers=HEADERS, auth=AUTH, timeout=timeout)
        elif method == "PATCH":
            resp = requests.patch(url, json=data, headers=HEADERS, auth=AUTH, timeout=timeout)
        else:
            raise ValueError(f"Unknown method: {method}")

        return resp
    except Exception as e:
        print(f"[ERROR] {method} {endpoint}: {str(e)}")
        return None


def create_project():
    """Create the OpenProject project."""
    print("\n" + "="*80)
    print("Creating OpenProject Project...")
    print("="*80)

    project_data = {
        "name": PROJECT_NAME,
        "identifier": PROJECT_IDENTIFIER,
        "description": PROJECT_DESCRIPTION,
        "public": True,
    }

    resp = api_call("POST", "/projects", project_data)
    if not resp or resp.status_code not in [200, 201]:
        print(f"[ERROR] Failed to create project. Status: {resp.status_code if resp else 'no response'}")
        if resp:
            print(f"  Response: {resp.text[:500]}")
        return None

    project = resp.json().get('_embedded', {}).get('project', {}) or resp.json()
    project_id = project.get('id')
    print(f"✓ Project created: {PROJECT_NAME}")
    print(f"  ID: {project_id}")
    print(f"  Identifier: {PROJECT_IDENTIFIER}")
    return project_id


def create_work_package(project_id, subject, description, parent_id=None, priority=2, estimated_hours=None):
    """Create a work package."""
    wp_data = {
        "subject": subject,
        "description": description,
        "type": {"href": f"/api/v3/types/{DEFAULT_TYPE_ID}"},
        "priority": {"href": f"/api/v3/priorities/{priority}"},
    }

    if parent_id:
        wp_data["parent"] = {"href": f"/api/v3/work_packages/{parent_id}"}

    if estimated_hours:
        wp_data["estimatedTime"] = f"PT{estimated_hours}H"

    resp = api_call("POST", f"/projects/{project_id}/work_packages", wp_data)
    if not resp or resp.status_code not in [200, 201]:
        print(f"[ERROR] Failed to create WP '{subject}'. Status: {resp.status_code if resp else 'none'}")
        if resp:
            print(f"  {resp.text[:300]}")
        return None

    wp = resp.json()
    wp_id = wp.get('id')
    return wp_id


def main():
    """Main execution."""
    try:
        print("\n" + "="*80)
        print("ODOO FINANCE CUSTOMIZATION PHASE 1 PROJECT CREATION")
        print("="*80)
        print(f"\nTarget URL: {OP_URL}")
        print(f"Project: {PROJECT_NAME}")
        print(f"Identifier: {PROJECT_IDENTIFIER}")

        # Create project
        project_id = create_project()
        if not project_id:
            print("\n[FATAL] Failed to create project. Exiting.")
            return 1

        print("\n" + "="*80)
        print("Creating Milestones and Work Packages...")
        print("="*80)

        # ─────────────────────────────────────────────────────────────────────
        # M0: PROJECT SETUP
        # ─────────────────────────────────────────────────────────────────────
        print("\n📋 M0 - Project Setup")
        m0_id = create_work_package(
            project_id,
            "M0 - Project Setup",
            (
                "Phase 0: Project setup and validation.\n\n"
                "Deliverables:\n"
                "- Confirm target Odoo version and installed OCA branches\n"
                "- Confirm module naming convention and repository structure\n"
                "- Create technical design note per module\n"
                "- Define security groups matrix\n"
                "- Prepare staging database for testing\n"
                "- Prepare sample finance test cases and expected outputs\n"
                "- Define journals to be used for R4 and R5\n"
                "- Freeze phase 1 scope versus later enhancements"
            ),
            priority=8,
            estimated_hours=16
        )
        if m0_id:
            for task in [
                ("Confirm target Odoo version and installed OCA branches", 2),
                ("Confirm module naming convention and repository structure", 2),
                ("Create technical design note per module", 3),
                ("Define security groups matrix", 2),
                ("Prepare staging database for testing", 4),
                ("Prepare sample finance test cases and expected outputs", 2),
                ("Define journals to be used for R4 and R5", 1),
                ("Freeze phase 1 scope versus later enhancements", 1),
            ]:
                create_work_package(project_id, task[0], "", parent_id=m0_id, estimated_hours=task[1])

        # ─────────────────────────────────────────────────────────────────────
        # M2: OCA GENERAL LEDGER RANGE FIX
        # ─────────────────────────────────────────────────────────────────────
        print("\n📋 M2 - OCA General Ledger Range Fix")
        m2_id = create_work_package(
            project_id,
            "M2 - OCA General Ledger Range Fix",
            (
                "R2: Fix OCA General Ledger account range filter (from/to).\n\n"
                "Scope:\n"
                "- Diagnosis of range filter defect\n"
                "- Root cause identification\n"
                "- Minimal patch implementation\n"
                "- Comprehensive regression test suite"
            ),
            priority=8,
            estimated_hours=24
        )
        if m2_id:
            tasks = [
                ("Section A – Diagnosis", [
                    ("Identify exact OCA report module and version", 1),
                    ("Reproduce issue in staging", 2),
                    ("Build controlled chart-of-accounts sample", 1),
                    ("Test with custom overrides enabled and disabled", 2),
                    ("Document current defect behavior across screen, PDF, and XLSX", 1),
                ]),
                ("Section B – Root Cause Analysis", [
                    ("Inspect wizard range domain logic", 1),
                    ("Inspect account ordering and comparison logic", 1),
                    ("Check export path data source parity", 1),
                    ("Choose minimal override point", 1),
                    ("Decide whether local patch or upstream cherry-pick is possible", 1),
                ]),
                ("Section C – Implementation and Testing", [
                    ("Implement minimal fix", 2),
                    ("Add regression test for blank range", 1),
                    ("Add regression test for same from/to", 1),
                    ("Add regression test for inclusive boundaries", 1),
                    ("Add regression test for leading-zero codes", 1),
                    ("Add regression test for multi-company", 1),
                    ("Add regression test for export parity", 1),
                    ("Validate no side effects on other filters", 1),
                ]),
            ]
            for section_name, section_tasks in tasks:
                section_id = create_work_package(project_id, section_name, "", parent_id=m2_id, estimated_hours=0)
                if section_id:
                    for task_name, hours in section_tasks:
                        create_work_package(project_id, task_name, "", parent_id=section_id, estimated_hours=hours)

        # ─────────────────────────────────────────────────────────────────────
        # M1: JOURNAL LINE REFERENCE EXTENSION
        # ─────────────────────────────────────────────────────────────────────
        print("\n📋 M1 - Journal Line Reference Extension")
        m1_id = create_work_package(
            project_id,
            "M1 - Journal Line Reference Extension",
            (
                "R1: Add three fields to account.move.line:\n"
                "- line_reference (Text)\n"
                "- line_reference_number (Text)\n"
                "- line_tax_number (Text)\n\n"
                "Features:\n"
                "- Fields editable in draft, read-only after posting\n"
                "- Tax number defaults from partner VAT if empty\n"
                "- Manager correction action for posted entries with audit\n"
                "- Full visibility in views, reports, and exports"
            ),
            priority=8,
            estimated_hours=20
        )
        if m1_id:
            tasks = [
                ("Section A – Data Model", [
                    ("Add fields on account.move.line: line_reference", 1),
                    ("Add fields on account.move.line: line_reference_number", 1),
                    ("Add fields on account.move.line: line_tax_number", 1),
                    ("Add tracking and audit support", 2),
                    ("Add security rule for posted-entry correction by Accounting Manager only", 1),
                    ("Define correction action behavior and audit note requirement", 1),
                ]),
                ("Section B – Views and Defaults", [
                    ("Add fields to journal item tree and form views", 2),
                    ("Default line_tax_number from partner VAT if empty", 1),
                    ("Keep fields editable in draft only", 1),
                    ("Lock fields after posting for normal users", 1),
                    ("Add manager-only correction action on posted entries", 2),
                ]),
                ("Section C – Testing and Visibility", [
                    ("Add fields to search/filter/group if needed", 1),
                    ("Validate export visibility", 1),
                    ("Create tests for draft edit", 1),
                    ("Create tests for partner default", 1),
                    ("Create tests for post-lock behavior", 1),
                    ("Create tests for manager correction logging", 1),
                ]),
            ]
            for section_name, section_tasks in tasks:
                section_id = create_work_package(project_id, section_name, "", parent_id=m1_id, estimated_hours=0)
                if section_id:
                    for task_name, hours in section_tasks:
                        create_work_package(project_id, task_name, "", parent_id=section_id, estimated_hours=hours)

        # ─────────────────────────────────────────────────────────────────────
        # M6: INVOICE APPROVAL AND ZATCA GATE
        # ─────────────────────────────────────────────────────────────────────
        print("\n📋 M6 - Invoice Approval and ZATCA Gate")
        m6_id = create_work_package(
            project_id,
            "M6 - Invoice Approval and ZATCA Gate",
            (
                "R6: Implement 3-stage invoice approval workflow:\n"
                "1. Draft Entry (creation)\n"
                "2. Under Review (reviewer stage)\n"
                "3. Approved (ready to post/send)\n"
                "4. Sent to ZATCA (after posting)\n\n"
                "Controls:\n"
                "- Post blocked unless approved\n"
                "- Send to ZATCA button manual and available only after approved+posted\n"
                "- Material edits reset invoice to Under Review\n"
                "- Full audit trail via chatter"
            ),
            priority=7,
            estimated_hours=28
        )
        if m6_id:
            tasks = [
                ("Section A – States and Permissions", [
                    ("Add approval fields on account.move", 1),
                    ("Add states: draft_entry, under_review, approved, rejected, sent_to_zatca", 2),
                    ("Create or adjust security groups: Invoice Creator, Reviewer, Poster, ZATCA Submitter", 2),
                    ("Map allowed actions per group", 1),
                ]),
                ("Section B – Workflow Controls", [
                    ("Add buttons: Submit, Approve, Reject, Post, Send to ZATCA, Reset to Draft", 2),
                    ("Add chatter and audit fields", 1),
                    ("Add list filters by approval state", 1),
                    ("Implement rejection reason capture", 1),
                ]),
                ("Section C – Material Edit Reset Logic", [
                    ("Define material edits: customer, invoice date, lines, product, qty, price, discount, taxes", 2),
                    ("Define material edits: analytic account, fiscal position, currency, payment terms", 1),
                    ("Exclude non-material admin notes from reset logic", 1),
                    ("Log reset reason in chatter", 1),
                ]),
                ("Section D – Posting and ZATCA Integration", [
                    ("Allow posting only after approval", 1),
                    ("Allow Send to ZATCA only after approved and posted", 1),
                    ("Reuse existing ZATCA integration call path", 2),
                    ("Add retry and failure handling", 2),
                    ("Log who sent and when", 1),
                ]),
                ("Section E – Data Migration and Testing", [
                    ("Migrate existing posted invoices to Approved", 1),
                    ("Migrate draft invoices to Draft Entry", 1),
                    ("Validate state consistency", 1),
                    ("Test normal flow", 2),
                    ("Test reject and resubmit", 1),
                    ("Test unauthorized action", 1),
                    ("Test material edit reset", 2),
                    ("Test ZATCA failure and retry", 2),
                ]),
            ]
            for section_name, section_tasks in tasks:
                section_id = create_work_package(project_id, section_name, "", parent_id=m6_id, estimated_hours=0)
                if section_id:
                    for task_name, hours in section_tasks:
                        create_work_package(project_id, task_name, "", parent_id=section_id, estimated_hours=hours)

        # ─────────────────────────────────────────────────────────────────────
        # M3: ANALYTIC PROJECT STATEMENT REPORT
        # ─────────────────────────────────────────────────────────────────────
        print("\n📋 M3 - Analytic Project Statement Report")
        m3_id = create_work_package(
            project_id,
            "M3 - Analytic Project Statement Report",
            (
                "R3: New analytic project statement report, wizard + on-screen + XLSX.\n\n"
                "Report displays:\n"
                "- Date, Move Number, Project, Lines grouped by project\n"
                "- Project-level debit account totals\n"
                "- Analytic distribution-aware allocation splits\n"
                "- Full on-screen and XLSX outputs with matching totals"
            ),
            priority=7,
            estimated_hours=40
        )
        if m3_id:
            tasks = [
                ("Section A – Requirements and Validation", [
                    ("Confirm exact report layout with finance", 1),
                    ("Confirm project subtotal and debit-account grouping logic", 1),
                    ("Confirm whether only posted entries are included by default", 1),
                    ("Validate analytic distribution handling on current database", 1),
                ]),
                ("Section B – Wizard and Query Layer", [
                    ("Create report wizard model", 2),
                    ("Add filters: date from/to, company, analytic accounts, include draft toggle", 2),
                    ("Build reporting service and query layer", 3),
                    ("Implement allocation-slice logic per move line", 2),
                ]),
                ("Section C – On-Screen Report", [
                    ("Build on-screen report with approved column order", 2),
                    ("Add grouping by project", 1),
                    ("Add grouped debit-account totals per project", 2),
                    ("Add totals and subtotals", 1),
                    ("Add access control by company and analytic visibility", 1),
                ]),
                ("Section D – XLSX Export", [
                    ("Implement XLSX export with approved layout", 2),
                    ("Ensure totals match screen output exactly", 1),
                    ("Add audit columns like move line ID and source debit/credit", 1),
                    ("Validate export labels if bilingual output is needed", 1),
                ]),
                ("Section E – Testing and Optimization", [
                    ("Test single allocation", 1),
                    ("Test multi-allocation", 2),
                    ("Test rounding", 1),
                    ("Test multi-company isolation", 1),
                    ("Test large dataset sanity", 2),
                    ("Optimize query if required", 2),
                    ("Prepare finance reconciliation examples", 2),
                ]),
            ]
            for section_name, section_tasks in tasks:
                section_id = create_work_package(project_id, section_name, "", parent_id=m3_id, estimated_hours=0)
                if section_id:
                    for task_name, hours in section_tasks:
                        create_work_package(project_id, task_name, "", parent_id=section_id, estimated_hours=hours)

        # ─────────────────────────────────────────────────────────────────────
        # M4: TIMESHEET LABOR ACCRUAL
        # ─────────────────────────────────────────────────────────────────────
        print("\n📋 M4 - Timesheet Labor Accrual")
        m4_id = create_work_package(
            project_id,
            "M4 - Timesheet Labor Accrual",
            (
                "R4: Monthly labor cost journal posting from approved timesheets.\n\n"
                "Workflow:\n"
                "- Select approved timesheets by month\n"
                "- Generate draft JE with Dr Wages / Cr WIP\n"
                "- Post only via Accounting Manager authorization\n"
                "- Duplicate prevention via stored reference links\n"
                "- Idempotent batch processing"
            ),
            priority=7,
            estimated_hours=32
        )
        if m4_id:
            tasks = [
                ("Section A – Configuration", [
                    ("Add configuration fields: direct_wages_account_id", 1),
                    ("Add configuration fields: wip_account_id", 1),
                    ("Confirm exact configuration location on project or analytic context", 1),
                    ("Confirm employee cost source fields", 1),
                    ("Build exception handling for missing employee or category cost", 2),
                ]),
                ("Section B – Batch Model and Linkage", [
                    ("Create labor posting batch model", 2),
                    ("Add timesheet linkage fields: posted flag, batch reference, move reference", 2),
                    ("Add batch states", 1),
                    ("Add audit history view", 1),
                ]),
                ("Section C – Batch Processing Logic", [
                    ("Select only approved unposted lines for target month", 2),
                    ("Compute hourly cost from employee monthly cost and standard monthly hours", 2),
                    ("Apply fallback to employee category cost", 1),
                    ("Block lines with no cost source and include them in exception report", 1),
                    ("Generate draft journal entry grouped by company and project", 2),
                    ("Post only via authorized accounting role", 1),
                ]),
                ("Section D – Idempotency and Reversal", [
                    ("Exclude already posted lines", 1),
                    ("Make batch posting idempotent", 2),
                    ("Prevent rerun duplication", 1),
                    ("Handle edited timesheet after posting through exception or reversal policy", 2),
                    ("Add reversal path for generated entries", 1),
                ]),
                ("Section E – Testing", [
                    ("Test approved versus unapproved inclusion", 1),
                    ("Test rerun behavior", 1),
                    ("Test missing cost fallback or blocking", 1),
                    ("Test multi-project month-end batch", 2),
                    ("Test accounting trace back to source timesheets", 1),
                ]),
            ]
            for section_name, section_tasks in tasks:
                section_id = create_work_package(project_id, section_name, "", parent_id=m4_id, estimated_hours=0)
                if section_id:
                    for task_name, hours in section_tasks:
                        create_work_package(project_id, task_name, "", parent_id=section_id, estimated_hours=hours)

        # ─────────────────────────────────────────────────────────────────────
        # M5: STOCK PROJECT MATERIAL RECLASSIFICATION
        # ─────────────────────────────────────────────────────────────────────
        print("\n📋 M5 - Stock Project Material Reclassification")
        m5_id = create_work_package(
            project_id,
            "M5 - Stock Project Material Reclassification",
            (
                "R5: Project material allocation from stock at product cost.\n\n"
                "Workflow:\n"
                "- Capture analytic account on delivery lines\n"
                "- Generate monthly reclassification entries\n"
                "- Dr Direct Materials / Cr Inventory (at valuation cost)\n"
                "- Fixed monthly grouping by company/period/project/accounts\n"
                "- Non-invasive to core stock valuation"
            ),
            priority=8,
            estimated_hours=48
        )
        if m5_id:
            tasks = [
                ("Section A – Analytic Capture", [
                    ("Add analytic or project field on stock.move", 2),
                    ("Expose field on delivery operation lines where needed", 2),
                    ("Define defaulting strategy from source document if available", 1),
                    ("Ensure field is stored and auditable", 1),
                ]),
                ("Section B – Reclassification Setup", [
                    ("Read valuation-based amounts from completed stock moves", 2),
                    ("Identify eligible moves not yet reclassified", 1),
                    ("Build monthly grouping logic fixed to company/period/project/accounts", 2),
                    ("Link stock moves to generated reclass entry", 1),
                ]),
                ("Section C – Journal Entry Generation", [
                    ("Create reclassification journal entry: debit direct materials", 1),
                    ("Create reclassification journal entry: credit inventory", 1),
                    ("Use valuation-derived cost only", 1),
                    ("Mark moves as reclassified", 1),
                    ("Put generated entries in dedicated journal if approved", 1),
                ]),
                ("Section D – Preventing Duplicates and Reversals", [
                    ("Prevent duplicate reclassification", 2),
                    ("Add reclassification batch or log model if needed", 1),
                    ("Add reversal option for generated batches", 2),
                    ("Handle partial deliveries and backorders correctly", 2),
                    ("Validate FIFO and AVCO compatibility", 2),
                ]),
                ("Section E – Testing and Reconciliation", [
                    ("Test single project", 1),
                    ("Test multiple project lines", 2),
                    ("Test partial delivery", 1),
                    ("Test backorder", 1),
                    ("Test FIFO", 2),
                    ("Test AVCO", 2),
                    ("Test rerun prevention", 1),
                    ("Reconcile reclass totals against stock valuation basis", 2),
                    ("Validate project reporting visibility", 1),
                ]),
            ]
            for section_name, section_tasks in tasks:
                section_id = create_work_package(project_id, section_name, "", parent_id=m5_id, estimated_hours=0)
                if section_id:
                    for task_name, hours in section_tasks:
                        create_work_package(project_id, task_name, "", parent_id=section_id, estimated_hours=hours)

        # ─────────────────────────────────────────────────────────────────────
        # M7: CROSS MODULE HARDENING AND DELIVERY
        # ─────────────────────────────────────────────────────────────────────
        print("\n📋 M7 - Cross Module Hardening and Delivery")
        m7_id = create_work_package(
            project_id,
            "M7 - Cross Module Hardening and Delivery",
            (
                "Final hardening, integration testing, UAT, and production deployment.\n\n"
                "Scope:\n"
                "- Standardize patterns across modules\n"
                "- Comprehensive test suite\n"
                "- UAT and sign-off\n"
                "- Finance walkthrough\n"
                "- Production deployment and rollback plan"
            ),
            priority=8,
            estimated_hours=36
        )
        if m7_id:
            tasks = [
                ("Standardize audit message style", 2),
                ("Standardize manager override pattern", 2),
                ("Standardize batch reversal approach for R4 and R5", 2),
                ("Validate no permission conflicts across accounting, inventory, timesheet roles", 2),
                ("Add unit and integration tests per module", 4),
                ("Add reconciliation tests for R3, R4, and R5", 4),
                ("Add workflow permission tests for R6", 2),
                ("Prepare finance walkthrough by module", 3),
                ("Execute UAT in sequence: R2, R1, R6, R3, R4, R5", 6),
                ("Freeze defects", 1),
                ("Approve production deployment plan", 1),
                ("Prepare rollback plan for R4, R5, and R6", 2),
            ]
            for task_name, hours in tasks:
                create_work_package(project_id, task_name, "", parent_id=m7_id, estimated_hours=hours)

        # ─────────────────────────────────────────────────────────────────────
        # Summary
        # ─────────────────────────────────────────────────────────────────────
        print("\n" + "="*80)
        print("✓ PROJECT CREATED SUCCESSFULLY")
        print("="*80)
        print(f"\nProject Name: {PROJECT_NAME}")
        print(f"Identifier: {PROJECT_IDENTIFIER}")
        print(f"\nMilestone Structure:")
        print("  ✓ M0 - Project Setup")
        print("  ✓ M2 - OCA General Ledger Range Fix")
        print("  ✓ M1 - Journal Line Reference Extension")
        print("  ✓ M6 - Invoice Approval and ZATCA Gate")
        print("  ✓ M3 - Analytic Project Statement Report")
        print("  ✓ M4 - Timesheet Labor Accrual")
        print("  ✓ M5 - Stock Project Material Reclassification")
        print("  ✓ M7 - Cross Module Hardening and Delivery")
        print(f"\n📍 Access at:")
        print(f"   {OP_URL}/projects/{PROJECT_IDENTIFIER}")
        print(f"\nLogin:\n   Username: admin\n   Password: admin")
        print("\n" + "="*80)

        return 0

    except Exception as e:
        print(f"\n[FATAL] {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
