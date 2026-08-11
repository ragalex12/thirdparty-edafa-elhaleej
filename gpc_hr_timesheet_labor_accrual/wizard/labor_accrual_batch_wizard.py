# Copyright 2026
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import _, fields, models
from odoo.exceptions import UserError


class LaborAccrualBatchWizard(models.TransientModel):
    _name = "labor.accrual.batch.wizard"
    _description = "Labor Accrual Batch Wizard"

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    period_start = fields.Date(
        string="Period start",
        required=True,
    )
    period_end = fields.Date(
        string="Period end",
        required=True,
    )

    def action_create_batch_and_populate_lines(self):
        """Create a draft batch for the period and populate lines from timesheets."""
        self.ensure_one()
        if self.period_start > self.period_end:
            raise UserError(_("Period start must be on or before period end."))
        if (self.period_start.year, self.period_start.month) != (
            self.period_end.year,
            self.period_end.month,
        ):
            raise UserError(
                _(
                    "Period start and end must be in the same calendar month so the "
                    "batch period key matches the populate date range."
                )
            )
        period_key = self.period_start.strftime("%Y-%m").strip()
        blocked = self.env["labor.accrual.batch"]._blocking_batch_for_period(
            self.company_id.id, period_key
        )
        if blocked:
            raise UserError(
                _(
                    "A labor accrual batch already exists for %(company)s and period %(period)s "
                    "(state: %(state)s). Open that batch, or use 'Reverse & release period' on a "
                    "posted batch to release the period before creating another run."
                )
                % {
                    "company": self.company_id.display_name,
                    "period": period_key,
                    "state": blocked.state,
                }
            )
        name = _("%(company)s — labor accrual %(period)s") % {
            "company": self.company_id.name,
            "period": period_key,
        }
        batch = self.env["labor.accrual.batch"].create(
            {
                "name": name,
                "company_id": self.company_id.id,
                "period_start": self.period_start,
                "period_end": self.period_end,
                "period_key": period_key,
                "state": "draft",
            }
        )
        batch.action_populate_lines()
        return {
            "type": "ir.actions.act_window",
            "res_model": "labor.accrual.batch",
            "res_id": batch.id,
            "view_mode": "form",
            "target": "current",
        }
