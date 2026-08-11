# Historical AAL missing Financial Account — root cause

Database: **`trgcc_mm_uat`** (clone of `trgcc`). Captured 2026-08-11.

Scope: `account.analytic.line` where analytic `account_id` is set **and** `general_account_id IS NULL`.
Do not guess. Evidence is SQL on this clone plus batch/move tables.

Labor modules were **not** installed on production `trgcc`. Timesheet rows keep `general_account_id` NULL even after a labor JE posts; the **posted JE creates a new AAL** with `general_account_id` / `move_line_id`.

## Summary counts (primary cause)

| Primary classification | Count | IDs |
|------------------------|------:|-----|
| 7 Legacy + 9 anomalous hours (never accrued, no batch, hourly_cost=0) | 7 | 29, 30, 32, 48, 49, 53, 58 |
| 7 Legacy + 10 no amount source (hourly_cost=0; hours otherwise usable) | 3 | 54, 55, 59 |
| 2 `include_in_payroll` not selected | 3 | 155, 158, 161 |
| 5 Journal never generated (cancelled/empty August batch) | 4 | 153, 154, 156, 157 |
| Accrued; source timesheet has no GL **by design** (GL on JE AAL 162/163) | 2 | 159, 160 |
| 9 Zero hours | 1 | 313 |
| **Total missing-GL with analytic account** | **20** | |

Non-timesheet AAL with GL (not in the missing-GL set): 12, 13, 162, 163.
Material consumption 16, 17 have `general_account_id` but **NULL** `account_id` (no project analytic) — out of this missing-GL filter.

## Row detail

| AAL | Date | Employee | Project | Hours | Amount | Payroll | Batch | move_line_id | general_account_id | Primary cause | Evidence |
|----:|------|----------|---------|------:|-------:|:-------:|-------|-------------:|-------------------:|---------------|----------|
| 29 | 2026-03-04 | ABDUL BASITH SHAIK (1369) | Internal (4) / AA 64 | 200 | 0.00 | T | none | | | 9 anomalous hours | 200h; hourly_cost=0; no `labor_accrual_batch_line`; modules absent on prod |
| 30 | 2026-03-04 | BAHADUR SINGH BOGATI (1318) | Internal (4) / AA 64 | 100 | 0.00 | T | none | | | 9 anomalous hours | 100h; hourly_cost=0; no batch line |
| 32 | 2026-03-04 | ABDUL QADIR MOHAMMAD YASIN (1304) | Internal (4) / AA 64 | 200 | 0.00 | T | none | | | 9 anomalous hours | 200h; hourly_cost=0; no batch line |
| 48 | 2026-02-28 | ABDUL BASITH SHAIK (1369) | Internal (4) / AA 64 | 43 | 0.00 | T | none | | | 9 anomalous hours | 43h; hourly_cost=0; no batch line |
| 49 | 2026-02-28 | ARIJ EKBAL KHAN (1335) | Internal (4) / AA 64 | 40 | 0.00 | T | none | | | 9 anomalous hours | 40h; hourly_cost=0; no batch line |
| 53 | 2026-04-08 | Administrator (1448) | New project (3) / AA 63 | 25 | 0.00 | T | none | | | 9 anomalous hours | 25h; hourly_cost=0; no batch line |
| 54 | 2026-04-08 | Administrator (1448) | New project (3) / AA 63 | 5 | 0.00 | T | none | | | 10 no amount (`hourly_cost=0`) | Hours 5 are in range; `amount=0`; employee 1448 hourly_cost=0.00; no batch. **Not** a safe JE sample without inventing a rate |
| 55 | 2026-04-08 | Administrator (1448) | New project (3) / AA 63 | 2 | 0.00 | T | none | | | 10 no amount (`hourly_cost=0`) | Same as 54 |
| 58 | 2026-01-31 | ABDUL AZIZ MUHAMMAD FIAZ (1352) | Riyas Package 1&2 (6) / AA 38 | 260 | 0.00 | T | none | | | 9 anomalous hours | 260h; hourly_cost=0; no batch line |
| 59 | 2026-01-31 | ABDUL AZIZ MUHAMMAD FIAZ (1352) | Riyas Package 1&2 (6) / AA 38 | 20 | 0.00 | T | none | | | 10 no amount (`hourly_cost=0`) | 20h ≤24; still amount 0 / hourly_cost 0; no batch |
| 153 | 2026-08-05 | UAT MM Emp One (1456) | Alpha (15) / AA 73 | 8 | -400 | T | 3 cancelled | | | 5 JE never generated | Batch 3 cancelled; line existed; no move |
| 154 | 2026-08-05 | UAT MM Emp Two (1457) | Beta (16) / AA 74 | 6 | -240 | T | 3 cancelled | | | 5 JE never generated | Batch 3 cancelled |
| 155 | 2026-08-05 | UAT MM Emp One (1456) | OptOut (17) | 8 | -400 | F | none | | | 2 payroll not selected | `include_in_payroll=false`; project 17 `exclude_from_payroll=true` |
| 156 | 2026-08-05 | UAT MM Emp One (1458) | Alpha (18) / AA 75 | 8 | -400 | T | none | | | 5 JE never generated | Eligible; not on posted batch; August draft 6 had no lines at capture |
| 157 | 2026-08-05 | UAT MM Emp Two (1459) | Beta (19) / AA 76 | 6 | -240 | T | none | | | 5 JE never generated | Same as 156 |
| 158 | 2026-08-05 | UAT MM Emp One (1458) | OptOut (20) | 8 | -400 | F | none | | | 2 payroll not selected | `include_in_payroll=false` |
| 159 | 2026-09-10 | UAT MM Emp One (1460) | Alpha (21) / AA 77 | 8 | -400 | T | 5 posted | | | Source AAL has no GL by design | Batch 5 / move 196; GL on AAL **162** (`general_account_id=131`, `move_line_id=922`) |
| 160 | 2026-09-10 | UAT MM Emp Two (1461) | Beta (22) / AA 78 | 6 | -240 | T | 5 posted | | | Source AAL has no GL by design | GL on AAL **163** (`general_account_id=131`, `move_line_id=921`) |
| 161 | 2026-09-10 | UAT MM Emp One (1460) | OptOut (23) | 8 | -400 | F | none | | | 2 payroll not selected | Excluded from batch 5 populate |
| 313 | 2026-08-11 | Administrator (1448) | Alpha (15) / AA 73 | 0 | 0.00 | T | none | | | 9 zero hours | `unit_amount=0`; `validated` NULL; leftover UI draft |

## Why old analytical items lack Financial Account

1. **Odoo timesheets are analytic-only until a journal posts a linked AAL.** `general_account_id` on the **timesheet** row is not filled by validation.
2. **Labor accrual was not deployed on production**, so no monthly JE existed for Jan–Apr 2026 rows.
3. **Original GCC employees have `hourly_cost=0`**, so even a later populate would skip them (`amount=0`).
4. **Anomalous hours** (25–260) are excluded from remediation until Finance validates them.
5. After a labor JE **does** post, Financial Account appears on the **new** AAL (`move_line_id` set), not by rewriting history on the timesheet.

## Safe vs excluded for retroactive UAT

**Excluded (do not accrue):** 29, 30, 32, 48, 49, 53, 58 (anomalous hours); 54, 55, 59 (no amount source — would invent rates); 155, 158, 161 (payroll opt-out); 313 (zero hours); 159, 160 (already in posted batch 5).

**Safe small sample (proven amount, ≤8h, payroll true, never posted):** **153, 154** (August; cancelled batch 3). 156/157 same pattern — held out of this sample (not mass-posted).
