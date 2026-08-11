# Copyright 2026
# Run ONLY via odoo shell on database trgcc_mm_uat.
# Never against trgcc / entgcc.
"""Populate identifiable MM-UAT-* records for the extended Gulf/MM UAT pack."""

from __future__ import annotations

import json
from datetime import date

MARKER = "gulf.mm.uat.extended_dataset.v1"
ALLOWED_DB = "trgcc_mm_uat"
FORBIDDEN_DBS = ("trgcc", "entgcc")

# Existing GCC COA — do not invent accounts.
DEBIT_LABOR_ID = 131  # 410028 Basic Salary - Projects
CREDIT_LABOR_ID = 57  # 202001 ACCRUED SALARIES
JOURNAL_SLR_ID = 23
JOURNAL_MISC_ID = 3
MATERIAL_ACC_ID = 97  # 400015 Material Tools
INCOME_ACC_ID = 156  # 500001 INCOME FROM PROJECTS (balancing offset only)


def _assert_test_db(env):
    db = env.cr.dbname
    if db in FORBIDDEN_DBS or db != ALLOWED_DB:
        raise RuntimeError("Refusing to seed database %r (allowed: %s)" % (db, ALLOWED_DB))


def _param(env, key, default=None):
    return env["ir.config_parameter"].sudo().get_param(key, default)


def _set_param(env, key, value):
    env["ir.config_parameter"].sudo().set_param(key, value)


def _plan(env):
    Plan = env["account.analytic.plan"]
    plan = Plan.search([], limit=1)
    if not plan:
        plan = Plan.create({"name": "MM-UAT Analytic Plan"})
    return plan


def _aa(env, company, name, plan):
    vals = {"name": name, "plan_id": plan.id}
    if "company_id" in env["account.analytic.account"]._fields:
        vals["company_id"] = company.id
    existing = env["account.analytic.account"].search([("name", "=", name)], limit=1)
    return existing or env["account.analytic.account"].create(vals)


def _project(env, company, name, aa, exclude=False):
    existing = env["project.project"].search([("name", "=", name)], limit=1)
    if existing:
        return existing
    vals = {
        "name": name,
        "company_id": company.id,
        "account_id": aa.id,
    }
    if "exclude_from_payroll" in env["project.project"]._fields:
        vals["exclude_from_payroll"] = exclude
    return env["project.project"].create(vals)


def _employee(env, company, name, hourly):
    existing = env["hr.employee"].search([("name", "=", name), ("company_id", "=", company.id)], limit=1)
    if existing:
        if "hourly_cost" in existing._fields:
            existing.hourly_cost = hourly
        return existing
    vals = {"name": name, "company_id": company.id}
    if "hourly_cost" in env["hr.employee"]._fields:
        vals["hourly_cost"] = hourly
    return env["hr.employee"].create(vals)


def _ts(env, *, name, employee, project, aa, day, hours, payroll=True, company=None):
    AAL = env["account.analytic.line"]
    existing = AAL.search([("name", "=", name)], limit=1)
    if existing:
        return existing
    vals = {
        "name": name,
        "employee_id": employee.id,
        "project_id": project.id,
        "account_id": aa.id,
        "unit_amount": hours,
        "date": day,
        "company_id": (company or env.company).id,
    }
    if "include_in_payroll" in AAL._fields:
        vals["include_in_payroll"] = payroll
    if "validated" in AAL._fields:
        vals["validated"] = True
    return AAL.create(vals)


def _material_move(env, *, name, day, amount, aa, company):
    Move = env["account.move"]
    existing = Move.search([("ref", "=", name)], limit=1)
    if existing:
        return existing
    move = Move.create(
        {
            "move_type": "entry",
            "journal_id": JOURNAL_MISC_ID,
            "date": day,
            "ref": name,
            "company_id": company.id,
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "name": name,
                        "account_id": MATERIAL_ACC_ID,
                        "debit": amount,
                        "credit": 0.0,
                        "analytic_distribution": {str(aa.id): 100.0},
                    },
                ),
                (
                    0,
                    0,
                    {
                        "name": name + " offset",
                        "account_id": INCOME_ACC_ID,
                        "debit": 0.0,
                        "credit": amount,
                    },
                ),
            ],
        }
    )
    move.action_post()
    return move


