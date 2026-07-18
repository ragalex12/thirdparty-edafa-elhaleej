#!/usr/bin/env python3
# Copyright 2026
# SPDX-License-Identifier: LGPL-3.0-or-later
#
# Demo: FIVE different projects (each with its own analytic account) →
# five timesheet lines → labor accrual batch → draft JE with FIVE debit lines
# (one analytic distribution per project group).
#
# Run:
#   odoo shell -c /etc/odoo/odoo.conf -d trgulf_Mrp \
#     < scripts/demo_labor_accrual_five_projects_verify.py
#
# Writes move id for Playwright:
#   /opt/localaddons/gpc_worker_timesheet_labor_accrual_bridge/e2e/.last-five-projects-move-id.txt

import os

from odoo import fields

NUM_PROJECTS = 5
BATCH_NAME = "LAB ACCR DEMO FIVE PROJECTS"
EMP_NAME = "LAB ACCR DEMO EMP (FIVE PROJECTS)"
E2E_DIR = "/opt/localaddons/gpc_worker_timesheet_labor_accrual_bridge/e2e"
MOVE_ID_FILE = os.path.join(E2E_DIR, ".last-five-projects-move-id.txt")

Company = env.company or env["res.company"].search([], limit=1)

from datetime import date as pydate

demo_date = pydate(2099, 1, 15)
period_start = period_end = demo_date
period_key = "FIVE-%04d%02d%02d" % (demo_date.year, demo_date.month, demo_date.day)


def _ensure_aa(name):
    AnalyticAccount = env["account.analytic.account"]
    aa = AnalyticAccount.search([("name", "=", name), ("company_id", "=", Company.id)], limit=1)
    if aa:
        return aa
    avals = {"name": name, "company_id": Company.id}
    if "plan_id" in AnalyticAccount._fields:
        Plan = env["account.analytic.plan"].search([], limit=1)
        if not Plan:
            Plan = env["account.analytic.plan"].create({"name": "Lab Accrual Five Projects Plan"})
        avals["plan_id"] = Plan.id
    return AnalyticAccount.create(avals)


if not (
    Company.labor_accrual_debit_account_id
    and Company.labor_accrual_credit_account_id
    and Company.labor_accrual_journal_id
):
    raise SystemExit("Configure labor_accrual_* accounts and journal on company.")

Employee = env["hr.employee"].search([("name", "=", EMP_NAME)], limit=1)
if not Employee:
    Employee = env["hr.employee"].create(
        {"name": EMP_NAME, "company_id": Company.id, "hourly_cost": 100.0}
    )
else:
    Employee.sudo().write({"hourly_cost": 100.0})

AAL = env["account.analytic.line"]
Project = env["project.project"]
plan_fnames = AAL._get_plan_fnames()
if not plan_fnames:
    raise SystemExit("Need at least one analytic plan column on account.analytic.line.")
primary_f = "account_id" if "account_id" in plan_fnames else plan_fnames[0]

Batch = env["labor.accrual.batch"]
Batch.search(
    [("company_id", "=", Company.id), ("name", "ilike", BATCH_NAME + "%")]
).unlink()

projects = []
timesheets = []
analytic_accounts = []

for i in range(1, NUM_PROJECTS + 1):
    aa_name = "LABOR ACCRUAL DEMO ANALYTIC P%d" % i
    proj_name = "LABOR ACCRUAL FIVE PROJ %d" % i
    ts_name = "LABOR ACCRUAL FIVE TS %d" % i

    aa = _ensure_aa(aa_name)
    analytic_accounts.append(aa)

    project = Project.search([("name", "=", proj_name), ("company_id", "=", Company.id)], limit=1)
    if not project:
        project = Project.create(
            {
                "name": proj_name,
                "company_id": Company.id,
                "allow_timesheets": True,
            }
        )
    project.write({"account_id": aa.id})
    projects.append(project)

    AAL.search([("name", "=", ts_name), ("project_id", "=", project.id)]).unlink()

    ts_vals = {
        "name": ts_name,
        "project_id": project.id,
        "employee_id": Employee.id,
        "company_id": Company.id,
        "unit_amount": float(i),
        "date": demo_date,
        primary_f: aa.id,
    }
    if "validated" in AAL._fields:
        ts_vals["validated"] = True
    if "include_in_payroll" in AAL._fields:
        ts_vals["include_in_payroll"] = True

    ts = AAL.create(ts_vals)
    timesheets.append(ts)

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

if len(batch.line_ids) != NUM_PROJECTS:
    raise SystemExit(
        "Expected %d batch lines (one per project/timesheet); got %s"
        % (NUM_PROJECTS, len(batch.line_ids))
    )

batch.action_generate_draft_move()
move = batch.move_id
debit_lines = move.line_ids.filtered(lambda l: l.debit > 0)
credit_lines = move.line_ids.filtered(lambda l: l.credit > 0)

debit_dists = [dl.analytic_distribution for dl in debit_lines]
unique_dists = {tuple(sorted((d or {}).items())) for d in debit_dists}

if len(debit_lines) != NUM_PROJECTS:
    raise SystemExit(
        "Expected %d debit lines; got %d" % (NUM_PROJECTS, len(debit_lines))
    )
if len(unique_dists) != NUM_PROJECTS:
    raise SystemExit(
        "Expected %d distinct analytic distributions on debits; got %d: %s"
        % (NUM_PROJECTS, len(unique_dists), debit_dists)
    )
if len(credit_lines) != 1:
    raise SystemExit("Expected 1 credit line; got %s" % len(credit_lines))
if any(credit_lines.mapped("analytic_distribution")):
    raise SystemExit("Credit line must not have analytic_distribution")

os.makedirs(E2E_DIR, exist_ok=True)
with open(MOVE_ID_FILE, "w", encoding="utf-8") as fh:
    fh.write(str(move.id))

print("=== LABOR ACCRUAL FIVE PROJECTS DEMO ===")
print("batch_id=%s batch_name=%s period_key=%s" % (batch.id, batch.name, period_key))
print("batch_line_count=%s" % len(batch.line_ids))
for bl in batch.line_ids:
    dist = batch._get_analytic_distribution_for_batch_line(bl)
    print(
        "  BATCH_LINE project=%s timesheet=%s amount=%s dist=%r"
        % (
            bl.project_id.display_name,
            bl.timesheet_line_id.display_name,
            bl.amount,
            dist,
        )
    )
print("move_id=%s" % move.id)
print("debit_line_count=%s" % len(debit_lines))
for dl in debit_lines:
    print("  DEBIT ml=%s debit=%s analytic_distribution=%r" % (dl.id, dl.debit, dl.analytic_distribution))
print("credit_total=%s" % credit_lines.credit)
print("PLAYWRIGHT_MOVE_ID_FILE=%s" % MOVE_ID_FILE)
print("GCC_ODOO_FIVE_PROJECTS_MOVE_ID=%s" % move.id)
env.cr.commit()
