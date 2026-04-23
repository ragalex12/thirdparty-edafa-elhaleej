# Copyright 2026
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    labor_accrual_debit_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Labor accrual debit account",
        check_company=True,
        help="General ledger account debited on monthly labor accrual journal entries "
        "generated from validated non-MO timesheets (exact meaning follows your chart of "
        "accounts and finance sign-off, e.g. direct wages or labor expense).",
    )
    labor_accrual_credit_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Labor accrual credit account",
        check_company=True,
        help="General ledger account credited on monthly labor accrual journal entries "
        "(e.g. work in progress or labor clearing, per finance sign-off).",
    )
    labor_accrual_journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Labor accrual journal",
        check_company=True,
        help="Journal used for draft/posted labor accrual entries from timesheet batches. "
        "Typically a miscellaneous / general journal.",
    )
