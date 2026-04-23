# Copyright 2026
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import _, models
from odoo.exceptions import UserError


class StockMove(models.Model):
    _inherit = "stock.move"

    def _gpc_project_issue_get_stock_valuation_account(self):
        """Stock valuation (inventory) account for this move, aligned with stock_account product accounts.

        Task 5 Phase 1 compares this account across all included outgoing moves; the journal entry
        in a later step will use the same category-level stock valuation account as automatic
        inventory postings.
        """
        self.ensure_one()
        accounts = self.product_id._get_product_accounts()
        acc = accounts.get("stock_valuation")
        if not acc:
            raise UserError(
                _(
                    "Cannot determine a stock valuation account for product “%(product)s”. "
                    "Configure the product category’s stock valuation account (or company default).",
                    product=self.product_id.display_name,
                )
            )
        return acc
