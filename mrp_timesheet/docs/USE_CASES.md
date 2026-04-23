# Manufacturing Timesheet — Use Cases

Each use case shows the **accounting entries** produced so you can trace exactly what the module posts.

---

## Use Case 1: Basic MO — Regular Time

**Scenario:** A worker logs 4 hours on a Manufacturing Order at SAR 100/h.

### Configuration
- Labor WIP Account: `510100 – Manufacturing WIP`
- Labor Clearing Account: `215100 – Payroll Accrual`
- Employee hourly_cost: `100.00 SAR`

### Steps
1. Open the MO → Timesheets tab → Add line: Employee=Ahmed, Hours=4, Description="Assembly".
2. Save.

### Journal Entry created instantly
```
Date     Account                         DR        CR      Analytic
----     -------                         --        --      --------
2025-03  510100  Manufacturing WIP      400.00            MO-Analytic (100%)
2025-03  215100  Payroll Accrual                  400.00  MO-Analytic (100%)
```
Ref: `LABOR/WH1/MO/00042/2025-03-15`  
Narration: `Employee: Ahmed | Hours: 4.00 | Type: Regular | Cost: 400.00 SAR | Triggered by: Ahmed (uid=12)`

### When payroll runs (Step 2 — outside this module)
```
Date     Account                         DR        CR
----     -------                         --        --
2025-03  215100  Payroll Accrual        400.00
2025-03  310100  Wages Payable                    400.00
```
After payroll: Clearing balance = 0 ✓

---

## Use Case 2: Overtime Hours

**Scenario:** Same worker logs 3 overtime hours on the same MO. Company overtime multiplier = 1.5×.

### Steps
1. Add a second line: Hours=3, **tick Is Overtime**.
2. Save.

### Journal Entry
```
Cost = 3 × 100 × 1.5 = 450.00 SAR

DR  510100  Manufacturing WIP     450.00
CR  215100  Payroll Accrual                450.00
```
Narration: `... | Type: Overtime | Cost: 450.00 SAR | ...`

---

## Use Case 3: Holiday Hours

**Scenario:** A line is marked as holiday (2.0×). Is Overtime is also ticked — holiday takes precedence.

```
Cost = 2h × 100 × 2.0 = 400.00 SAR  (not 1.5×, holiday wins)

DR  510100  Manufacturing WIP     400.00
CR  215100  Payroll Accrual                400.00
```
Narration: `... | Type: Holiday | Cost: 400.00 SAR | ...`

---

## Use Case 4: Editing a Timesheet Line (Reversal + Recreate)

**Scenario:** You originally logged 2 hours but the actual time was 5 hours. You edit the line.

### Original JE (on create)
```
DR  510100  Manufacturing WIP     200.00
CR  215100  Payroll Accrual                200.00
Ref: LABOR/WH1/MO/00042/2025-03-15
```

### After changing Hours from 2 → 5 (automatic reversal)
```
Reversal JE (auto):
DR  215100  Payroll Accrual       200.00
CR  510100  Manufacturing WIP              200.00
Ref: REV/LABOR/WH1/MO/00042/2025-03-15

New JE (auto):
DR  510100  Manufacturing WIP     500.00
CR  215100  Payroll Accrual                500.00
Ref: LABOR/WH1/MO/00042/2025-03-15
```

Net effect: WIP = 500, Clearing = 500 (correct final state).

---

## Use Case 5: Deleting a Timesheet Line

**Scenario:** A line was added by mistake. You delete it.

### On delete (automatic reversal before deletion)
```
Reversal JE:
DR  215100  Payroll Accrual       200.00
CR  510100  Manufacturing WIP              200.00
Ref: REV/LABOR/...
```

Net effect: WIP = 0, Clearing = 0 (as if the line was never added).

---

## Use Case 6: Multiple Workers, Multiple Days

**Scenario:** Production order WH1/MO/00042 runs over 3 days with 3 employees.

| Date | Employee | Hours | Rate | Cost |
|------|----------|-------|------|------|
| 2025-03-10 | Ahmed (Assembler) | 4 | 100 | 400 |
| 2025-03-10 | Sara (Technician) | 3 | 120 | 360 |
| 2025-03-11 | Ahmed | 6 | 100 | 600 |
| 2025-03-12 | Khalid (Specialist) | 2 | 150 | 300 |

