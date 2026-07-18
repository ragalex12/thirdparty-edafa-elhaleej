# GPC Worker Timesheet Labor Accrual Bridge

Integrates `workers_timesheet` with `gpc_hr_timesheet_labor_accrual` via inheritance on `labor.accrual.batch`.

## Odoo unit tests

```bash
export ODOO_CONF=/path/to/odoo.conf
export ODOO_DB=your_database
./scripts/run_odoo_tests.sh
```

Adjust `ODOO_BIN` if your `odoo-bin` path differs.

## Playwright E2E

See `e2e/README.md`. Quick path:

```bash
cd e2e
./run.sh
```
