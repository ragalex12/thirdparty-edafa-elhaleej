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

        # --- Accounts (TestStockValuationCommon in Odoo 19 does not set these up) ---
        cls.account_expense = cls.env["account.account"].search(
            [
                ("company_ids", "in", cls.company.ids),
                ("account_type", "=", "expense"),
            ],
            limit=1,
        )
        if not cls.account_expense:
            cls.account_expense = cls.env["account.account"].create(
                {
                    "name": "GPC Test Expense",
                    "code": "GPCEXP",
                    "account_type": "expense",
                    "company_ids": [Command.set(cls.company.ids)],
                }
            )
        cls.account_income = cls.env["account.account"].search(
            [
                ("company_ids", "in", cls.company.ids),
                ("account_type", "=", "income"),
            ],
            limit=1,
        )
        if not cls.account_income:
            cls.account_income = cls.env["account.account"].create(
                {
                    "name": "GPC Test Income",
                    "code": "GPCINC",
                    "account_type": "income",
                    "company_ids": [Command.set(cls.company.ids)],
                }
            )

        # --- Product category with standard costing + automatic real-time valuation ---
        cls.category_standard_auto = cls.env["product.category"].create(
            {
                "name": "GPC Standard Auto",
                "property_valuation": "real_time",
                "property_cost_method": "standard",
            }
        )

        # --- Common product creation values (reused across tests) ---
        # uom_po_id lives on product.template and cannot be set on product.product directly.
        cls.product_common_vals = {
            "is_storable": True,
            "uom_id": cls.uom_id.id,
        }

        # --- Default storable product used in most helpers ---
        cls.product_standard_auto = cls.env["product.product"].create(
            {
                **cls.product_common_vals,
                "name": "GPC Standard Auto Product",
                "categ_id": cls.category_standard_auto.id,
                "standard_price": 5.0,
            }
        )

        # --- Enable GPC flow + configure debit account on company ---
        cls.picking_type_out.gpc_project_issue_enabled = True
        cls.company.write(
            {
                "gpc_project_issue_debit_account_id": cls.account_expense.id,
            }
        )

    def _gpc_create_analytic_account(self, name="GPC Test Analytic"):
        # account.analytic.plan has no company_id in Odoo 19 — search without it.
        plan = self.env["account.analytic.plan"].search([], limit=1)
        if not plan:
            plan = self.env["account.analytic.plan"].create({"name": "GPC Test Plan"})
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
            # In Odoo 19, stock.move.name is computed from product — omit it.
            self.env["stock.move"].create(
                {
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

    def test_posting_preserves_analytic_distribution(self):
        """Analytic distribution must survive posting (not wiped by account locking)."""
        picking = self._gpc_done_delivery_with_gpc_fields()
        move = picking._gpc_project_issue_create_draft_journal_entry()
        debit_lines = move.line_ids.filtered(lambda l: l.debit > 0)
        aa = picking.gpc_issue_analytic_account_id
        self.assertIn(str(aa.id), debit_lines.analytic_distribution or {})
        picking.action_post_gpc_project_issue_entry()
        self.assertEqual(move.state, "posted")
        debit_lines_posted = move.line_ids.filtered(lambda l: l.debit > 0)
        self.assertIn(str(aa.id), debit_lines_posted.analytic_distribution or {})

    def test_post_entry_no_linked_move_raises(self):
        """action_post_gpc_project_issue_entry must raise when no JE is linked."""
        picking = self._gpc_done_delivery_with_gpc_fields()
        self.assertFalse(picking.gpc_issue_move_id)
        with self.assertRaises(UserError):
            picking.action_post_gpc_project_issue_entry()

    def test_post_entry_already_posted_raises(self):
        """Posting a non-draft entry must raise UserError."""
        picking = self._gpc_done_delivery_with_gpc_fields()
        move = picking._gpc_project_issue_create_draft_journal_entry()
        picking.action_post_gpc_project_issue_entry()
        self.assertEqual(move.state, "posted")
        with self.assertRaises(UserError):
            picking.action_post_gpc_project_issue_entry()

    def test_wizard_creates_draft_je_and_opens_it(self):
        """Wizard action must create a draft JE and return an act_window pointing to it."""
        picking = self._gpc_done_delivery_with_gpc_fields()
        self.assertFalse(picking.gpc_issue_move_id)
        wizard = self.env["gpc.project.issue.wizard"].create(
            {"picking_id": picking.id}
        )
        action = wizard.action_create_draft_journal_entry()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "account.move")
        self.assertTrue(action.get("res_id"))
        move = self.env["account.move"].browse(action["res_id"])
        self.assertEqual(move.state, "draft")
        self.assertEqual(picking.gpc_issue_move_id, move)

    def test_wizard_default_get_picking_from_context(self):
        """Wizard must pre-populate picking_id from context key default_picking_id."""
        picking = self._gpc_done_delivery_with_gpc_fields()
        wizard = (
            self.env["gpc.project.issue.wizard"]
            .with_context(default_picking_id=picking.id)
            .create({})
        )
        self.assertEqual(wizard.picking_id, picking)

    def test_open_wizard_action_returns_correct_shape(self):
        """action_open_gpc_project_issue_wizard must return a new-target act_window."""
        picking = self._gpc_done_delivery_with_gpc_fields()
        action = picking.action_open_gpc_project_issue_wizard()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "gpc.project.issue.wizard")
        self.assertEqual(action["target"], "new")
        self.assertEqual(action["context"].get("default_picking_id"), picking.id)

    def test_narration_contains_html_line_breaks(self):
        """Draft JE narration must contain HTML line breaks (not raw \\n).

        Odoo's HTML field sanitizer converts <br/> to <br> on storage,
        so we assert for <br> and the absence of raw newlines.
        """
        picking = self._gpc_done_delivery_with_gpc_fields()
        move = picking._gpc_project_issue_create_draft_journal_entry()
        narration = str(move.narration or "")
        self.assertIn("<br", narration)
        self.assertNotIn("\n", narration)

    def test_gpc_issue_move_state_stored_and_updated(self):
        """gpc_issue_move_state is stored; it must reflect JE state changes."""
        picking = self._gpc_done_delivery_with_gpc_fields()
        self.assertFalse(picking.gpc_issue_move_state)
        picking._gpc_project_issue_create_draft_journal_entry()
        # stored field must show 'draft' without re-browse
        picking.invalidate_recordset(["gpc_issue_move_state"])
        self.assertEqual(picking.gpc_issue_move_state, "draft")
        picking.action_post_gpc_project_issue_entry()
        picking.invalidate_recordset(["gpc_issue_move_state"])
        self.assertEqual(picking.gpc_issue_move_state, "posted")

    def test_je_has_check_company_on_picking_backlink(self):
        """account.move.gpc_issue_picking_id must carry check_company metadata."""
        field = self.env["account.move"]._fields.get("gpc_issue_picking_id")
        self.assertIsNotNone(field)
        self.assertTrue(
            getattr(field, "check_company", False),
            "gpc_issue_picking_id must have check_company=True",
        )


