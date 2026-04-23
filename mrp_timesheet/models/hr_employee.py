# -*- coding: utf-8 -*-

from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    hourly_cost = fields.Monetary(
        string='Hourly Cost',
        currency_field='currency_id',
        help='Cost per hour used for timesheet and manufacturing labor costing (e.g. when logging time on a Manufacturing Order).',
    )
    currency_id = fields.Many2one(
        related='company_id.currency_id',
        depends=['company_id'],
    )
