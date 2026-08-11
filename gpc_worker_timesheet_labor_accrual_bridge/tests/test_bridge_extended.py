# Copyright 2026
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

"""Bridge eligibility chain: timesheet → include_in_payroll → populate."""

from odoo import fields
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.gpc_worker_timesheet_labor_accrual_bridge.tests.common import (
    analytic_account_vals,
)


@tagged("post_install", "-at_install")
class TestWorkerLaborAccrualBridgeExtended(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.Batch = cls.env["labor.accrual.batch"]
        cls.AAL = cls.env["account.analytic.line"]
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "MM-UAT-EMP-BRIDGE",
                "company_id": cls.company.id,
                "hourly_cost": 40.0,
            }
        )
        cls.project = cls.env["project.project"].create(
            {"name": "MM-UAT-PROJ-BRIDGE", "company_id": cls.company.id}
        )
        cls.project_b = cls.env["project.project"].create(
            {"name": "MM-UAT-PROJ-BRIDGE-B", "company_id": cls.company.id}
        )
        cls.project_optout = cls.env["project.project"].create(
            {
                "name": "MM-UAT-PROJ-BRIDGE-OUT",
                "company_id": cls.company.id,
                "exclude_from_payroll": True,
            }
        )

    def _batch(self):
        return self.Batch.create(
            {
                "name": "MM-UAT-BATCH-BRIDGE",
                "company_id": self.company.id,
                "period_start": fields.Date.from_string("2025-02-01"),
                "period_end": fields.Date.from_string("2025-02-28"),
                "state": "draft",
            }
        )

    def _create_line(self, **kwargs):
        vals = {
            "name": "MM-UAT-TS-bridge",
            "company_id": self.company.id,
            "employee_id": self.employee.id,
            "project_id": self.project.id,
            "unit_amount": 8.0,
            "date": fields.Date.from_string("2025-02-10"),
        }
        if "validated" in self.AAL._fields:
            vals["validated"] = True
        vals.update(kwargs)
        if "account_id" in self.AAL._fields and "account_id" not in vals:
            vals["account_id"] = self.env["account.analytic.account"].create(
                analytic_account_vals(self.env, self.company, "MM-UAT-AA-BR")
            ).id
        return self.AAL.create(vals)

    def test_optout_project_skipped_by_populate(self):
        line = self._create_line(project_id=self.project_optout.id)
        if "include_in_payroll" in self.AAL._fields:
            self.assertFalse(line.include_in_payroll)
        batch = self._batch()
        batch.action_populate_lines()
        self.assertNotIn(line.id, batch.line_ids.mapped("timesheet_line_id").ids)

    def test_zero_hours_skipped(self):
        line = self._create_line(unit_amount=0.0)
        batch = self._batch()
        batch.action_populate_lines()
        self.assertNotIn(line.id, batch.line_ids.mapped("timesheet_line_id").ids)

    def test_employee_two_projects_both_populated(self):
        a = self._create_line(name="proj-a", unit_amount=4.0)
        b = self._create_line(
            name="proj-b",
            unit_amount=4.0,
            project_id=self.project_b.id,
        )
        batch = self._batch()
        batch.action_populate_lines()
        ids = set(batch.line_ids.mapped("timesheet_line_id").ids)
        self.assertEqual(ids, {a.id, b.id})
        self.assertAlmostEqual(sum(batch.line_ids.mapped("amount")), 320.0, places=2)

    def test_same_day_two_lines_both_populated(self):
        a = self._create_line(name="dup-look-a", unit_amount=3.0)
        b = self._create_line(name="dup-look-b", unit_amount=3.0)
        batch = self._batch()
        batch.action_populate_lines()
        self.assertEqual(len(batch.line_ids), 2)
        self.assertEqual(set(batch.line_ids.mapped("timesheet_line_id").ids), {a.id, b.id})

    def test_historical_false_flag_not_populated(self):
        if "include_in_payroll" not in self.AAL._fields:
            self.skipTest("include_in_payroll missing")
        line = self._create_line(include_in_payroll=False)
        batch = self._batch()
        batch.action_populate_lines()
        self.assertNotIn(line.id, batch.line_ids.mapped("timesheet_line_id").ids)
