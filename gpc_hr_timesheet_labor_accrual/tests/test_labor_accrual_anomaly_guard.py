# Copyright 2026
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

"""Hard hours guard: do not accrue >24h per line or per employee/day."""

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.gpc_hr_timesheet_labor_accrual.tests.test_labor_accrual import (
    _analytic_account_vals,
    _make_account,
    _make_journal,
)


@tagged("post_install", "-at_install")
class TestLaborAccrualAnomalyGuard(TransactionCase):
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
            cls.env, "Anom Guard Dr", "AGDR01", "expense", cls.company
        )
        cls.credit_acc = _make_account(
            cls.env, "Anom Guard Cr", "AGCR01", "liability_current", cls.company
        )
        cls.journal = _make_journal(cls.env, "Anom Guard Journal", "AGJ1", cls.company)
        cls.company.write(
            {
                "labor_accrual_debit_account_id": cls.debit_acc.id,
                "labor_accrual_credit_account_id": cls.credit_acc.id,
                "labor_accrual_journal_id": cls.journal.id,
            }
        )
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "MM-UAT-EMP-ANOM-GUARD",
                "company_id": cls.company.id,
                "hourly_cost": 50.0,
            }
        )
        cls.employee_b = cls.env["hr.employee"].create(
            {
                "name": "MM-UAT-EMP-ANOM-GUARD-B",
                "company_id": cls.company.id,
                "hourly_cost": 40.0,
            }
        )
        cls.aa = cls.env["account.analytic.account"].create(
            _analytic_account_vals(cls.env, cls.company, "MM-UAT-AA-ANOM-GUARD")
        )
        cls.project = cls.env["project.project"].create(
            {
                "name": "MM-UAT-PROJ-ANOM-GUARD",
                "company_id": cls.company.id,
                "account_id": cls.aa.id,
            }
        )

    def _batch(self, **kwargs):
        vals = {
            "name": "MM-UAT-BATCH-ANOM-GUARD",
            "company_id": self.company.id,
            "period_start": fields.Date.from_string("2025-12-01"),
            "period_end": fields.Date.from_string("2025-12-31"),
            "state": "draft",
        }
        vals.update(kwargs)
        return self.Batch.create(vals)

    def _ts(self, **kwargs):
        vals = {
            "name": "MM-UAT-TS-anom-guard",
            "company_id": self.company.id,
            "employee_id": self.employee.id,
            "project_id": self.project.id,
            "account_id": self.aa.id,
            "unit_amount": 8.0,
            "date": fields.Date.from_string("2025-12-10"),
        }
        if "include_in_payroll" in self.AAL._fields:
            vals["include_in_payroll"] = True
        if "validated" in self.AAL._fields:
            vals["validated"] = True
        vals.update(kwargs)
        return self.AAL.create(vals)

    def _ids(self, batch):
        return set(batch.line_ids.mapped("timesheet_line_id").ids)

    def test_boundary_24h_exact_is_accrued(self):
        ts = self._ts(name="bound-24", unit_amount=24.0)
        batch = self._batch()
        batch.action_populate_lines()
        self.assertIn(ts.id, self._ids(batch))
        self.assertAlmostEqual(sum(batch.line_ids.mapped("amount")), 24.0 * 50.0, places=2)

    def test_24_01_and_25h_excluded(self):
        over = self._ts(name="bound-24-01", unit_amount=24.01)
        h25 = self._ts(
            name="anom-25",
            unit_amount=25.0,
            date=fields.Date.from_string("2025-12-11"),
        )
        ok = self._ts(
            name="ok-8",
            unit_amount=8.0,
            date=fields.Date.from_string("2025-12-12"),
        )
        batch = self._batch()
        batch.action_populate_lines()
        ids = self._ids(batch)
        self.assertNotIn(over.id, ids)
        self.assertNotIn(h25.id, ids)
        self.assertIn(ok.id, ids)
        self.assertEqual(over.unit_amount, 24.01)
        self.assertEqual(h25.unit_amount, 25.0)

    def test_40_100_200_260_excluded_and_not_deleted(self):
        created = []
        for hours in (40.0, 100.0, 200.0, 260.0):
            created.append(
                self._ts(
                    name="anom-%s" % int(hours),
                    unit_amount=hours,
                    date=fields.Date.from_string("2025-12-15"),
                    employee_id=self.employee_b.id,
                )
            )
        ok = self._ts(name="ok-6", unit_amount=6.0)
        batch = self._batch()
        batch.action_populate_lines()
        ids = self._ids(batch)
        for ts in created:
            self.assertNotIn(ts.id, ids)
            self.assertTrue(ts.exists())
            self.assertGreater(ts.unit_amount, 24.0)
        self.assertIn(ok.id, ids)

    def test_same_day_lines_totaling_24_or_less_accrued(self):
        a = self._ts(name="day-8", unit_amount=8.0)
        b = self._ts(name="day-6", unit_amount=6.0)
        c = self._ts(
            name="day-10",
            unit_amount=10.0,
            date=fields.Date.from_string("2025-12-20"),
        )
        d = self._ts(
            name="day-14",
            unit_amount=14.0,
            date=fields.Date.from_string("2025-12-20"),
        )
        batch = self._batch()
        batch.action_populate_lines()
        ids = self._ids(batch)
        self.assertEqual(ids, {a.id, b.id, c.id, d.id})
        self.assertAlmostEqual(
            sum(batch.line_ids.mapped("amount")),
            (8 + 6) * 50 + (10 + 14) * 50,
            places=2,
        )

    def test_same_day_lines_totaling_over_24_all_excluded(self):
        a = self._ts(name="cum-16", unit_amount=16.0)
        b = self._ts(name="cum-16b", unit_amount=16.0)
        other = self._ts(
            name="other-emp-8",
            unit_amount=8.0,
            employee_id=self.employee_b.id,
        )
        batch = self._batch()
        batch.action_populate_lines()
        ids = self._ids(batch)
        self.assertNotIn(a.id, ids)
        self.assertNotIn(b.id, ids)
        self.assertIn(other.id, ids)
        self.assertEqual(a.unit_amount, 16.0)
        self.assertEqual(b.unit_amount, 16.0)

    def test_normal_8h_and_6h_still_work_and_post(self):
        a = self._ts(name="n8", unit_amount=8.0)
        b = self._ts(
            name="n6",
            unit_amount=6.0,
            date=fields.Date.from_string("2025-12-13"),
        )
        self._ts(name="anom-in-period", unit_amount=25.0)
        batch = self._batch()
        batch.action_populate_lines()
        self.assertEqual(self._ids(batch), {a.id, b.id})
        self.assertAlmostEqual(sum(batch.line_ids.mapped("amount")), 700.0, places=2)
        batch.action_generate_draft_move()
        move = batch.move_id
        self.assertAlmostEqual(sum(move.line_ids.mapped("debit")), 700.0, places=2)
        self.assertAlmostEqual(sum(move.line_ids.mapped("credit")), 700.0, places=2)
        batch.action_post_move()
        self.assertEqual(batch.state, "posted")
        self.assertEqual(move.state, "posted")

    def test_generate_blocks_manually_injected_anomaly_line(self):
        ok = self._ts(name="ok-inject", unit_amount=8.0)
        anom = self._ts(name="inject-25", unit_amount=25.0)
        batch = self._batch()
        batch.action_populate_lines()
        self.assertEqual(self._ids(batch), {ok.id})
        self.env["labor.accrual.batch.line"].create(
            {
                "batch_id": batch.id,
                "timesheet_line_id": anom.id,
                "amount": 25.0 * 50.0,
                "employee_id": anom.employee_id.id,
                "project_id": anom.project_id.id,
                "line_date": anom.date,
            }
        )
        with self.assertRaises(UserError) as ctx:
            batch.action_generate_draft_move()
        msg = str(ctx.exception).lower()
        self.assertIn("24", msg)
        self.assertIn(str(anom.id), str(ctx.exception))
        self.assertFalse(batch.move_id)
        self.assertEqual(anom.unit_amount, 25.0)
