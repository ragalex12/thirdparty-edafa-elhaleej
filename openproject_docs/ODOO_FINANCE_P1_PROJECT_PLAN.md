# Odoo Finance Customization Phase 1 – OpenProject Implementation Plan

**Status:** Ready for Execution (Awaiting Cloudflare Tunnel)  
**Date Prepared:** April 9, 2026  
**Target URL:** https://generated-complexity-ireland-fully.trycloudflare.com/projects/odoo-fin-cust-p1  
**Baseline Document:** Approved Functional Specification + Technical Direction

---

## Executive Summary

This document describes the complete OpenProject project structure for delivery of Odoo Finance Customization Phase 1 (R1–R6 from the approved Functional Specification). The project contains:

- **8 Milestones** organized by implementation sequence
- **~200 Work Packages** covering data model, views, logic, testing, and integration
- **Clear dependency ordering** to enable parallel and sequential work
- **Detailed test scenarios** and acceptance criteria per request

All project structure has been generated via Python script. Once OpenProject is reachable via Cloudflare tunnel, the scripts will create the full project automatically.

---

## Project Overview

| Item | Value |
|------|-------|
| **Project Name** | Odoo Finance Customization Phase 1 |
| **Identifier (slug)** | odoo-fin-cust-p1 |
| **Scope** | Requests R1–R6 from approved specification |
| **Phase** | Phase 1 implementation + optional enhancements noted |
| **Target Odoo** | 19.x (exact version to be confirmed in M0) |
| **Baseline** | Approved Functional Specification + Technical Direction, April 9, 2026 |

---

## Milestone Structure (Execution Sequence)

### M0 – Project Setup (High Priority)
**Effort:** 16 hours  
**Purpose:** Validate environment, confirm scope, prepare infrastructure  
**Deliverables:**
- Confirm Odoo version and OCA branches
- Create technical design notes per module
- Security groups matrix
- Staging database
- Sample test cases
- Freeze scope vs. enhancements

### M2 – OCA General Ledger Range Fix (High Priority)
**Effort:** 24 hours  
**Purpose:** Fix reported account range filter bug in OCA GL report  
**Request:** R2  
**Approach:** Diagnose → minimal patch → regression tests  
**Deliverables:**
- Root cause documentation
- Minimal code fix
- 7-case regression test suite
- Validation across screen/PDF/XLSX

### M1 – Journal Line Reference Extension (High Priority)
**Effort:** 20 hours  
**Purpose:** Add three transactional fields to account move lines  
**Request:** R1  
**Approach:** Model fields + views + partner defaulting + post-lock controls + manager correction  
**Deliverables:**
- line_reference, line_reference_number, line_tax_number fields
- Draft edit, posting lock, manager correction action
- Partner VAT auto-fill
- Tests for draft/post behavior and correction audit

### M6 – Invoice Approval and ZATCA Gate (Normal Priority)
**Effort:** 28 hours  
**Purpose:** Implement 3-stage invoice approval workflow + ZATCA submission control  
**Request:** R6  
**Approach:** Approval states on account.move + permission gates + material edit reset logic  
**Deliverables:**
- Draft Entry → Under Review → Approved → Sent to ZATCA states
- Post gated by approval
- Send to ZATCA manual button after posted+approved
- Material edit reset to review (10 field types identified)
- Migration script for existing invoices
- Full workflow and permission tests

### M3 – Analytic Project Statement Report (Normal Priority)
**Effort:** 40 hours  
**Purpose:** New project-centric analytic statement with project-wise debit totals  
**Request:** R3  
**Approach:** Wizard + on-screen + XLSX, allocation-aware  
**Column Layout (Screen / XLSX):**
- Date | Move Number | Journal | Account | Project | Partner | Allocation % | Debit | Credit
- Plus: Project Subtotal | Debit Account Group Totals per Project
- XLSX adds: Move Line ID, Source Values, Currency for audit

**Deliverables:**
- Report wizard with filters (date, company, projects, draft toggle)
- On-screen tree view with grouping and subtotals
- XLSX export with identical totals and audit columns
- Multi-allocation handling and reconciliation tests

### M4 – Timesheet Labor Accrual (Normal Priority)
**Effort:** 32 hours  
**Purpose:** Generate labor cost journal entries from approved timesheets (monthly batches)  
**Request:** R4  
**Approach:** Batch approval-based posting with idempotency and source linkage  
**Costing Source (Phase 1):** Employee monthly cost ÷ standard monthly hours → fallback employee category cost  
**Deliverables:**
- Project-level account mapping config (direct wages, WIP accounts)
- Monthly labor posting batch model with state and history
- Draft JE generation grouped by company + project
- Idempotent posting with duplicate prevention
- Reversal path for adjustments
- Tests for approved/unapproved, rerun, missing costs, traces

