# Labor accrual demo data on database `newtr`

Demo datasets match **`trgulf_Mrp`** behavior (single analytic, multi-analytic same project, five projects).

## One-command setup

```bash
/opt/localaddons/gpc_hr_timesheet_labor_accrual/scripts/demo_labor_accrual_setup_all.sh newtr
```

For another database:

```bash
./scripts/demo_labor_accrual_setup_all.sh YOUR_DB_NAME
```

Requires modules installed and company **Labor Accrual** accounts + journal configured.

---

## What was created (reference run)

| Scenario | Batch name | Period (timesheet date) | Move ID | Debit lines |
|----------|------------|-------------------------|---------|-------------|
| Single analytic | `LAB ACCR DEMO VERIFY DEMO-SINGLE-20990113` | 2099-01-13 | **3041** | 1 + credit |
| Multi analytic (1 project, 2 analytics) | `LAB ACCR DEMO MULTI ANALYTIC` | 2099-01-14 | **3042** | 2 + credit |
| Five projects | `LAB ACCR DEMO FIVE PROJECTS` | 2099-01-15 | **3043** | 5 + credit |

Company: **مؤسسة فيصل المحمدي التجارية** (id 1)

---

## Open in the UI

1. Log in with database **`newtr`** (web login: `?db=newtr`).
2. **Accounting → Transactions → Labor Accrual Batches**.
3. Open **`LAB ACCR DEMO FIVE PROJECTS`** (main screenshot scenario).
4. Click **Journal entry** → **Journal Items** → expect **5 debit lines** with analytic tags and **1 credit** (1,500 total).

Direct journal entry URLs (adjust host):

- Five projects: `/web#id=3043&model=account.move`
- Multi analytic: `/web#id=3042&model=account.move`
- Single analytic: `/web#id=3041&model=account.move`

---

## Playwright screenshots

```bash
cd /opt/localaddons/gpc_worker_timesheet_labor_accrual_bridge/e2e
GCC_ODOO_WEB_URL=http://127.0.0.1:8069 \
GCC_ODOO_DB=newtr \
GCC_ODOO_MULTI_ANALYTIC_MOVE_ID=3042 \
GCC_ODOO_FIVE_PROJECTS_MOVE_ID=3043 \
npm run test:journal-screenshots
```

Output:

- `e2e/screenshots/labor-accrual-multi-analytic/03-journal-items-multi-analytic-debit-lines.png` (2 analytic debit lines)
- `e2e/screenshots/labor-accrual-five-projects/03-journal-items-five-analytic-debit-lines.png` (5 analytic debit lines)

---

## Demo dates

Scripts use fixed dates so they do not mix with live timesheets:

- Single: **2099-01-13**
- Multi: **2099-01-14**
- Five projects: **2099-01-15**

Re-running the setup script replaces prior demo batches/timesheets for those scenarios.

---

## Other `tr*` databases on this server

| Database | Notes |
|----------|--------|
| `newtr` | Demo loaded (this doc) |
| `trgulf_Mrp` | Original dev / Playwright reference |
| `tr_new_guld_mrp`, `trgulf_cons`, `trgulf_trade`, `Gulf_trade` | Not loaded; run setup script if needed |
