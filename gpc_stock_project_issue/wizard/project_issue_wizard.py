# Copyright 2026
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import _, api, fields, models


class GpcProjectIssueWizard(models.TransientModel):
    _name = "gpc.project.issue.wizard"
    _description = "Project Issue from Stock (Task 5)"

    picking_id = fields.Many2one(
        comodel_name="stock.picking",
        string="Transfer",
        required=True,
        readonly=True,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        pid = self.env.context.get("default_picking_id")
        if pid:
            res["picking_id"] = pid
        return res

    def action_create_draft_journal_entry(self):
        """Create the Task 5 draft account.move and open it."""
        self.ensure_one()
        move = self.picking_id._gpc_project_issue_create_draft_journal_entry()
        return {
            "type": "ir.actions.act_window",
            "name": _("Draft journal entry"),
            "res_model": "account.move",
            "res_id": move.id,
            "view_mode": "form",
            "target": "current",
            "context": {"create": False},
        }
