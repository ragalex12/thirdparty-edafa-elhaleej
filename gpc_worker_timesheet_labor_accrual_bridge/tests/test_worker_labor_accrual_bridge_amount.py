# Copyright 2026
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

"""Focused tests for bridge domain and amount resolution."""

from unittest.mock import patch

from odoo import fields
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.gpc_worker_timesheet_labor_accrual_bridge.tests.common import (
    analytic_account_vals,
)


@tagged("post_install", "-at_install")
class TestWorkerLaborAccrualBridgeAmount(TransactionCase):
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
                "name": "Bridge Amount Worker",
                "company_id": cls.company.id,
            }
        )
        if "hourly_cost" in cls.employee._fields:
            cls.employee.hourly_cost = 50.0

        cls.project = cls.Project.create(
            {
                "name": "Bridge Amount Project",
                "company_id": cls.company.id,
            }
        )

    def _batch(self):
        return self.Batch.create(
            {
                "name": "Bridge amount batch",
                "company_id": self.company.id,
                "period_start": fields.Date.from_string("2024-03-01"),
                "period_end": fields.Date.from_string("2024-03-31"),
                "period_key": "2024-03-amt",
                "state": "draft",
            }
        )

    def _create_line(self, **kwargs):
        vals = {
            "name": "Bridge amount ts",
            "company_id": self.company.id,
            "employee_id": self.employee.id,
            "project_id": self.project.id,
            "unit_amount": 4.0,
            "date": fields.Date.from_string("2024-03-10"),
        }
        if "validated" in self.AAL._fields and "validated" not in kwargs:
            vals["validated"] = True
        if "include_in_payroll" in self.AAL._fields and "include_in_payroll" not in kwargs:
            vals["include_in_payroll"] = True
        vals.update(kwargs)
        if "account_id" in self.AAL._fields and "account_id" not in vals:
            vals["account_id"] = self.env["account.analytic.account"].create(
                analytic_account_vals(self.env, self.company, "Bridge Analytic Amt")
            ).id
        return self.AAL.create(vals)

    def test_eligible_domain_includes_include_in_payroll_when_field_exists(self):
        batch = self._batch()
        dom = batch._get_eligible_timesheet_domain()
        if "include_in_payroll" not in self.AAL._fields:
            self.skipTest("include_in_payroll not on account.analytic.line")
        self.assertIn(("include_in_payroll", "=", True), dom)

    def test_fallback_amount_uses_hourly_cost_when_super_and_labor_cost_zero(self):
        batch = self._batch()
        line = self._create_line(unit_amount=2.0)
        if "hourly_cost" not in self.employee._fields:
            self.skipTest("hourly_cost not on hr.employee")
        if "labor_cost" in line._fields and (line.labor_cost or 0.0) > 0.0:
            self.skipTest("labor_cost is positive; fallback chain not exercised.")

        amount = batch._get_labor_amount_for_line(line)
        expected = 2.0 * 50.0
        self.assertAlmostEqual(amount, expected, places=2)

    def test_populate_logs_summary(self):
        batch = self._batch()
        line = self._create_line(unit_amount=1.0)
        if batch._get_labor_amount_for_line(line) <= 0:
            self.skipTest("No positive resolved amount for populate summary test.")

        with patch(
            "odoo.addons.gpc_worker_timesheet_labor_accrual_bridge.models."
            "labor_accrual_batch._logger"
        ) as mock_logger:
            batch.action_populate_lines()
            self.assertTrue(mock_logger.info.called)
            msg = str(mock_logger.info.call_args)
            self.assertIn("Worker accrual populate summary", msg)
            self.assertIn(str(batch.id), msg)

        self.assertIn(line, batch.line_ids.mapped("timesheet_line_id"))
