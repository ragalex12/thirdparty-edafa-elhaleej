# Analytical Items vs Journal Items

Meeting: change report data source to **Analytical Items**, not Journal Items.

Database: `trgcc_mm_uat`. Excel P&L columns were **not** added.

## Scenario 1 — Timesheet exists, no Journal Item

| | |
|--|--|
| Example | `MM-UAT-TS-2026-05-001` (and all `MM-UAT-TS-*`) |
| Analytical Item | YES (`account.analytic.line`, `account_id` set) |
| Journal Item | NO (`move_line_id` NULL, `general_account_id` NULL) |
| Statement | YES — account label **Timesheet / no GL** |

SQL: 124 MM-UAT timesheets, all still no GL after posting labor JEs (source row is never rewritten).

## Scenario 2 — Labor JE posted

| | |
|--|--|
| Example | `SLR/2026/05/0001` move 396, batch 280 |
| Journal Items | YES — 5 debit 410028 with analytic + 1 credit 202001 **without** analytic |
| Resulting AAL | YES — new AAL with `general_account_id=131`, `move_line_id` set |
| Statement | Uses **AAL** (`source=aal`); AML fallback does not duplicate |

May JE: debit 4970 = credit 4970. Credit analytic empty by design.

## Scenario 3 — Material accounting line

| | |
|--|--|
| Example | `MISC/2026/05/0006` move 393, ref `MM-UAT-MAT-BETA-2026-05` |
| Journal Items | Dr 1500 account 97 Material Tools + analytic; Cr 1500 account 156 no analytic |
| GL-backed AAL | YES on the debit |
| Statement | Financial account = Material Tools, not Timesheet / no GL |

Offset credit has no project analytic, so it does **not** appear as a project credit. That is AAL-primary behaviour, not a P&L netting rule.

## No duplication check

Posted JE appears once per analytic debit slice. Automated: `test_no_duplicate_when_aal_represents_aml`. UAT export Apr–Oct 2026: 154 statement rows.