@tagged("post_install", "-at_install")
class TestGpcAnalyticDistribution(TestGpcStockProjectIssuePhase1):
    """Focused tests for analytic distribution on GPC project issue journal entries.

    Inherits the full Phase 1 setup so all fixtures (product, company, accounts) are
    already available without duplication.
    """

    # ── helpers ──────────────────────────────────────────────────────────────

    def _get_debit_line(self, move):
        return move.line_ids.filtered(lambda l: l.debit > 0)

    def _get_credit_line(self, move):
        return move.line_ids.filtered(lambda l: l.credit > 0)

    # ── 1. Distribution shape & correctness ──────────────────────────────────

    def test_analytic_debit_line_has_exactly_100_percent(self):
        """The debit (project/WIP) line must carry 100 % allocation — not 50, not 0."""
        picking = self._gpc_done_delivery_with_gpc_fields()
        move = picking._gpc_project_issue_create_draft_journal_entry()
        aa = picking.gpc_issue_analytic_account_id
        dist = self._get_debit_line(move).analytic_distribution or {}
        self.assertAlmostEqual(
            dist.get(str(aa.id), 0.0),
            100.0,
            places=2,
            msg="Debit line must allocate exactly 100 % to the analytic account",
        )

    def test_analytic_credit_line_has_no_distribution(self):
        """The credit (stock valuation) line must NOT carry any analytic distribution.

        Inventory accounts should not appear in analytic reports.
        """
        picking = self._gpc_done_delivery_with_gpc_fields()
        move = picking._gpc_project_issue_create_draft_journal_entry()
        credit_dist = self._get_credit_line(move).analytic_distribution
        self.assertFalse(
            credit_dist,
            "Credit (stock valuation) line must have no analytic distribution",
        )

    def test_analytic_distribution_key_is_string_account_id(self):
        """analytic_distribution keys must be string IDs (Odoo 19 JSON format)."""
        picking = self._gpc_done_delivery_with_gpc_fields()
        move = picking._gpc_project_issue_create_draft_journal_entry()
        aa = picking.gpc_issue_analytic_account_id
        dist = self._get_debit_line(move).analytic_distribution or {}
        self.assertIn(
            str(aa.id),
            dist,
            "analytic_distribution key must be the string ID of the analytic account",
        )
        # Ensure it is not stored as an integer key (would silently break Odoo lookup)
        self.assertNotIn(
            aa.id,
            dist,
            "analytic_distribution key must not be an integer",
        )

    def test_analytic_distribution_total_sums_to_100(self):
        """Sum of all distribution percentages on the debit line must equal 100.

        Odoo enforces this on posting; verifying it on draft catches issues early.
        """
        picking = self._gpc_done_delivery_with_gpc_fields()
        move = picking._gpc_project_issue_create_draft_journal_entry()
        dist = self._get_debit_line(move).analytic_distribution or {}
        total = sum(dist.values())
        self.assertAlmostEqual(
            total,
            100.0,
            places=2,
            msg="Total analytic distribution on debit line must sum to 100 %%",
        )

    def test_analytic_only_one_account_in_distribution(self):
        """Phase 1 creates a single-account distribution — no splits."""
        picking = self._gpc_done_delivery_with_gpc_fields()
        move = picking._gpc_project_issue_create_draft_journal_entry()
        dist = self._get_debit_line(move).analytic_distribution or {}
        self.assertEqual(
            len(dist),
            1,
            "Phase 1 must produce exactly one analytic account in the distribution",
        )

    # ── 2. Account identity & company ────────────────────────────────────────

    def test_analytic_account_matches_picking_field(self):
        """The analytic account in the JE must be exactly the one set on the picking."""
        aa = self._gpc_create_analytic_account(name="Specific Analytic AA")
        picking = self._gpc_done_delivery_with_gpc_fields()
        picking.gpc_issue_analytic_account_id = aa
        move = picking._gpc_project_issue_create_draft_journal_entry()
        dist = self._get_debit_line(move).analytic_distribution or {}
        self.assertIn(
            str(aa.id),
            dist,
            "JE debit line must reference the analytic account set on the picking",
        )

    def test_analytic_different_accounts_produce_different_distributions(self):
        """Two pickings with different analytic accounts must produce different JE distributions."""
        aa1 = self._gpc_create_analytic_account(name="Analytic AA1")
        aa2 = self._gpc_create_analytic_account(name="Analytic AA2")

        picking1 = self._gpc_done_delivery_with_gpc_fields()
        picking1.gpc_issue_analytic_account_id = aa1
        move1 = picking1._gpc_project_issue_create_draft_journal_entry()

        picking2 = self._gpc_done_delivery_with_gpc_fields()
        picking2.gpc_issue_analytic_account_id = aa2
        move2 = picking2._gpc_project_issue_create_draft_journal_entry()

        dist1 = self._get_debit_line(move1).analytic_distribution or {}
        dist2 = self._get_debit_line(move2).analytic_distribution or {}

        self.assertIn(str(aa1.id), dist1)
        self.assertNotIn(str(aa2.id), dist1)
        self.assertIn(str(aa2.id), dist2)
        self.assertNotIn(str(aa1.id), dist2)

    def test_analytic_account_belongs_to_same_company(self):
        """The analytic account on the picking must belong to the same company (check_company)."""
        field = self.env["stock.picking"]._fields.get("gpc_issue_analytic_account_id")
        self.assertIsNotNone(field)
        self.assertTrue(
            getattr(field, "check_company", False),
            "gpc_issue_analytic_account_id must have check_company=True",
        )

    # ── 3. Posting behaviour ─────────────────────────────────────────────────

    def test_analytic_distribution_intact_after_posting(self):
        """Posting the JE must not change or remove the analytic distribution."""
        picking = self._gpc_done_delivery_with_gpc_fields()
        move = picking._gpc_project_issue_create_draft_journal_entry()
        aa = picking.gpc_issue_analytic_account_id
        dist_before = dict(self._get_debit_line(move).analytic_distribution or {})

        picking.action_post_gpc_project_issue_entry()

        dist_after = dict(self._get_debit_line(move).analytic_distribution or {})
        self.assertEqual(
            dist_before,
            dist_after,
            "analytic_distribution must be identical before and after posting",
        )

    def test_analytic_allows_posting_without_validation_error(self):
        """Odoo validates that analytic distribution sums to 100 % on posting.

        A correct 100 % distribution must allow posting without raising.
        """
        picking = self._gpc_done_delivery_with_gpc_fields()
        picking._gpc_project_issue_create_draft_journal_entry()
        # Must not raise any ValidationError or UserError
        picking.action_post_gpc_project_issue_entry()
        self.assertEqual(picking.gpc_issue_move_id.state, "posted")

    # ── 4. Amount alignment ──────────────────────────────────────────────────

    def test_analytic_debit_amount_matches_inventory_cost(self):
        """The debit line amount (= analytic amount) must equal the valued inventory cost."""
        picking = self._gpc_done_delivery_with_gpc_fields(out_qty=4)
        basis = picking._gpc_project_issue_prepare_accounting_basis()
        move = picking._gpc_project_issue_create_draft_journal_entry()
        debit_line = self._get_debit_line(move)
        self.assertAlmostEqual(
            debit_line.debit,
            basis["total_value"],
            places=2,
            msg="Analytic debit amount must equal the total valued inventory cost",
        )

    def test_analytic_amount_scales_with_quantity(self):
        """Analytic amount must scale linearly with the delivered quantity (standard cost)."""
        # out_qty=2 → cost should be 2 × 5.00 = 10.00
        picking_2 = self._gpc_done_delivery_with_gpc_fields(out_qty=2)
        move_2 = picking_2._gpc_project_issue_create_draft_journal_entry()
        amount_2 = self._get_debit_line(move_2).debit

        # out_qty=4 → cost should be 4 × 5.00 = 20.00
        picking_4 = self._gpc_done_delivery_with_gpc_fields(out_qty=4)
        move_4 = picking_4._gpc_project_issue_create_draft_journal_entry()
        amount_4 = self._get_debit_line(move_4).debit

        self.assertAlmostEqual(
            amount_4,
            amount_2 * 2,
            places=2,
            msg="Doubling the quantity must double the analytic debit amount",
        )
