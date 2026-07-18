# Copyright 2026 GPC
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

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
        digits=(16, 4),
        default=1.0,
    )

    def _gpc_effective_quantity(self):
        self.ensure_one()
        if self.display_type != "product":
            return self.quantity
        if self.length_cm and self.width_cm:
            area = (self.length_cm * self.width_cm) / 10000.0
        else:
            area = self.area_sqm or 1.0
        return self.quantity * area
