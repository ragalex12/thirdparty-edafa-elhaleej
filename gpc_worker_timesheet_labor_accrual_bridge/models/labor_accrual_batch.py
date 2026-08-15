# Copyright 2026
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

import logging

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class LaborAccrualBatch(models.Model):
    _inherit = "labor.accrual.batch"

    def _get_eligible_timesheet_domain(self):
        """Keep base domain and enforce worker payroll eligibility when available."""
        self.ensure_one()
        domain = list(super()._get_eligible_timesheet_domain())
        aal_fields = self.env["account.analytic.line"]._fields

        # Bridge rule (phase 1): when available, only payroll-included worker lines.
        if "include_in_payroll" in aal_fields:
            domain.append(("include_in_payroll", "=", True))

        # Phase 1 rule: include all work_status values (no extra domain yet).
        return domain

    def _get_worker_metre_amount(self, analytic_line):
        """Phase 2 extension hook for metre-based worker costing."""
        analytic_line.ensure_one()
        return 0.0

    def _get_worker_fallback_amount(self, analytic_line):
        """Worker fallback when labor_cost is unavailable/non-positive.

        Defensive checks avoid relying on optional fields that may not exist
        in every deployment.
        """
        analytic_line.ensure_one()
        unit_amount = getattr(analytic_line, "unit_amount", 0.0) or 0.0
        if unit_amount <= 0.0:
            return 0.0

        employee = getattr(analytic_line, "employee_id", False)
        if employee and "hourly_cost" in employee._fields:
            hourly_cost = employee.hourly_cost or 0.0
            if hourly_cost > 0.0:
                return unit_amount * hourly_cost

        return self._get_worker_metre_amount(analytic_line)

    def _get_labor_amount_for_line(self, analytic_line):
        """Bridge amount resolver with safe fallback priority."""
        self.ensure_one()

        amount = super()._get_labor_amount_for_line(analytic_line)
        if amount > 0.0:
            return amount

        if "labor_cost" in analytic_line._fields:
            line_labor_cost = analytic_line.labor_cost or 0.0
            if line_labor_cost > 0.0:
                amount = line_labor_cost
            else:
                amount = self._get_worker_fallback_amount(analytic_line)
        else:
            amount = self._get_worker_fallback_amount(analytic_line)

        currency = self.company_id.currency_id
        if currency:
            amount = currency.round(amount)
        return amount

    def action_populate_lines(self):
        """Replace batch lines and report debug counters/reasons."""
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft batches can be populated."))
        if not self.period_start or not self.period_end:
            raise UserError(_("Period start and end are required."))
        if self.period_start > self.period_end:
            raise UserError(_("Period start must be on or before period end."))

        AAL = self.env["account.analytic.line"]
        candidate_domain = [
            ("company_id", "=", self.company_id.id),
            ("date", ">=", self.period_start),
            ("date", "<=", self.period_end),
        ]
        candidate_count = AAL.search_count(candidate_domain)

        eligible_domain = self._get_eligible_timesheet_domain()
        analytic_lines = AAL.search(eligible_domain)
        eligible_count = len(analytic_lines)
        # Disabled per client request — 2026-08-15
        # analytic_lines, hour_skips = self._filter_timesheets_for_daily_hours(analytic_lines)
        hour_skips = []

        replaced_count = len(self.line_ids)
        self.line_ids.unlink()

        BatchLine = self.env["labor.accrual.batch.line"]
        skipped_zero_amount = 0
        skipped_reasons = list(hour_skips)
        created_count = 0

        for aal in analytic_lines:
            amount = self._get_labor_amount_for_line(aal)
            if amount <= 0.0:
                skipped_zero_amount += 1
                skipped_reasons.append(
                    {
                        "timesheet_line_id": aal.id,
                        "reason": "no_confirmed_amount_source_or_non_positive",
                    }
                )
                continue
            BatchLine.create(
                {
                    "batch_id": self.id,
                    "timesheet_line_id": aal.id,
                    "amount": amount,
                    "employee_id": aal.employee_id.id,
                    "project_id": aal.project_id.id,
                    "line_date": aal.date,
                }
            )
            created_count += 1

        _logger.info(
            (
                "Worker accrual populate summary | batch_id=%s | replaced=%s | "
                "candidates=%s | eligible=%s | skipped_zero_amount=%s | "
                "skipped_anomalous_hours=%s | created=%s"
            ),
            self.id,
            replaced_count,
            candidate_count,
            eligible_count,
            skipped_zero_amount,
            len(hour_skips),
            created_count,
        )
        if skipped_reasons:
            _logger.debug(
                "Worker accrual skipped reasons | batch_id=%s | samples=%s",
                self.id,
                skipped_reasons[:25],
            )

        return True

