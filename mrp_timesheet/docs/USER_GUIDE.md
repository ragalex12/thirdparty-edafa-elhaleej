# Manufacturing Timesheet — User Guide

**Module version:** 19.0.8.0  
**Applies to:** Odoo 19 Community/Enterprise

---

## 1. Prerequisites

Before using this module you need:

| App | Purpose |
|-----|---------|
| Manufacturing (`mrp`) | Manufacturing Orders |
| Timesheets (`hr_timesheet`) | Timesheet lines |
| Stock Accounting (`stock_account`) | Accounting journals |
| HR (`hr`) | Employee records |
| Project (`project`) | Project-based JEs (optional) |
| Accounting (`account`) | Chart of accounts, journal entries |

Users who configure accounts must be in the **Accounting / Administrator** group.  
Users who log time only need standard Manufacturing user rights — the module uses `sudo()` internally for JE creation.

---

## 2. First-time Configuration

### 2.1 Open the Labor Cost Accounting tab

`Settings → Companies → [Your company] → Labor Cost Accounting tab`

> **Tip:** This tab is only visible to users with the Accounting / Administrator role.

---

### 2.2 Set the two accounts

The module uses a **two-account transit model**:

| Field | Account type | Example code | Description |
|-------|-------------|-------------|-------------|
| **Labor WIP Account** | Asset / Current Asset | `510100` | Debited immediately when a timesheet line is saved. Represents direct labor absorbed into the product's production cost. |
| **Labor Clearing Account** | Liability / Current Liability | `215100` | Credited immediately when a timesheet line is saved. A transit account that is zeroed-out when payroll runs. |

**Why two accounts?**  
This is the standard two-step payroll accrual approach:
```
Step 1 (timesheet saved)   DR Labor WIP 510100   CR Labor Clearing 215100
Step 2 (payroll confirmed) DR Labor Clearing      CR Wages Payable / Bank
```
After payroll, Clearing = 0, WIP carries the cost, Wages Payable shows cash owed.

---

### 2.3 Set the Labor Cost Journal

| Field | Type | Description |
|-------|------|-------------|
| **Labor Cost Journal** | General / Miscellaneous journal | The journal used for all automatic labor JEs. Falls back to the company stock journal if not set. |

> **Tip:** Create a dedicated journal called "Labor Cost" so labor entries are easily filtered in the General Ledger.

---

### 2.4 Set rate multipliers (optional)

| Field | Default | When applied |
|-------|---------|-------------|
| **Overtime Rate Multiplier** | 1.5 | When **Is Overtime** is ticked on a timesheet line |
| **Holiday Rate Multiplier** | 2.0 | When **Is Holiday** is ticked (takes precedence over overtime) |

Set to `1.0` to disable a multiplier.

---

### 2.5 Set employee hourly cost

`Employees → [Employee] → HR Settings tab → Hourly Cost`

The system resolves the rate in this priority order:

1. `employee.hourly_cost` — set directly on the employee
2. `employee.timesheet_cost` — if the HR Payroll module adds this field
3. `product.standard_price` — on the timesheet line's product
4. `0.0` — no JE created (labor cost = 0)

---

### 2.6 Optional: Per-project JE toggle

`Project → [Project] → Settings tab → Labor Cost Accounting`

| Field | Description |
|-------|-------------|
| **Generate Labor Journal Entries** | Enable to auto-create JEs for timesheets on this project (even without an MO link) |
| **Labor WIP Account (Override)** | Override company WIP account for this project only |
| **Labor Clearing Account (Override)** | Override company Clearing account for this project only |

---

### 2.7 Optional: Per-workcenter account override

`Manufacturing → Configuration → Work Centers → [Workcenter] → Costing tab`

| Field | Description |
|-------|-------------|
| **Labor Account (Override)** | Overrides the WIP debit account for timesheet lines on work orders using this workcenter |

---

## 3. Account Override Hierarchy

For each JE the system resolves accounts in this order:

```
1. Project override    project.labor_wip_account_id / labor_clearing_account_id
2. Workcenter override mrp.workcenter.labor_account_id (WIP/debit only)
3. Company default     res.company.labor_wip_account_id / labor_clearing_account_id
```

---

## 4. Daily Use

### 4.1 Logging time on a Manufacturing Order

1. Open **Manufacturing → Operations → Manufacturing Orders**.
2. Open or create an MO. Set **Analytic Account** (optional but recommended for reporting).
3. Open the **Timesheets** tab.
4. Click **Add a line**:

| Field | Description |
|-------|-------------|
| **Date** | Day worked |
| **Employee** | Worker (rate comes from their Hourly Cost) |
| **Description** | Short note: "Assembly", "Quality check", etc. |
| **Hours** | Time spent (e.g. `2.5`) |
| **Is Overtime** | Tick to apply Overtime Rate Multiplier |
| **Is Holiday** | Tick to apply Holiday Rate Multiplier (overrides overtime) |

