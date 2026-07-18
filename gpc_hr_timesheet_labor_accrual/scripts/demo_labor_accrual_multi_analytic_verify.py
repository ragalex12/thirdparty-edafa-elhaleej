#!/usr/bin/env python3
# Copyright 2026
# SPDX-License-Identifier: LGPL-3.0-or-later
#
# Demo: ONE project, TWO timesheet lines with DIFFERENT analytic accounts →
# labor accrual batch → draft JE with TWO debit lines (grouped by analytic_distribution).
#
# Run:
#   odoo shell -c /etc/odoo/odoo.conf -d trgulf_Mrp < scripts/demo_labor_accrual_multi_analytic_verify.py
#
# Writes move id for Playwright to:
#   ../gpc_worker_timesheet_labor_accrual_bridge/e2e/.last-multi-analytic-move-id.txt

import os
from datetime import date

from odoo import fields
from odoo.tools.sql import SQL

PROJECT_NAME = "LABOR ACCRUAL MULTI ANALYTIC PROJECT"
ANALYTIC_A_NAME = "LABOR ACCRUAL DEMO ANALYTIC A"
ANALYTIC_B_NAME = "LABOR ACCRUAL DEMO ANALYTIC B"
EMP_NAME = "LAB ACCR DEMO EMP (MULTI ANALYTIC)"
TS_A_NAME = "LABOR ACCRUAL MULTI TS LINE A"
TS_B_NAME = "LABOR ACCRUAL MULTI TS LINE B"
BATCH_NAME = "LAB ACCR DEMO MULTI ANALYTIC"

Company = env.company or env["res.company"].search([], limit=1)

from datetime import date as pydate

demo_date = pydate(2099, 1, 14)
period_start = period_end = demo_date
period_key = "MULTI-%04d%02d%02d" % (demo_date.year, demo_date.month, demo_date.day)


def _ensure_aa(name):
    AnalyticAccount = env["account.analytic.account"]
    aa = AnalyticAccount.search([("name", "=", name), ("company_id", "=", Company.id)], limit=1)
    if aa:
        return aa
    avals = {"name": name, "company_id": Company.id}
    if "plan_id" in AnalyticAccount._fields:
        Plan = env["account.analytic.plan"].search([], limit=1)
        if not Plan:
            Plan = env["account.analytic.plan"].create({"name": "Lab Accrual Multi Plan"})
        avals["plan_id"] = Plan.id
    return AnalyticAccount.create(avals)


aa_a = _ensure_aa(ANALYTIC_A_NAME)
aa_b = _ensure_aa(ANALYTIC_B_NAME)

Project = env["project.project"]
project = Project.search([("name", "=", PROJECT_NAME), ("company_id", "=", Company.id)], limit=1)
if not project:
    project = Project.create(
        {
            "name": PROJECT_NAME,
            "company_id": Company.id,
            "allow_timesheets": True,
        }
    )
project.write({"account_id": aa_a.id})

Employee = env["hr.employee"].search([("name", "=", EMP_NAME)], limit=1)
if not Employee:
    Employee = env["hr.employee"].create(
        {"name": EMP_NAME, "company_id": Company.id, "hourly_cost": 100.0}
    )
else:
    Employee.sudo().write({"hourly_cost": 100.0})

if not (Company.labor_accrual_debit_account_id and Company.labor_accrual_credit_account_id and Company.labor_accrual_journal_id):
    raise SystemExit("Configure labor_accrual_* accounts and journal on company.")

AAL = env["account.analytic.line"]
Batch = env["labor.accrual.batch"]
Batch.search(
    [("company_id", "=", Company.id), ("name", "ilike", BATCH_NAME + "%")]
).unlink()

AAL.search(
    [
        ("name", "in", [TS_A_NAME, TS_B_NAME]),
        ("project_id", "=", project.id),
    ]
).unlink()

plan_fnames = AAL._get_plan_fnames()
if len(plan_fnames) < 1:
    raise SystemExit("Need at least one analytic plan column on account.analytic.line.")

primary_f = "account_id" if "account_id" in plan_fnames else plan_fnames[0]
secondary_f = None
for f in plan_fnames:
    if f != primary_f:
        secondary_f = f
        break

ts_a_vals = {
    "name": TS_A_NAME,
    "project_id": project.id,
    "employee_id": Employee.id,
    "company_id": Company.id,
    "unit_amount": 1.0,
    "date": demo_date,
    primary_f: aa_a.id,
}
ts_b_vals = {
    "name": TS_B_NAME,
    "project_id": project.id,
    "employee_id": Employee.id,
    "company_id": Company.id,
    "unit_amount": 2.0,
    "date": demo_date,
    primary_f: aa_a.id,
}
if "validated" in AAL._fields:
    ts_a_vals["validated"] = True
    ts_b_vals["validated"] = True
if "include_in_payroll" in AAL._fields:
    ts_a_vals["include_in_payroll"] = True
    ts_b_vals["include_in_payroll"] = True

ts_a = AAL.create(ts_a_vals)
ts_b = AAL.create(ts_b_vals)

if secondary_f:
    env.cr.execute(
        SQL(
            "UPDATE account_analytic_line SET %s = %s WHERE id = %s",
            SQL.identifier(secondary_f),
            aa_b.id,
            ts_b.id,
        )
    )
    ts_b.invalidate_recordset()
elif "analytic_distribution" in ts_b._fields:
    ts_b.write({"analytic_distribution": {str(aa_b.id): 100.0}})

batch = Batch.create(
    {
        "name": BATCH_NAME,
        "company_id": Company.id,
        "period_start": period_start,
        "period_end": period_end,
        "period_key": period_key,
        "state": "draft",
    }
)
batch.action_populate_lines()
if len(batch.line_ids) < 2:
    raise SystemExit("Expected 2 batch lines; got %s" % len(batch.line_ids))

batch.action_generate_draft_move()
move = batch.move_id
debit_lines = move.line_ids.filtered(lambda l: l.debit > 0)
credit_lines = move.line_ids.filtered(lambda l: l.credit > 0)

e2e_dir = "/opt/localaddons/gpc_worker_timesheet_labor_accrual_bridge/e2e"
os.makedirs(e2e_dir, exist_ok=True)
id_file = os.path.join(e2e_dir, ".last-multi-analytic-move-id.txt")
with open(id_file, "w", encoding="utf-8") as fh:
    fh.write(str(move.id))

print("=== LABOR ACCRUAL MULTI ANALYTIC DEMO ===")
print("project_id=%s project_name=%s" % (project.id, project.name))
print("analytic_a_id=%s analytic_b_id=%s" % (aa_a.id, aa_b.id))
print("timesheet_a_id=%s timesheet_b_id=%s" % (ts_a.id, ts_b.id))
print("batch_id=%s batch_name=%s" % (batch.id, batch.name))
print("move_id=%s move_name=%s" % (move.id, move.name))
print("debit_line_count=%s" % len(debit_lines))
for dl in debit_lines:
    print("  DEBIT ml=%s amount=%s analytic_distribution=%r" % (dl.id, dl.debit, dl.analytic_distribution))
print("credit_line_count=%s credit_has_analytic=%s" % (len(credit_lines), bool(credit_lines.analytic_distribution)))
print("PLAYWRIGHT_MOVE_ID_FILE=%s" % id_file)
print("GCC_ODOO_MULTI_ANALYTIC_MOVE_ID=%s" % move.id)
env.cr.commit()
