# Copyright 2026
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).
"""Cross-module analytic-line tests for gpc_stock_project_issue.

Covers two integration points:

1. ``gpc_account_move_line_reference_ext``
   Adds ``line_reference``, ``line_reference_number``, ``line_tax_number`` to
   ``account.move.line``.  GPC project issue JEs are ``move_type='entry'`` so
   every line carries those fields.  Tests verify the fields exist, are writable,
   persist through posting, and that the move_type gate is correct.

2. ``gpc_hr_timesheet_labor_accrual``  (skipped when module is not installed)
   Creates labor-accrual JEs with the same ``{str(id): 100.0}`` analytic format.
   Tests verify that both modules produce compatible analytic_distribution shapes
   and that analytic lines from both sources can be queried together.
"""

from odoo.tests.common import tagged

from odoo.addons.gpc_stock_project_issue.tests.test_project_issue import (
    TestGpcStockProjectIssuePhase1,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────────────────────

def _module_installed(env, technical_name):
    return bool(
        env["ir.module.module"].search(
            [("name", "=", technical_name), ("state", "=", "installed")],
            limit=1,
        )
    )


# ─────────────────────────────────────────────────────────────────────────────
# 1.  gpc_account_move_line_reference_ext × gpc_stock_project_issue
# ─────────────────────────────────────────────────────────────────────────────

@tagged("post_install", "-at_install")
class TestGpcStockIssueReferenceFields(TestGpcStockProjectIssuePhase1):
    """Journal-item reference fields on GPC project issue entries.

    Requires gpc_account_move_line_reference_ext to be installed.
    All tests are skipped when the module is absent.
    """

    def setUp(self):
        super().setUp()
        if not _module_installed(self.env, "gpc_account_move_line_reference_ext"):
            self.skipTest(
                "gpc_account_move_line_reference_ext is not installed — skipping reference-field tests."
            )

    # ── field presence ────────────────────────────────────────────────────────

    def test_reference_fields_exist_on_move_line(self):
        """line_reference, line_reference_number, line_tax_number must be ORM fields."""
        fields_map = self.env["account.move.line"]._fields
        for fname in ("line_reference", "line_reference_number", "line_tax_number"):
            self.assertIn(
                fname,
                fields_map,
                "account.move.line must have field %r (gpc_account_move_line_reference_ext)" % fname,
            )

    def test_reference_fields_are_stored(self):
        """All three reference fields must be stored (store=True)."""
        fields_map = self.env["account.move.line"]._fields
        for fname in ("line_reference", "line_reference_number", "line_tax_number"):
            field = fields_map.get(fname)
            self.assertIsNotNone(field)
            self.assertTrue(
                field.store,
                "Field %r must be store=True to support filtering and reporting" % fname,
            )

    # ── writable on GPC project issue lines ──────────────────────────────────

    def test_line_reference_writable_on_debit_line(self):
        """line_reference can be set on the debit (project/WIP) journal item."""
        picking = self._gpc_done_delivery_with_gpc_fields()
        move = picking._gpc_project_issue_create_draft_journal_entry()
        debit_line = move.line_ids.filtered(lambda l: l.debit > 0)
        debit_line.line_reference = "GPC-PROJ-001"
        self.assertEqual(debit_line.line_reference, "GPC-PROJ-001")

    def test_line_reference_writable_on_credit_line(self):
        """line_reference can be set on the credit (stock valuation) journal item."""
        picking = self._gpc_done_delivery_with_gpc_fields()
        move = picking._gpc_project_issue_create_draft_journal_entry()
        credit_line = move.line_ids.filtered(lambda l: l.credit > 0)
        credit_line.line_reference = "INV-CREDIT-001"
        self.assertEqual(credit_line.line_reference, "INV-CREDIT-001")

    def test_all_reference_fields_writable_on_debit_line(self):
        """All three reference fields can be set simultaneously on a debit line."""
        picking = self._gpc_done_delivery_with_gpc_fields()
        move = picking._gpc_project_issue_create_draft_journal_entry()
        debit_line = move.line_ids.filtered(lambda l: l.debit > 0)
        debit_line.write(
            {
                "line_reference": "REF-001",
                "line_reference_number": "REFNUM-2026",
                "line_tax_number": "TAX-123456",
            }
        )
        self.assertEqual(debit_line.line_reference, "REF-001")
        self.assertEqual(debit_line.line_reference_number, "REFNUM-2026")
        self.assertEqual(debit_line.line_tax_number, "TAX-123456")

    # ── persistence through posting ───────────────────────────────────────────

    def test_line_reference_persists_after_posting(self):
        """line_reference set on draft entry must survive journal posting unchanged."""
        picking = self._gpc_done_delivery_with_gpc_fields()
        move = picking._gpc_project_issue_create_draft_journal_entry()
        debit_line = move.line_ids.filtered(lambda l: l.debit > 0)
        debit_line.line_reference = "POST-PERSIST-TEST"

        picking.action_post_gpc_project_issue_entry()
        self.assertEqual(move.state, "posted")

        debit_line.invalidate_recordset(["line_reference"])
        self.assertEqual(
            debit_line.line_reference,
            "POST-PERSIST-TEST",
            "line_reference must not be cleared or modified by posting",
        )

    def test_all_reference_fields_persist_after_posting(self):
        """All three reference fields survive posting."""
        picking = self._gpc_done_delivery_with_gpc_fields()
        move = picking._gpc_project_issue_create_draft_journal_entry()
        debit_line = move.line_ids.filtered(lambda l: l.debit > 0)
        debit_line.write(
            {
                "line_reference": "R1",
                "line_reference_number": "RN1",
                "line_tax_number": "TN1",
            }
        )
        picking.action_post_gpc_project_issue_entry()
        debit_line.invalidate_recordset(
            ["line_reference", "line_reference_number", "line_tax_number"]
        )
        self.assertEqual(debit_line.line_reference, "R1")
        self.assertEqual(debit_line.line_reference_number, "RN1")
        self.assertEqual(debit_line.line_tax_number, "TN1")

    # ── move_type gate ────────────────────────────────────────────────────────

    def test_gpc_project_issue_je_has_move_type_entry(self):
        """GPC project issue JEs are move_type='entry' so the reference-fields view is active."""
        picking = self._gpc_done_delivery_with_gpc_fields()
        move = picking._gpc_project_issue_create_draft_journal_entry()
        self.assertEqual(
            move.move_type,
            "entry",
            "GPC project issue JEs must be move_type='entry' for reference fields to appear in the form",
        )

    # ── analytic + reference coexistence ─────────────────────────────────────

    def test_analytic_and_reference_coexist_on_debit_line(self):
        """Analytic distribution and line_reference can both be set on the same journal item."""
        picking = self._gpc_done_delivery_with_gpc_fields()
        move = picking._gpc_project_issue_create_draft_journal_entry()
        debit_line = move.line_ids.filtered(lambda l: l.debit > 0)

        aa = picking.gpc_issue_analytic_account_id
        self.assertIn(str(aa.id), debit_line.analytic_distribution or {})

        debit_line.line_reference = "ANALYTIC+REF"
        self.assertEqual(debit_line.line_reference, "ANALYTIC+REF")
        # Analytic must be untouched
        self.assertIn(str(aa.id), debit_line.analytic_distribution or {})

    def test_reference_field_searchable_across_gpc_je_lines(self):
        """line_reference is stored, so domain search on account.move.line works."""
        picking = self._gpc_done_delivery_with_gpc_fields()
        move = picking._gpc_project_issue_create_draft_journal_entry()
        debit_line = move.line_ids.filtered(lambda l: l.debit > 0)
        unique_ref = "SEARCH-GPC-%d" % debit_line.id
        debit_line.line_reference = unique_ref

        found = self.env["account.move.line"].search(
            [("line_reference", "=", unique_ref)]
        )
        self.assertEqual(len(found), 1)
        self.assertEqual(found, debit_line)


# ─────────────────────────────────────────────────────────────────────────────
# 2.  gpc_hr_timesheet_labor_accrual × gpc_stock_project_issue (analytic parity)
# ─────────────────────────────────────────────────────────────────────────────

@tagged("post_install", "-at_install")
class TestGpcAnalyticCrossModuleParity(TestGpcStockProjectIssuePhase1):
    """Verify that analytic distribution produced by gpc_stock_project_issue is
    structurally compatible with that produced by gpc_hr_timesheet_labor_accrual.

    All tests are skipped when gpc_hr_timesheet_labor_accrual is not installed.
    """

    def setUp(self):
        super().setUp()
        if not _module_installed(self.env, "gpc_hr_timesheet_labor_accrual"):
            self.skipTest(
                "gpc_hr_timesheet_labor_accrual is not installed — skipping cross-module analytic tests."
            )

    def _make_labor_batch_move(self, analytic_account):
        """Create a posted labor accrual JE for the given analytic account.

        Returns the posted account.move.
        """
        # Accounts
        debit_acc = self.env["account.account"].search(
            [("company_ids", "in", self.company.ids), ("account_type", "=", "expense")],
            limit=1,
        )
        credit_acc = self.env["account.account"].search(
            [
                ("company_ids", "in", self.company.ids),
                ("account_type", "=", "liability_current"),
            ],
            limit=1,
        )
        journal = self.env["account.journal"].search(
            [("company_id", "=", self.company.id), ("type", "=", "general")],
            limit=1,
        )
        if not debit_acc or not credit_acc or not journal:
            self.skipTest("Cannot find required accounts/journal for labor accrual setup.")

        self.company.write(
            {
                "labor_accrual_debit_account_id": debit_acc.id,
                "labor_accrual_credit_account_id": credit_acc.id,
                "labor_accrual_journal_id": journal.id,
            }
        )

        # Employee
        employee = self.env["hr.employee"].search(
            [("company_id", "=", self.company.id), ("hourly_cost", ">", 0)], limit=1
        )
        if not employee:
            self.skipTest("No employee with hourly_cost > 0 found for labor accrual test.")

        # Project linked to analytic account
        project = self.env["project.project"].create(
            {
                "name": "CrossModule Project",
                "company_id": self.company.id,
                "account_id": analytic_account.id,
            }
        )

        # Timesheet line
        ts_vals = {
            "name": "cross module ts",
            "company_id": self.company.id,
            "employee_id": employee.id,
            "project_id": project.id,
            "unit_amount": 2.0,
            "date": "2025-11-15",
            "account_id": analytic_account.id,
        }
        AAL = self.env["account.analytic.line"]
        if "validated" in AAL._fields:
            ts_vals["validated"] = True
        self.env["account.analytic.line"].create(ts_vals)

        # Batch
        import uuid
        period_key = "2025-11-%s" % uuid.uuid4().hex[:6]
        batch = self.env["labor.accrual.batch"].create(
            {
                "name": "CrossModule Batch",
                "company_id": self.company.id,
                "period_start": "2025-11-01",
                "period_end": "2025-11-30",
                "period_key": period_key,
                "state": "draft",
            }
        )
        batch.action_populate_lines()
        if not batch.line_ids:
            self.skipTest("Labor accrual batch produced no lines — check employee hourly_cost.")
        batch.action_generate_draft_move()
        batch.action_post_move()
        return batch.move_id

    # ── analytic distribution format parity ───────────────────────────────────

    def test_both_modules_use_same_analytic_distribution_format(self):
        """Both modules must produce {str(account_id): 100.0} on their debit lines."""
        aa = self._gpc_create_analytic_account(name="CrossMod Analytic")

        # Stock project issue JE
        picking = self._gpc_done_delivery_with_gpc_fields()
        picking.gpc_issue_analytic_account_id = aa
        stock_move = picking._gpc_project_issue_create_draft_journal_entry()
        stock_debit = stock_move.line_ids.filtered(lambda l: l.debit > 0)
        stock_dist = stock_debit.analytic_distribution or {}

        # Labor accrual JE
        labor_move = self._make_labor_batch_move(aa)
        labor_debit = labor_move.line_ids.filtered(lambda l: l.debit > 0)
        labor_dist = labor_debit.analytic_distribution or {}

        # Both must carry the same analytic account key
        self.assertIn(str(aa.id), stock_dist, "Stock issue debit must carry analytic account")
        self.assertIn(str(aa.id), labor_dist, "Labor accrual debit must carry analytic account")

        # Both must be 100 %
        self.assertAlmostEqual(stock_dist.get(str(aa.id), 0.0), 100.0, places=2)
        self.assertAlmostEqual(labor_dist.get(str(aa.id), 0.0), 100.0, places=2)

    def test_both_modules_credit_lines_have_no_analytic(self):
        """Credit lines from both modules must be free of analytic distribution."""
        aa = self._gpc_create_analytic_account(name="CrossMod Analytic Credit")

        picking = self._gpc_done_delivery_with_gpc_fields()
        picking.gpc_issue_analytic_account_id = aa
        stock_move = picking._gpc_project_issue_create_draft_journal_entry()
        stock_credit = stock_move.line_ids.filtered(lambda l: l.credit > 0)

        labor_move = self._make_labor_batch_move(aa)
        labor_credit = labor_move.line_ids.filtered(lambda l: l.credit > 0)

        self.assertFalse(
            stock_credit.analytic_distribution,
            "Stock issue credit line must have no analytic distribution",
        )
        self.assertFalse(
            labor_credit.analytic_distribution,
            "Labor accrual credit line must have no analytic distribution",
        )

    def test_analytic_lines_from_both_modules_searchable_by_account(self):
        """account.move.line search by analytic_distribution key finds lines from both modules."""
        aa = self._gpc_create_analytic_account(name="CrossMod Search Analytic")

        picking = self._gpc_done_delivery_with_gpc_fields()
        picking.gpc_issue_analytic_account_id = aa
        stock_move = picking._gpc_project_issue_create_draft_journal_entry()

        labor_move = self._make_labor_batch_move(aa)

        # Use Odoo's analytic_distribution domain syntax to find both debit lines
        key = str(aa.id)
        found = self.env["account.move.line"].search(
            [("analytic_distribution", "like", key)]
        )
        found_move_ids = found.mapped("move_id.id")
        self.assertIn(
            stock_move.id,
            found_move_ids,
            "Stock issue JE debit line must be findable by analytic account key",
        )
        self.assertIn(
            labor_move.id,
            found_move_ids,
            "Labor accrual JE debit line must be findable by analytic account key",
        )

    def test_total_analytic_debit_sums_both_modules(self):
        """Total debit carrying a given analytic = stock issue amount + labor accrual amount."""
        aa = self._gpc_create_analytic_account(name="CrossMod Sum Analytic")

        picking = self._gpc_done_delivery_with_gpc_fields(out_qty=2)
        picking.gpc_issue_analytic_account_id = aa
        stock_move = picking._gpc_project_issue_create_draft_journal_entry()
        stock_amount = sum(
            l.debit for l in stock_move.line_ids.filtered(lambda l: l.debit > 0)
        )

        labor_move = self._make_labor_batch_move(aa)
        labor_amount = sum(
            l.debit for l in labor_move.line_ids.filtered(lambda l: l.debit > 0)
        )

        key = str(aa.id)
        all_debit_lines = self.env["account.move.line"].search(
            [
                ("analytic_distribution", "like", key),
                ("debit", ">", 0),
                ("move_id", "in", [stock_move.id, labor_move.id]),
            ]
        )
        total_analytic_debit = sum(all_debit_lines.mapped("debit"))
        self.assertAlmostEqual(
            total_analytic_debit,
            stock_amount + labor_amount,
            places=2,
            msg="Combined analytic debit from both modules must equal the sum of individual amounts",
        )
