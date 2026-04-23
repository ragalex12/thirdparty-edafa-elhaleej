# Manufacturing Timesheet — Labor Cost Integration

Integrates timesheet time-tracking with Manufacturing Orders in Odoo 19 and automatically posts **real-time labor cost journal entries** to the General Ledger using a two-step payroll reconciliation model.

---

## Features

| Feature | Description |
|---------|-------------|
| Timesheet tab on MO | Log employee hours directly on a Manufacturing Order |
| Real-time JE generation | Each saved timesheet line creates Debit WIP / Credit Clearing JE immediately |
| Overtime & Holiday rates | Per-line flags apply company-configured rate multipliers (1.5× / 2.0×) |
| Per-project JEs | Projects can opt-in to generate JEs without needing an MO |
| Account override hierarchy | Project → Workcenter → Company default |
| JE reversal on edit/delete | Changing or deleting a line automatically reverses the prior JE |
| Clearing balance wizard | Manufacturing → Reporting → Labor Clearing Balance Check |
| Security | `sudo()` for JE creation, caller audit trail in narration, multi-company `ir.rule` |

---

## Dependencies

- `mrp` — Manufacturing
- `hr_timesheet` — Timesheets
- `stock_account` — Inventory valuation / journals
- `hr` — Employees
- `project` — Projects (for project-based JEs)

---

## Installation

1. Copy this folder into your Odoo addons path (`localaddons/` or `addons/`).
2. Restart Odoo.
3. Update the app list and install **Manufacturing Timesheet**.

---

## Configuration

### Task 91 – Accounting Setup

Before using the labor cost features you must configure three accounts and one journal on your company.

#### Step 1 — Open company settings

`Settings → Companies → [Your Company] → Labor Cost Accounting tab`

> This tab is visible only to users in the **Accounting / Administrator** group.

#### Step 2 — Set the three accounts

| Field | Account type | Purpose |
|-------|-------------|---------|
| **Labor WIP Account** | Asset (WIP / Current Asset) | **Debited** when a timesheet line is saved. Represents direct labor absorbed into production cost. Example: `510100 – Manufacturing WIP` |
| **Labor Clearing Account** | Liability (Current Liability / Payable) | **Credited** when a timesheet line is saved. Cleared when payroll runs. Example: `215100 – Payroll Accrual` |
| **Labor Cost Journal** | General / Miscellaneous | Journal used for automatic labor JEs. Falls back to the company stock journal if not set. |

#### Step 3 — Set rate multipliers (optional)

| Field | Default | Purpose |
|-------|---------|---------|
| Overtime Rate Multiplier | 1.5 | Applied when `Is Overtime` is ticked on a timesheet line |
| Holiday Rate Multiplier | 2.0 | Applied when `Is Holiday` is ticked (takes precedence over overtime) |

#### Step 4 — Set employee hourly cost

`Employees → [Employee] → HR Settings → Hourly Cost`

Priority: `employee.hourly_cost` → `employee.timesheet_cost` → `product.standard_price`

---

## Two-step Payroll Reconciliation Flow

```
Step 1 – Timesheet saved (this module)
  DR  Labor WIP Account         510100   +200 SAR
  CR  Labor Clearing Account    215100   +200 SAR
      (Payroll not yet run — accrual sits on clearing)

Step 2 – Payroll confirmed (hr_payroll_account)
  DR  Labor Clearing Account    215100   −200 SAR   ← cancels Step 1 accrual
  CR  Wages Payable / Bank      310100   +200 SAR   ← actual cash obligation
```

**Net result after both steps:**
- Clearing account balance = **0** (fully reconciled)
- WIP carries the true direct labor cost
- Wages Payable / Bank reflects cash owed to employees

Use **Manufacturing → Reporting → Labor Clearing Balance Check** to monitor the outstanding balance on the clearing account at any time.

---

## Per-project Labor JEs (without MO)

1. Open a project: `Project → [Project] → Settings tab → Labor Cost Accounting`
2. Enable **Generate Labor Journal Entries**
3. Optionally set account overrides (override the company defaults for this project)
4. Any timesheet line saved on this project will now auto-generate a JE

---

## Account Override Hierarchy

For each JE the system resolves accounts in this order:

```
1. Project override   (project.labor_wip_account_id / labor_clearing_account_id)
2. Workcenter override (mrp.workcenter.labor_account_id — WIP only)
3. Company default    (res.company.labor_wip_account_id / labor_clearing_account_id)
```

---

## Audit Trail

Every auto-generated JE narration includes the real caller's identity before `sudo()` is applied:

```
Employee: Ahmed Al-Rashid | Hours: 4.00 | Type: Regular | Cost: 400.00 SAR | Triggered by: Ahmed (uid=12)
```

Reversals include:
```
Reversal of labor JE for timesheet: Assembly step 3 | Triggered by: Ahmed (uid=12)
```

---

## Security

| Layer | Mechanism |
|-------|-----------|
| UI visibility | `groups="account.group_account_manager"` on all account config fields |
| JE creation | `sudo()` — manufacturing workers don't need accounting rights |
| Audit | Real caller name + uid embedded in JE narration before sudo() |
| Multi-company | Global `ir.rule` prevents cross-company MO timesheet access |
| Field integrity | `check_company=True` on all `Many2one` account fields |

---

## Models

| Model | Added fields |
|-------|-------------|
| `res.company` | `labor_wip_account_id`, `labor_clearing_account_id`, `labor_cost_journal_id`, `overtime_rate_multiplier`, `holiday_rate_multiplier` |
| `hr.employee` | `hourly_cost` |
| `mrp.production` | `analytic_account_id`, `timesheet_ids`, `timesheet_labor_cost`, `timesheet_cost_posted`, `timesheet_labor_move_id` |
| `account.analytic.line` | `mrp_production_id`, `is_overtime`, `is_holiday`, `labor_cost`, `labor_move_id` |
| `project.project` | `generate_labor_je`, `labor_wip_account_id` (override), `labor_clearing_account_id` (override) |
| `mrp.workcenter` | `labor_account_id` (WIP override) |
| `mrp.labor.clearing.check.wizard` | Balance check wizard |

---

## Documentation

- **[User Guide](docs/USER_GUIDE.md)** — Step-by-step for accountants and production managers
- **[Use Cases](docs/USE_CASES.md)** — Real-world scenarios with journal entry examples
- **[Developer Guide](docs/OPENPROJECT_SETUP_GUIDE.md)** — OpenProject setup and infrastructure notes
