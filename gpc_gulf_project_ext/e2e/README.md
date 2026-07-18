# GPC Gulf Project Ext — Playwright E2E (screenshots)

Captures UI evidence for **WP #136–#138** (project dashboard, contract amount, quotation dimensions).

## Prerequisites

- Node.js 18+
- Module `gpc_gulf_project_ext` installed on target DB
- Odoo reachable from this machine

## Environment

Loads `/opt/.env` (or `DOTENV_CONFIG_PATH`):

| Variable | Description |
|----------|-------------|
| `GCC_ODOO_WEB_URL` / `GPC_GULF_ODOO_URL` | Base URL, e.g. `http://127.0.0.1:8069` or `https://gpc.odoo.com.se` |
| `GCC_ODOO_LOGIN` | Login |
| `GCC_ODOO_PASSWORD` | Password |
| `GCC_ODOO_DB` | Database, e.g. `trgulf_Mrp` |

For **local** Odoo on this server:

```bash
export GPC_GULF_ODOO_URL=http://127.0.0.1:8069
export GCC_ODOO_DB=trgulf_Mrp
```

## Setup

```bash
# 1) Seed UAT project + quotation (writes e2e/.playwright-seed.json)
sudo -u odoo odoo shell -c /etc/odoo/odoo.conf -d trgulf_Mrp --no-http \
  < /opt/localaddons/gpc_gulf_project_ext/scripts/seed_playwright_data.py

# 2) Install Playwright
cd /opt/localaddons/gpc_gulf_project_ext/e2e
npm install
npx playwright install chromium
```

## Run screenshots

```bash
cd /opt/localaddons/gpc_gulf_project_ext/e2e
npm run test:screenshots
```

Headed (debug):

```bash
npx playwright test tests/gulf-project-phase1-screenshots.spec.ts --headed
```

## Output

PNG/PDF files under `e2e/screenshots/gulf-phase1/` — **see index for what each screenshot documents:**

- [`screenshots/gulf-phase1/README.md`](screenshots/gulf-phase1/README.md) — English (what we did per file)
- [`screenshots/gulf-phase1/INDEX_AR.md`](screenshots/gulf-phase1/INDEX_AR.md) — Arabic summary table

| File | Content |
|------|---------|
| `01-login-page.png` | Login screen |
| `03-project-form.png` | Project form |
| `04-project-expected-budget-contract-amount.png` | `contract_amount` field |
| `05-project-description-tab.png` | Description tab |
| `06-project-dashboard.png` | Project dashboard |
| `08-quotation-form-dimensions.png` | Quotation with Length/Width/Area |
| `09-quotation-order-lines.png` | Order lines crop — **64,562.40** |
| `10-quotation-print-dialog.png` | Print dialog |
| `11-final-quotation.png` | Final quotation totals |

HTML report: `npx playwright show-report`

## Notes

- Restart Odoo / hard-refresh browser after upgrading `gpc_gulf_project_ext` assets.
- If dashboard panel is empty, confirm module is installed and open project **Dashboard** (project updates kanban).
