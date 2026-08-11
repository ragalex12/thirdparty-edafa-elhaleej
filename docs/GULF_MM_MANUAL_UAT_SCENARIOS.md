# Gulf/MM manual UAT scenarios

Environment: `trgcc_mm_uat` only. Industrial P&L logic is out of scope.

Legend: **PASS** = verified this run (SQL / automated test / generated XLSX). Screenshot column points at evidence files.

| Test ID | Title | Meeting | Preconditions | Test data | Steps | Expected | Actual | PASS/FAIL | Screenshot | SQL | Notes |
|---------|-------|---------|---------------|-----------|-------|----------|--------|-----------|------------|-----|-------|
| MM-UAT-001 | New 8h timesheet + Generate Journal | M01 | Labor config 131/57/23 | EMP-01 Alpha May | Create TS → populate → draft → post | Balanced JE | SLR/2026/05/0001 4970 | PASS | 50_dataset_overview | move 396 | Demo Alpha |
| MM-UAT-002 | Normal 6h line | M01 | same | TS-2026-05-002 6h | Include in May batch | Amount 6×50 | in batch 280 | PASS | 50 | batch lines | |
| MM-UAT-003 | Multiple lines same employee/day | M01 | same | 007+008 on 2026-05-06 | Both stored | Two AALs | PASS | 51_timesheets | aal names | |
| MM-UAT-004 | Multiple projects same employee/day | M01 | same | MULTI-A / MULTI-B | Two projects 4h+4h | Both populated | PASS | 51 | batch 280 | |
| MM-UAT-005 | Different hourly costs | M01 | EMP-01/02/03 | 50/40/30 | Amounts = h×rate | 5 debit slices May | PASS | 52_je_posted | move 396 | |
| MM-UAT-006 | include_in_payroll True default | M04 | normal project | new TS | Flag true | True | PASS | auto payroll tests | | |
| MM-UAT-007 | include_in_payroll False opt-out | M04 | OPTOUT project | TS-2026-05-EXCL | Populate skips | Not in batch 280 | PASS | 51 | payroll_false=3 | |
| MM-UAT-008 | Project onchange keeps True | M04 | normal project | onchange | Flag stays true | True | PASS | auto | | |
| MM-UAT-009 | Opt-out onchange False | M04 | OPTOUT | onchange | Flag false | False | PASS | auto | | |
| MM-UAT-010 | Anomaly hours 25–260 | M03 | HIST Apr 28 | ANOM-* | Stored; not in Apr 1–7 batch | 5 rows unit_amount>24 | PASS | 53_anomalies | anom_gt24=5 | Populate does not filter >24h if in range |
| MM-UAT-011 | Zero hours | M03 | ALPHA | ZEROHOURS | Populate skip | unit_amount=0 | PASS | 53 | | |
| MM-UAT-012 | Posted labor JE accounts | M06 | batch 280 | move 396 | Dr 410028 analytic; Cr 202001 none | Balanced | PASS | 52 | SQL aml | |
| MM-UAT-013 | Draft JE stays draft | M13 | October | move 399 | Do not post | state=draft, unnamed | PASS | 54_draft_je | move 399 | Posted statement excludes it |
| MM-UAT-014 | Retroactive April 1–7 | M07 M16 | LEGACY TS | batch 281 | Post SLR/2026/04/0001 | 4 lines 1600 | PASS | 55_retro | batch 281 | Source TS still no GL |
| MM-UAT-015 | Source TS remains no GL | M12 | after post | May TS | Inspect general_account_id | NULL | PASS | 55 | aal_ts_no_gl=124 | By design |
| MM-UAT-016 | Held-back April 20–25 | M16 | HELD TS | not in 1–7 period | Still no GL, no batch | 5 TS | PASS | 55 | HELD names | Staged |
| MM-UAT-017 | Zero hourly cost skipped | M03 | EMP-04 | ZEROCOST | Populate skip | amount 0 | PASS | auto | | |
| MM-UAT-018 | Duplicate-looking TS both accrue | M01 | DUP-A/B | same day/project/hours | Two batch lines | both in 280 | PASS | 51 | | |
| MM-UAT-019 | Duplicate period blocked | M01 | May posted | create second May | ValidationError | Error then cancelled leftover | PASS | 54 | batches 284 cancelled | Seeder now uses savepoint |
| MM-UAT-020 | Statement AAL-primary | M02 | wizard Apr–Oct | 154 rows | JE via AAL | PASS | 56_statement | inventory | |
| MM-UAT-021 | Timesheet / no GL label | M02 | TS rows | account column | Label present | PASS | 56 | | |
| MM-UAT-022 | Material GL account on statement | M02 S3 | BETA MISC | Material Tools | Not Timesheet label | PASS | 56 | move 393 | |
| MM-UAT-023 | No AML/AAL duplicate | M17 | posted JE | one row per slice | source=aal | PASS | auto | | |
| MM-UAT-024 | Large result set | M17 | June 84 lines | 50+ report rows | 154 rows | PASS | 56 | | |
| MM-UAT-025 | Foreign company timesheet | M15 | company 23 | TS-WRONGCO | GCC batch ignores | foreign.ok | PASS | 57_company | res_company 23 | |
| MM-UAT-026 | Foreign journal/accounts blocked | M15 | SQL bypass tests | UserError | No move | PASS | auto 3 guards + credit | | |
| MM-UAT-027 | Cross-month period rejected | M01 | Nov–Dec | ValidationError | PASS | auto + seeder | | savepoint |
| MM-UAT-028 | XLSX equals Phase-1, no P&L | M08 | styled export | RTL, 6 columns | No مواد/أجور/… | PASS | 44/47 + new xlsx | mm_uat_extended_statement.xlsx | |
| MM-UAT-029 | Empty statement range | M17 | 2010 dates | 0 rows | PASS | auto test_empty_result | | |
| MM-UAT-030 | Production untouched | M05 | trgcc | 10 TS, 0 labor mods | PASS | prod SQL this run | | |
| MM-UAT-031 | Arabic timesheet on XLSX | M08 | TS-عربي-001 | string in export | PASS | xlsx | | |
| MM-UAT-032 | Mixed eligible/ineligible populate | M04 | May EXCL + eligible | 16 lines | PASS | batch 280 | | |
| MM-UAT-033 | GLONLY material without TS labor | M02 | move 394 | statement GL row | PASS | 56 | | |
| MM-UAT-034 | Demo path Alpha 3 workers | client demo | EMP-01..03 | TS→JE→statement | PASS | 50 | | |
| MM-UAT-035 | Rerun populate on posted blocked | M01 | batch 280 posted | UserError/state | posted immutable populate | PASS | code `state != draft` | | |

Manual PASS: **35/35** executed scenarios (automated + SQL). UI click-path screenshots for every row were not re-recorded; dataset HTML pack **50–57** covers the records.
