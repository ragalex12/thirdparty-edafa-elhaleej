# OpenProject — Revised Phase 1 execution order (paste into WP or wiki)

**Date:** 2026-04-09  
**Applies to:** GPC Odoo 19 — Phase 1 backend modules

## Summary for PM

- **M0 WP1, WP2, WP3** remain **completed foundation** steps.
- **Implementation order changed to backend-first** (no full security matrix as next gate).
- **Wave 1 (implement first):** **M2 → M1 → M3**
- **Wave 2:** **M4 → M5 → M6**
- **Wave 3 (before UAT/production):** **Security & permissions hardening** (full groups matrix, cross-module least privilege) — **not** scheduled immediately after M0.

## Suggested OpenProject actions

1. **Reorder** work packages (or milestone backlog) to match:
   - `M2 - OCA General Ledger Range Fix` (`gpc_account_gl_range_fix_local`) — **first**
   - `M1 - Journal Line Reference Extension` (`gpc_account_move_line_reference_ext`) — **second**
   - `M3 - Analytic Project Statement Report` (`gpc_report_analytic_project_statement`) — **third**
   - Then M4, M5, M6 in order.

2. **Create** a work package (or milestone) titled **“Phase 1 — Security & permissions hardening (pre-UAT)”** with:
   - Description: Full security groups matrix, record rules, SoD review across M1–M6.
   - **Schedule:** After M6 functional completion, **before** UAT sign-off.
   - **Dependency:** Blocks production go-live, **not** backend development.

3. **Link** repository docs:
   - `docs/phase1/PHASE1_EXECUTION_PLAN.md`
   - `docs/phase1/M0_WP3_TECHNICAL_DESIGN_NOTES.md`

4. **Notes field** on each implementation WP: *“Minimum roles documented in design doc §3 / module §5; full matrix deferred to pre-UAT hardening WP.”*

## Milestone → module map

| WP | Module |
|----|--------|
| M2 | `gpc_account_gl_range_fix_local` |
| M1 | `gpc_account_move_line_reference_ext` |
| M3 | `gpc_report_analytic_project_statement` |
| M4 | `gpc_hr_timesheet_labor_accrual` |
| M5 | `gpc_stock_project_material_reclass` |
| M6 | `gpc_account_invoice_approval_zatca_gate` |
