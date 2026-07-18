# Copyright 2026
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).


def analytic_account_vals(env, company, name):
    vals = {"name": name, "company_id": company.id}
    if "plan_id" in env["account.analytic.account"]._fields:
        plan = env["account.analytic.plan"].search([], limit=1)
        if not plan:
            plan = env["account.analytic.plan"].create({"name": "Bridge Test Plan"})
        vals["plan_id"] = plan.id
    return vals
