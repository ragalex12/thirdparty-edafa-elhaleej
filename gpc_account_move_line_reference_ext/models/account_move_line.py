# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    line_reference = fields.Char(
        string="Line Reference",
        store=True,
        help="Free-text reference for this journal item line.",
    )
    line_reference_number = fields.Char(
        string="Reference Number",
        store=True,
        help="Secondary free-text reference number for this journal item line.",
    )
    line_tax_number = fields.Char(
        string="Tax Number",
        store=True,
        help="Tax identification number for this journal item line.",
    )

    @api.onchange("partner_id")
    def _onchange_partner_id_line_tax_number(self):
        for line in self:
            if not line.line_tax_number and line.partner_id and line.partner_id.vat:
                line.line_tax_number = line.partner_id.vat
