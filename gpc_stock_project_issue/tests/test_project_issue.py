# Copyright 2026
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import Command, fields
from odoo.exceptions import UserError
from odoo.tests.common import tagged

from odoo.addons.stock_account.tests.common import TestStockValuationCommon


@tagged("post_install", "-at_install")
class TestGpcStockProjectIssuePhase1(TestStockValuationCommon):
    """Phase 1 automated tests for gpc_stock_project_issue."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.picking_type_out.gpc_project_issue_enabled = True
        cls.company.write(
            {
                "gpc_project_issue_debit_account_id": cls.account_expense.id,
            }
        )

    def _gpc_create_analytic_account(self, name="GPC Test Analytic"):
        plan = self.env["account.analytic.plan"].search(
            [("company_id", "in", [False, self.company.id])],
            limit=1,
        )
        if not plan:
            plan = self.env["account.analytic.plan"].create(
                {
                    "name": "GPC Test Plan",
                    "company_id": self.company.id,
                }
            )
        return self.env["account.analytic.account"].create(
            {
                "name": name,
                "company_id": self.company.id,
                "plan_id": plan.id,
            }
        )

    def _gpc_create_project(self, name="GPC Test Project"):
        return self.env["project.project"].create(
            {
                "name": name,
                "company_id": self.company.id,
            }
        )

    def _gpc_minimal_balanced_move(self):
        """Minimal draft journal entry (not linked to a picking)."""
        return self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": self.company.account_stock_journal_id.id,
                "company_id": self.company.id,
                "line_ids": [
                    Command.create(
                        {
                            "account_id": self.account_expense.id,
                            "name": "t",
                            "debit": 1.0,
                            "credit": 0.0,
                        }
                    ),
                    Command.create(
                        {
                            "account_id": self.account_income.id,
                            "name": "t",
                            "debit": 0.0,
                            "credit": 1.0,
                        }
                    ),
                ],
            }
        )

    def _gpc_done_delivery_with_gpc_fields(self, product=None, out_qty=2):
        """Receipt stock, deliver, set project + analytic on the outgoing picking."""
        product = product or self.product_standard_auto
        self._make_in_move(product, 10, unit_cost=5.0, create_picking=True)
        out = self._make_out_move(product, out_qty, create_picking=True)
        picking = out.picking_id
        picking.write(
            {
                "gpc_issue_project_id": self._gpc_create_project().id,
                "gpc_issue_analytic_account_id": self._gpc_create_analytic_account().id,
            }
        )
        return picking

    def test_models_registered(self):
        self.env["gpc.project.issue.wizard"]
        self.assertTrue(self.env["stock.picking"]._fields.get("gpc_issue_project_id"))
        self.assertTrue(self.env["stock.picking"]._fields.get("gpc_issue_move_id"))
        self.assertTrue(self.env["account.move"]._fields.get("gpc_issue_picking_id"))
        self.assertTrue(self.env["stock.picking.type"]._fields.get("gpc_project_issue_enabled"))

    def test_picking_type_gpc_flag_exists_and_respected(self):
        """Operation type flag gates eligibility when disabled."""
        self.assertIn("gpc_project_issue_enabled", self.env["stock.picking.type"]._fields)
        picking = self._gpc_done_delivery_with_gpc_fields()
        self.picking_type_out.gpc_project_issue_enabled = False
        with self.assertRaises(UserError):
            picking._gpc_project_issue_check_eligibility()
        self.picking_type_out.gpc_project_issue_enabled = True
        picking._gpc_project_issue_check_eligibility()

    def test_eligibility_not_done(self):
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.picking_type_out.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "gpc_issue_project_id": self._gpc_create_project().id,
                "gpc_issue_analytic_account_id": self._gpc_create_analytic_account().id,
            }
        )
        self.assertNotEqual(picking.state, "done")
        with self.assertRaises(UserError):
            picking._gpc_project_issue_check_eligibility()

    def test_eligibility_operation_type_not_enabled(self):
        self.picking_type_out.gpc_project_issue_enabled = False
        try:
            picking = self._gpc_done_delivery_with_gpc_fields()
            with self.assertRaises(UserError):
                picking._gpc_project_issue_check_eligibility()
        finally:
            self.picking_type_out.gpc_project_issue_enabled = True

    def test_eligibility_missing_project(self):
        picking = self._gpc_done_delivery_with_gpc_fields()
        picking.gpc_issue_project_id = False
        with self.assertRaises(UserError):
            picking._gpc_project_issue_check_eligibility()

    def test_eligibility_missing_analytic(self):
        picking = self._gpc_done_delivery_with_gpc_fields()
        picking.gpc_issue_analytic_account_id = False
        with self.assertRaises(UserError):
            picking._gpc_project_issue_check_eligibility()

    def test_eligibility_move_already_linked(self):
        picking = self._gpc_done_delivery_with_gpc_fields()
        picking.gpc_issue_move_id = self._gpc_minimal_balanced_move()
        with self.assertRaises(UserError):
            picking._gpc_project_issue_check_eligibility()

    def test_basis_incoming_picking_has_no_out_moves(self):
        """Receipt (incoming) moves are not included; basis preparation fails."""
        self.picking_type_in.gpc_project_issue_enabled = True
        try:
            self._make_in_move(self.product_standard_auto, 5, unit_cost=5.0, create_picking=True)
            in_move = self.env["stock.move"].search(
                [
                    ("product_id", "=", self.product_standard_auto.id),
                    ("picking_id.picking_type_id", "=", self.picking_type_in.id),
                ],
                order="id desc",
                limit=1,
            )
            picking = in_move.picking_id
            picking.write(
                {
                    "gpc_issue_project_id": self._gpc_create_project().id,
                    "gpc_issue_analytic_account_id": self._gpc_create_analytic_account().id,
                }
            )
            self.assertEqual(picking.state, "done")
            included = picking._gpc_project_issue_get_included_moves()
            self.assertFalse(included)
            with self.assertRaises(UserError):
                picking._gpc_project_issue_prepare_accounting_basis()
        finally:
            self.picking_type_in.gpc_project_issue_enabled = False

    def test_basis_zero_valued_amount_blocked(self):
        product_zero = self.env["product.product"].create(
            {
                **self.product_common_vals,
                "name": "GPC Zero Standard",
                "categ_id": self.category_standard_auto.id,
                "standard_price": 0.0,
            }
        )
        self._make_in_move(product_zero, 5, unit_cost=0.0, create_picking=True)
        out = self._make_out_move(product_zero, 1, create_picking=True)
        picking = out.picking_id
        picking.write(
            {
                "gpc_issue_project_id": self._gpc_create_project().id,
                "gpc_issue_analytic_account_id": self._gpc_create_analytic_account().id,
            }
        )
        with self.assertRaises(UserError) as cm:
            picking._gpc_project_issue_prepare_accounting_basis()
        self.assertIn("not positive", str(cm.exception).lower())

    def test_basis_mixed_stock_valuation_accounts_blocked(self):
        account_val_b = self.env["account.account"].create(
            {
                "name": "GPC Stock Val B",
                "code": "GPCSTVB",
                "account_type": "asset_current",
                "company_ids": [fields.Command.set(self.company.ids)],
            }
        )
        category_b = self.env["product.category"].create(
            {
                "name": "GPC Cat B",
                "property_valuation": "real_time",
                "property_cost_method": "standard",
                "property_stock_valuation_account_id": account_val_b.id,
            }
        )
        product_b = self.env["product.product"].create(
            {
                **self.product_common_vals,
                "name": "GPC Product Val B",
                "categ_id": category_b.id,
                "standard_price": 10.0,
            }
        )
        self._make_in_move(self.product_standard_auto, 10, unit_cost=5.0, create_picking=True)
        self._make_in_move(product_b, 10, unit_cost=5.0, create_picking=True)
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.picking_type_out.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "company_id": self.company.id,
            }
        )
        for product in (self.product_standard_auto, product_b):
            self.env["stock.move"].create(
                {
                    "name": product.name,
                    "product_id": product.id,
                    "product_uom_qty": 1,
                    "product_uom": product.uom_id.id,
                    "location_id": self.stock_location.id,
                    "location_dest_id": self.customer_location.id,
                    "picking_id": picking.id,
                    "picking_type_id": self.picking_type_out.id,
                }
            )
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty
            move.picked = True
        picking.button_validate()
        picking.write(
            {
                "gpc_issue_project_id": self._gpc_create_project().id,
                "gpc_issue_analytic_account_id": self._gpc_create_analytic_account().id,
            }
        )
        with self.assertRaises(UserError) as cm:
            picking._gpc_project_issue_prepare_accounting_basis()
        err = str(cm.exception).lower()
        self.assertTrue("same stock valuation account" in err or "mix" in err)

    def test_basis_included_moves_match_outgoing_done(self):
        picking = self._gpc_done_delivery_with_gpc_fields(out_qty=3)
        basis = picking._gpc_project_issue_prepare_accounting_basis()
        included = basis["included_moves"]
        self.assertEqual(len(included), 1)
        self.assertTrue(all(m.is_out for m in included))
        self.assertTrue(all(m.state == "done" for m in included))
        self.assertEqual(included.product_id, self.product_standard_auto)

    def test_draft_je_generation_and_links(self):
        picking = self._gpc_done_delivery_with_gpc_fields()
        basis = picking._gpc_project_issue_prepare_accounting_basis()
        move = picking._gpc_project_issue_create_draft_journal_entry()
        self.assertEqual(move.state, "draft")
        self.assertEqual(move, picking.gpc_issue_move_id)
        self.assertEqual(move.gpc_issue_picking_id, picking)
        debit_lines = move.line_ids.filtered(lambda l: l.debit > 0)
        credit_lines = move.line_ids.filtered(lambda l: l.credit > 0)
        self.assertEqual(len(debit_lines), 1)
        self.assertEqual(len(credit_lines), 1)
        self.assertEqual(debit_lines.account_id, self.company.gpc_project_issue_debit_account_id)
        self.assertEqual(credit_lines.account_id, basis["stock_valuation_account_id"])
        self.assertAlmostEqual(debit_lines.debit, basis["total_value"], places=2)
        self.assertAlmostEqual(credit_lines.credit, basis["total_value"], places=2)
        aa = picking.gpc_issue_analytic_account_id
        dist = debit_lines.analytic_distribution or {}
        self.assertIn(str(aa.id), dist)

    def test_posting_and_picking_state(self):
        picking = self._gpc_done_delivery_with_gpc_fields()
        move = picking._gpc_project_issue_create_draft_journal_entry()
        self.assertEqual(picking.gpc_issue_move_state, "draft")
        picking.action_post_gpc_project_issue_entry()
        self.assertEqual(move.state, "posted")
        self.assertEqual(picking.gpc_issue_move_state, "posted")
