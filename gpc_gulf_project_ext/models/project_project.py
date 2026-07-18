# Copyright 2026 GPC
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = "project.project"

    contract_amount = fields.Monetary(
        string="Contract Amount / مبلغ التعاقد",
        currency_field="currency_id",
        tracking=True,
        groups="project.group_project_manager",
    )
    project_valuebvat = fields.Float(groups="project.group_project_manager")
    project_valueavat = fields.Float(groups="project.group_project_manager")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "contract_amount" in vals and "project_valuebvat" not in vals:
                vals["project_valuebvat"] = vals["contract_amount"]
            elif "project_valuebvat" in vals and "contract_amount" not in vals:
                vals["contract_amount"] = vals["project_valuebvat"]
        return super().create(vals_list)

    def write(self, vals):
        if self.env.context.get("gpc_skip_contract_sync"):
            return super().write(vals)

        if "contract_amount" in vals and "project_valuebvat" not in vals:
            vals = dict(vals, project_valuebvat=vals["contract_amount"])
        elif "project_valuebvat" in vals and "contract_amount" not in vals:
            vals = dict(vals, contract_amount=vals["project_valuebvat"])

        return super().write(vals)

    def get_panel_data(self):
        panel_data = super().get_panel_data()
        if not panel_data:
            return panel_data
        panel_data.update({
            "show_project_details": True,
            "description": self.description or False,
        })
        if self.env.user.has_group("project.group_project_manager"):
            panel_data.update({
                "show_contract_amount": True,
                "contract_amount": self.contract_amount or 0.0,
            })
        else:
            panel_data["show_contract_amount"] = False
        return panel_data
