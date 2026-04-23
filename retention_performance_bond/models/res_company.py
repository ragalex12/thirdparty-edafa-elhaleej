# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    retention_receivable_account_id = fields.Many2one(
        "account.account",
        string="Retention Receivable (10%)",
        domain="[('account_type', 'in', ['asset_current', 'asset_receivable']), ('company_id', '=', id)]",
        help="Asset account for retention amounts. This represents the portion of invoice amount retained by the customer, typically 10% of the invoice total, to be collected later.",
    )
    performance_bond_receivable_account_id = fields.Many2one(
        "account.account",
        string="Performance Bonds Receivable",
        domain="[('account_type', 'in', ['asset_current', 'asset_receivable']), ('company_id', '=', id)]",
        help="Asset account for performance bond amounts. This represents amounts held as security for contract performance and quality assurance.",
    )
    deduction_balance_account_id = fields.Many2one(
        "account.account",
        string="Balance Account for journal entry",
        domain="[('company_id', '=', id)]",
        help="Account used as credit side (balance account) in deduction journal entries. Can be receivable, revenue, or any other account type.",
    )
