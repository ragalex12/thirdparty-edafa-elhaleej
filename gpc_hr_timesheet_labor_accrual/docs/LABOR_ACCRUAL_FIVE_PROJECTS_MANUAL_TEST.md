# Manual UI test — Five projects, five analytic accounts

Repeat the automated **five projects** scenario by hand in Odoo: five different projects (each with its own analytic account), five timesheet lines in the same period, then a labor accrual batch and journal entry with **five debit lines** (each with analytic) and **one credit** line (no analytic).

---

## Before you start

### Modules

- `gpc_hr_timesheet_labor_accrual` installed and upgraded (≥ `19.0.1.0.5`).
- If you use worker timesheets: `gpc_worker_timesheet_labor_accrual_bridge` installed (adds `include_in_payroll` filter on populate).

### User rights

- **Accounting / Billing** (or `account.group_account_user`) so you see:
  - **Accounting → Transactions → Labor Accrual (from period)**
  - **Accounting → Transactions → Labor Accrual Batches**
  - Buttons **Populate lines** and **Generate draft entry**

### Company setup

**Settings → Companies → [your company] → Labor Accrual** tab:

| Field | Purpose |
|--------|---------|
| Labor accrual debit account | Expense account on debit lines |
| Labor accrual credit account | WIP / offset account on credit line |
| Labor accrual journal | Miscellaneous (or your accrual journal) |

Save the company if you change anything.

### Pick one test day

Use **today’s date** (or one fixed date) for all timesheets and for the batch period. Example: **17 May 2026**.

Use a **unique period key** if another active batch already exists for the same month (e.g. `FIVE-20260517` instead of `2026-05`).

---

## Path A — Quick verify (demo data already created)

Use this if someone ran the demo script on the database:

```bash
odoo shell -c /etc/odoo/odoo.conf -d trgulf_Mrp \
  < /opt/localaddons/gpc_hr_timesheet_labor_accrual/scripts/demo_labor_accrual_five_projects_verify.py
```

Then in the UI:

