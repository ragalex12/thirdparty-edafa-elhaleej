# Copyright 2026 GPC
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _prepare_product_base_line_for_taxes_computation(self, product_line):
        self.ensure_one()
        is_invoice = self.is_invoice(include_receipts=True)
        sign = self.direction_sign if is_invoice else 1
        if is_invoice:
            rate = self.invoice_currency_rate
        else:
            rate = (
                (abs(product_line.amount_currency) / abs(product_line.balance))
                if product_line.balance
                else 0.0
            )

        quantity = product_line.quantity if is_invoice else 1.0
        if (
            is_invoice
            and product_line.display_type == "product"
            and hasattr(product_line, "_gpc_effective_quantity")
        ):
            quantity = product_line._gpc_effective_quantity()

        return self.env["account.tax"]._prepare_base_line_for_taxes_computation(
            product_line,
            price_unit=product_line.price_unit if is_invoice else product_line.amount_currency,
            quantity=quantity,
            discount=product_line.discount if is_invoice else 0.0,
            rate=rate,
            sign=sign,
            special_mode=False if is_invoice else "total_excluded",
        )
