# Copyright 2026 GPC
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    length_cm = fields.Float(
        string="Length (CM) / الطول",
        digits=(16, 2),
    )
    width_cm = fields.Float(
        string="Width/Height (CM) / العرض",
        digits=(16, 2),
    )
    area_sqm = fields.Float(
        string="Area (M²) / المساحة",
        compute="_compute_area_sqm",
        store=True,
        digits=(16, 4),
    )

    @api.depends("length_cm", "width_cm")
    def _compute_area_sqm(self):
        for line in self:
            if line.length_cm and line.width_cm:
                line.area_sqm = (line.length_cm * line.width_cm) / 10000.0
            else:
                line.area_sqm = 1.0

    def _gpc_effective_quantity(self):
        self.ensure_one()
        return self.product_uom_qty * (self.area_sqm or 1.0)

    def _prepare_base_line_for_taxes_computation(self, **kwargs):
        self.ensure_one()
        if not self.display_type:
            kwargs.setdefault("quantity", self._gpc_effective_quantity())
        return super()._prepare_base_line_for_taxes_computation(**kwargs)

    @api.depends(
        "product_uom_qty",
        "discount",
        "price_unit",
        "tax_ids",
        "length_cm",
        "width_cm",
        "area_sqm",
    )
    def _compute_amount(self):
        return super()._compute_amount()

    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line(**optional_values)
        if not self.display_type:
            res.update({
                "length_cm": self.length_cm,
                "width_cm": self.width_cm,
                "area_sqm": self.area_sqm,
            })
        return res
