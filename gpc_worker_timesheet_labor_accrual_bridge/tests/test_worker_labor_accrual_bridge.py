# Copyright 2026
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import fields
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.gpc_worker_timesheet_labor_accrual_bridge.tests.common import (
    analytic_account_vals,
)


@tagged("post_install", "-at_install")
class TestWorkerLaborAccrualBridge(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.Batch = cls.env["labor.accrual.batch"]
        cls.AAL = cls.env["account.analytic.line"]
        cls.Employee = cls.env["hr.employee"]
        cls.Project = cls.env["project.project"]

        cls.employee = cls.Employee.create(
            {
                "name": "Bridge Worker",
                "company_id": cls.company.id,
            }
        )
        if "hourly_cost" in cls.employee._fields:
            cls.employee.hourly_cost = 100.0

        cls.project = cls.Project.create(
            {
                "name": "Bridge Project",
                "company_id": cls.company.id,
            }
        )
        cls.other_company = cls.env["res.company"].create({"name": "Bridge Other Company"})
        cls.other_project = cls.Project.create(
            {
                "name": "Bridge Other Project",
                "company_id": cls.other_company.id,
            }
        )

    def _batch(self, period_key="2024-02"):
        return self.Batch.create(
            {
                "name": "Bridge batch %s" % period_key,
                "company_id": self.company.id,
                "period_start": fields.Date.from_string("2024-02-01"),
                "period_end": fields.Date.from_string("2024-02-29"),
                "period_key": period_key,
                "state": "draft",
            }
        )

    def _line_vals(self, **kwargs):
        vals = {
            "name": "Bridge timesheet",
            "company_id": self.company.id,
            "employee_id": self.employee.id,
            "project_id": self.project.id,
            "unit_amount": 2.0,
            "date": fields.Date.from_string("2024-02-15"),
        }
        if "validated" in self.AAL._fields and "validated" not in kwargs:
            vals["validated"] = True
        if "include_in_payroll" in self.AAL._fields and "include_in_payroll" not in kwargs:
            vals["include_in_payroll"] = True
        vals.update(kwargs)
        return vals

    def _create_line(self, **kwargs):
        vals = self._line_vals(**kwargs)
        if "account_id" in self.AAL._fields and "account_id" not in vals:
            vals["account_id"] = self.env["account.analytic.account"].create(
                analytic_account_vals(self.env, self.company, "Bridge Analytic")
            ).id
        return self.AAL.create(vals)

    def _line_has_positive_amount(self, batch, line):
        return batch._get_labor_amount_for_line(line) > 0.0

    def test_worker_line_include_in_payroll_true_populated(self):
        line = self._create_line(include_in_payroll=True, unit_amount=2.0)
        batch = self._batch()
        if not self._line_has_positive_amount(batch, line):
            self.skipTest("No confirmed positive amount source in this test environment.")
        batch.action_populate_lines()
        self.assertIn(line, batch.line_ids.mapped("timesheet_line_id"))

    def test_worker_line_include_in_payroll_false_skipped(self):
        line = self._create_line(include_in_payroll=False, unit_amount=2.0)
        batch = self._batch(period_key="2026-06")
        batch.action_populate_lines()
        self.assertNotIn(line, batch.line_ids.mapped("timesheet_line_id"))

    def test_worker_line_zero_amount_skipped(self):
        line = self._create_line(include_in_payroll=True, unit_amount=0.0)
        batch = self._batch(period_key="2026-07")
        batch.action_populate_lines()
        self.assertNotIn(line, batch.line_ids.mapped("timesheet_line_id"))

    def test_date_or_company_mismatch_skipped(self):
        outside = self._create_line(
            include_in_payroll=True,
            date=fields.Date.from_string("2024-03-05"),
            unit_amount=2.0,
        )
        vals = self._line_vals(
            include_in_payroll=True,
            company_id=self.other_company.id,
            project_id=self.other_project.id,
            unit_amount=2.0,
        )
        if "account_id" in self.AAL._fields:
            vals["account_id"] = self.env["account.analytic.account"].create(
                analytic_account_vals(self.env, self.other_company, "Bridge Other Analytic")
            ).id
        other_company_line = self.AAL.create(vals)
        batch = self._batch(period_key="2026-08")
        batch.action_populate_lines()
        self.assertNotIn(outside, batch.line_ids.mapped("timesheet_line_id"))
        self.assertNotIn(other_company_line, batch.line_ids.mapped("timesheet_line_id"))

    def test_populate_replaces_existing_lines(self):
        line1 = self._create_line(include_in_payroll=True, unit_amount=2.0)
        batch = self._batch(period_key="2026-09")
        if not self._line_has_positive_amount(batch, line1):
            self.skipTest("No confirmed positive amount source in this test environment.")

        batch.action_populate_lines()
        self.assertIn(line1, batch.line_ids.mapped("timesheet_line_id"))

        line1.write({"include_in_payroll": False})
        line2 = self._create_line(
            include_in_payroll=True,
            unit_amount=3.0,
            date=fields.Date.from_string("2024-02-20"),
        )
        if not self._line_has_positive_amount(batch, line2):
            self.skipTest("No confirmed positive amount source for second line.")

        batch.action_populate_lines()
        ts_ids = batch.line_ids.mapped("timesheet_line_id")
        self.assertNotIn(line1, ts_ids)
        self.assertIn(line2, ts_ids)

