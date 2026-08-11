# Executive Summary

Labor accrual + analytic-statement work was implemented and proven on an isolated clone **`trgcc_mm_uat`**. Production **`trgcc` was not written**: 0 module installs, 0 journals, 0 SQL backfills.

Safe UAT timesheets (8h / 6h) produced posted journal **SLR/2026/09/0001**, balanced **640.00 SR**: Dr `410028 Basic Salary - Projects` with project analytic, Cr `202001 ACCRUED SALARIES` with no analytic. Statement is now **AAL-primary**; timesheets without GL render **Timesheet / no GL**.

Industrial P&L Excel remains **CHANGE_REQUEST_REQUIRED**.

# Environment

Production:
`trgcc` (owner odoo, 108 MB, PostgreSQL 16.13) — https://gpc.odoo.com.se

Test:
`trgcc_mm_uat` (owner odoo, 91 MB after restore)

Public names `MM` / `trgulf_Mrp` are **not** Postgres databases on this host. Database selector lists: `entgcc`, `trgcc`, `trgcc_mm_uat`. `entgcc` was not used.

# Safety

- production writes: **0**
- production accounting entries created: **0**
- production modules installed: **0**
- production timesheet count after UAT: **10** (unchanged)
- UAT crons disabled: **49**
- UAT mail servers: none active; catchall `uat-disabled.invalid`

# Baseline Findings

Production `trgcc` (2026-08-11 19:36 UTC):

| Item | Result |
|------|--------|
| Timesheets (`employee_id` set) | **10** |
| `general_account_id` on those 10 | **NULL** |
| `move_line_id` on those 10 | **NULL** |
| `account_id` on those 10 | **set** |
| GL-linked analytic rows | **4** |
| `include_in_payroll` column | **absent** |
| `labor_accrual_batch` | **absent** |
| Labor modules | **not in ir_module_module / not installed** |
| Installed | `legacy_mixed_system`, `gpc_gulf_hr_payroll_ext`, `gpc_gulf_project_ext`, `gcc_timesheet_type`, `hr_timesheet` |
| Logs Worker/Labor accrual / include_in_payroll | **0 matches** |

Timesheet IDs: 29, 30, 32, 48, 49, 53, 54, 55, 58, 59 (hours include 260 / 200 — anomalies).

# Root Causes

