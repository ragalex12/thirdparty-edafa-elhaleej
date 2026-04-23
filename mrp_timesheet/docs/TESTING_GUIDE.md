# Manufacturing Timesheet — Testing Guide

This guide explains how to manually test every feature of the module step by step. It mirrors the automated test cases TC-01 → TC-07 (in `tests/test_mrp_timesheet.py`) with UI-friendly instructions.

---

## Before You Start

### Minimum setup required

1. **Company → Labor Cost Accounting tab** — set:
   - Labor WIP Account (any asset/WIP account, e.g. `510100`)
   - Labor Clearing Account (any liability account, e.g. `215100`)
   - Labor Cost Journal (any General journal)

2. **One employee** with `hourly_cost > 0` (e.g. SAR 100/h)
   `Employees → [Employee] → HR Settings → Hourly Cost = 100`

3. **One Manufacturing Order** with an Analytic Account set
   `Manufacturing → Operations → Manufacturing Orders → Analytic Account`

> **Tip:** You can verify setup quickly in **Settings → Companies → Labor Cost Accounting tab** and confirm all three fields are set.

---

## TC-01 — Basic MO Timesheet → Correct JE Accounts

**What we test:** Saving a timesheet line on an MO creates a posted JE that debits WIP and credits Clearing.

### Steps
1. Open an MO that has an Analytic Account set.
2. Go to the **Timesheets** tab.
3. Add a line:
   - Employee: (your test employee with hourly_cost=100)
   - Hours: `2`
   - Description: `TC-01 test`
   - Date: today
4. Click **Save** (or navigate away).

### Expected results
- **Labor Cost** column on the line = `200.00`
- **JE** column shows a JE reference (e.g. `TA/2025/03/0001`)
- Open that JE:
  - State: **Posted**
  - 2 lines:
    - DR 200.00 → your Labor WIP Account
    - CR 200.00 → your Labor Clearing Account
  - Narration: `Employee: ... | Hours: 2.00 | Type: Regular | Cost: 200.00 SAR | Triggered by: ...`
  - Analytic distribution: 100% to the MO's analytic account

### ✓ Pass criteria
- [ ] JE is posted
- [ ] DR = WIP account, CR = Clearing account
- [ ] Amount = 200.00
- [ ] Analytic distribution set

---

## TC-02 — Overtime / Holiday Multipliers

**What we test:** `is_overtime` applies 1.5× multiplier; `is_holiday` applies 2.0× and takes precedence.

### Steps — Overtime
1. On the same MO, add another timesheet line:
   - Employee: same, Hours: `4`, tick **Is Overtime**
2. Save.

### Expected result
- Labor Cost = `600.00` (4 × 100 × 1.5)
- JE debit = `600.00`

### Steps — Holiday
1. Add another line: Hours: `2`, tick both **Is Overtime** AND **Is Holiday**
2. Save.

### Expected result
- Labor Cost = `400.00` (2 × 100 × 2.0 — holiday takes precedence)
- JE narration shows `Type: Holiday`

### ✓ Pass criteria
- [ ] Overtime line: cost = 600
- [ ] Holiday line: cost = 400 (not 300)
- [ ] Narration shows correct type

---

## TC-03 — Edit Timesheet Line → JE Reversed + Recreated

**What we test:** Changing hours reverses the original JE and posts a new one.

### Steps
1. Use the TC-01 line (2h = 200.00, has a JE).
2. Note the JE reference from the **JE** column.
3. Change **Hours** from `2` to `5`.
4. Save.

### Expected results
- **Labor Cost** = `500.00`
- **JE** column shows a **new** JE reference (different from the original)
- Open the **original** JE:
  - It now has a **Reversal Move** (see Reversal entry button or `reversal_move_ids`)
  - The reversal is also posted (DR/CR swapped for 200.00)
- Open the **new** JE:
  - DR 500.00 → WIP account
  - CR 500.00 → Clearing account

### ✓ Pass criteria
- [ ] Original JE reversed
- [ ] New JE = 500.00
- [ ] Old JE has reversal_move_ids populated

---

## TC-04 — Missing Account Config → No JE, No Crash

**What we test:** If the Clearing account is not set, no JE is created but the system does not crash.

### Steps
1. Go to **Settings → Companies → Labor Cost Accounting tab**.
2. **Clear** the **Labor Clearing Account** field. Save.
3. On an MO, add a timesheet line: Hours=2, Employee with hourly_cost=100.
4. Save.

### Expected results
- **Labor Cost** = `200.00` (field still computed correctly)
- **JE** column = empty (no JE created)
- No error message shown

5. Restore the Clearing account in company settings.

### ✓ Pass criteria
- [ ] No error
- [ ] labor_cost computed correctly
- [ ] No JE created

---

## TC-05 — Project-Based Timesheet JE

**What we test:** Timesheets on a project (no MO link) generate JEs only when the project's `generate_labor_je` toggle is enabled.

### Steps — Project WITH toggle ON
1. Go to **Project → [any project] → Settings tab → Labor Cost Accounting**.
2. Enable **Generate Labor Journal Entries**. Save.
3. Go to **Timesheets → My Timesheets** (or Timesheets app).
4. Add a new line linked to that project (no MO):
   - Employee, Hours=3, Date, Description.
5. Save.

