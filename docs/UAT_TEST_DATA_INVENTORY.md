# UAT test data inventory

Database: **`trgcc_mm_uat`**  
Marker: `gulf.mm.uat.extended_dataset.v1`  
Prefix: `MM-UAT-*`  
Historical production clones (AAL 29–59, earlier UAT 153–163) were **not** overwritten.

Full JSON: `evidence/.../xlsx/mm_uat_extended_inventory.json`

## Companies

| ID | Name |
|---:|------|
| 1 | GCC |
| 23 | MM-UAT-CO-FOREIGN |

## Projects

| Key | project_id | analytic_id | Notes |
|-----|----------:|------------:|-------|
| ALPHA | 115 | 245 | Demo payroll project |
| BETA | 116 | 246 | Timesheet + material |
| LEGACY | 117 | 247 | April retro subset |
| PAYROLL | 118 | 248 | Default include payroll |
| OPTOUT | 119 | 249 | `exclude_from_payroll=True` |
| GLONLY | 120 | 250 | Material JE only |
| TSONLY | 121 | 251 | Timesheet only |
| MIXED | 122 | 252 | TS + material |
| HIST | 123 | 253 | Anomaly / zero-cost |
| HELD | 124 | 254 | Held-back April 20–25 |
| WRONGCO | 126 | (foreign AA) | Company 23 |

## Employees

| Key | id | hourly_cost | Role |
|-----|---:|------------:|------|
| 01 | 1514 | 50 | Alpha demo |
| 02 | 1515 | 40 | Alpha / retro |
| 03 | 1516 | 30 | Alpha / retro |
| 04 | 1517 | 0 | Zero cost (populate skip) |
| 05 | 1518 | 75 | Mixed / retro |
| 06 | 1519 | 50 | Opt-out lines |
| 07 | 1520 | 45 | Multi-project / Arabic TS |
| 08 | 1521 | 50 | Anomaly hours |
| 09 | 1522 | 40 | Beta |
| 10 | 1523 | 55 | Legacy / held |
| 12 | 1524 | 50 | Duplicate-looking |
| 11 | 1525 | 50 | Foreign company 23 |

## Timesheets

124 lines named `MM-UAT-TS-*` (123 seeded + 1 foreign). All remain `general_account_id` NULL.

| Bucket | Count (approx) |
|--------|----------------|
| Payroll true | 121 |
| Payroll false | 3 |
| Hours > 24 | 5 (25/40/100/200/260) |
| Zero hours | 1 |

## Material / misc moves (existing COA)

| id | name | amount | project |
|---:|------|-------:|---------|
| 393 | MISC/2026/05/0006 | 1500 | BETA |
| 394 | MISC/2026/05/0007 | 2200 | GLONLY |
| 395 | MISC/2026/05/0008 | 800 | MIXED |

Accounts: Dr 97 Material Tools, Cr 156 INCOME FROM PROJECTS (balancing only; not a P&L mapping).

## Labor batches

| id | name | period | state | lines | move |
|---:|------|--------|-------|------:|------|
| 280 | MM-UAT-BATCH-2026-05-POSTED | 2026-05 | posted | 16 | 396 `SLR/2026/05/0001` 4970 |
| 281 | MM-UAT-BATCH-2026-04-RETRO | 2026-04 (1–7) | posted | 4 | 397 `SLR/2026/04/0001` 1600 |
| 282 | MM-UAT-BATCH-2026-06-POSTED | 2026-06 | posted | 84 | 398 `SLR/2026/06/0001` 31680 |
| 283 | MM-UAT-BATCH-2026-10-DRAFT | 2026-10 | draft | 3 | 399 draft 1040 |

Duplicate-period and cross-month creates were attempted, raised ValidationError, and leftover rows were **cancelled** (ids 284, 285).

## Statement / XLSX

Wizard GCC, 2026-04-01 → 2026-10-31, posted: **154 rows**, debit 121090, credit 0 (credits have no analytic).  
File: `xlsx/mm_uat_extended_statement.xlsx`.

## Config (unchanged GCC)

Debit 131 `410028` · Credit 57 `202001` · Journal 23 SLR.
