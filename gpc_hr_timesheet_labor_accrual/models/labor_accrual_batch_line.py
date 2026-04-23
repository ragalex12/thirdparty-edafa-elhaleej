# Copyright 2026
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import fields, models


class LaborAccrualBatchLine(models.Model):
    _name = "labor.accrual.batch.line"
    _description = "Labor Accrual Batch Line"
    _sql_constraints = [
        (
            "labor_accrual_batch_line_batch_timesheet_uniq",
            "UNIQUE(batch_id, timesheet_line_id)",
            "Each timesheet line can only appear once in a batch.",
        ),
    ]

    batch_id = fields.Many2one(
        comodel_name="labor.accrual.batch",
        string="Batch",
        required=True,
        ondelete="cascade",
        index=True,
    )
    timesheet_line_id = fields.Many2one(
        comodel_name="account.analytic.line",
        string="Timesheet line",
        required=True,
        ondelete="restrict",
        index=True,
    )
    amount = fields.Monetary(
        help="Labor amount taken from timesheet labor cost when available.",
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="batch_id.currency_id",
        store=True,
    )
    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Employee (snapshot)",
        readonly=True,
        help="Employee on the timesheet line at generation time.",
    )
    project_id = fields.Many2one(
        comodel_name="project.project",
        string="Project (snapshot)",
        readonly=True,
        help="Project on the timesheet line at generation time.",
    )
    line_date = fields.Date(
        string="Line date (snapshot)",
        readonly=True,
        help="Date of the analytic line at generation time.",
    )