def _batch(env, *, name, company, start, end):
    Batch = env["labor.accrual.batch"]
    existing = Batch.search([("name", "=", name)], limit=1)
    if existing:
        return existing
    return Batch.create(
        {
            "name": name,
            "company_id": company.id,
            "period_start": start,
            "period_end": end,
            "state": "draft",
        }
    )


def seed(env):
    _assert_test_db(env)
    company = env.company
    if company.name != "GCC" and company.id != 1:
        # still allow if this is the UAT main company
        pass

    if _param(env, MARKER):
        return {"skipped": True, "reason": "already seeded", "marker": MARKER}

    # Safety: company labor config must already be the real GCC accounts.
    company.write(
        {
            "labor_accrual_debit_account_id": DEBIT_LABOR_ID,
            "labor_accrual_credit_account_id": CREDIT_LABOR_ID,
            "labor_accrual_journal_id": JOURNAL_SLR_ID,
        }
    )

    plan = _plan(env)
    projects = {}
    specs = [
        ("ALPHA", False),
        ("BETA", False),
        ("LEGACY", False),
        ("PAYROLL", False),
        ("OPTOUT", True),
        ("GLONLY", False),
        ("TSONLY", False),
        ("MIXED", False),
        ("HIST", False),
        ("HELD", False),
    ]
    for key, optout in specs:
        aa = _aa(env, company, "MM-UAT-AA-%s" % key, plan)
        projects[key] = {
            "aa": aa,
            "project": _project(env, company, "MM-UAT-PROJ-%s" % key, aa, exclude=optout),
        }

    employees = {
        "01": _employee(env, company, "MM-UAT-EMP-01", 50.0),
        "02": _employee(env, company, "MM-UAT-EMP-02", 40.0),
        "03": _employee(env, company, "MM-UAT-EMP-03", 30.0),
        "04": _employee(env, company, "MM-UAT-EMP-04", 0.0),
        "05": _employee(env, company, "MM-UAT-EMP-05", 75.0),
        "06": _employee(env, company, "MM-UAT-EMP-06", 50.0),
        "07": _employee(env, company, "MM-UAT-EMP-07", 45.0),
        "08": _employee(env, company, "MM-UAT-EMP-08", 50.0),
        "09": _employee(env, company, "MM-UAT-EMP-09", 40.0),
        "10": _employee(env, company, "MM-UAT-EMP-10", 55.0),
        "12": _employee(env, company, "MM-UAT-EMP-12", 50.0),
    }

    foreign = {"ok": False}
    try:
        other = env["res.company"].search([("name", "=", "MM-UAT-CO-FOREIGN")], limit=1)
        if not other:
            other = env["res.company"].create({"name": "MM-UAT-CO-FOREIGN"})
        emp11 = _employee(env, other, "MM-UAT-EMP-11", 50.0)
        aa_fx = _aa(env, other, "MM-UAT-AA-WRONGCO", plan)
        proj_fx = _project(env, other, "MM-UAT-PROJ-WRONGCO", aa_fx)
        ts_fx = _ts(
            env,
            name="MM-UAT-TS-2026-05-WRONGCO",
            employee=emp11,
            project=proj_fx,
            aa=aa_fx,
            day=date(2026, 5, 8),
            hours=8.0,
            company=other,
        )
        foreign = {
            "ok": True,
            "company_id": other.id,
            "employee_id": emp11.id,
            "project_id": proj_fx.id,
            "timesheet_id": ts_fx.id,
        }
    except Exception as exc:  # noqa: BLE001 — company create may require extra CoA
        foreign = {"ok": False, "error": str(exc)}

    created_ts = []

    def add_ts(*args, **kwargs):
        rec = _ts(*args, **kwargs)
        created_ts.append(rec)
        return rec

    # --- Demo Alpha (May) ---
    for emp_key, day, hours, extra in [
        ("01", date(2026, 5, 4), 8.0, "001"),
        ("01", date(2026, 5, 5), 6.0, "002"),
        ("02", date(2026, 5, 4), 8.0, "003"),
        ("02", date(2026, 5, 5), 8.0, "004"),
        ("03", date(2026, 5, 4), 8.0, "005"),
        ("03", date(2026, 5, 6), 8.0, "006"),
        ("01", date(2026, 5, 6), 4.0, "007"),  # same employee, second line same week
        ("01", date(2026, 5, 6), 3.0, "008"),  # same day multiple lines
    ]:
        add_ts(
            env,
            name="MM-UAT-TS-2026-05-%s" % extra,
            employee=employees[emp_key],
            project=projects["ALPHA"]["project"],
            aa=projects["ALPHA"]["aa"],
            day=day,
            hours=hours,
        )
    add_ts(
        env,
        name="MM-UAT-TS-2026-05-EXCL",
        employee=employees["01"],
        project=projects["OPTOUT"]["project"],
        aa=projects["OPTOUT"]["aa"],
        day=date(2026, 5, 6),
        hours=8.0,
        payroll=False,
    )

    # Beta mixed: timesheet + material
    add_ts(
        env,
        name="MM-UAT-TS-2026-05-BETA",
        employee=employees["09"],
        project=projects["BETA"]["project"],
        aa=projects["BETA"]["aa"],
        day=date(2026, 5, 12),
        hours=8.0,
    )
    mat_beta = _material_move(
        env,
        name="MM-UAT-MAT-BETA-2026-05",
        day=date(2026, 5, 12),
        amount=1500.0,
        aa=projects["BETA"]["aa"],
        company=company,
    )
    mat_glonly = _material_move(
        env,
        name="MM-UAT-MAT-GLONLY-2026-05",
        day=date(2026, 5, 15),
        amount=2200.0,
        aa=projects["GLONLY"]["aa"],
        company=company,
    )
    mat_mixed = _material_move(
        env,
        name="MM-UAT-MAT-MIXED-2026-05",
        day=date(2026, 5, 18),
        amount=800.0,
        aa=projects["MIXED"]["aa"],
        company=company,
    )
    add_ts(
        env,
        name="MM-UAT-TS-2026-05-MIXED",
        employee=employees["05"],
        project=projects["MIXED"]["project"],
        aa=projects["MIXED"]["aa"],
        day=date(2026, 5, 18),
        hours=8.0,
    )
    add_ts(
        env,
        name="MM-UAT-TS-2026-05-TSONLY",
        employee=employees["07"],
        project=projects["TSONLY"]["project"],
        aa=projects["TSONLY"]["aa"],
        day=date(2026, 5, 20),
        hours=8.0,
    )
    add_ts(
        env,
        name="MM-UAT-TS-عربي-001",
        employee=employees["07"],
        project=projects["TSONLY"]["project"],
        aa=projects["TSONLY"]["aa"],
        day=date(2026, 5, 21),
        hours=8.0,
    )

    # Multi-project same employee/day
    add_ts(
        env,
        name="MM-UAT-TS-2026-05-MULTI-A",
        employee=employees["07"],
        project=projects["PAYROLL"]["project"],
        aa=projects["PAYROLL"]["aa"],
        day=date(2026, 5, 22),
        hours=4.0,
    )
    add_ts(
        env,
        name="MM-UAT-TS-2026-05-MULTI-B",
        employee=employees["07"],
        project=projects["MIXED"]["project"],
        aa=projects["MIXED"]["aa"],
        day=date(2026, 5, 22),
        hours=4.0,
    )

    # Zero cost (skipped by populate)
    add_ts(
        env,
        name="MM-UAT-TS-2026-05-ZEROCOST",
        employee=employees["04"],
        project=projects["PAYROLL"]["project"],
        aa=projects["PAYROLL"]["aa"],
        day=date(2026, 5, 25),
        hours=8.0,
    )
    # Zero hours
    add_ts(
        env,
        name="MM-UAT-TS-2026-05-ZEROHOURS",
        employee=employees["01"],
        project=projects["ALPHA"]["project"],
        aa=projects["ALPHA"]["aa"],
        day=date(2026, 5, 26),
        hours=0.0,
    )
    # Duplicate-looking
    add_ts(
        env,
        name="MM-UAT-TS-2026-05-DUP-A",
        employee=employees["12"],
        project=projects["PAYROLL"]["project"],
        aa=projects["PAYROLL"]["aa"],
        day=date(2026, 5, 27),
        hours=8.0,
    )
    add_ts(
        env,
        name="MM-UAT-TS-2026-05-DUP-B",
        employee=employees["12"],
        project=projects["PAYROLL"]["project"],
        aa=projects["PAYROLL"]["aa"],
        day=date(2026, 5, 27),
        hours=8.0,
    )

    # --- April retro subset (1-7) + held-back (20-25) + anomalies (28) ---
    for i, emp_key in enumerate(("10", "05", "02", "03"), start=1):
        add_ts(
            env,
            name="MM-UAT-TS-2026-04-RETRO-%03d" % i,
            employee=employees[emp_key],
            project=projects["LEGACY"]["project"],
            aa=projects["LEGACY"]["aa"],
            day=date(2026, 4, i),
            hours=8.0,
        )
    for i in range(1, 6):
        add_ts(
            env,
            name="MM-UAT-TS-2026-04-HELD-%03d" % i,
            employee=employees["10"],
            project=projects["HELD"]["project"],
            aa=projects["HELD"]["aa"],
            day=date(2026, 4, 19 + i),
            hours=8.0,
        )
    for hours, tag in (
        (25.0, "25H"),
        (40.0, "40H"),
        (100.0, "100H"),
        (200.0, "200H"),
        (260.0, "260H"),
    ):
        add_ts(
            env,
            name="MM-UAT-TS-2026-04-ANOM-%s" % tag,
            employee=employees["08"],
            project=projects["HIST"]["project"],
            aa=projects["HIST"]["aa"],
            day=date(2026, 4, 28),
            hours=hours,
        )
    add_ts(
        env,
        name="MM-UAT-TS-2026-04-FALSEPAY",
        employee=employees["06"],
        project=projects["OPTOUT"]["project"],
        aa=projects["OPTOUT"]["aa"],
        day=date(2026, 4, 28),
        hours=8.0,
        payroll=False,
    )
    add_ts(
        env,
        name="MM-UAT-TS-2026-04-ZEROCOST",
        employee=employees["04"],
        project=projects["HIST"]["project"],
        aa=projects["HIST"]["aa"],
        day=date(2026, 4, 28),
        hours=5.0,
    )

    # --- June volume for large statement / XLSX ---
    seq = 1
    june_days = [date(2026, 6, d) for d in (1, 2, 3, 4, 8, 9, 10, 11, 15, 16, 17, 18)]
    june_emp_proj = [
        ("01", "ALPHA"),
        ("02", "ALPHA"),
        ("03", "PAYROLL"),
        ("05", "MIXED"),
        ("07", "TSONLY"),
        ("09", "BETA"),
        ("12", "PAYROLL"),
    ]
    for day in june_days:
        for emp_key, proj_key in june_emp_proj:
            add_ts(
                env,
                name="MM-UAT-TS-2026-06-%03d" % seq,
                employee=employees[emp_key],
                project=projects[proj_key]["project"],
                aa=projects[proj_key]["aa"],
                day=day,
                hours=8.0,
            )
            seq += 1

    # October draft batch candidates
    for i, emp_key in enumerate(("01", "02", "09"), start=1):
        add_ts(
            env,
            name="MM-UAT-TS-2026-10-%03d" % i,
            employee=employees[emp_key],
            project=projects["ALPHA"]["project"],
            aa=projects["ALPHA"]["aa"],
            day=date(2026, 10, i),
            hours=8.0,
        )
    add_ts(
        env,
        name="MM-UAT-TS-2026-10-EXCL",
        employee=employees["06"],
        project=projects["OPTOUT"]["project"],
        aa=projects["OPTOUT"]["aa"],
        day=date(2026, 10, 2),
        hours=8.0,
        payroll=False,
    )

    # --- Batches ---
    batch_may = _batch(
        env,
        name="MM-UAT-BATCH-2026-05-POSTED",
        company=company,
        start=date(2026, 5, 1),
        end=date(2026, 5, 31),
    )
    batch_may.action_populate_lines()
    batch_may.action_generate_draft_move()
    batch_may.action_post_move()

    batch_apr = _batch(
        env,
        name="MM-UAT-BATCH-2026-04-RETRO",
        company=company,
        start=date(2026, 4, 1),
        end=date(2026, 4, 7),
    )
    batch_apr.action_populate_lines()
    batch_apr.action_generate_draft_move()
    batch_apr.action_post_move()

    batch_jun = _batch(
        env,
        name="MM-UAT-BATCH-2026-06-POSTED",
        company=company,
        start=date(2026, 6, 1),
        end=date(2026, 6, 30),
    )
    batch_jun.action_populate_lines()
    batch_jun.action_generate_draft_move()
    batch_jun.action_post_move()

    batch_oct = _batch(
        env,
        name="MM-UAT-BATCH-2026-10-DRAFT",
        company=company,
        start=date(2026, 10, 1),
        end=date(2026, 10, 31),
    )
    batch_oct.action_populate_lines()
    batch_oct.action_generate_draft_move()
    # leave draft / unposted on purpose

    # Duplicate period / cross-month attempts (expected fail).
    # Catching ValidationError without rollback would leave the row in this
    # cursor and commit it — always rollback the savepoint.
    dup_error = None
    try:
        with env.cr.savepoint():
            env["labor.accrual.batch"].create(
                {
                    "name": "MM-UAT-BATCH-2026-05-DUP-ATTEMPT",
                    "company_id": company.id,
                    "period_start": date(2026, 5, 1),
                    "period_end": date(2026, 5, 31),
                    "state": "draft",
                }
            )
    except Exception as exc:  # noqa: BLE001
        dup_error = type(exc).__name__ + ": " + str(exc).split("\n")[0]

    cross_error = None
    try:
        with env.cr.savepoint():
            env["labor.accrual.batch"].create(
                {
                    "name": "MM-UAT-BATCH-CROSS-MONTH",
                    "company_id": company.id,
                    "period_start": date(2026, 11, 15),
                    "period_end": date(2026, 12, 15),
                    "state": "draft",
                }
            )
    except Exception as exc:  # noqa: BLE001
        cross_error = type(exc).__name__ + ": " + str(exc).split("\n")[0]

    wizard = env["analytic.project.statement.wizard"].create(
        {
            "company_id": company.id,
            "date_from": date(2026, 4, 1),
            "date_to": date(2026, 10, 31),
            "target_move": "posted",
        }
    )
    rows = wizard._get_report_phase1_rows()
    xlsx_model = env["report.gpc_aps.proj_stmt_xlsx"].with_context(
        active_model="analytic.project.statement.wizard"
    )
    content, ext = xlsx_model.create_xlsx_report(wizard.ids, {})
    xlsx_path = "/tmp/mm_uat_extended_statement.xlsx"
    with open(xlsx_path, "wb") as fh:
        fh.write(content)

    inv = {
        "db": env.cr.dbname,
        "marker": MARKER,
        "company_id": company.id,
        "projects": {k: {"project_id": v["project"].id, "aa_id": v["aa"].id} for k, v in projects.items()},
        "employees": {k: emp.id for k, emp in employees.items()},
        "foreign": foreign,
        "timesheet_ids": [t.id for t in created_ts],
        "timesheet_count": len(created_ts),
        "material_moves": [mat_beta.id, mat_glonly.id, mat_mixed.id],
        "batches": {
            "may_posted": {
                "id": batch_may.id,
                "state": batch_may.state,
                "lines": len(batch_may.line_ids),
                "move_id": batch_may.move_id.id,
                "move_state": batch_may.move_id.state,
                "move_name": batch_may.move_id.name,
            },
            "apr_retro": {
                "id": batch_apr.id,
                "state": batch_apr.state,
                "lines": len(batch_apr.line_ids),
                "move_id": batch_apr.move_id.id,
                "move_state": batch_apr.move_id.state,
                "move_name": batch_apr.move_id.name,
            },
            "jun_posted": {
                "id": batch_jun.id,
                "state": batch_jun.state,
                "lines": len(batch_jun.line_ids),
                "move_id": batch_jun.move_id.id,
                "move_state": batch_jun.move_id.state,
                "move_name": batch_jun.move_id.name,
            },
            "oct_draft": {
                "id": batch_oct.id,
                "state": batch_oct.state,
                "lines": len(batch_oct.line_ids),
                "move_id": batch_oct.move_id.id,
                "move_state": batch_oct.move_id.state,
            },
        },
        "duplicate_period_error": dup_error,
        "cross_month_error": cross_error,
        "statement_row_count": len(rows),
        "statement_debit": sum(r.get("debit") or 0 for r in rows),
        "statement_credit": sum(r.get("credit") or 0 for r in rows),
        "xlsx_ext": ext,
        "xlsx_bytes": len(content),
        "xlsx_path": xlsx_path,
    }
    _set_param(env, MARKER, json.dumps({"seeded": True, "timesheets": len(created_ts)}))
    path = "/tmp/mm_uat_extended_inventory.json"
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(inv, fh, indent=2, default=str)
    env.cr.commit()
    return inv


if "env" in globals():
    result = seed(env)  # noqa: F821
    print(json.dumps(result, indent=2, default=str))
