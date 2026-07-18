#!/usr/bin/env python3
"""Seed Playwright UAT data for gpc_gulf_project_ext — run via odoo shell."""
import json
import os
from pathlib import Path

MARKER = "GPC Playwright Phase1 UAT"
PRODUCT_NAME = "GPC Playwright Dimension Product"

login = os.environ.get("GCC_ODOO_LOGIN", "support@edafa.sa")
user = env["res.users"].search([("login", "=", login)], limit=1)
if not user:
    user = env.ref("base.user_admin")
seed_env = env(user=user)
company = seed_env.company

Product = seed_env["product.product"].search([("name", "=", PRODUCT_NAME)], limit=1)
if not Product:
    Product = seed_env["product.product"].create({
        "name": PRODUCT_NAME,
        "type": "service",
        "list_price": 490.0,
    })

project = seed_env["project.project"].search([("name", "=", MARKER)], limit=1)
if not project:
    project = seed_env["project.project"].create({
        "name": MARKER,
        "company_id": company.id,
        "description": "<p>Playwright <strong>description</strong> with list:</p><ul><li>Item A</li><li>Item B</li></ul>",
        "contract_amount": 591706.80,
    })
else:
    project.write({
        "description": "<p>Playwright <strong>description</strong> with list:</p><ul><li>Item A</li><li>Item B</li></ul>",
        "contract_amount": 591706.80,
    })

partner = seed_env["res.partner"].search([], limit=1)
order = seed_env["sale.order"].search([
    ("partner_id", "=", partner.id),
    ("order_line.product_id", "=", Product.id),
    ("order_line.length_cm", "=", 180.0),
], limit=1)
if not order:
    order = seed_env["sale.order"].create({
        "partner_id": partner.id,
        "company_id": company.id,
        "order_line": [(0, 0, {
            "product_id": Product.id,
            "product_uom_qty": 24,
            "price_unit": 490.0,
            "length_cm": 180.0,
            "width_cm": 305.0,
        })],
    })
else:
    order.order_line.write({
        "product_uom_qty": 24,
        "price_unit": 490.0,
        "length_cm": 180.0,
        "width_cm": 305.0,
    })

dashboard_action = seed_env.ref("project.project_update_all_action")
sales_action = seed_env.ref("sale.action_quotations")

out = {
    "project_id": project.id,
    "project_name": project.name,
    "sale_order_id": order.id,
    "sale_order_name": order.name,
    "expected_line_total": 64562.40,
    "dashboard_action_id": dashboard_action.id,
    "quotations_action_id": sales_action.id,
    "company_name": company.name,
    "seed_user_login": login,
}
path = Path("/opt/localaddons/gpc_gulf_project_ext/e2e/.playwright-seed.json")
path.write_text(json.dumps(out, indent=2), encoding="utf-8")
env.cr.commit()
print(f"Wrote {path}")
print(json.dumps(out, indent=2))
