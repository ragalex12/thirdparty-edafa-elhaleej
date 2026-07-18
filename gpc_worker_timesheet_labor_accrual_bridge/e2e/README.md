# Labor Accrual Bridge — Playwright E2E

Smoke test: log in, open **Labor Accrual Batches**, open a batch if present, assert **Populate lines** is visible.

## Prerequisites

- Node.js 18+
- Playwright browsers: `npx playwright install chromium`

## Environment

Playwright loads the first file that exists, in order:

1. `DOTENV_CONFIG_PATH` (absolute path to a `.env` file)
2. `../../../.env` relative to this `e2e/` folder (i.e. `/opt/.env` when addons live under `/opt/localaddons/`)
3. `/opt/.env` (local staging file — **never commit**)

You can still export variables in your shell instead of using a file.

Otherwise set variables in your shell (or `set -a; source /opt/.env; set +a`):

| Variable | Description |
|----------|-------------|
| `GCC_ODOO_WEB_URL` | Base URL (no trailing slash), e.g. `http://localhost:8119` |
| `GCC_ODOO_LOGIN` | User login |
| `GCC_ODOO_PASSWORD` | Password |
| `GCC_ODOO_DB` | Optional database name |
| `GCC_ODOO_LABOR_ACCRUAL_ACTION_ID` | Optional numeric action id for direct navigation |
| `GCC_ODOO_LABOR_ACCR_PERIOD_START` | ISO date for period wizard (default `2025-09-01`) |
| `GCC_ODOO_LABOR_ACCR_PERIOD_END` | ISO date for period wizard (default `2025-09-30`) |
| `GCC_ODOO_LABOR_ACCR_LIST_ROW_MATCH` | Substring to pick a list row when the wizard cannot create a batch (default in code: `2025-09`) |

Resolve action id in Odoo shell:

```python
env.ref('gpc_hr_timesheet_labor_accrual.action_labor_accrual_batch').id
```

## Run

**Recommended** if `npm install` fails on your filesystem (chmod/rename errors on `node_modules`):

```bash
cd projects/edafaa_gcc_clone/gpc_worker_timesheet_labor_accrual_bridge/e2e
chmod +x run.sh
export GCC_ODOO_LOGIN=... GCC_ODOO_PASSWORD=... GCC_ODOO_WEB_URL=http://localhost:8119
./run.sh
```

Standard (install under `e2e/`):

```bash
cd projects/edafaa_gcc_clone/gpc_worker_timesheet_labor_accrual_bridge/e2e
npm install
npx playwright install chromium
npx playwright test
```

Headed:

```bash
npm run test:headed
```

Screenshots (writes PNGs under `e2e/screenshots/`, gitignored):

```bash
npm run test:screenshots
# or headed:
npx playwright test tests/odoo-staging-screenshots.spec.ts --headed
```

**Full Accounting flow** (wizard **Labor Accrual (from period)** → dates → *Create batch and populate lines* → *Populate lines* → *Generate draft entry* → open JE → Journal Items; PNGs under `screenshots/labor-accrual-flow/`):

```bash
npm run test:screenshots:workflow
```

**Same project, multiple analytics → Journal Entry form** (screenshots like production JE with Analytic Distribution tags):

```bash
# 1) Create demo data (two timesheets, one project, two analytic accounts, draft JE)
odoo shell -c /etc/odoo/odoo.conf -d trgulf_Mrp \
  < /opt/localaddons/gpc_hr_timesheet_labor_accrual/scripts/demo_labor_accrual_multi_analytic_verify.py

# 2) Playwright (reads e2e/.last-multi-analytic-move-id.txt or GCC_ODOO_MULTI_ANALYTIC_MOVE_ID)
cd gpc_worker_timesheet_labor_accrual_bridge/e2e
npm run test:multi-analytic
```

Screenshots: `screenshots/labor-accrual-multi-analytic/` — especially `03-journal-items-multi-analytic-debit-lines.png`.

**Five different projects → five analytic accounts on JE** (one debit line per project analytic):

```bash
odoo shell -c /etc/odoo/odoo.conf -d trgulf_Mrp \
  < /opt/localaddons/gpc_hr_timesheet_labor_accrual/scripts/demo_labor_accrual_five_projects_verify.py

cd gpc_worker_timesheet_labor_accrual_bridge/e2e
npm run test:five-projects
```

Screenshots: `screenshots/labor-accrual-five-projects/` — especially `03-journal-items-five-analytic-debit-lines.png`.

## Notes

- The user must belong to **Accounting / Billing** (or equivalent) so **Labor Accrual Batches** and **Populate lines** are available.
- Menu labels differ by locale; adjust selectors in `tests/labor-accrual-batch.spec.ts` if needed.
