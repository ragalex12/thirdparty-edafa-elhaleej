# -*- coding: utf-8 -*-

from odoo import fields, models


class ProjectProject(models.Model):
    _inherit = "project.project"

    exclude_from_payroll = fields.Boolean(
        string="Exclude from payroll",
        default=False,
        help="Explicit opt-out: timesheets on this project default to "
        "Include in Payroll = False. Leave unchecked so timesheets stay eligible.",
    )
