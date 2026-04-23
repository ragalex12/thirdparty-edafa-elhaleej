# Copyright 2026
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    gpc_project_issue_journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="GPC project issue journal",
        check_company=True,
        domain="[('company_id', '=', id)]",
        help="Journal for Task 5 GPC project issue entries. If empty, the company stock journal is used.",
    )
    gpc_project_issue_debit_account_id = fields.Many2one(
        comodel_name="account.account",
        string="GPC project issue debit account",
        check_company=True,
        help="Debit line (project / WIP / expense) for Phase 1 project material issues from stock. "
        "The credit line uses the inventory stock valuation account from the transfer’s valued moves.",
    )
