# -*- coding: utf-8 -*-
"""
Task 75 – Labor Clearing Account Balance Check Wizard (optional)

Purpose
-------
The Labor Clearing Account is a transit account in the two-step payroll
reconciliation flow:

  Step 1 (timesheet posting)  → CR Labor Clearing
  Step 2 (payroll run)        → DR Labor Clearing

After both steps the net balance should be zero.  This wizard reports the
current outstanding balance on the clearing account so accountants can
identify periods where the payroll run has not yet cancelled timesheet
accruals.

Usage
-----
Manufacturing → Reporting → Labor Clearing Balance Check
  – or –
Accounting → Reporting → Labor Clearing Balance Check

The wizard reads posted account.move.lines for the configured clearing
account and groups them by period (month), reporting:
  - Total debited (payroll clearing)
  - Total credited (timesheet accrual)
  - Outstanding balance (credit − debit)
"""

from odoo import api, fields, models


class LaborClearingCheckWizard(models.TransientModel):
    _name = 'mrp.labor.clearing.check.wizard'
    _description = 'Labor Clearing Account Balance Check'

    # ── Filters ───────────────────────────────────────────────────────────────
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )
    date_from = fields.Date(
        string='From',
        required=True,
        default=lambda self: fields.Date.today().replace(day=1),
    )
    date_to = fields.Date(
        string='To',
        required=True,
        default=fields.Date.today,
    )
    clearing_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Clearing Account',
        compute='_compute_clearing_account_id',
        readonly=False,
        store=False,
    )

    # ── Results ───────────────────────────────────────────────────────────────
    total_credited = fields.Monetary(
        string='Total Accrued (CR)',
        currency_field='currency_id',
        readonly=True,
    )
    total_debited = fields.Monetary(
        string='Total Cleared by Payroll (DR)',
        currency_field='currency_id',
        readonly=True,
    )
    outstanding_balance = fields.Monetary(
        string='Outstanding Balance',
        currency_field='currency_id',
        readonly=True,
        help='Positive = payroll has not yet cleared this amount. '
             'Should be zero after payroll run.',
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        related='company_id.currency_id',
    )
    line_ids = fields.One2many(
        comodel_name='mrp.labor.clearing.check.line',
        inverse_name='wizard_id',
        string='Detail Lines',
        readonly=True,
    )

    @api.depends('company_id')
    def _compute_clearing_account_id(self):
        for wiz in self:
            wiz.clearing_account_id = wiz.company_id.labor_clearing_account_id

    def action_check(self):
        """Compute clearing account balance and populate line_ids."""
        self.ensure_one()
        self.line_ids.unlink()

        if not self.clearing_account_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'No Clearing Account',
                    'message': 'No Labor Clearing Account configured for this company.',
                    'type': 'warning',
                    'sticky': False,
                },
            }

        domain = [
            ('account_id', '=', self.clearing_account_id.id),
            ('parent_state', '=', 'posted'),
            ('company_id', '=', self.company_id.id),
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
        ]
        lines = self.env['account.move.line'].search(domain, order='date asc')

        total_cr = sum(lines.mapped('credit'))
        total_dr = sum(lines.mapped('debit'))
        self.total_credited = total_cr
        self.total_debited = total_dr
        self.outstanding_balance = total_cr - total_dr

        # Group by month
        months = {}
        for aml in lines:
            key = aml.date.strftime('%Y-%m')
            if key not in months:
                months[key] = {'debit': 0.0, 'credit': 0.0, 'label': aml.date.strftime('%B %Y')}
            months[key]['debit'] += aml.debit
            months[key]['credit'] += aml.credit

        line_vals = []
        for key in sorted(months):
            m = months[key]
            line_vals.append({
                'wizard_id': self.id,
                'period': m['label'],
                'total_credited': m['credit'],
                'total_debited': m['debit'],
                'outstanding_balance': m['credit'] - m['debit'],
            })
        self.env['mrp.labor.clearing.check.line'].create(line_vals)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.labor.clearing.check.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }


class LaborClearingCheckLine(models.TransientModel):
    _name = 'mrp.labor.clearing.check.line'
    _description = 'Labor Clearing Check Detail Line'

    wizard_id = fields.Many2one(
        comodel_name='mrp.labor.clearing.check.wizard',
        ondelete='cascade',
    )
    period = fields.Char(string='Period', readonly=True)
    total_credited = fields.Monetary(
        string='Accrued (CR)',
        currency_field='currency_id',
        readonly=True,
    )
    total_debited = fields.Monetary(
        string='Cleared by Payroll (DR)',
        currency_field='currency_id',
        readonly=True,
    )
    outstanding_balance = fields.Monetary(
        string='Outstanding',
        currency_field='currency_id',
        readonly=True,
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        related='wizard_id.currency_id',
    )