1. Odoo timesheets are analytic-only until a JE posts (`general_account_id` stays NULL).
2. Labor accrual stack lived in `/home/sabry/edafa_elhaleej` and was **not on production**.
3. `include_in_payroll` onchange copied `project.use_for_payroll` (default False) → silent exclusion.
4. `period_key` could drift from `period_start`/`period_end` (WP #405).
5. `account.move._post()` default `soft=True` left UAT moves in **draft** while marking the batch posted.
6. Analytic statement was **AML-primary**.

# Code Changes

Branch: `gulf-mm-uat-20260811`

| Commit | Message |
|--------|---------|
| `f5bb343` | fix(timesheet): preserve payroll eligibility on project onchange |
| `571a56e` | fix(labor-accrual): keep period key and dates synchronized |
| `2420797` | fix(analytic-statement): use analytic lines as primary source |
| `accd2fe` | test(mm): add labor accrual and statement UAT coverage |
| (this commit) | test(mm): adapt labor/statement tests to Odoo 19 schema |

Accounting design (unchanged, documented):

```
Dr Labor expense  (analytic = project)
Cr Accrued salaries / clearing  (no analytic)
```

Credit analytic is **not** added (would double-count project P&L).

# Module Versions

| Module | Source version installed on UAT |
|--------|----------------------------------|
| workers_timesheet | 19.0.1.1.0 |
| gpc_hr_timesheet_labor_accrual | 19.0.1.0.7 |
| gpc_worker_timesheet_labor_accrual_bridge | 19.0.1.0.0 |
| report_xlsx | 19.0.1.0.0 |
| gpc_analytic_project_statement | 19.0.1.7.0 |

# Test Database Creation

- Dump: `/var/backups/gulf_mm_uat/trgcc_20260811_223821.dump`
- Size: **9716737 bytes (9.3M)**
- Timestamp: **2026-08-11T22:38:21+03:00**
- PostgreSQL: 16.13
- Source owner: odoo
- Filestore copied: `/var/lib/odoo/filestore/trgcc_mm_uat` (19M)
- Restore exit: **0**
- UAT AAL count after restore: **14** (same as prod)

# Labor Accrual UAT

Safe records (not the 200h/260h lines):

| AAL | Name | Hours | Flag | Amount |
|-----|------|------:|------|-------:|
| 159 | UAT MM eligible 8h | 8 | True | -400 |
| 160 | UAT MM eligible 6h | 6 | True | -240 |
| 161 | UAT MM excluded | 8 | False | -400 |

- Batch **5** `UAT MM labor accrual 2026-09`, `period_key=2026-09` (forced from dates; stale `2099-01` overwritten)
- Populate: 2 lines, total **640.00** (excluded 161 skipped)
- Move **196** `SLR/2026/09/0001` **posted**, journal SLR (23)
- AML 921 Dr 240 account 131 analytic `{78:100}`; AML 922 Dr 400 account 131 analytic `{77:100}`; AML 923 Cr 640 account 57 **no analytic**
- Posted AAL 162/163: `general_account_id=131`, `move_line_id` 921/922
- Original timesheets 159/160 still `general_account_id` NULL (source hours unchanged)
- Second active batch for 2026-09: **blocked** (ValidationError)

`include_in_payroll` after install defaulted **True** on existing UAT rows (column default). No historical SQL was run.

# Include in Payroll Fix

- Default remains True
- Onchange / create / write: True unless `project.exclude_from_payroll`
- Does **not** copy `use_for_payroll`

# Period Key Fix

- `period_key` always `YYYY-MM` from `period_start`
- Same-calendar-month constraint on batch and wizard
- Populate domain uses dates (Jan 14/21 unit test added)

WP **#405 not closed** (original 600h / batch 444 evidence is a different snapshot).

# Accounting Verification

Existing GCC COA used (not invented):

| Role | ID | Name |
|------|----|------|
| Debit expense | 131 | Basic Salary - Projects (code 410028) |
| Credit clearing | 57 | ACCRUED SALARIES (code 202001) |
| Journal | 23 | Salaries (SLR) |

Industrial bucket mapping (مواد / overhead / مبيعات) is **FINANCE_MAPPING_REQUIRED** and was not guessed.

# Analytic Statement Fix

`_get_report_phase1_rows` is **AAL-primary**. AML explosion only if no AAL has that `move_line_id`.

UAT September rows (5): 2 eligible timesheets + 1 excluded timesheet (Timesheet / no GL) + 2 JE AAL (410028). `duplicate_aml=False`.

Financial **sum** of timesheet amounts **plus** JE AAL would double labour if used as a P&L. Transaction listing is intentional; P&L Excel is out of scope.

# Reconciliation

| Check | Result |
|-------|--------|
| Populate total | 640.00 |
| JE debit | 640.00 |
| JE credit | 640.00 |
| Posted | yes |
| Debit analytic | yes (two projects) |
| Credit analytic | empty |
| Prod `trgcc` journals | unchanged |

# Historical Data Anomalies

UAT clone (do **not** accrue until reviewed):

| id | date | hours |
|----|------|------:|
| 58 | 2026-01-31 | 260 |
| 29 | 2026-03-04 | 200 |
| 32 | 2026-03-04 | 200 |
| 30 | 2026-03-04 | 100 |
| 48 | 2026-02-28 | 43 |
| 49 | 2026-02-28 | 40 |
| 53 | 2026-04-08 | 25 |

Counts: ts=19 on UAT (10 cloned + UAT extras), gt24=7, eq200=2, eq260=1, nonpos=0.

No historical SQL on production. No historical SQL flag update on UAT (defaults already True).

# Screenshots

Folder: `/home/sabry/evidence/gulf_mm_uat_20260811/screenshots/`

Replacement UI proof (not home-page substitutes):

| File | What it proves |
|------|----------------|
| `21_timesheet_form_include_in_payroll.png` | Timesheet 159 form, **Include in Payroll** checked, Worker & payroll group |
| `22_project_onchange_optout_payroll_false.png` | New timesheet, project OptOut → Include in Payroll **unchecked** |
| `23_project_onchange_alpha_payroll_true.png` | Same form, project Alpha → Include in Payroll **checked** |
| `24_project_exclude_from_payroll.png` | Project OptOut form, **Exclude from payroll** checked |
| `25_company_labor_accrual_config.png` | Company Labor Accrual tab: 410028 / 202001 / Salaries |
| `26_analytic_statement_wizard.png` | Analytic Project Statement wizard (Export XLSX) |
| `27_timesheets_list_payroll_column.png` | All Timesheets list with Include in Payroll column |
| `29_statement_rows_timesheet_and_je.png` | Sept 2026 rows: Timesheet / no GL (yellow) + JE `SLR/2026/09/0001` once per project debit (blue, source=aal) |

JSON of the same rows: `sql/statement_rows.json` (5 rows, 3 Timesheet/no GL, 2 JE AAL, 0 AML duplicates).

# SQL Evidence

`/home/sabry/evidence/gulf_mm_uat_20260811/sql/` plus `before_after/e2e_result.json`.

# Logs

- Install: UAT modules installed; description HTML missing was fixed; no remaining CRITICAL after retry
- E2E: Worker accrual populate summary in Odoo logs
- Tests: `/home/sabry/evidence/gulf_mm_uat_20260811/logs/tests.log`

# Automated Tests

Re-run on `trgcc_mm_uat` only (log: `logs/tests.log`):

**0 failed, 0 error(s) of 54 tests.**

| Module | Tests | Result |
|--------|------:|--------|
| gpc_analytic_project_statement | 22 | PASS (1 justified SKIP) |
| gpc_hr_timesheet_labor_accrual | 35 | PASS (1 justified SKIP) |
| workers_timesheet | 7 | PASS |

Fixes (tests only; no production schema change, no fake AAL `analytic_distribution` column):

- Statement `setUpClass` now uses `TransactionCase` + Odoo 19 analytic **plan without `company_id`**.
- Labor helper no longer `UPDATE account_analytic_line.analytic_distribution` (column does not exist). `analytic_distribution` is asserted on **`account.move.line`**. Posted AAL is checked via `account_id`, `general_account_id`, `move_line_id`.
- Statement proves AAL-primary, Timesheet / no GL, posted JE once, no AML/AAL double count.

Justified SKIPs:

1. `test_line_specific_date_when_supported` — AAL-primary uses `account.analytic.line.date`; this schema stores the **journal date** on AAL, not AML `line_date`.
2. `test_populate_excludes_mo_timesheet_when_field_exists` — `account.analytic.line` has **no** `mrp_production_id` on this DB (`mrp_timesheet` not installed).

# Known Limitations

- Timesheet rows and JE AAL both appear on the statement (hours vs posted cost). That is a listing, not an Industrial P&L.
- `_post(soft=False)` required on this Odoo 19+e.
- `validated=True` required for populate (field exists on this DB).
- Odoo 19 `account.analytic.line` has no SQL column `analytic_distribution` (that JSON is on `account.move.line`).

# Out-of-Scope Change Request

Industrial P&L Excel report:
`CHANGE_REQUEST_REQUIRED`

Finance must define mappings for Materials, Direct Labor, Manufacturing Overhead, Revenue. No hardcoded guesses.

# Production Deployment Plan

WAIT FOR SABRY APPROVAL.

1. Backup `trgcc` again.
2. Deploy branch modules to `/opt/localaddons`.
3. `-i` on a **new** clone first, then production only after sign-off.
4. Configure company labor accounts (131 / 57 / SLR) only after Finance confirms.
5. Do **not** populate historical 200h/260h lines.

# Rollback Plan

- UAT: drop `trgcc_mm_uat` (not production). Restore dump `trgcc_20260811_223821.dump` if needed.
- Production: no changes to roll back. If later deployed: uninstall/upgrade reverse + restore the pre-deploy dump.

# OpenProject

- Parent: [#88](https://master.tailcf9988.ts.net:10081/work_packages/88)
- This work: [#441](https://master.tailcf9988.ts.net:10081/work_packages/441)
- Related comment on [#405](https://master.tailcf9988.ts.net:10081/work_packages/405) — **not closed**

# Git Commits

https://github.com/sabryyoussef/edafa_elhaleej/tree/gulf-mm-uat-20260811

`f5bb343`, `571a56e`, `2420797`, `accd2fe`, plus the test-schema adaptation commit on this branch.

# Final Verdict

`GULF_MM_UAT_PASS_READY_FOR_PROD_APPROVAL`

Production recommendation remains **do not deploy** until Sabry gives explicit approval. Industrial P&L Excel stays `CHANGE_REQUEST_REQUIRED`.
