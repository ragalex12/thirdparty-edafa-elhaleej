# Copyright 2026
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

"""Extended labor-accrual UAT: journals, company guards, no-GL source AAL."""

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.gpc_hr_timesheet_labor_accrual.tests.test_labor_accrual import (
    _make_account,
    _make_journal,
    _analytic_account_vals,
)


@tagged("post_install", "-at_install")
class TestLaborAccrualExtended(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                mail_create_nolog=True,
                mail_notrack=True,
                tracking_disable=True,
            )
        )
        cls.company = cls.env.company
        cls.AAL = cls.env["account.analytic.line"]
        cls.Batch = cls.env["labor.accrual.batch"]
        cls.debit_acc = _make_account(
            cls.env, "Ext Lab Dr", "ELDR01", "expense", cls.company
        )
        cls.credit_acc = _make_account(
            cls.env, "Ext Lab Cr", "ELCR01", "liability_current", cls.company
        )
        cls.journal = _make_journal(cls.env, "Ext Labor Journal", "ELJ1", cls.company)
        cls.company.write(
            {
                "labor_accrual_debit_account_id": cls.debit_acc.id,
                "labor_accrual_credit_account_id": cls.credit_acc.id,
                "labor_accrual_journal_id": cls.journal.id,
            }
        )
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "MM-UAT-EMP-ACC",
                "company_id": cls.company.id,
                "hourly_cost": 50.0,
            }
        )
        cls.employee_zero = cls.env["hr.employee"].create(
            {
                "name": "MM-UAT-EMP-ZERO",
                "company_id": cls.company.id,
                "hourly_cost": 0.0,
            }
        )
        cls.aa = cls.env["account.analytic.account"].create(
            _analytic_account_vals(cls.env, cls.company, "MM-UAT-AA-ACC")
        )
        cls.project = cls.env["project.project"].create(
            {
                "name": "MM-UAT-PROJ-ACC",
                "company_id": cls.company.id,
                "account_id": cls.aa.id,
            }
        )
        cls.aa_b = cls.env["account.analytic.account"].create(
            _analytic_account_vals(cls.env, cls.company, "MM-UAT-AA-ACC-B")
        )
        cls.project_b = cls.env["project.project"].create(
            {
                "name": "MM-UAT-PROJ-ACC-B",
                "company_id": cls.company.id,
                "account_id": cls.aa_b.id,
            }
        )

    def _batch(self, start="2025-03-01", end="2025-03-31", **kwargs):
        vals = {
            "name": "MM-UAT-BATCH-%s" % start[:7],
            "company_id": self.company.id,
            "period_start": fields.Date.from_string(start),
            "period_end": fields.Date.from_string(end),
            "state": "draft",
        }
        vals.update(kwargs)
        return self.Batch.create(vals)

    def _ts(self, **kwargs):
        vals = {
            "name": "MM-UAT-TS-acc",
            "company_id": self.company.id,
            "employee_id": self.employee.id,
            "project_id": self.project.id,
            "account_id": self.aa.id,
            "unit_amount": 8.0,
            "date": fields.Date.from_string("2025-03-10"),
        }
        if "include_in_payroll" in self.AAL._fields:
            vals["include_in_payroll"] = True
        if "validated" in self.AAL._fields:
            vals["validated"] = True
        vals.update(kwargs)
        return self.AAL.create(vals)

    def test_generate_blocks_foreign_company_credit_account(self):
        other = self.env["res.company"].create({"name": "MM-UAT-CO-FX-CR"})
        foreign_credit = _make_account(
            self.env, "Foreign Labor Cr", "FXCR99", "liability_current", other
        )
        self._ts()
        batch = self._batch()
        batch.action_populate_lines()
        if not batch.line_ids:
            self.skipTest("No batch line created.")
        bak = self.company.labor_accrual_credit_account_id
        self.env.cr.execute(
            "UPDATE res_company SET labor_accrual_credit_account_id = %s WHERE id = %s",
            (foreign_credit.id, self.company.id),
        )
        self.company.invalidate_recordset(["labor_accrual_credit_account_id"])
        try:
            with self.assertRaises(UserError) as ctx:
                batch.action_generate_draft_move()
            msg = str(ctx.exception).lower()
            self.assertTrue(
                "cross-company credit" in msg or "does not belong" in msg, msg
            )
            self.assertFalse(batch.move_id)
        finally:
            self.env.cr.execute(
                "UPDATE res_company SET labor_accrual_credit_account_id = %s WHERE id = %s",
                (bak.id, self.company.id),
            )
            self.company.invalidate_recordset(["labor_accrual_credit_account_id"])

    def test_populate_skips_include_in_payroll_false(self):
        if "include_in_payroll" not in self.AAL._fields:
            self.skipTest("include_in_payroll missing")
        ok = self._ts(name="eligible")
        skipped = self._ts(
            name="excluded",
            include_in_payroll=False,
            date=fields.Date.from_string("2025-03-11"),
        )
        batch = self._batch()
        batch.action_populate_lines()
        ids = batch.line_ids.mapped("timesheet_line_id").ids
        self.assertIn(ok.id, ids)
        self.assertNotIn(skipped.id, ids)

    def test_populate_skips_zero_hourly_cost(self):
        self._ts(employee_id=self.employee_zero.id, name="zero-rate")
        batch = self._batch()
        batch.action_populate_lines()
        self.assertFalse(batch.line_ids)

    def test_populate_excludes_anomaly_hours_even_when_amount_positive(self):
        """Single-line >24h must not enter populate even if hourly_cost would yield an amount."""
        ts = self._ts(name="anom-25", unit_amount=25.0)
        batch = self._batch()
        batch.action_populate_lines()
        self.assertNotIn(ts.id, batch.line_ids.mapped("timesheet_line_id").ids)
        self.assertTrue(ts.exists())
        self.assertEqual(ts.unit_amount, 25.0)

    def test_mixed_eligible_ineligible_counts(self):
        a = self._ts(name="mix-a", unit_amount=8.0)
        b = self._ts(
            name="mix-b",
            unit_amount=6.0,
            date=fields.Date.from_string("2025-03-12"),
            project_id=self.project_b.id,
            account_id=self.aa_b.id,
        )
        self._ts(
            name="mix-excl",
            include_in_payroll=False,
            date=fields.Date.from_string("2025-03-13"),
        )
        self._ts(
            name="mix-zero",
            employee_id=self.employee_zero.id,
            date=fields.Date.from_string("2025-03-14"),
        )
        batch = self._batch()
        batch.action_populate_lines()
        self.assertEqual(len(batch.line_ids), 2)
        self.assertAlmostEqual(sum(batch.line_ids.mapped("amount")), 8 * 50 + 6 * 50, places=2)
        self.assertEqual(set(batch.line_ids.mapped("timesheet_line_id").ids), {a.id, b.id})

    def test_credit_line_has_no_analytic_debit_does(self):
        self._ts()
        batch = self._batch()
        batch.action_populate_lines()
        batch.action_generate_draft_move()
        move = batch.move_id
        self.assertTrue(move)
        self.assertEqual(move.state, "draft")
        for line in move.line_ids.filtered(lambda l: l.debit > 0):
            self.assertTrue(line.analytic_distribution)
            self.assertEqual(line.account_id, self.debit_acc)
        for line in move.line_ids.filtered(lambda l: l.credit > 0):
            self.assertFalse(line.analytic_distribution)
            self.assertEqual(line.account_id, self.credit_acc)
        self.assertAlmostEqual(sum(move.line_ids.mapped("debit")), sum(move.line_ids.mapped("credit")), places=2)

    def test_totals_by_project_match_debit_slices(self):
        self._ts(unit_amount=8.0)
        self._ts(
            unit_amount=6.0,
            date=fields.Date.from_string("2025-03-15"),
            project_id=self.project_b.id,
            account_id=self.aa_b.id,
        )
        batch = self._batch()
        batch.action_populate_lines()
        batch.action_generate_draft_move()
        move = batch.move_id
        debit = move.line_ids.filtered(lambda l: l.debit > 0)
        self.assertEqual(len(debit), 2)
        amounts = sorted(debit.mapped("debit"))
        self.assertEqual(amounts, [300.0, 400.0])
        self.assertAlmostEqual(sum(debit.mapped("debit")), 700.0, places=2)

    def test_draft_move_not_posted(self):
        self._ts()
        batch = self._batch()
        batch.action_populate_lines()
        batch.action_generate_draft_move()
        self.assertEqual(batch.move_id.state, "draft")
        self.assertEqual(batch.state, "draft")

    def test_post_creates_gl_aal_source_timesheet_stays_no_gl(self):
        ts = self._ts()
        self.assertFalse(ts.general_account_id)
        self.assertFalse(ts.move_line_id)
        batch = self._batch()
        batch.action_populate_lines()
        batch.action_generate_draft_move()
        batch.action_post_move()
        ts.invalidate_recordset()
        self.assertFalse(ts.general_account_id, "Source timesheet must stay analytic-only")
        self.assertFalse(ts.move_line_id)
        posted_aal = self.AAL.search(
            [("move_line_id", "in", batch.move_id.line_ids.ids)]
        )
        self.assertTrue(posted_aal)
        self.assertTrue(all(posted_aal.mapped("general_account_id")))
        self.assertTrue(all(posted_aal.mapped("move_line_id")))

    def test_duplicate_period_blocked_after_populate(self):
        self._ts()
        batch = self._batch()
        batch.action_populate_lines()
        with self.assertRaises(ValidationError):
            self._batch(name="MM-UAT-BATCH-DUP")

    def test_cancelled_draft_releases_period(self):
        self._ts()
        batch = self._batch()
        batch.action_populate_lines()
        batch.write({"state": "cancelled"})
        other = self._batch(name="MM-UAT-BATCH-AFTER-CANCEL")
        self.assertTrue(other)
        self.assertEqual(other.period_key, "2025-03")

    def test_period_key_mismatch_on_create_is_overwritten(self):
        batch = self._batch(period_key="2099-01")
        self.assertEqual(batch.period_key, "2025-03")

    def test_same_day_two_lines_both_populated(self):
        a = self._ts(name="same-day-a", unit_amount=3.0)
        b = self._ts(name="same-day-b", unit_amount=5.0)
        batch = self._batch()
        batch.action_populate_lines()
        ids = batch.line_ids.mapped("timesheet_line_id").ids
        self.assertEqual(set(ids), {a.id, b.id})
        self.assertAlmostEqual(sum(batch.line_ids.mapped("amount")), 400.0, places=2)