Each save creates its own JE immediately. **Total WIP debit = 1,660 SAR.**

### Timesheet Labor Cost on MO = 1,660.00 SAR

### On payroll: single clearing debit of 1,660.00 SAR

---

## Use Case 7: Project-Based Timesheet (No MO)

**Scenario:** A consulting project tracks labor costs without Manufacturing Orders.

### Configuration
- Open the project → Settings tab → Enable **Generate Labor Journal Entries**
- Optionally set project-level WIP/Clearing overrides

### Steps
1. Log time on the project in Timesheets (standard Odoo timesheet).
2. Save — JE is created using project accounts (or company defaults).

```
DR  510100  Manufacturing WIP     300.00    ← or project override account
CR  215100  Payroll Accrual                300.00
```

> **Note:** Analytic distribution uses the timesheet line's analytic account when no MO analytic account is set.

---

## Use Case 8: Per-Project Account Override

**Scenario:** Project "EXPO-2025" should charge to a different WIP account than the default.

### Configuration on Project
- Labor WIP Account (Override): `510200 – Project Cost EXPO`
- Labor Clearing Account (Override): leave blank → falls back to company default

### JE for timesheets on EXPO-2025
```
DR  510200  Project Cost EXPO     200.00    ← project override
CR  215100  Payroll Accrual                200.00    ← company default
```

---

## Use Case 9: Workcenter Account Override

**Scenario:** Work orders on "CNC Machine" should debit a specific machine cost account.

### Configuration on Workcenter
- Labor Account (Override): `510300 – CNC Machine Labor`

### JE for timesheets linked to MOs with CNC work orders
```
DR  510300  CNC Machine Labor     150.00    ← workcenter override
CR  215100  Payroll Accrual                150.00    ← company default
```

---

## Use Case 10: Missing Configuration (Safe Degradation)

**Scenario:** Clearing account is not set. A timesheet line is saved.

**Result:**
- `labor_cost` is still computed correctly (e.g. 200.00 SAR).
- No JE is created (silent skip — no error, no crash).
- The **Labor Clearing Balance Check** wizard will show 0 for this period.
- You can configure the accounts later and the next edit to the line will generate the JE.

---

## Use Case 11: Clearing Account Balance Check

**Scenario:** End of month. You want to confirm payroll cleared all timesheet accruals.

### Steps
1. Go to **Manufacturing → Reporting → Labor Clearing Balance Check**.
2. Set Date From: `2025-03-01`, Date To: `2025-03-31`.
3. Click **Check Balance**.

### Example result
| Period | Accrued (CR) | Cleared by Payroll (DR) | Outstanding |
|--------|-------------|------------------------|-------------|
| March 2025 | 2,460.00 | 2,460.00 | **0.00** ✓ |
| April 2025 | 800.00 | 0.00 | **800.00** ← payroll not yet run |

Outstanding > 0 in a prior closed period indicates a reconciliation gap.

---

## Use Case 12: Multi-Company Isolation

**Scenario:** Company A and Company B share the same Odoo instance. Workers in Company A should not see MO timesheets from Company B.

**How it's enforced:**
- Global `ir.rule` on `account.analytic.line` restricts visibility to MOs whose company is in the current user's allowed companies.
- `check_company=True` on all `Many2one` account fields prevents cross-company account selection in the UI.
- JE creation always uses `company_id = timesheet_line.company_id`.

No additional configuration required — this is enforced automatically.

---

## Summary Table

| Use Case | Key Feature | JE Created? |
|----------|------------|-------------|
| Regular MO time | `create()` trigger | Yes |
| Overtime | `is_overtime` flag × 1.5 | Yes |
| Holiday | `is_holiday` flag × 2.0 | Yes (overrides overtime) |
| Edit hours | `write()` trigger | Old reversed + new |
| Delete line | `unlink()` trigger | Old reversed |
| Multiple workers | Per-line JEs | One per line |
| Project (no MO) | `generate_labor_je=True` | Yes |
| Project override | Project account fields | Yes (different accounts) |
| Workcenter override | `labor_account_id` | Yes (different WIP) |
| Missing config | Silent degradation | No (no crash) |
| Month-end check | Clearing balance wizard | N/A (reporting) |
| Multi-company | `ir.rule` + `check_company` | N/A (security) |
