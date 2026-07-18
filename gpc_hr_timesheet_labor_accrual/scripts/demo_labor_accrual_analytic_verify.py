#!/usr/bin/env python3
# Copyright 2026
# SPDX-License-Identifier: LGPL-3.0-or-later
#
# Reproducible demo: LABOR ACCRUAL ANALYTIC DEMO PROJECT + JSON analytic on timesheet,
# single-day batch, debit move line with analytic_distribution { "<aa_id>": 100.0 }.
#
# Run (local Odoo + PostgreSQL from /etc/odoo/odoo.conf):
#   odoo shell -c /etc/odoo/odoo.conf -d trgulf_Mrp < scripts/demo_labor_accrual_analytic_verify.py

import calendar
from datetime import date

from odoo import fields
from odoo.tools.sql import SQL

PROJECT_NAME = "LABOR ACCRUAL ANALYTIC DEMO PROJECT"
ANALYTIC_NAME = "LABOR ACCRUAL DEMO ANALYTIC"
EMP_NAME = "LAB ACCR DEMO EMP (ANALYTIC)"
TS_NAME = "LABOR ACCRUAL DEMO TIMESHEET LINE"
BATCH_PREFIX = "LAB ACCR DEMO VERIFY"

Company = env.company or env["res.company"].search([], limit=1)

from datetime import date as pydate

# Fixed demo date so multiple demo scripts do not share the same timesheet day.
demo_date = pydate(2099, 1, 13)
period_start = period_end = demo_date
period_key = "DEMO-SINGLE-%04d%02d%02d" % (demo_date.year, demo_date.month, demo_date.day)

AnalyticAccount = env["account.analytic.account"]
aa = AnalyticAccount.search([("name", "=", ANALYTIC_NAME), ("company_id", "=", Company.id)], limit=1)
if not aa:
    avals = {"name": ANALYTIC_NAME, "company_id": Company.id}
    if "plan_id" in AnalyticAccount._fields:
        Plan = env["account.analytic.plan"].search([], limit=1)
        if not Plan:
            Plan = env["account.analytic.plan"].create({"name": "Lab Accrual Demo Plan"})
        avals["plan_id"] = Plan.id
    aa = AnalyticAccount.create(avals)

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
if project.account_id:
    project.write({"account_id": False})

Employee = env["hr.employee"].search([("name", "=", EMP_NAME)], limit=1)
if not Employee:
    Employee = env["hr.employee"].create(
        {
            "name": EMP_NAME,
            "company_id": Company.id,
            "hourly_cost": 100.0,
        }
    )
else:
    Employee.sudo().write({"hourly_cost": 100.0})

debit_acc = Company.labor_accrual_debit_account_id
credit_acc = Company.labor_accrual_credit_account_id
journal = Company.labor_accrual_journal_id
if not (debit_acc and credit_acc and journal):
    raise SystemExit(
        "Configure company labor_accrual_debit_account_id, labor_accrual_credit_account_id, "
        "labor_accrual_journal_id first."
    )

Batch = env["labor.accrual.batch"]
batch_name = "%s %s" % (BATCH_PREFIX, period_key)
Batch.search(
    [("company_id", "=", Company.id), ("name", "ilike", BATCH_PREFIX + "%")]
).unlink()

AAL = env["account.analytic.line"]
AAL.search([("name", "=", TS_NAME), ("project_id", "=", project.id)]).unlink()

plan_fnames = AAL._get_plan_fnames()
if not plan_fnames:
    raise SystemExit("account.analytic.line has no analytic plan columns.")

ts_vals = {
    "name": TS_NAME,
    "project_id": project.id,
    "employee_id": Employee.id,
    "company_id": Company.id,
    "unit_amount": 1.0,
    "date": demo_date,
    plan_fnames[0]: aa.id,
    "analytic_distribution": {str(aa.id): 100.0},
}
if "validated" in AAL._fields:
    ts_vals["validated"] = True
if "include_in_payroll" in AAL._fields:
    ts_vals["include_in_payroll"] = True

ts = AAL.create(ts_vals)

# Optional: prove JSON-only path — clear plan columns, keep ORM distribution
for fname in ts._get_plan_fnames():
    env.cr.execute(
        SQL(
            "UPDATE account_analytic_line SET %s = NULL WHERE id = %s",
            SQL.identifier(fname),
            ts.id,
        )
    )
env.cr.commit()
ts.invalidate_recordset()
ts.write({"analytic_distribution": {str(aa.id): 100.0}})
ts.invalidate_recordset()

batch = Batch.create(
    {
        "name": batch_name,
        "company_id": Company.id,
        "period_start": period_start,
        "period_end": period_end,
        "period_key": period_key,
        "state": "draft",
    }
)
batch.action_populate_lines()
if not batch.line_ids:
    raise SystemExit("No batch lines (check timesheet domain / labor amount).")

batch.action_generate_draft_move()
move = batch.move_id
debit = move.line_ids.filtered(lambda l: l.debit > 0)
credit = move.line_ids.filtered(lambda l: l.credit > 0)

print("=== LABOR ACCRUAL ANALYTIC DEMO — EVIDENCE ===")
print("company_id=%s" % Company.id)
print("analytic_account_id=%s name=%s" % (aa.id, aa.name))
print("project_id=%s name=%s project_account_id=%s" % (project.id, project.name, project.account_id.id))
print("employee_id=%s" % Employee.id)
print("timesheet_line_id=%s" % ts.id)
print("timesheet_analytic_distribution=%r" % (ts.analytic_distribution,))
print("batch_id=%s" % batch.id)
print("move_id=%s" % move.id)
print("debit_move_line_ids=%s" % debit.ids)
print("credit_move_line_ids=%s" % credit.ids)
for dl in debit:
    print("DEBIT ml=%s analytic_distribution=%r" % (dl.id, dl.analytic_distribution))
for cl in credit:
    print("CREDIT ml=%s analytic_distribution=%r" % (cl.id, cl.analytic_distribution))

env.cr.commit()
