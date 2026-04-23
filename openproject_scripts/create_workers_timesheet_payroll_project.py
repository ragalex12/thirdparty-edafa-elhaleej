#!/usr/bin/env python3
"""
OpenProject Project Creator for Workers Timesheet Payroll Fix
==============================================================
Creates a comprehensive project documenting the diagnosis, fix, and follow-up
work for the AttributeError in account.analytic.line model caused by missing
use_for_payroll field from uninstalled workers_project_sheets module.

This project tracks:
1. Completed work (diagnosis, patch, validation, documentation)
2. Pending work (training observation, production deployment, architectural refactor)

Run: python3 create_workers_timesheet_payroll_project.py
"""

import sys
import json
import time
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta

# ─── Configuration ────────────────────────────────────────────────────────────
OP_URL    = "http://localhost:8090"
API_TOKEN = "f1336582f568d3dc0c27a938d711c10c5f3cb81366aed6ad27b663dc2a7034b3"
AUTH      = HTTPBasicAuth("apikey", API_TOKEN)
HEADERS   = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}

# ─── Project Definition ───────────────────────────────────────────────────────
PROJECT_NAME       = "Odoo 19 – Workers Timesheet Payroll Fix"
PROJECT_IDENTIFIER = "odoo19-workers-payroll-fix"
PROJECT_DESCRIPTION = (
    "Diagnosis and stabilization of AttributeError in account.analytic.line model "
    "caused by missing use_for_payroll field when workers_project_sheets module is uninstalled. "
    "Includes defensive patch implementation, training validation, and long-term architectural improvements."
)

def api_call(method, endpoint, data=None):
    """Make API call to OpenProject."""
    url = f"{OP_URL}/api/v3{endpoint}"
    try:
        if method == "GET":
            resp = requests.get(url, headers=HEADERS, auth=AUTH, timeout=30)
        elif method == "POST":
            resp = requests.post(url, json=data, headers=HEADERS, auth=AUTH, timeout=30)
        elif method == "PATCH":
            resp = requests.patch(url, json=data, headers=HEADERS, auth=AUTH, timeout=30)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        # Print response for debugging
        print(f"[{method}] {endpoint}")
        print(f"  Status: {resp.status_code}")
        if resp.status_code not in [200, 201]:
            print(f"  Error: {resp.text[:500]}")
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
        print("[ERROR] Failed to create project")
        return None
    
    project = resp.json().get('_embedded', {}).get('project', {}) or resp.json()
    project_id = project.get('id')
    print(f"✓ Project created: {PROJECT_NAME} (ID: {project_id})")
    return project_id

def create_work_package(project_id, subject, description, parent_id=None, status="new", priority=5, estimated_hours=None):
    """Create a work package."""
    wp_data = {
        "subject": subject,
        "description": description,
        "status": {"name": status},
        "priority": {"id": priority},
    }
    
    if parent_id:
        wp_data["parent"] = {"href": f"/api/v3/work_packages/{parent_id}"}
    
    if estimated_hours:
        wp_data["estimatedTime"] = f"PT{estimated_hours}H"
    
    resp = api_call("POST", f"/projects/{project_id}/work_packages", wp_data)
    if not resp or resp.status_code not in [200, 201]:
        return None
    
    wp = resp.json()
    wp_id = wp.get('id')
    print(f"  • {subject} (ID: {wp_id})")
    return wp_id

