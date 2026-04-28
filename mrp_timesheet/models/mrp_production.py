# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError
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

    @api.depends('timesheet_ids', 'timesheet_ids.unit_amount', 'timesheet_ids.employee_id', 'timesheet_ids.product_id', 'timesheet_ids.amount')
    def _compute_timesheet_labor_cost(self):
        for order in self:
            order.timesheet_labor_cost = order._get_timesheet_labor_total()

    def _get_timesheet_labor_total(self):
        """Compute total labor cost from timesheet lines (hours × hourly cost per line)."""
        self.ensure_one()
        total = 0.0
        for line in self.timesheet_ids:
            total += line._get_timesheet_labor_cost_for_production()
        return float_round(total, precision_digits=self.company_id.currency_id.decimal_places)

    def _post_inventory(self, cancel_backorder=False):
        res = super()._post_inventory(cancel_backorder=cancel_backorder)
        for order in self:
            order._post_timesheet_labor_cost_if_any()
        return res

    def _post_timesheet_labor_cost_if_any(self):
        """Create a journal entry for timesheet labor cost when MO is done (only once)."""
        self.ensure_one()
        if self.timesheet_cost_posted or not self.timesheet_ids:
            return
        labor_total = self._get_timesheet_labor_total()
        if labor_total <= 0:
            return

        company = self.company_id
        labor_account = company.production_labor_expense_account_id
        if not labor_account:
            raise UserError(
                'Please set the "Production labor expense account" in Accounting settings '
                '(or in Company) to post timesheet labor cost.'
            )

        # Use the finished product's stock valuation account for the debit (increase inventory value)
        finished_product = self.product_id
        if not finished_product:
            return
        stock_valuation_account = finished_product.categ_id.property_stock_valuation_account_id
        if not stock_valuation_account:
            raise UserError(
                'The product category "%s" has no Stock Valuation Account. '
                'Configure it to post timesheet labor cost.'
                % finished_product.categ_id.name
            )

        journal = company.account_stock_journal_id
        if not journal:
            raise UserError(
                'No Stock Journal configured for company "%s". Set it in Settings > Companies or in Inventory settings.'
                % company.name
            )
        # Create one JE: Debit Stock Valuation (inventory), Credit Labor expense
        move_vals = {
            'move_type': 'entry',
            'date': self.date_finished or fields.Date.context_today(self),
            'journal_id': journal.id,
            'company_id': company.id,
            'ref': 'MO %s – Timesheet labor' % self.name,
            'line_ids': [
                (0, 0, {
                    'name': 'Timesheet labor – %s' % self.name,
                    'account_id': stock_valuation_account.id,
                    'debit': labor_total,
                    'credit': 0.0,
                    'currency_id': company.currency_id.id,
                }),
                (0, 0, {
                    'name': 'Timesheet labor – %s' % self.name,
                    'account_id': labor_account.id,
                    'debit': 0.0,
                    'credit': labor_total,
                    'currency_id': company.currency_id.id,
                }),
            ],
        }
        account_move = self.env['account.move'].create(move_vals)
        account_move._post()

        self.write({
            'timesheet_cost_posted': True,
            'timesheet_labor_move_id': account_move.id,
        })