1. Log in to Odoo (same company as the script).
2. **Accounting** app → **Transactions** → **Labor Accrual Batches**.
3. Open batch **`LAB ACCR DEMO FIVE PROJECTS`**.
4. Continue from [Step 4 — Review batch lines](#step-4--review-batch-lines) below (or [Step 5](#step-5--generate-draft-journal-entry) if lines and JE already exist).

---

## Path B — Full manual setup (create everything in the UI)

### Step 1 — Create five analytic accounts

1. Go to **Accounting → Configuration → Analytic Accounts** (menu name may vary).
2. Create **five** analytic accounts, for example:

   | Name |
   |------|
   | `LABOR ACCRUAL DEMO ANALYTIC P1` |
   | `LABOR ACCRUAL DEMO ANALYTIC P2` |
   | `LABOR ACCRUAL DEMO ANALYTIC P3` |
   | `LABOR ACCRUAL DEMO ANALYTIC P4` |
   | `LABOR ACCRUAL DEMO ANALYTIC P5` |

3. Assign each to an analytic plan if your database requires it.

---

### Step 2 — Create five projects (one analytic each)

1. **Project** app (or **Projects** from the app menu).
2. Create **five** projects, e.g. `LABOR ACCRUAL FIVE PROJ 1` … `LABOR ACCRUAL FIVE PROJ 5`.
3. On each project form, set **Analytic Account** (or your project analytic field) to the matching **P1 … P5** account.
4. Enable **Timesheets** on the project if there is an option (`allow_timesheets`).

---

### Step 3 — Enter five timesheet lines (same employee, same date)

1. Open **Timesheets** (or **Timesheet** on each project).
2. Use **one employee** for all lines (set **Hourly Cost** on the employee if amounts show as 0 — e.g. `100` SAR/hour).
3. For **the same calendar date** (your test day), log **one line per project**:

   | Project | Hours (example) | Analytic on line |
   |---------|-----------------|------------------|
   | FIVE PROJ 1 | 1.0 | P1 (from project or line) |
   | FIVE PROJ 2 | 2.0 | P2 |
   | FIVE PROJ 3 | 3.0 | P3 |
   | FIVE PROJ 4 | 4.0 | P4 |
   | FIVE PROJ 5 | 5.0 | P5 |

4. Confirm each line meets accrual rules:
   - **Validated** = Yes (if your timesheets use validation).
   - **Not linked to a manufacturing order** (MO field empty), if you use `mrp_timesheet`.
   - **Include in payroll** = Yes (if `gpc_worker_timesheet_labor_accrual_bridge` is installed).
   - **Positive hours** and **non-zero labor amount** on populate (check `labor_cost` or employee hourly cost).

5. Save all lines.

**Expected amounts (with hourly cost 100):** 100 + 200 + 300 + 400 + 500 = **1,500** total.

---

### Step 4 — Create labor accrual batch for that period

**Option 4a — Wizard (recommended)**

1. **Accounting** → **Transactions** → **Labor Accrual (from period)**.
2. Set **Period start** and **Period end** to your test day (both the same date).
3. Click **Create batch and populate lines**.
4. You are taken to the new batch form. Set:
   - **Name:** e.g. `LAB ACCR DEMO FIVE PROJECTS`
   - **Period key:** e.g. `FIVE-20260517` (must not conflict with another active batch for the same company/period)

**Option 4b — Existing batch list**

1. **Accounting** → **Transactions** → **Labor Accrual Batches**.
2. **New**.
3. Fill **Name**, **Period start**, **Period end**, **Period key**, **Company**.
4. Save.

---

### Step 4 — Review batch lines

1. On the batch form (state **Draft**), click **Populate lines** (if lines are empty).
2. Open the **Lines** tab.

**Expected:**

| Check | Expected |
|--------|----------|
| Number of lines | **5** |
| Projects | **5 different** project names |
| Amounts | Five positive amounts (e.g. 100, 200, 300, 400, 500) |
| Total | **1,500** (with hourly cost 100) |

If you see fewer than 5 lines:

- Widen **period start/end** to include all timesheet dates.
- Confirm timesheets are **validated** and not MO-linked.
- Confirm **include in payroll** where the bridge module applies.
- Confirm **labor amount** &gt; 0 (employee hourly cost or timesheet labor cost).

---

### Step 5 — Generate draft journal entry

1. On the same batch, click **Generate draft entry**.
2. Wait for save; the **Journal entry** field (`move_id`) should link to a new draft `account.move`.
3. Click the **Journal entry** link (or open it from the field).

---

### Step 6 — Verify Journal Items (main test)

1. On the journal entry form, open the **Journal Items** tab.
2. Zoom out or scroll so you can see all rows.

**Expected:**

| # | Account (typical) | Label | Analytic distribution | Debit | Credit |
|---|-------------------|--------|------------------------|-------|--------|
| 1–5 | Labor accrual **debit** account (company config) | `Labor accrual expense (batch total)` | **Different tag per line** (P1…P5) | 100, 200, 300, 400, 500 | 0 |
| 6 | Labor accrual **credit** / WIP account | `Labor accrual offset (batch total)` | **Empty** | 0 | **1,500** |
| Total | | | | **1,500** | **1,500** |

**Pass criteria:**

- Exactly **five** debit lines with **five different** analytic distributions (one per project).
- Exactly **one** credit line with **no** analytic.
- Debits sum = credit = batch total.

---

### Step 7 — Optional checks

- **Post** — only if you intend to post; use **Reverse & release period** later if you need to recreate the batch for the same period key.
- **Regenerate** — click **Generate draft entry** again on a draft batch; the old draft move should be replaced.
- **Debug** — set system parameter `gpc_hr_timesheet_labor_accrual.debug_analytic` = `1`, repeat **Generate draft entry**, read server log for per-line `analytic_distribution`.

---

## Menu reference (English UI)

| Step | Navigation |
|------|------------|
| Labor accrual wizard | **Accounting → Transactions → Labor Accrual (from period)** |
| Batch list | **Accounting → Transactions → Labor Accrual Batches** |
| Company config | **Settings → Companies → [Company] → Labor Accrual** |
| Analytic accounts | **Accounting → Configuration → Analytic Accounts** (path may vary) |
| Projects / timesheets | **Project** app or **Timesheets** |

Arabic or custom menus: search for **Labor Accrual** / **استحقاق** equivalents under **Accounting / Transactions**.

---

## Compare with automated test

| Item | Value |
|------|--------|
| Demo script | `scripts/demo_labor_accrual_five_projects_verify.py` |
| Batch name | `LAB ACCR DEMO FIVE PROJECTS` |
| Playwright | `npm run test:five-projects` in `gpc_worker_timesheet_labor_accrual_bridge/e2e` |
| Reference screenshot | `e2e/screenshots/labor-accrual-five-projects/03-journal-items-five-analytic-debit-lines.png` |

---

## Troubleshooting

| Symptom | What to check |
|---------|----------------|
| Menu missing | User in Accounting group; module installed |
| “Configure company…” on generate | Debit/credit accounts + journal on company |
| “Active batch already exists for period” | Use another **period key** or reverse/cancel the other batch |
| Populate finds 0 lines | Dates, validation, MO, `include_in_payroll`, company |
| Amounts all 0 | Employee **Hourly Cost** or timesheet **labor cost** |
| Only 1 debit line | All timesheets share the **same** analytic distribution; use **different** project analytics |
| Debit without analytic | Project/timesheet has no analytic; see `docs/LABOR_ACCRUAL_ANALYTIC_FIX.md` |

---

## Related documentation

- Analytic fix details: `docs/LABOR_ACCRUAL_ANALYTIC_FIX.md`
- Same project, two analytics: demo `demo_labor_accrual_multi_analytic_verify.py`