def main():
    """Main execution."""
    try:
        # Create project
        project_id = create_project()
        if not project_id:
            print("[ERROR] Failed to create project")
            return 1
        
        print("\n" + "="*80)
        print("Creating Work Packages...")
        print("="*80)
        
        # ─── PHASE 1: ROOT CAUSE DIAGNOSIS ───────────────────────────────────
        print("\n📋 Phase 1: Root Cause Diagnosis [COMPLETED]")
        phase1_id = create_work_package(
            project_id,
            "Phase 1: Root Cause Diagnosis",
            (
                "Complete analysis of the AttributeError in account.analytic.line.\n\n"
                "**Findings:**\n"
                "- Error: AttributeError: 'project.project' object has no attribute 'use_for_payroll'\n"
                "- Location: workers_timesheet/models/account_analytic_line.py, _onchange_project_id() method\n"
                "- Root cause: workers_project_sheets module is uninstalled in training database\n"
                "- Missing field: use_for_payroll defined in workers_project_sheets.project_project (line 11)\n"
                "- Dependency issue: Circular dependency prevents simple manifest fix\n"
                "  - workers_project_sheets depends on workers_timesheet\n"
                "  - Cannot add reverse dependency without architectural refactor\n"
                "\n**Module States Verified:**\n"
                "- workers_timesheet: INSTALLED\n"
                "- workers_project_sheets: UNINSTALLED (in training database trgulf_Mrp)\n"
                "- workers_reports: UNINSTALLED (in training database)\n"
            ),
            status="Closed",
            priority=8,
            estimated_hours=2
        )
        
        create_work_package(
            project_id,
            "Analyze error traceback and module dependencies",
            "Read error logs and map dependency relationships between modules.",
            parent_id=phase1_id,
            status="Closed",
            estimated_hours=0.5
        )
        
        create_work_package(
            project_id,
            "Query database for module installation states",
            "Use PostgreSQL to verify workers_project_sheets uninstalled in training DB.",
            parent_id=phase1_id,
            status="Closed",
            estimated_hours=0.5
        )
        
        create_work_package(
            project_id,
            "Review field definitions in workers_project_sheets",
            "Confirm use_for_payroll field definition at workers_project_sheets/models/project_project.py line 11.",
            parent_id=phase1_id,
            status="Closed",
            estimated_hours=0.5
        )
        
        create_work_package(
            project_id,
            "Evaluate long-term architectural solutions",
            "Document why simple manifest fix won't work and identify refactor requirements.",
            parent_id=phase1_id,
            status="Closed",
            estimated_hours=0.5
        )
        
        # ─── PHASE 2: DEFENSIVE PATCH IMPLEMENTATION ──────────────────────────
        print("\n🔧 Phase 2: Defensive Patch Implementation [COMPLETED]")
        phase2_id = create_work_package(
            project_id,
            "Phase 2: Defensive Patch Implementation",
            (
                "Apply defensive field-existence guard to prevent AttributeError.\n\n"
                "**Solution Pattern:**\n"
                "```python\n"
                "@api.onchange('project_id')\n"
                "def _onchange_project_id(self):\n"
                "    for rec in self:\n"
                "        if rec.project_id and 'use_for_payroll' in rec.project_id._fields:\n"
                "            rec.include_in_payroll = rec.project_id.use_for_payroll\n"
                "        else:\n"
                "            rec.include_in_payroll = False\n"
                "```\n\n"
                "**Rationale:**\n"
                "- Checks field existence before accessing: 'use_for_payroll' in rec.project_id._fields\n"
                "- Provides safe default: False when field missing\n"
                "- Preserves intended logic when field available\n"
                "- Backward compatible, matches Odoo framework best practices\n"
                "- Minimal risk stabilization that works regardless of module install state\n"
            ),
            status="Closed",
            priority=8,
            estimated_hours=1.5
        )
        
        create_work_package(
            project_id,
            "Create backup of original file",
            "Backup account_analytic_line.py to models/backups/ with timestamp.",
            parent_id=phase2_id,
            status="Closed",
            estimated_hours=0.25
        )
        
        create_work_package(
            project_id,
            "Apply defensive guard to _onchange_project_id method",
            "Replace direct field access with field-existence check.",
            parent_id=phase2_id,
            status="Closed",
            estimated_hours=0.5
        )
        
        create_work_package(
            project_id,
            "Validate Python syntax",
            "Run python3 -m py_compile to verify syntax correctness.",
            parent_id=phase2_id,
            status="Closed",
            estimated_hours=0.25
        )
        
        create_work_package(
            project_id,
            "Verify patch applies cleanly",
            "Confirm no merge conflicts and patch location is correct.",
            parent_id=phase2_id,
            status="Closed",
            estimated_hours=0.25
        )
        
        # ─── PHASE 3: TRAINING VALIDATION ────────────────────────────────────
        print("\n✅ Phase 3: Training Validation [COMPLETED]")
        phase3_id = create_work_package(
            project_id,
            "Phase 3: Training Validation",
            (
                "Multi-level testing of patched code in training database (trgulf_Mrp).\n\n"
                "**Validation Results:**\n"
                "1. Python Syntax: ✓ PASS (no compilation errors)\n"
                "2. Module Upgrade: ✓ PASS (exit code 0, SUCCESS status)\n"
                "3. Runtime Onchange: ✓ PASS (ONCHANGE_OK, no AttributeError)\n"
                "\n**Test Commands:**\n"
                "- Syntax: python3 -m py_compile /opt/localaddons/workers_timesheet/models/account_analytic_line.py\n"
                "- Module: /usr/bin/odoo -c /etc/odoo/odoo.conf -d trgulf_Mrp -u workers_timesheet --stop-after-init\n"
                "- Runtime: Odoo shell project_id onchange test with test data\n"
            ),
            status="Closed",
            priority=8,
            estimated_hours=2
        )
        
        create_work_package(
            project_id,
            "Module upgrade test in training DB",
            "Execute: /usr/bin/odoo -c /etc/odoo/odoo.conf -d trgulf_Mrp -u workers_timesheet --stop-after-init",
            parent_id=phase3_id,
            status="Closed",
            estimated_hours=0.5
        )
        
        create_work_package(
            project_id,
            "Runtime onchange execution test",
            "Test project_id onchange via Odoo shell with sample data.",
            parent_id=phase3_id,
            status="Closed",
            estimated_hours=0.75
        )
        
        create_work_package(
            project_id,
            "Verify no AttributeError in logs",
            "Review training database upgrade logs for errors.",
            parent_id=phase3_id,
            status="Closed",
            estimated_hours=0.25
        )
        
        create_work_package(
            project_id,
            "Document validation results",
            "Record all test results in comprehensive report.",
            parent_id=phase3_id,
            status="Closed",
            estimated_hours=0.5
        )
        
        # ─── PHASE 4: DOCUMENTATION ──────────────────────────────────────────
        print("\n📄 Phase 4: Documentation [COMPLETED]")
        phase4_id = create_work_package(
            project_id,
            "Phase 4: Documentation",
            (
                "Create comprehensive audit trail and reference documentation.\n\n"
                "**Documentation Created:**\n"
                "- TRAINING_workers_timesheet_payroll_diagnosis_2026-04-05.md\n"
                "- 9 sections: Summary, Findings, Root Cause, Dependency Assessment, Backups, Changes, Validation, Recommendations, Commands\n"
                "- Complete audit trail for compliance and knowledge transfer\n"
                "- Timestamp and versioning for traceability\n"
            ),
            status="Closed",
            priority=5,
            estimated_hours=1.5
        )
        
        create_work_package(
            project_id,
            "Write root cause analysis",
            "Document error, missing field, circular dependency issue.",
            parent_id=phase4_id,
            status="Closed",
            estimated_hours=0.5
        )
        
        create_work_package(
            project_id,
            "Document all changes made",
            "Record file locations, backup paths, code changes.",
            parent_id=phase4_id,
            status="Closed",
            estimated_hours=0.25
        )
        
        create_work_package(
            project_id,
            "Document validation tests and results",
            "Record all commands run and their outputs.",
            parent_id=phase4_id,
            status="Closed",
            estimated_hours=0.5
        )
        
        create_work_package(
            project_id,
            "Create OpenProject project structure",
            "Set up work packages in OpenProject for tracking and stakeholder visibility.",
            parent_id=phase4_id,
            status="Closed",
            estimated_hours=0.25
        )
        
        # ─── PHASE 5: TRAINING OBSERVATION ───────────────────────────────────
        print("\n📊 Phase 5: Training Observation (PENDING)")
        phase5_id = create_work_package(
            project_id,
            "Phase 5: Training Observation Period",
            (
                "Monitor training database (trgulf_Mrp) for 24-48 hours to verify patch stability.\n\n"
                "**Objective:**\n"
                "Confirm defensive patch prevents AttributeError in real-world usage patterns "
                "before production deployment.\n\n"
                "**Test Scenarios:**\n"
                "- Create timesheets with various project states\n"
                "- Test project_id field changes during timesheet entry\n"
                "- Verify include_in_payroll defaults to False when field unavailable\n"
                "- Check for any related errors in logs\n"
                "- Validate payroll calculations with both settings\n\n"
                "**Success Criteria:**\n"
                "- No AttributeError in account.analytic.line operations\n"
                "- No related errors in Odoo logs\n"
                "- Automated payroll flow executes without crashes\n"
            ),
            status="New",
            priority=8,
            estimated_hours=4
        )
        
        create_work_package(
            project_id,
            "Create test timesheets with various project configurations",
            "Test timesheet creation with projects where workers_project_sheets is/isn't providing use_for_payroll.",
            parent_id=phase5_id,
            status="New",
            estimated_hours=1
        )
        
        create_work_package(
            project_id,
            "Verify include_in_payroll defaults correctly",
            "Confirm defensive default (False) is applied when use_for_payroll field absent.",
            parent_id=phase5_id,
            status="New",
            estimated_hours=1
        )
        
        create_work_package(
            project_id,
            "Monitor Odoo logs for AttributeError occurrences",
            "Check /var/log/odoo/ and training database logs for any errors.",
            parent_id=phase5_id,
            status="New",
            estimated_hours=1
        )
        
        create_work_package(
            project_id,
            "Document training observation results",
            "Record all test results and stability findings.",
            parent_id=phase5_id,
            status="New",
            estimated_hours=1
        )
        
        # ─── PHASE 6: PRODUCTION DEPLOYMENT ──────────────────────────────────
        print("\n🚀 Phase 6: Production Deployment (PENDING)")
        phase6_id = create_work_package(
            project_id,
            "Phase 6: Production Deployment",
            (
                "Deploy defensive patch to production after successful training validation.\n\n"
                "**Prerequisites:**\n"
                "- 24-48 hour training observation completed successfully\n"
                "- No AttributeError occurrences in training\n"
                "- All testing passed\n"
                "- Stakeholder approval obtained\n\n"
                "**Deployment Steps:**\n"
                "1. Back up production workers_timesheet code\n"
                "2. Apply same defensive patch to production module\n"
                "3. Execute module upgrade on production database\n"
                "4. Monitor production logs for errors\n"
                "5. Verify payroll calculations function correctly\n"
            ),
            status="New",
            priority=8,
            estimated_hours=3
        )
        
        create_work_package(
            project_id,
            "Backup production workers_timesheet code",
            "Create timestamped backup before any modifications.",
            parent_id=phase6_id,
            status="New",
            estimated_hours=0.5
        )
        
        create_work_package(
            project_id,
            "Apply defensive patch to production module",
            "Deploy same patch used in training to production code.",
            parent_id=phase6_id,
            status="New",
            estimated_hours=0.5
        )
        
        create_work_package(
            project_id,
            "Execute production module upgrade",
            "Run: /usr/bin/odoo -c /etc/odoo/odoo.conf -d <prod-db> -u workers_timesheet --stop-after-init",
            parent_id=phase6_id,
            status="New",
            estimated_hours=1
        )
        
        create_work_package(
            project_id,
            "Monitor production logs post-deployment",
            "Check for errors and verify payroll flow execution.",
            parent_id=phase6_id,
            status="New",
            estimated_hours=1
        )
        
        # ─── PHASE 7: LONG-TERM ARCHITECTURAL REFACTOR ────────────────────────
        print("\n🏗️  Phase 7: Architecture Refactor (FUTURE)")
        phase7_id = create_work_package(
            project_id,
            "Phase 7: Long-Term Architectural Refactor",
            (
                "Create shared base module to eliminate implicit cross-module assumptions.\n\n"
                "**Problem:**\n"
                "- workers_timesheet code depends on use_for_payroll field\n"
                "- Field defined in workers_project_sheets\n"
                "- Circular dependency prevents simple manifest fix\n"
                "- Current defensive patch is temporary stabilization\n\n"
                "**Solution:**\n"
                "Create workers_payroll_base module containing:\n"
                "- use_for_payroll and related payroll-project integration fields\n"
                "- Define in shared base instead of project_project extension\n"
                "- Both workers_timesheet and workers_project_sheets depend on workers_payroll_base\n"
                "\n**Benefits:**\n"
                "- Eliminates circular dependency\n"
                "- Supports flexible module combinations\n"
                "- Cleaner architecture for future payroll enhancements\n"
                "- Simplifies maintenance and troubleshooting\n"
            ),
            status="New",
            priority=3,
            estimated_hours=8
        )
        
        create_work_package(
            project_id,
            "Design workers_payroll_base module structure",
            "Plan module dependencies, field locations, and integration points.",
            parent_id=phase7_id,
            status="New",
            estimated_hours=2
        )
        
        create_work_package(
            project_id,
            "Create workers_payroll_base manifest and models",
            "Implement base module with payroll-related fields.",
            parent_id=phase7_id,
            status="New",
            estimated_hours=2
        )
        
        create_work_package(
            project_id,
            "Refactor workers_project_sheets to inherit from base",
            "Update dependencies and remove duplicated fields.",
            parent_id=phase7_id,
            status="New",
            estimated_hours=2
        )
        
        create_work_package(
            project_id,
            "Update workers_timesheet dependencies",
            "Add workers_payroll_base to manifest, update code if needed.",
            parent_id=phase7_id,
            status="New",
            estimated_hours=1
        )
        
        create_work_package(
            project_id,
            "Test refactored architecture",
            "Verify all modules work correctly with new structure.",
            parent_id=phase7_id,
            status="New",
            estimated_hours=1
        )
        
        print("\n" + "="*80)
        print("✓ OpenProject Project Created Successfully")
        print("="*80)
        print(f"\nProject Name: {PROJECT_NAME}")
        print(f"Project ID: {project_id}")
        print(f"Identifier: {PROJECT_IDENTIFIER}")
        print(f"\n📍 Access at: http://127.0.0.1:8088/projects/{PROJECT_IDENTIFIER}")
        print("\n📊 Work Packages Summary:")
        print("  ✓ Phase 1: Root Cause Diagnosis [COMPLETED]")
        print("  ✓ Phase 2: Defensive Patch Implementation [COMPLETED]")
        print("  ✓ Phase 3: Training Validation [COMPLETED]")
        print("  ✓ Phase 4: Documentation [COMPLETED]")
        print("  ⏳ Phase 5: Training Observation Period [PENDING - 24-48h]")
        print("  ⏳ Phase 6: Production Deployment [PENDING - after Phase 5]")
        print("  📋 Phase 7: Long-Term Architectural Refactor [FUTURE - post-stabilization]")
        
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
