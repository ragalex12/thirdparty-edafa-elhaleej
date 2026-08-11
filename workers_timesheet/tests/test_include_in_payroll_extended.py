# -*- coding: utf-8 -*-
"""Extended Include in Payroll UAT cases from the 11 Aug 2026 meeting."""

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestIncludeInPayrollExtended(TransactionCase):
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
        cls.employee = cls.env["hr.employee"].create(
            {"name": "MM-UAT-EMP-PAYROLL", "hourly_cost": 45.0}
        )
        cls.project_normal = cls.env["project.project"].create(
            {"name": "MM-UAT-PROJ-PAYROLL", "company_id": cls.env.company.id}
        )
        cls.project_optout = cls.env["project.project"].create(
            {
                "name": "MM-UAT-PROJ-OPTOUT",
                "company_id": cls.env.company.id,
                "exclude_from_payroll": True,
            }
        )
        cls.project_other = cls.env["project.project"].create(
            {"name": "MM-UAT-PROJ-OTHER", "company_id": cls.env.company.id}
        )

    def _create(self, **kwargs):
        vals = {
            "name": "MM-UAT-TS-payroll",
            "employee_id": self.employee.id,
            "unit_amount": 8.0,
            "company_id": self.env.company.id,
            "project_id": self.project_normal.id,
        }
        vals.update(kwargs)
        return self.env["account.analytic.line"].create(vals)

    def test_saved_reopened_keeps_true(self):
        line = self._create()
        self.assertTrue(line.include_in_payroll)
        line.invalidate_recordset()
        again = self.env["account.analytic.line"].browse(line.id)
        self.assertTrue(again.include_in_payroll)

    def test_switch_normal_to_optout_sets_false(self):
        line = self._create()
        line.write({"project_id": self.project_optout.id})
        self.assertFalse(line.include_in_payroll)

    def test_switch_optout_to_normal_sets_true(self):
        line = self._create(project_id=self.project_optout.id)
        self.assertFalse(line.include_in_payroll)
        line.write({"project_id": self.project_normal.id})
        self.assertTrue(line.include_in_payroll)

    def test_explicit_false_on_normal_project_is_stored(self):
        line = self._create(include_in_payroll=False)
        self.assertFalse(line.include_in_payroll)

    def test_unrelated_edit_does_not_reset_explicit_false(self):
        line = self._create(include_in_payroll=False)
        line.write({"name": "MM-UAT-TS-payroll edited", "unit_amount": 6.0})
        self.assertFalse(line.include_in_payroll)

    def test_multiple_lines_same_employee_day(self):
        a = self._create(name="MM-UAT-TS-same-day-a", unit_amount=4.0)
        b = self._create(
            name="MM-UAT-TS-same-day-b",
            unit_amount=4.0,
            project_id=self.project_other.id,
        )
        self.assertTrue(a.include_in_payroll)
        self.assertTrue(b.include_in_payroll)
        self.assertEqual(a.date, b.date)

    def test_zero_hours_does_not_clear_flag(self):
        line = self._create(unit_amount=0.0)
        self.assertTrue(line.include_in_payroll)

    def test_anomaly_hours_do_not_clear_flag(self):
        for hours in (25.0, 40.0, 100.0, 200.0, 260.0):
            line = self._create(name="MM-UAT-TS-anom-%s" % int(hours), unit_amount=hours)
            self.assertTrue(
                line.include_in_payroll,
                "Anomalous %sh must not silently uncheck payroll" % hours,
            )

    def test_onchange_optout_then_create_false(self):
        rec = self.env["account.analytic.line"].new(
            {
                "name": "onchange",
                "employee_id": self.employee.id,
                "unit_amount": 8.0,
                "company_id": self.env.company.id,
            }
        )
        rec.project_id = self.project_optout
        rec._onchange_project_id()
        self.assertFalse(rec.include_in_payroll)
