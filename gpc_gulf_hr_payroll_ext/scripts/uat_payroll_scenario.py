#!/usr/bin/env python3
"""UAT for gpc_gulf_hr_payroll_ext — run via odoo shell."""
from datetime import date

MARKER = "GPC Gulf Payroll UAT Employee"
WAGE = 10000.0
TRAVEL = 500.0
OTHER = 200.0
OT = 1500.0
BONUS = 1000.0
DED = 300.0
EXPECTED_NET = WAGE + TRAVEL + OTHER + OT + BONUS - DED  # 12900.0

struct = env.ref("gpc_gulf_hr_payroll_ext.structure_gulf_standard")
assert struct.code == "GULF", f"structure code={struct.code}"

employee = env["hr.employee"].search([("name", "=", MARKER)], limit=1)
assert employee, "Run seed_payroll_uat.py first"

today = date.today()
month_start = today.replace(day=1)
if today.month == 12:
    month_end = today.replace(day=31)
else:
    from calendar import monthrange
    month_end = today.replace(day=monthrange(today.year, today.month)[1])

contracts = env["hr.payslip"].get_contract(employee, month_start, month_end)
assert contracts, "No active contract for employee"

payslip = env["hr.payslip"].create({
    "employee_id": employee.id,
    "contract_id": contracts[0],
    "struct_id": struct.id,
    "date_from": month_start,
    "date_to": month_end,
})
payslip.onchange_employee()

for line in payslip.input_line_ids:
    if line.code == "OT_AMT":
        line.amount = OT
    elif line.code == "BONUS":
        line.amount = BONUS
    elif line.code == "DED_OTHER":
        line.amount = DED

payslip.action_compute_sheet()
net_line = payslip.line_ids.filtered(lambda l: l.code == "NET")
assert net_line, "NET line missing"
net = net_line[0].total
assert abs(net - EXPECTED_NET) < 0.01, f"NET={net} expected={EXPECTED_NET}"

basic = payslip.get_salary_line_total("BASIC")
assert abs(basic - WAGE) < 0.01, f"BASIC={basic}"

import json
from pathlib import Path
seed_path = Path("/opt/localaddons/gpc_gulf_hr_payroll_ext/e2e/.playwright-seed.json")
if seed_path.is_file():
    data = json.loads(seed_path.read_text(encoding="utf-8"))
    data["payslip_id"] = payslip.id
    data["expected_net"] = EXPECTED_NET
    seed_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

print(f"UAT PASSED: NET={net} (expected {EXPECTED_NET}) OT={OT} BONUS={BONUS} DED={DED}")