### M5 – Stock Project Material Reclassification (High Priority, High Complexity)
**Effort:** 48 hours  
**Purpose:** Allocate delivered materials to projects via monthly reclassification entry  
**Request:** R5  
**Approach:** Stock move analytic capture + secondary reclassification at valuation cost  
**Phase 1 Grouping (Fixed):** Monthly by company + posting month + project (analytic) + direct materials account + inventory account  
**Deliverables:**
- Analytic account field on stock.move with defaulting strategy
- Valuation-amount reading from completed stock moves
- Monthly reclassification entry: Dr Direct Materials / Cr Inventory
- Non-invasive to core stock valuation
- Duplicate prevention and reversal
- Tests for single/multi-project, FIFO/AVCO, partial delivery, reconciliation

### M7 – Cross Module Hardening and Delivery (High Priority)
**Effort:** 36 hours  
**Purpose:** Integration, standardization, UAT, production deployment  
**Approach:** Unified patterns, test suites, walkthrough, staged rollout  
**Deliverables:**
- Standardized audit, override, and batch reversal patterns
- Unit + integration test suite per module
- Reconciliation tests for R3/R4/R5
- Finance walkthrough + UAT (R2 → R1 → R6 → R3 → R4 → R5)
- Production deployment and rollback plans for R4/R5/R6

---

## Work Package Breakdown by Module

### Module 1: account_move_line_reference_ext (R1)
**Type:** Standalone  
**Dependencies:** account, mail  
**Sections:**
- A: Data Model (6 packages)
- B: Views and Defaults (5 packages)
- C: Testing and Visibility (6 packages)

### Module 2: oca_gl_range_fix_local (R2)
**Type:** Standalone  
**Dependencies:** account, OCA financial reporting  
**Sections:**
- A: Diagnosis (5 packages)
- B: Root Cause (5 packages)
- C: Implementation and Testing (8 packages)

### Module 3: analytic_project_statement_report (R3)
**Type:** Standalone (shared reporting patterns)  
**Dependencies:** account, analytic, report_xlsx  
**Sections:**
- A: Requirements (4 packages)
- B: Wizard and Query (4 packages)
- C: On-Screen Report (5 packages)
- D: XLSX Export (4 packages)
- E: Testing (7 packages)

### Module 4: hr_timesheet_labor_accrual (R4)
**Type:** Shared operational-accounting bridge  
**Dependencies:** hr_timesheet, project, analytic, account  
**Sections:**
- A: Configuration (5 packages)
- B: Batch Model (4 packages)
- C: Batch Processing (6 packages)
- D: Idempotency and Reversal (5 packages)
- E: Testing (5 packages)

### Module 5: stock_project_material_reclass (R5)
**Type:** Shared inventory-accounting bridge  
**Dependencies:** stock, stock_account, analytic, account  
**Sections:**
- A: Analytic Capture (4 packages)
- B: Reclassification Setup (4 packages)
- C: Journal Entry Generation (5 packages)
- D: Duplicate Prevention (5 packages)
- E: Testing and Reconciliation (9 packages)

### Module 6: account_invoice_approval_zatca_gate (R6)
**Type:** Standalone with localization touch points  
**Dependencies:** account, mail, ZATCA integration  
**Sections:**
- A: States and Permissions (4 packages)
- B: Workflow Controls (4 packages)
- C: Material Edit Reset Logic (4 packages)
- D: Posting and ZATCA Integration (5 packages)
- E: Data Migration and Testing (8 packages)

---

## How to Execute Project Creation

### Prerequisites
1. OpenProject accessible via Cloudflare tunnel
2. Service responding on https://generated-complexity-ireland-fully.trycloudflare.com
3. API token available (auto-detected from create_simple_project.py)

### Execution Methods

#### Option 1: Automatic with Tunnel Detection (Recommended)
```bash
bash /opt/localaddons/openproject_scripts/run_create_finance_project.sh
```
This launcher script:
- Checks tunnel connectivity
- Reports status
- Launches project creation if ready
- Provides troubleshooting if unavailable

#### Option 2: Direct Script Execution
```bash
python3 /opt/localaddons/openproject_scripts/create_odoo_finance_phase1_project.py
```
Direct execution without tunnel check (use if you know service is ready).

#### Option 3: From Any Directory (with alias)
```bash
source /opt/localaddons/openproject_tools/openproject_aliases.sh
op-create-finance
```
(Requires alias setup in .bashrc)

