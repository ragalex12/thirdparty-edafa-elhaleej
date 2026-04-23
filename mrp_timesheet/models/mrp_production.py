# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools import float_round


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Analytic Account',
        check_company=True,
        help='Analytic account used for timesheet lines linked to this manufacturing order.',
    )
    timesheet_ids = fields.One2many(
        comodel_name='account.analytic.line',
        inverse_name='mrp_production_id',
        string='Timesheets',
        help='Timesheet lines logged on this manufacturing order.',
    )
    timesheet_count = fields.Integer(
        string='Timesheet Count',
        compute='_compute_timesheet_count',
    )
    timesheet_labor_cost = fields.Monetary(
        string='Timesheet Labor Cost',
        compute='_compute_timesheet_labor_cost',
        currency_field='currency_id',
        help='Total labor cost from timesheet lines (hours × hourly cost).',
    )
    timesheet_cost_posted = fields.Boolean(
        string='Timesheet Cost Posted',
        default=False,
        copy=False,
        help='True when the labor cost journal entry has been created.',
    )
    timesheet_labor_move_id = fields.Many2one(
        comodel_name='account.move',
        string='Timesheet Labor Journal Entry',
        copy=False,
        readonly=True,
        help='Journal entry that posted timesheet labor cost to inventory.',
    )
    currency_id = fields.Many2one(
        related='company_id.currency_id',
        depends=['company_id'],
    )

    def _compute_timesheet_count(self):
        for order in self:
            order.timesheet_count = len(order.timesheet_ids)

    @api.depends(
        'timesheet_ids',
        'timesheet_ids.labor_cost',
        'timesheet_ids.unit_amount',
        'timesheet_ids.employee_id',
        'timesheet_ids.is_overtime',
        'timesheet_ids.is_holiday',
    )
    def _compute_timesheet_labor_cost(self):
        for order in self:
            order.timesheet_labor_cost = order._get_timesheet_labor_total()

    def _get_timesheet_labor_total(self):
        """Sum labor_cost from all timesheet lines (uses Step 2 computed field)."""
        self.ensure_one()
        total = sum(self.timesheet_ids.mapped('labor_cost'))
        return float_round(total, precision_digits=self.company_id.currency_id.decimal_places)

    def _post_inventory(self, cancel_backorder=False):
        res = super()._post_inventory(cancel_backorder=cancel_backorder)
        for order in self:
            order._post_timesheet_labor_cost_if_any()
        return res

    def _post_timesheet_labor_cost_if_any(self):
        """Task 69 – Reconciliation mode: generate JEs for all unposted timesheet lines.

        Called automatically by _post_inventory() when MO is marked Done.
        - Skips lines that already have a labor_move_id (idempotent).
        - Sets timesheet_cost_posted = True only when at least one JE is posted.
        - Re-entrant safe: lines already posted via the real-time trigger (Step 4)
          are skipped silently, so this serves as a reconciliation pass.
        """
        self.ensure_one()
        if not self.timesheet_ids:
            return

        posted_count = 0
        for line in self.timesheet_ids:
            if line.labor_move_id:
                # Already posted by real-time trigger — count it
                posted_count += 1
                continue
            move = line._generate_labor_cost_move()
            if move:
                posted_count += 1

        if posted_count and not self.timesheet_cost_posted:
            self.with_context(skip_labor_je=True).write({'timesheet_cost_posted': True})
