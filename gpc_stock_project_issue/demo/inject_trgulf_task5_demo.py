# Run: ODOO_RC=/etc/odoo/odoo.conf odoo shell -d trgulf_Mrp < inject_trgulf_task5_demo.py
# Injected context: `env` is provided by Odoo shell.

from odoo import Command

DEMO_PROJECT = "GPC Task5 Demo Project"
DEMO_TAG = "GPC-TASK5-DEMO"


def _main():
    company = env.company
    User = env["res.users"].sudo()
    admin = User.search([("login", "=", "admin")], limit=1) or env.user

    # --- Locations & picking types
    wh = env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1)
    if not wh:
        raise RuntimeError("No warehouse for company %s" % company.name)
    stock_loc = wh.lot_stock_id
    sup_loc = env.ref("stock.stock_location_suppliers")
    cust_loc = env.ref("stock.stock_location_customers")
    ptype_in = env["stock.picking.type"].search(
        [("code", "=", "incoming"), ("warehouse_id", "=", wh.id)], limit=1
    )
    ptype_out = env["stock.picking.type"].search(
        [("code", "=", "outgoing"), ("warehouse_id", "=", wh.id)], limit=1
    )
    if not ptype_in or not ptype_out:
        raise RuntimeError("Missing incoming/outgoing operation types for warehouse.")

    ptype_out.gpc_project_issue_enabled = True

    # --- Company: debit account (must differ from stock valuation account used on moves)
    Account = env["account.account"]
    debit_acc = Account.search(
        [
            ("company_ids", "in", company.ids),
            ("account_type", "=", "expense"),
        ],
        limit=1,
    )
    if not debit_acc:
        debit_acc = Account.search([("company_ids", "in", company.ids)], limit=1)
    if not debit_acc:
        raise RuntimeError("No suitable expense account for GPC debit line.")

    journal = company.account_stock_journal_id or env["account.journal"].search(
        [("company_id", "=", company.id), ("type", "=", "general")], limit=1
    )
    company.write(
        {
            "gpc_project_issue_debit_account_id": debit_acc.id,
            "gpc_project_issue_journal_id": journal.id if journal else False,
        }
    )

    # --- Analytic + project
    # account.analytic.plan has no company_id in Odoo 19.
    plan = env["account.analytic.plan"].search([], limit=1)
    if not plan:
        plan = env["account.analytic.plan"].create({"name": "GPC Demo Plan"})
    analytic = env["account.analytic.account"].search(
        [("name", "=", DEMO_TAG), ("company_id", "in", [False, company.id])], limit=1
    )
    if not analytic:
        analytic = env["account.analytic.account"].create(
            {
                "name": DEMO_TAG,
                "plan_id": plan.id,
                "company_id": company.id,
            }
        )
    Project = env["project.project"]
    project = Project.search(
        [("name", "=", DEMO_PROJECT), ("company_id", "=", company.id)], limit=1
    )
    if not project:
        project = Project.create(
            {
                "name": DEMO_PROJECT,
                "company_id": company.id,
            }
        )

    # --- Storable product with valuation
    product = env["product.product"].search(
        [
            ("is_storable", "=", True),
            ("company_id", "in", [False, company.id]),
        ],
        limit=1,
    )
    if not product:
        raise RuntimeError("No storable product found — add a storable product first.")

    # Ensure a positive standard cost so SVLs are non-zero.
    if not product.standard_price:
        product.standard_price = 10.0

    uom = product.uom_id
    qty_in = 10.0
    qty_out = 2.0
    unit_cost = 5.0

    # --- Receipt (stock in) — use picking-based workflow so SVLs are created correctly.
    in_pick = env["stock.picking"].create(
        {
            "picking_type_id": ptype_in.id,
            "location_id": sup_loc.id,
            "location_dest_id": stock_loc.id,
            "company_id": company.id,
            "move_ids": [
                Command.create(
                    {
                        "name": product.display_name,
                        "product_id": product.id,
                        "product_uom": uom.id,
                        "product_uom_qty": qty_in,
                        "location_id": sup_loc.id,
                        "location_dest_id": stock_loc.id,
                        "price_unit": unit_cost,
                    }
                )
            ],
        }
    )
    in_pick.action_confirm()
    in_pick.action_assign()
    for move in in_pick.move_ids:
        move.quantity = move.product_uom_qty
        move.picked = True
    in_pick.button_validate()

    # --- Delivery (stock out) — done picking with GPC fields
    out_pick = env["stock.picking"].create(
        {
            "picking_type_id": ptype_out.id,
            "location_id": stock_loc.id,
            "location_dest_id": cust_loc.id,
            "company_id": company.id,
            "gpc_issue_project_id": project.id,
            "gpc_issue_analytic_account_id": analytic.id,
            "move_ids": [
                Command.create(
                    {
                        "name": product.display_name,
                        "product_id": product.id,
                        "product_uom": uom.id,
                        "product_uom_qty": qty_out,
                        "location_id": stock_loc.id,
                        "location_dest_id": cust_loc.id,
                    }
                )
            ],
        }
    )
    out_pick.action_confirm()
    out_pick.action_assign()
    for move in out_pick.move_ids:
        move.quantity = move.product_uom_qty
        move.picked = True
    out_pick.button_validate()

    env.cr.commit()

    print("=== GPC Task 5 demo data ready ===")
    print("Company:", company.name)
    print("Delivery (open this transfer):", out_pick.name, "| id=", out_pick.id)
    print("Product:", product.display_name, "| qty out:", qty_out)
    print("Project:", project.name, "| Analytic:", analytic.name)
    print("Operation type GPC enabled:", ptype_out.name)
    print("Next in UI: Inventory → open transfer → tab GPC project issue → header GPC project issue")
    print("URL hint: /odoo/stock.picking/%s" % out_pick.id)


_main()
