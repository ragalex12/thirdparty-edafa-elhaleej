# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    retention_receivable_account_id = fields.Many2one(
        "account.account",
        related="company_id.retention_receivable_account_id",
        readonly=False,
        string="Retention Account",
        domain="[('account_type', 'in', ['asset_current', 'asset_receivable'])]",
        help="Asset account for retention amounts. This represents the portion of invoice amount retained by the customer, typically 10% of the invoice total.",
    )
    performance_bonds_account_id = fields.Many2one(
        "account.account",
        related="company_id.performance_bond_receivable_account_id",
        readonly=False,
        string="Performance Bonds Account",
        domain="[('account_type', 'in', ['asset_current', 'asset_receivable'])]",
        help="Asset account for performance bond amounts. This represents amounts held as security for contract performance.",
    )
    deduction_balance_account_id = fields.Many2one(
        "account.account",
        related="company_id.deduction_balance_account_id",
        readonly=False,
        string="Balance Account for journal entry",
        domain="[]",
        help="Account used as credit side (balance account) in deduction journal entries. Can be receivable, revenue, or any other account type.",
    )