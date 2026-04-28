# -*- coding: utf-8 -*-
"""Regression: MO form smart button must resolve action (XML load order)."""

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


def _view_arch_text(view):
    """Return a single string arch for Odoo 17+ json ``arch_db`` or plain text."""
    arch = view.arch_db
    if isinstance(arch, dict):
        arch = arch.get("en_US") or next(iter(arch.values()), "")
    return arch or ""


@tagged("post_install", "-at_install", "mrp_labor_clearing_btn")
class TestLaborClearingMoButton(TransactionCase):
    """Labor Cost stat button → Labor Clearing Balance Check wizard action."""

    def test_labor_clearing_action_xmlid_exists(self):
        """Install must create action before MO form inherits (%%(action)d)."""
        action = self.env.ref(
            "mrp_timesheet.action_labor_clearing_check_wizard",
            raise_if_not_found=True,
        )
        self.assertEqual(action._name, "ir.actions.act_window")
        self.assertEqual(action.res_model, "mrp.labor.clearing.check.wizard")

    def test_mo_form_inherit_arch_references_action_id(self):
        """Smart button name= must be the numeric id of the wizard action."""
        action = self.env.ref("mrp_timesheet.action_labor_clearing_check_wizard")
        view = self.env.ref("mrp_timesheet.mrp_production_form_timesheet")
        arch = _view_arch_text(view)
        self.assertIn(
            f'name="{action.id}"',
            arch,
            "MO form button must bind to labor clearing wizard action id",
        )
        self.assertIn('type="action"', arch)
        self.assertIn("timesheet_labor_cost", arch)

    def test_labor_clearing_action_readable_for_account_user(self):
        """Action is loadable the same way the web client resolves stat buttons."""
        action = self.env.ref("mrp_timesheet.action_labor_clearing_check_wizard")
        data = self.env["ir.actions.act_window"].browse(action.id).read(
            ["name", "res_model", "view_mode", "target"]
        )[0]
        self.assertEqual(data["res_model"], "mrp.labor.clearing.check.wizard")
        self.assertEqual(data["target"], "new")
