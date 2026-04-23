# Copyright 2026
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    gpc_project_issue_enabled = fields.Boolean(
        string="Allow GPC project issue",
        default=False,
        copy=False,
        help="When enabled, transfers of this operation type can use the GPC project issue flow "
        "(Task 5): after validation, users may run the project issue wizard to build draft "
        "accounting entries linked to a project/analytic target. "
        "Leave disabled for operation types that must not participate in project material issue.",
    )
