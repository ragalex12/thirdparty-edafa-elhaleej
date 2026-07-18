#!/usr/bin/env python3
"""UAT script for gpc_gulf_project_ext — run via odoo shell."""
# Usage: sudo -u odoo odoo shell -c /etc/odoo/odoo.conf -d trgulf_Mrp < /opt/localaddons/gpc_gulf_project_ext/scripts/uat_scenario.py

Product = env["product.product"].create({
    "name": "GPC UAT Dimension Product",
    "type": "service",
    "list_price": 490.0,
})
partner = env["res.partner"].search([], limit=1)
project = env["project.project"].create({
    "name": "GPC UAT Project",
    "description": "<p>UAT <strong>description</strong></p>",
    "contract_amount": 591706.80,
})
assert project.project_valuebvat == 591706.80, f"sync fail: {project.project_valuebvat}"

panel = project.get_panel_data()
assert panel.get("show_project_details"), "panel flag missing"
assert "UAT" in (panel.get("description") or ""), "description missing in panel"
assert abs(panel.get("contract_amount", 0) - 591706.80) < 0.01, "contract_amount in panel"

order = env["sale.order"].create({
    "partner_id": partner.id,
    "order_line": [(0, 0, {
        "product_id": Product.id,
        "product_uom_qty": 24,
        "price_unit": 490.0,
        "length_cm": 180.0,
        "width_cm": 305.0,
    })],
})
line = order.order_line[0]
assert abs(line.area_sqm - 5.49) < 0.01, f"area={line.area_sqm}"
assert abs(line.price_subtotal - 64562.40) < 0.01, f"line subtotal={line.price_subtotal}"
assert abs(order.amount_untaxed - 64562.40) < 0.01, f"order untaxed={order.amount_untaxed}"

order.action_confirm()
invoice = order._create_invoices()
inv_line = invoice.invoice_line_ids.filtered(lambda l: l.display_type == "product")
assert abs(inv_line.price_subtotal - 64562.40) < 0.01, f"invoice line={inv_line.price_subtotal}"
assert abs(invoice.amount_untaxed - 64562.40) < 0.01, f"invoice untaxed={invoice.amount_untaxed}"

fallback = env["sale.order"].create({
    "partner_id": partner.id,
    "order_line": [(0, 0, {
        "product_id": Product.id,
        "product_uom_qty": 10,
        "price_unit": 100.0,
    })],
})
assert abs(fallback.order_line[0].price_subtotal - 1000.0) < 0.01

print("UAT PASSED: client scenario 64562.40 + fallback + panel + sync")