### Expected result
- **Labor Cost** column (if shown) = `300.00`
- A JE is created linked to this line

### Steps — Project WITHOUT toggle
1. On a **different** project (or the same with toggle OFF):
2. Add a timesheet line: Hours=3.
3. Save.

### Expected result
- **Labor Cost** = `300.00` (computed)
- **No JE** created

### ✓ Pass criteria
- [ ] Toggle ON → JE created
- [ ] Toggle OFF → no JE, no error

---

## TC-06 — Multi-Company: JE in Correct Company

**What we test:** The generated JE belongs to the same company as the timesheet line.

### Steps
1. Create a timesheet line on an MO (as in TC-01).
2. Open the generated JE.
3. Check the **Company** field on the JE header.
4. Go to **Journal Items** tab — check **Company** on each line.

### Expected results
- JE Company = timesheet line's company
- All journal item lines have the same company

### ✓ Pass criteria
- [ ] JE company = correct company
- [ ] All move lines = same company

---

## TC-07 — Delete Timesheet → JE Reversed

**What we test:** Deleting a timesheet line that has a JE automatically reverses the JE first.

### Steps
1. On an MO, create a timesheet line (2h → JE created for 200.00).
2. Note the JE reference.
3. **Delete the line** (click the trash icon on the timesheet row, or use the Action menu).

### Expected results
- The timesheet line is gone
- The original JE now has a **reversal entry** (REV/LABOR/...)
- The reversal JE is **Posted**
- Net accounting impact = 0 (as if the line was never created)

### ✓ Pass criteria
- [ ] Line deleted
- [ ] Original JE has reversal
- [ ] Reversal is posted

---

## TC-08 — Clearing Account Balance Check Wizard

**What we test:** The wizard correctly reports outstanding (uncleared) balances.

### Steps
1. Complete TC-01 (creates a 200 SAR JE on clearing account).
2. Go to **Manufacturing → Reporting → Labor Clearing Balance Check**.
3. Set:
   - Company: your company
   - From: first day of current month
   - To: today
4. Click **Check Balance**.

### Expected results
- **Total Accrued (CR)** ≥ 200.00 (at least the TC-01 entry)
- **Total Cleared by Payroll (DR)** = whatever payroll has posted
- **Outstanding** = CR − DR
- Monthly breakdown shown in the detail table

### ✓ Pass criteria
- [ ] Wizard opens without error
- [ ] CR > 0 (reflects the test JEs)
- [ ] Detail lines grouped by month

---

## TC-09 — Account Validation Constraints

**What we test:** The constraints prevent misconfiguration.

### Test A — WIP = Clearing (should fail)
1. Go to **Settings → Companies → Labor Cost Accounting tab**.
2. Set **Labor Clearing Account** to the **same** account as **Labor WIP Account**.
3. Click **Save**.
4. Expected: **Validation Error** — "WIP Account and Clearing Account must be different."

### Test B — Multiplier < 1.0 (should fail)
1. Set **Overtime Rate Multiplier** to `0.5`.
2. Click **Save**.
3. Expected: **Validation Error** — "Overtime Rate Multiplier must be ≥ 1.0."

### Test C — Clearing account wrong type (advisory)
1. Set **Labor Clearing Account** to an **expense** account (not a liability).
2. Click **Save**.
3. Expected: **Validation Error** with advice to use a liability account.

### ✓ Pass criteria
- [ ] Test A raises error
- [ ] Test B raises error
- [ ] Test C raises error with account_type guidance

---

## TC-10 — View Restrictions (Account Manager Only)

**What we test:** Labor account fields are hidden for non-accounting users.

### Steps
1. Log in as a **Manufacturing User** (not in Accounting group).
2. Open **Settings → Companies** → select your company.
3. Check: the **Labor Cost Accounting** tab should **not be visible**.
4. Open an MO → Timesheets tab → the **Labor Cost** and **JE** columns should not be visible.
5. Open **Manufacturing → Configuration → Work Centers** → the **Labor Account (Override)** field should not be visible.

### Log in as **Accounting Manager**
6. Same checks — all fields and tabs should now be visible.

### ✓ Pass criteria
- [ ] Non-accounting user cannot see account config fields
- [ ] Accounting manager can see all fields

---

## Automated Test Suite

The automated tests in `tests/test_mrp_timesheet.py` cover TC-01 → TC-07 programmatically.

To run them (requires a test database without broken third-party addons):

```bash
python3 /usr/bin/odoo \
  --db_host=127.0.0.1 --db_user=odoo --db_password=<pass> \
  -d <test_db> \
  --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/opt/localaddons \
  --test-enable \
  "--test-tags=/mrp_timesheet" \
  --stop-after-init --no-http --workers=0
```

Alternatively, the tests can be run via RPC against a live database using the verification scripts used during development (see development notes for the `trgulf_Mrp` database).

---

## Quick Smoke Test Checklist

For a fast sanity check after install or upgrade:

- [ ] Company Labor Cost Accounting tab visible (logged in as Accounting Manager)
- [ ] Set WIP, Clearing, Journal on company
- [ ] Set hourly_cost on one employee
- [ ] Create MO → add timesheet line → save → JE appears in JE column
- [ ] Edit hours → JE is reversed + new one created
- [ ] Delete line → JE is reversed
- [ ] Open Labor Clearing Balance Check → wizard loads, shows balance
