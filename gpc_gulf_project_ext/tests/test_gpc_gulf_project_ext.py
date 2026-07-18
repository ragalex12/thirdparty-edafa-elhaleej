# Copyright 2026 GPC
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestGpcGulfProjectExt(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create({
            "name": "Gulf Test Product",
            "type": "service",
            "list_price": 490.0,
        })
        cls.partner = cls.env["res.partner"].create({"name": "Gulf Test Customer"})
        cls.project = cls.env["project.project"].create({
            "name": "Gulf Test Project",
            "description": "<p>Test <strong>description</strong></p>",
            "contract_amount": 591706.80,
            "privacy_visibility": "followers",
        })

    def _create_collaborator_user(self, name, login):
        user = self.env["res.users"].create({
            "name": name,
            "login": login,
            "group_ids": [
                (6, 0, [
                    self.env.ref("base.group_user").id,
                    self.env.ref("project.group_project_user").id,
                ]),
            ],
        })
        self.project.message_subscribe(partner_ids=user.partner_id.ids)
        return user

    def test_contract_amount_sync(self):
        self.assertEqual(self.project.project_valuebvat, 591706.80)
        self.project.write({"project_valuebvat": 100000.0})
        self.assertEqual(self.project.contract_amount, 100000.0)

    def test_area_line_total_client_scenario(self):
        order = self.env["sale.order"].create({
            "partner_id": self.partner.id,
            "order_line": [(0, 0, {
                "product_id": self.product.id,
                "product_uom_qty": 24,
                "price_unit": 490.0,
                "length_cm": 180.0,
                "width_cm": 305.0,
            })],
        })
        line = order.order_line[0]
        self.assertAlmostEqual(line.area_sqm, 5.49, places=2)
        self.assertAlmostEqual(line.price_subtotal, 64562.40, places=2)
        self.assertAlmostEqual(order.amount_untaxed, 64562.40, places=2)

    def test_area_fallback_standard_pricing(self):
        order = self.env["sale.order"].create({
            "partner_id": self.partner.id,
            "order_line": [(0, 0, {
                "product_id": self.product.id,
                "product_uom_qty": 10,
                "price_unit": 100.0,
            })],
        })
        line = order.order_line[0]
        self.assertEqual(line.area_sqm, 1.0)
        self.assertAlmostEqual(line.price_subtotal, 1000.0, places=2)

    def test_invoice_preserves_dimension_totals(self):
        order = self.env["sale.order"].create({
            "partner_id": self.partner.id,
            "order_line": [(0, 0, {
                "product_id": self.product.id,
                "product_uom_qty": 24,
                "price_unit": 490.0,
                "length_cm": 180.0,
                "width_cm": 305.0,
            })],
        })
        order.action_confirm()
        invoice = order._create_invoices()
        inv_line = invoice.invoice_line_ids.filtered(lambda l: l.display_type == "product")
        self.assertAlmostEqual(inv_line.area_sqm, 5.49, places=2)
        self.assertAlmostEqual(inv_line.price_subtotal, 64562.40, places=2)
        self.assertAlmostEqual(invoice.amount_untaxed, 64562.40, places=2)

    def test_panel_data_includes_description_and_contract(self):
        panel = self.project.get_panel_data()
        self.assertTrue(panel.get("show_project_details"))
        self.assertIn("description", panel["description"])
        self.assertTrue(panel.get("show_contract_amount"))
        self.assertAlmostEqual(panel["contract_amount"], 591706.80, places=2)

    def test_panel_data_hides_contract_for_project_user(self):
        project_user = self._create_collaborator_user(
            "Gulf Project User",
            "gulf_project_user_test",
        )
        panel = self.project.with_user(project_user).get_panel_data()
        self.assertTrue(panel.get("show_project_details"))
        self.assertIn("description", panel["description"])
        self.assertFalse(panel.get("show_contract_amount"))
        self.assertNotIn("contract_amount", panel)

    def test_budget_fields_hidden_from_project_user(self):
        project_user = self._create_collaborator_user(
            "Gulf Project User Budget",
            "gulf_project_user_budget_test",
        )
        project = self.project.with_user(project_user)
        for field_name in ("contract_amount", "project_valuebvat", "project_valueavat"):
            with self.assertRaises(AccessError, msg=field_name):
                _ = project[field_name]