5. **Save the record.** The JE is created and posted immediately — no need to mark the MO as done.

The **Labor Cost** column updates automatically per line. The **Timesheet Labor Cost** field on the MO shows the running total.

---

### 4.2 What happens when you save a timesheet line

```
On save:
  1. labor_cost = unit_amount × hourly_rate × multiplier
  2. Check accounts: WIP, Clearing, Journal (project → workcenter → company)
  3. If all three are configured:
       DR  Labor WIP Account    (e.g. 510100)    +labor_cost
       CR  Labor Clearing Acct  (e.g. 215100)    +labor_cost
  4. JE is posted immediately, analytic distribution set to MO's analytic account
  5. labor_move_id links the timesheet line to the JE
```

---

### 4.3 Editing a timesheet line

If you change **Hours**, **Employee**, **Is Overtime**, **Is Holiday**, **Product**, or **Date** on a saved line:

1. The existing JE is **automatically reversed** (a reversal entry is posted).
2. A **new JE** is created with the corrected amount.

You can see both the original JE and its reversal in **Accounting → Journal Entries** filtered by reference `LABOR/...` and `REV/LABOR/...`.

---

### 4.4 Deleting a timesheet line

Deleting a line triggers an automatic reversal of its JE first, keeping the ledger clean.

---

### 4.5 Audit trail

Every JE narration includes:

```
Employee: Ahmed Al-Rashid | Hours: 4.00 | Type: Overtime | Cost: 600.00 SAR | Triggered by: Ahmed (uid=12)
```

Reversal narration:
```
Reversal of labor JE for timesheet: Assembly step 3 | Triggered by: Ahmed (uid=12)
```

---

### 4.6 When MO is marked Done

When you click **Mark as Done**, the module runs a reconciliation pass (`_post_timesheet_labor_cost_if_any`) that checks for any timesheet lines without a JE (e.g. lines added before accounts were configured) and generates their JEs at that point.

This is a safety net — in normal usage JEs are already created in real time as lines are saved.

---

## 5. Checking the Clearing Account Balance

`Manufacturing → Reporting → Labor Clearing Balance Check`

This wizard shows:

| Column | Description |
|--------|-------------|
| **Period** | Calendar month |
| **Accrued (CR)** | Total credited by timesheet JEs (Step 1) |
| **Cleared by Payroll (DR)** | Total debited by payroll JEs (Step 2) |
| **Outstanding** | CR − DR. Should be 0 after payroll runs. |

A positive outstanding means payroll has not yet cleared the accrual for that period.

---

## 6. Smart Button on MO

On the Manufacturing Order form, a **Labor Cost** smart button appears (visible to Accounting users) when the MO has timesheet lines. It shows the total labor cost at a glance.

---

## 7. Where to Find Everything

| What | Where |
|------|-------|
| Labor WIP Account | Settings → Companies → Labor Cost Accounting tab |
| Labor Clearing Account | Settings → Companies → Labor Cost Accounting tab |
| Labor Cost Journal | Settings → Companies → Labor Cost Accounting tab |
| Overtime/Holiday multipliers | Settings → Companies → Labor Cost Accounting tab |
| Employee Hourly Cost | Employees → [Employee] → HR Settings tab |
| Per-project JE toggle | Project → [Project] → Settings tab |
| Workcenter account override | Manufacturing → Configuration → Work Centers → Costing tab |
| Timesheets tab on MO | Manufacturing Order form → Timesheets tab |
| Labor Cost (per line) | Timesheets tab → Labor Cost column (optional) |
| JE link (per line) | Timesheets tab → JE column (optional) |
| Total labor cost | MO form → Timesheet Labor Cost field |
| Labor JE | Accounting → Journal Entries → search "LABOR/" |
| Reversal JE | Accounting → Journal Entries → search "REV/LABOR/" |
| Clearing balance | Manufacturing → Reporting → Labor Clearing Balance Check |

---

## 8. Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Timesheet saved but no JE created | Accounts not configured | Set WIP + Clearing accounts and Journal on company |
| JE created but wrong amount | Employee hourly_cost = 0 | Set Hourly Cost on the employee form |
| Multiplier not applied | Wrong flag or multiplier = 1.0 | Tick Is Overtime / Is Holiday on the line; check company multiplier values |
| JE in wrong account | No project/workcenter override needed | Remove the override or correct the hierarchy |
| Clearing balance non-zero | Payroll not yet run for that period | Normal — it will be cleared when payroll posts |
| Cannot see Labor Cost tab | Not in Accounting group | Ask your admin for Accounting / Manager access |
| Constraint error on accounts | WIP and Clearing set to same account | They must be different accounts |
| Constraint error on clearing account type | Account type is not a liability | Use a Current Liability or Payable account for the clearing account |
