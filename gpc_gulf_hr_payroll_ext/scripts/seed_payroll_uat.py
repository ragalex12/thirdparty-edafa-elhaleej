#!/usr/bin/env python3
"""Seed payroll UAT data for gpc_gulf_hr_payroll_ext — run via odoo shell."""
import json
import os
from datetime import date
from pathlib import Path

MARKER = "GPC Gulf Payroll UAT Employee"
TEMPLATE_NAME = "Gulf Payroll Template UAT"

login = os.environ.get("GCC_ODOO_LOGIN", "support@edafa.sa")
user = env["res.users"].search([("login", "=", login)], limit=1)
if not user:
    user = env.ref("base.user_admin")
seed_env = env(user=user)
company = seed_env.company

struct = seed_env.ref("gpc_gulf_hr_payroll_ext.structure_gulf_standard", raise_if_not_found=False)
if not struct:
    raise RuntimeError("Install gpc_gulf_hr_payroll_ext first")

template = seed_env["hr.version"].search([
    ("name", "=", TEMPLATE_NAME),
    ("employee_id", "=", False),
], limit=1)
if not template:
    template = seed_env.ref("gpc_gulf_hr_payroll_ext.contract_template_gulf_uat", raise_if_not_found=False)
if template:
    template.write({
        "struct_id": struct.id,
        "wage": 10000.0,
        "travel_allowance": 500.0,
        "other_allowance": 200.0,
        "company_id": company.id,
    })

employee = seed_env["hr.employee"].search([("name", "=", MARKER)], limit=1)
if not employee:
    employee = seed_env["hr.employee"].create({
        "name": MARKER,
        "company_id": company.id,
    })

today = date.today()
month_start = today.replace(day=1)
version = seed_env["hr.version"].search([
    ("employee_id", "=", employee.id),
    ("contract_date_start", "<=", today),
    "|", ("contract_date_end", "=", False), ("contract_date_end", ">=", today),
], limit=1, order="date_version desc")
if not version:
    version = employee.create_contract(month_start)
    version.write({
        "contract_template_id": template.id,
        "struct_id": struct.id,
        "wage": 10000.0,
        "travel_allowance": 500.0,
        "other_allowance": 200.0,
        "contract_date_start": month_start,
        "contract_date_end": False,
    })
else:
    version.write({
        "contract_template_id": template.id,
        "struct_id": struct.id,
        "wage": 10000.0,
        "travel_allowance": 500.0,
        "other_allowance": 200.0,
    })

out = {
    "employee_id": employee.id,
    "employee_name": employee.name,
    "version_id": version.id,
    "structure_id": struct.id,
    "structure_name": struct.name,
    "expected_net": 12900.0,
    "company_name": company.name,
    "seed_user_login": login,
}
path = Path("/opt/localaddons/gpc_gulf_hr_payroll_ext/e2e/.playwright-seed.json")
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(out, indent=2), encoding="utf-8")
print(f"Seeded payroll UAT: employee={employee.id} version={version.id} struct={struct.name}")
env.cr.commit()
