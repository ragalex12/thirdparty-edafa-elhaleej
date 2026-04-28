# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    production_labor_expense_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Production Labor Expense Account',
        check_company=True,
        help='Expense account used when posting timesheet labor cost to manufacturing (credited in the labor journal entry).',
    )
