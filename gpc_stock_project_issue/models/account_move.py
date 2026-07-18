# Copyright 2026
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    gpc_issue_picking_id = fields.Many2one(
        comodel_name="stock.picking",
        string="Project issue picking",
        copy=False,
        check_company=True,
        index=True,
        help="Picking this entry was generated for (Task 5 traceability).",
    )
