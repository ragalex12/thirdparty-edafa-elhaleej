# Plan: Manufacturing Order Timesheet Tab Module

## Status (updated)

| # | Task | Status |
|---|------|--------|
| 1 | Create module folder and `__manifest__.py` | ✅ Done |
| 2 | Add `analytic_account_id` and `timesheet_ids` on `mrp.production` | ✅ Done |
| 3 | Add `mrp_production_id` on `account.analytic.line` + inverse for `timesheet_ids` | ✅ Done |
| 4 | Inherit MO form view; add Timesheets tab and list for `timesheet_ids` | ✅ Done |
| 5 | “Log time” (inline via editable tree + default context) | ✅ Done |
| 6 | Company / access (analytic_account_id has `check_company=True`) | ✅ Done |
| 7 | Auto-create analytic account when empty | ⬜ Optional, not done |
| 8 | README with install and usage | ✅ Done |
| 9 | **Timesheet labor → production cost** (JE when MO done) | ✅ Done |

**Implemented:** Module `mrp_timesheet` with Timesheet tab and **labor cost posting**: when MO is done, total timesheet labor cost is posted as one journal entry (Debit Stock Valuation, Credit Production Labor Expense). Configure **Production Labor Expense Account** on the company. Remaining optional: auto-create analytic account, Work Order tab, `account_analytic_line_views.xml`, icon.

---

## Goal
Create a new Odoo addon that adds a **Timesheet** tab to the **Manufacturing Order** form, so users can view and record time spent on each MO using standard analytic lines (`account.analytic.line`).

## Target
- **Form:** Manufacturing Order (`mrp.production`)
- **Tab content:** List (and optionally create/edit) timesheet lines linked to the MO
- **Odoo version:** 19 (to align with existing addons in this workspace)

---

## 1. Module identity

| Item | Value |
|------|--------|
| **Technical name** | `mrp_timesheet` (or `mrp_analytic_timesheet`) |
| **Display name** | Manufacturing Timesheet / MO Timesheet |
| **Category** | Manufacturing |
| **Location** | `/opt/localaddons/mrp_timesheet/` |

---

## 2. Dependencies

- **`mrp`** – Manufacturing (MO form, work orders if needed later).
- **`hr_timesheet`** – Provides timesheet UI, timer, and integration with `account.analytic.line`.  
  **Alternative:** If you want to avoid HR, depend only on **`analytic`** (and optionally **`account`**) and use raw `account.analytic.line`; no timer, minimal UI – more work for the same result.  
  **Recommendation:** Depend on **`hr_timesheet`** so the tab can reuse existing timesheet behaviour (e.g. “Log time” button, unit_amount in hours).

So in `__manifest__.py`:

```python
'depends': ['mrp', 'hr_timesheet'],
```

---

## 3. Data model

### 3.1 Link MO to analytic

- **Option A – Analytic account on MO**  
  Add `analytic_account_id` (Many2one to `account.analytic.account`) on `mrp.production`.  
  Timesheet lines are linked by having `account_id = MO.analytic_account_id`.  
  - Pros: Standard Odoo pattern; reporting by analytic account includes MO time.  
  - Cons: User must set (or we auto-create) an analytic account per MO.

- **Option B – Direct link on analytic line**  
  Add optional `mrp_production_id` on `account.analytic.line` (or use generic `res_model` / `res_id`).  
  - Pros: No need for analytic account on MO if you only care about “time per MO”.  
  - Cons: Reporting by analytic account won’t show MO unless you also set `account_id`; a bit less standard.

**Recommendation:** **Option A** – add `analytic_account_id` on `mrp.production` and show in the tab all `account.analytic.line` where `account_id = production.analytic_account_id`. Optionally allow creating the analytic account automatically when the user first logs time.

### 3.2 Model changes

1. **`mrp.production`** (inherit)
   - Add field: `analytic_account_id` → `account.analytic.account` (optional).
   - Add computed or related field: `timesheet_ids` → One2many to `account.analytic.line` (domain: `account_id = analytic_account_id`), or a dedicated relation if you add `mrp_production_id` on lines.
   - If using Option A only: `timesheet_ids` = computed from `env['account.analytic.line'].search([('account_id', '=', self.analytic_account_id.id)])` (and filter by company), or store a proper inverse relation if you add a back-link on the line.

2. **`account.analytic.line`** (optional but useful)
   - Add optional `mrp_production_id` → `mrp.production` for direct link and easier filtering/grouping.
   - When creating a line from the MO tab, set both `account_id` (from MO) and `mrp_production_id`.

