# -*- coding: utf-8 -*-

from odoo import fields, models


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    # ── Task 50 – Optional per-workcenter labor account override ─────────────
    labor_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Labor Account (Override)',
        check_company=True,
        help='Optional. When set, timesheet lines on work orders for this '
             'workcenter will debit this account instead of the company '
             'Labor WIP Account.',
    )
