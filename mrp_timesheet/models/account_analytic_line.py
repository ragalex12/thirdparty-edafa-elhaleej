# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    mrp_production_id = fields.Many2one(
        comodel_name='mrp.production',
        string='Manufacturing Order',
        index=True,
        ondelete='set null',
        help='Manufacturing order this timesheet line is linked to.',
    )

    def _get_timesheet_labor_cost_for_production(self):
        """
        Return labor cost for this line for production costing.
        Uses line.amount if set, else unit_amount × hourly rate (employee or product).
        """
        self.ensure_one()
        if self.amount and self.company_id:
            # amount can be negative (credit), we want positive cost for labor
            return abs(self.amount)
        hours = self.unit_amount or 0.0
        if hours <= 0:
            return 0.0
        # Hourly rate: employee (hr.employee hourly_cost / timesheet_cost), then product cost
        rate = 0.0
        if self.employee_id:
            emp = self.employee_id
            if hasattr(emp, 'hourly_cost') and emp.hourly_cost:
                rate = emp.hourly_cost
            elif hasattr(emp, 'timesheet_cost') and emp.timesheet_cost:
                rate = emp.timesheet_cost
        if rate == 0 and self.product_id:
            rate = self.product_id.standard_price or 0.0
        return hours * rate
