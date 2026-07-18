#!/usr/bin/env bash
# Install/upgrade labor accrual modules and load all UI demo datasets on a database.
#
# Usage:
#   ./demo_labor_accrual_setup_all.sh newtr
#   ./demo_labor_accrual_setup_all.sh trgulf_Mrp
#
set -euo pipefail

DB="${1:-newtr}"
ODOO_CONF="${ODOO_CONF:-/etc/odoo/odoo.conf}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Labor accrual demo setup | database: ${DB} ==="

odoo -c "${ODOO_CONF}" -d "${DB}" \
  -u gpc_hr_timesheet_labor_accrual,gpc_worker_timesheet_labor_accrual_bridge \
  --stop-after-init

for script in \
  demo_labor_accrual_analytic_verify.py \
  demo_labor_accrual_multi_analytic_verify.py \
  demo_labor_accrual_five_projects_verify.py
do
  echo ""
  echo ">>> ${script}"
  odoo shell -c "${ODOO_CONF}" -d "${DB}" < "${SCRIPT_DIR}/${script}"
done

echo ""
echo "=== Done. Open in Odoo (db=${DB}): ==="
echo "  - LAB ACCR DEMO VERIFY (single analytic)     | period 2099-01-13"
echo "  - LAB ACCR DEMO MULTI ANALYTIC               | period 2099-01-14"
echo "  - LAB ACCR DEMO FIVE PROJECTS                | period 2099-01-15"
echo "  Accounting → Transactions → Labor Accrual Batches"