### Expected Output
Successful execution produces:
- Project created: `odoo-fin-cust-p1`
- 8 milestones with parent-child hierarchy
- ~200 total work packages
- Console summary with project URL and login

### Post-Creation Activities
1. **Verify:** Open browser → https://generated-complexity-ireland-fully.trycloudflare.com/projects/odoo-fin-cust-p1
2. **Login:** admin / admin
3. **Review:** Check milestones in project settings → roadmap
4. **Customize (if needed):**
   - Adjust priority levels
   - Add team assignments
   - Set actual target dates
   - Add sprints if using agile methodology

---

## Priority and Effort Summary

| Milestone | Priority | Effort (hrs) | Status |
|-----------|----------|-------------|--------|
| M0 – Setup | High | 16 | Ready |
| M2 – GL Fix | High | 24 | Ready |
| M1 – Reference Fields | High | 20 | Ready |
| M6 – Invoice Approval | Normal | 28 | Ready |
| M3 – Statement Report | Normal | 40 | Ready |
| M4 – Labor Accrual | Normal | 32 | Ready |
| M5 – Material Reclass | High | 48 | Ready |
| M7 – Hardening | High | 36 | Ready |
| **Total** | — | **244** | **Ready** |

---

## Key Assumptions and Notes

### Project Structure
- Assumes OpenProject v14+
- Uses standard Task type for work packages
- Milestone hierarchy via parent-child relationships
- Priority scale: 8 (High) / 7 (Normal) / 2 (Low) as needed

### Phase 1 vs. Optional Enhancements
All work packages listed are Phase 1 must-have deliverables.  
Optional later enhancements (noted in baseline doc) are NOT included in this structure.

### Dependency Management
Execution sequence is documented but not enforced via OpenProject dependencies.  
Team should:
1. Read baseline specification before project start
2. Confirm phase 1 scope with Finance and Technical Leads
3. Use project milestone sequence as execution plan

### Module Naming
Module names follow Odoo naming conventions:
- `account_move_line_reference_ext` → extends account.move.line
- `oca_gl_range_fix_local` → local patch for OCA module
- `analytic_project_statement_report` → new reporting module
- `hr_timesheet_labor_accrual` → finance bridge from timesheet
- `stock_project_material_reclass` → finance bridge from stock
- `account_invoice_approval_zatca_gate` → extends account.move with approval + ZATCA

---

## Files in This Assignment

| File | Purpose | Status |
|------|---------|--------|
| `create_odoo_finance_phase1_project.py` | Main project creation script | ✓ Ready |
| `run_create_finance_project.sh` | Launcher with tunnel detection | ✓ Ready |
| `ODOO_FINANCE_P1_PROJECT_PLAN.md` | This document | ✓ Complete |

---

## Next Steps

1. **Immediate:** Ensure OpenProject service and Cloudflare tunnel are operational
2. **Execute:** Run launcher script or Python command
3. **Verify:** Confirm all 8 milestones and ~200 work packages appear in project
4. **Sign-Off:** Finance Manager and Technical Lead approve project structure
5. **Start Work:** Follow milestone sequence starting with M0 – Project Setup

---

## Support and Troubleshooting

### Script Fails to Connect
- Verify: `curl https://generated-complexity-ireland-fully.trycloudflare.com/ | head`
- Check Cloudflare tunnel is running: `pgrep cloudflared`
- Check OpenProject service: `ps aux | grep puma`
- Review logs: `/var/log/openproject/*.log` or check tunnel endpoint logs

### Projects Already Exist
The script includes duplicate prevention:
- If `odoo-fin-cust-p1` already exists, script will report error
- To override, manually delete old project first or modify identifier in script

### API Authentication Issues
- Verify API token in `create_simple_project.py` is valid
- Test connectivity: `python3 /opt/localaddons/openproject_scripts/test_openproject_connection.py`
- Check user permissions in OpenProject

### Work Packages Not Appearing
- Refresh browser after 30 seconds
- Check project → sidebar → Work Packages to verify load
- If parent packages missing, check project → Roadmap for hierarchical view

---

## Project Approval Checklist

Before development starts, confirm:

- [ ] Project structure reviewed and approved
- [ ] Milestone sequence understood by team
- [ ] ~200 work packages meet baseline specification
- [ ] Tech Lead reviewed module design and dependencies
- [ ] Finance Manager approved scope boundaries (Phase 1 vs. optional)
- [ ] Odoo version and OCA branches confirmed in M0
- [ ] Testing plan understood (each module + M7 integration)
- [ ] Deployment plan reviewed (rollback documented for R4/R5/R6)

---

**Prepared by:** Odoo Implementation Analysis  
**Date:** April 9, 2026  
**Version:** 1.0 – Ready for Execution