---

## 4. UI – Timesheet tab on MO form

1. **Form view inheritance**
   - Inherit `mrp.production` form view (e.g. `mrp.mrp_production_form_view`).
   - Add a new **notebook page** (tab) after existing tabs, e.g. label **“Timesheets”**.

2. **Tab content**
   - **List of lines:** One2many to `account.analytic.line` (e.g. `timesheet_ids`).
   - Columns: e.g. Date, Employee/User, Description, Unit Amount (hours), optionally Project/Task if you integrate project later.
   - **Actions:** “Log time” (open wizard or inline form to create a line linked to this MO’s analytic account and optionally `mrp_production_id`). If using `hr_timesheet`, reuse or mimic its “Log time” behaviour so unit_amount and product/employee are set correctly.

3. **Placement**
   - Use xpath to insert the new page inside the main form notebook (e.g. after “Components” or “Other Info” tab).

---

## 5a. Timesheet labor → production cost (implemented)

- When the MO is **marked done** (`_post_inventory`), the module computes **total labor cost** from `timesheet_ids`: for each line, cost = `amount` (if set) or `unit_amount ×` (employee hourly cost or product cost).
- A **single journal entry** is created (only once per MO): **Debit** finished product’s Stock Valuation account, **Credit** company’s **Production Labor Expense Account**. So inventory value increases by the labor cost.
- **Configuration:** Set **Production Labor Expense Account** on the company (Settings → Companies). Set **Stock Journal** for the company. Set employee **Hourly Cost** (or use timesheet line product/amount) for cost per hour.
- **Fields:** `timesheet_labor_cost` (computed), `timesheet_cost_posted`, `timesheet_labor_move_id` on `mrp.production`; `production_labor_expense_account_id` on `res.company`.

---

## 5. Behaviour and business rules

- **Visibility:** Show tab only when the MO has an analytic account (or always show tab and show a message “Set an analytic account to log time” when it’s missing).
- **Creating lines from MO:** Pre-fill `account_id` from `production.analytic_account_id`, and `mrp_production_id` if you added it; user fills date, user/employee, description, unit_amount.
- **Company:** Restrict analytic lines and analytic account to the same company as the MO.
- **Optional:** Auto-create analytic account when user clicks “Log time” and MO has none (e.g. name “MO/WH-MO00042”).

---

## 6. File structure (current)

```
mrp_timesheet/
├── __init__.py
├── __manifest__.py
├── README.md
├── MRP_TIMESHEET_PLAN.md      # this plan
├── models/
│   ├── __init__.py
│   ├── mrp_production.py      # analytic_account_id, timesheet_ids, timesheet_count
│   └── account_analytic_line.py  # mrp_production_id
├── views/
│   └── mrp_production_views.xml   # MO form: analytic_account_id + Timesheets tab (editable tree)
├── security/
│   └── ir.model.access.csv    # empty (no new models)
└── static/
    └── description/
        └── icon.png           # optional, not added yet
```

Not added yet: `account_analytic_line_views.xml` (show MO on line form/list), icon, auto-create analytic account.

---

## 7. Implementation order (checklist)

1. [x] Create module folder and `__manifest__.py` (depends: `mrp`, `hr_timesheet`).
2. [x] Add `analytic_account_id` and `timesheet_ids` on `mrp.production` (models).
3. [x] Add `mrp_production_id` on `account.analytic.line` and inverse relation for `timesheet_ids`.
4. [x] Inherit MO form view; add “Timesheets” tab and list view for `timesheet_ids` (editable tree).
5. [x] “Log time” via editable tree + context `default_account_id`, `default_mrp_production_id`.
6. [x] Company: `analytic_account_id` has `check_company=True`.
7. [ ] Optional: auto-create analytic account when empty and user logs time.
8. [x] README with install steps and usage (set analytic account, open tab, log time).

---

## 8. Alternative: Tab on Work Order instead of (or in addition to) MO

If you use **work orders** (`mrp.workorder`), the same idea can be applied there: add `analytic_account_id` and a Timesheet tab on the work order form so time is recorded per operation. The plan above can be duplicated for `mrp.workorder` in a second phase if needed.

---

## 9. Clarification

- **“This module”** was interpreted as the **Manufacturing** app (MO form).  
- If you instead want the timesheet tab on another form (e.g. **Company** in `company_stock_journal_ui`), the same pattern applies: add analytic (or link) on that model and add a tab showing `account.analytic.line`; only the target model and view xpath change.

Once you confirm the target (MO only, or MO + work order, or another form), implementation can follow this plan step by step.
