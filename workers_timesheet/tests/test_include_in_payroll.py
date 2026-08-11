# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestIncludeInPayroll(TransactionCase):
    """Payroll eligibility must not be silently cleared by selecting a project."""

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
        cls.employee = cls.env["hr.employee"].create({"name": "UAT Payroll Emp"})
        cls.project_normal = cls.env["project.project"].create(
            {"name": "UAT Normal Project", "company_id": cls.env.company.id}
        )
        cls.project_optout = cls.env["project.project"].create(
            {
                "name": "UAT Opt-out Project",
                "company_id": cls.env.company.id,
                "exclude_from_payroll": True,
            }
        )

    def _new_line(self, **kwargs):
        vals = {
            "name": "uat payroll ts",
            "employee_id": self.employee.id,
            "unit_amount": 8.0,
            "company_id": self.env.company.id,
        }
        vals.update(kwargs)
        return self.env["account.analytic.line"].new(vals)

    def test_case1_no_project_defaults_true(self):
        line = self.env["account.analytic.line"].create(
            {
                "name": "no project yet",
                "employee_id": self.employee.id,
                "unit_amount": 8.0,
                "company_id": self.env.company.id,
            }
        )
        self.assertTrue(line.include_in_payroll)

    def test_case2_normal_project_stays_true(self):
        rec = self._new_line()
        rec.project_id = self.project_normal
        rec._onchange_project_id()
        self.assertTrue(rec.include_in_payroll)
        created = self.env["account.analytic.line"].create(
            {
                "name": "normal project",
                "employee_id": self.employee.id,
                "project_id": self.project_normal.id,
                "unit_amount": 8.0,
                "company_id": self.env.company.id,
            }
        )
        self.assertTrue(created.include_in_payroll)

    def test_case3_explicit_opt_out_false(self):
        rec = self._new_line()
        rec.project_id = self.project_optout
        rec._onchange_project_id()
        self.assertFalse(rec.include_in_payroll)
        created = self.env["account.analytic.line"].create(
            {
                "name": "opt out",
                "employee_id": self.employee.id,
                "project_id": self.project_optout.id,
                "unit_amount": 8.0,
                "company_id": self.env.company.id,
            }
        )
        self.assertFalse(created.include_in_payroll)

    def test_case4_edit_eligible_line_no_unexpected_reset(self):
        line = self.env["account.analytic.line"].create(
            {
                "name": "eligible",
                "employee_id": self.employee.id,
                "project_id": self.project_normal.id,
                "unit_amount": 8.0,
                "company_id": self.env.company.id,
            }
        )
        self.assertTrue(line.include_in_payroll)
        line.write({"name": "eligible edited", "unit_amount": 6.0})
        self.assertTrue(line.include_in_payroll)

    def test_use_for_payroll_false_does_not_uncheck(self):
        """Regression: do not copy use_for_payroll (default False)."""
        if "use_for_payroll" in self.project_normal._fields:
            self.project_normal.use_for_payroll = False
        rec = self._new_line(include_in_payroll=True)
        rec.project_id = self.project_normal
        rec._onchange_project_id()
        self.assertTrue(rec.include_in_payroll)
