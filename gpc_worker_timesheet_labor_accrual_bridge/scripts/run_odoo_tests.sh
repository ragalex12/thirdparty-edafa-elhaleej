#!/usr/bin/env bash
# Run Odoo unit tests for gpc_worker_timesheet_labor_accrual_bridge.
#
# Usage:
#   export ODOO_CONF=/path/to/odoo.conf
#   export ODOO_DB=your_database
#   ./scripts/run_odoo_tests.sh
#
# Optional:
#   ODOO_BIN   path to odoo-bin (default: ../../../odoo19/odoo19/odoo-bin)
#   ADDONS     extra addons path if needed

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE_ODOO="$(cd "${ROOT}/../../.." && pwd)"
ODOO_BIN="${ODOO_BIN:-${BASE_ODOO}/odoo19/odoo19/odoo-bin}"
ODOO_CONF="${ODOO_CONF:?Set ODOO_CONF to your odoo.conf}"
ODOO_DB="${ODOO_DB:?Set ODOO_DB to your database name}"

exec "${ODOO_BIN}" \
  -c "${ODOO_CONF}" \
  -d "${ODOO_DB}" \
  --stop-after-init \
  --test-enable \
  -u gpc_worker_timesheet_labor_accrual_bridge \
  --test-tags /gpc_worker_timesheet_labor_accrual_bridge
