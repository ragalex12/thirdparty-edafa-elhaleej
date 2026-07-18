# Copyright 2026
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

# Set ir.config_parameter key to "1" to log per-line analytic resolution when generating draft moves.
_DEBUG_ANALYTIC_PARAM = "gpc_hr_timesheet_labor_accrual.debug_analytic"


class LaborAccrualBatch(models.Model):
    _name = "labor.accrual.batch"
    _description = "Labor Accrual Batch"
    _order = "period_start desc, id desc"

    @api.model
    def _blocking_batch_for_period(self, company_id, period_key):
        """Return a draft or posted batch for the same company and period key, if any."""
        if not company_id or not period_key:
            return self.browse()
        return self.search(
            [
                ("company_id", "=", company_id),
                ("period_key", "=", period_key),
                ("state", "in", ("draft", "posted")),
            ],
            limit=1,
        )

    name = fields.Char(
        required=True,
        help="Short label for this accrual run (e.g. month and company).",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    period_key = fields.Char(
        string="Period key",
        required=True,
        index=True,
        help="Stable identifier for the accrual month, typically YYYY-MM. "
        "Together with company, must be unique among draft and posted batches.",
    )
    period_start = fields.Date(
        string="Period start",
        required=True,
        index=True,
        help="First calendar day included in this accrual (inclusive).",
    )
    period_end = fields.Date(
        string="Period end",
        required=True,
        index=True,
        help="Last calendar day included in this accrual (inclusive).",
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("posted", "Posted"),
            ("cancelled", "Cancelled"),
        ],
        string="State",
        default="draft",
        required=True,
        copy=False,
    )
    move_id = fields.Many2one(
        comodel_name="account.move",
        string="Journal entry",
        readonly=True,
        copy=False,
        help="Draft or posted journal entry for this batch, once generated.",
    )
    reversal_move_id = fields.Many2one(
        comodel_name="account.move",
        string="Reversal entry",
        readonly=True,
        copy=False,
        help="Posted reversal move created when this batch was reversed for correction.",
    )
    reversed_at = fields.Datetime(
        string="Reversed on",
        readonly=True,
        copy=False,
    )
    reversed_by = fields.Many2one(
        comodel_name="res.users",
        string="Reversed by",
        readonly=True,
        copy=False,
    )
    posted_at = fields.Datetime(
        string="Posted on",
        readonly=True,
        copy=False,
        help="When the journal entry was posted (if applicable).",
    )
    posted_by = fields.Many2one(
        comodel_name="res.users",
        string="Posted by",
        readonly=True,
        copy=False,
        help="User who posted the journal entry.",
    )
    line_ids = fields.One2many(
        comodel_name="labor.accrual.batch.line",
        inverse_name="batch_id",
        string="Lines",
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="company_id.currency_id",
        store=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            pk = vals.get("period_key")
            if isinstance(pk, str):
                vals["period_key"] = pk.strip()
        return super().create(vals_list)

    def write(self, vals):
        vals = dict(vals)
        pk = vals.get("period_key")
        if isinstance(pk, str):
            vals["period_key"] = pk.strip()
        return super().write(vals)

    @api.constrains("company_id", "period_key", "state")
    def _check_at_most_one_active_batch_per_period(self):
        """Phase 1: only one draft or posted batch per company + period_key."""
        for rec in self:
            if rec.state not in ("draft", "posted"):
                continue
            key = (rec.period_key or "").strip()
            if not key:
                raise ValidationError(_("Period key is required for draft and posted batches."))
            other = self.search(
                [
                    ("id", "!=", rec.id),
                    ("company_id", "=", rec.company_id.id),
                    ("period_key", "=", key),
                    ("state", "in", ("draft", "posted")),
                ],
                limit=1,
            )
            if other:
                raise ValidationError(
                    _(
                        "An active labor accrual batch already exists for this company and period "
                        "(%(key)s): %(name)s (%(state)s). Open that batch, or reverse a posted batch "
                        "to release the period."
                    )
                    % {"key": key, "name": other.name, "state": other.state}
                )

    def _get_eligible_timesheet_domain(self):
        """Domain for timesheet analytic lines included in this accrual (Phase 1)."""
        self.ensure_one()
        company = self.company_id
        AAL = self.env["account.analytic.line"]
        domain = [
            ("company_id", "=", company.id),
            ("date", ">=", self.period_start),
            ("date", "<=", self.period_end),
            ("employee_id", "!=", False),
            ("project_id", "!=", False),
            ("unit_amount", ">", 0),
        ]
        if "validated" in AAL._fields:
            domain.append(("validated", "=", True))
        else:
            _logger.warning(
                "gpc_hr_timesheet_labor_accrual: account.analytic.line has no 'validated' "
                "field; accrual selection does not filter on validation. "
                "Confirm hr_timesheet / approval is installed and fields match this Odoo version."
            )
        if "mrp_production_id" in AAL._fields:
            domain.append(("mrp_production_id", "=", False))
        return domain

    def _get_labor_amount_for_line(self, analytic_line):
        """Resolve monetary amount from mrp_timesheet labor_cost when present."""
        self.ensure_one()
        currency = self.company_id.currency_id
        amount = 0.0
        if "labor_cost" in analytic_line._fields:
            amount = analytic_line.labor_cost or 0.0
        if currency:
            amount = currency.round(amount)
        return amount

    def action_populate_lines(self):
        """Replace batch lines from eligible timesheet lines (no journal entry)."""
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft batches can be populated."))
        if not self.period_start or not self.period_end:
            raise UserError(_("Period start and end are required."))
        if self.period_start > self.period_end:
            raise UserError(_("Period start must be on or before period end."))

        self.line_ids.unlink()
        domain = self._get_eligible_timesheet_domain()
        analytic_lines = self.env["account.analytic.line"].search(domain)
        BatchLine = self.env["labor.accrual.batch.line"]

        for aal in analytic_lines:
            amount = self._get_labor_amount_for_line(aal)
            if amount <= 0.0:
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
        return True

    def _get_company_labor_accrual_config(self):
        """Return (debit_account, credit_account, journal) or raise UserError if incomplete."""
        self.ensure_one()
        company = self.company_id
        debit = company.labor_accrual_debit_account_id
        credit = company.labor_accrual_credit_account_id
        journal = company.labor_accrual_journal_id
        missing = []
        if not debit:
            missing.append(_("Labor accrual debit account"))
        if not credit:
            missing.append(_("Labor accrual credit account"))
        if not journal:
            missing.append(_("Labor accrual journal"))
        if missing:
            raise UserError(
                _(
                    "Configure the following on company '%(company)s' before generating "
                    "a labor accrual entry: %(fields)s."
                )
                % {"company": company.display_name, "fields": ", ".join(missing)}
            )
        return debit, credit, journal

    def _get_labor_accrual_move_total(self):
        self.ensure_one()
        currency = self.company_id.currency_id
        total = sum(self.line_ids.mapped("amount"))
        if currency:
            total = currency.round(total)
        return total

    def _labor_accrual_analytic_debug_enabled(self):
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(_DEBUG_ANALYTIC_PARAM, "0")
            in ("1", "true", "True", "yes", "Yes")
        )

    def _labor_accrual_log_analytic_resolution(
        self,
        batch_line,
        ts,
        project,
        selected_aa,
        source,
        ts_account_ids,
        project_account_ids,
    ):
        if not self._labor_accrual_analytic_debug_enabled():
            return
        _logger.info(
            "Labor accrual analytic resolve | batch_id=%s batch_line_id=%s timesheet_id=%s "
            "project_id=%s selected_analytic_account_id=%s source=%s "
            "timesheet_analytic_account_ids=%s project_analytic_account_ids=%s",
            self.id,
            batch_line.id,
            ts.id if ts else None,
            project.id if project else None,
            selected_aa.id if selected_aa else False,
            source,
            ts_account_ids,
            project_account_ids,
        )

    def _get_single_analytic_account_for_labor_accrual_line(self, batch_line):
        """Return (analytic_account | empty, source_label).

        Business rule: **exactly one** analytic account per accrual source line.
        Priority:
          1. Timesheet line — ``_get_analytic_accounts()`` must contain 0 or 1 account;
             if >1 → :class:`UserError` (no silent collapse / composite keys).
          2. Project ``account_id`` (primary project analytic on ``project.project``).
          3. Else other project plan columns via ``_get_analytic_accounts()`` — again 0 or 1 only.

        Task / employee are **not** consulted here (timesheet already embeds project/task context in Odoo).

        :returns: (record ``account.analytic.account`` or empty, str source tag)
        """
        self.ensure_one()
        ts = batch_line.timesheet_line_id
        project = batch_line.project_id
        empty_aa = self.env["account.analytic.account"].browse()

        if ts and hasattr(ts, "_get_analytic_accounts"):
            ts_accs = ts._get_analytic_accounts()
            ts_ids = ts_accs.ids
            if len(ts_accs) > 1:
                self._labor_accrual_log_analytic_resolution(
                    batch_line, ts, project, empty_aa, "conflict_timesheet", ts_ids, []
                )
                raise UserError(
                    _(
                        "Labor accrual cannot build this journal entry: timesheet line “%(ts)s” "
                        "resolves to multiple analytic accounts (%(ids)s). "
                        "Business rule: one analytic account per accrual line. "
                        "Split the timesheet or leave a single analytic on the line."
                    )
                    % {"ts": ts.display_name, "ids": ", ".join(map(str, ts_ids))}
                )
            if len(ts_accs) == 1:
                aa = ts_accs[0]
                self._labor_accrual_log_analytic_resolution(
                    batch_line, ts, project, aa, "timesheet", ts_ids, []
                )
                return aa, "timesheet"

        proj_ids = []
        if project:
            if project.account_id:
                aa = project.account_id
                self._labor_accrual_log_analytic_resolution(
                    batch_line, ts, project, aa, "project.account_id", [], [aa.id]
                )
                return aa, "project.account_id"
            if hasattr(project, "_get_analytic_accounts"):
                paccs = project._get_analytic_accounts()
                proj_ids = paccs.ids
                if len(paccs) > 1:
                    self._labor_accrual_log_analytic_resolution(
                        batch_line, ts, project, empty_aa, "conflict_project", [], proj_ids
                    )
                    raise UserError(
                        _(
                            "Labor accrual cannot build this journal entry: project “%(proj)s” "
                            "has multiple analytic accounts (%(ids)s) and no single "
                            "“Project Account” (account_id) is set. "
                            "Set one project analytic account or reduce analytic plans to one."
                        )
                        % {"proj": project.display_name, "ids": ", ".join(map(str, proj_ids))}
                    )
                if len(paccs) == 1:
                    aa = paccs[0]
                    self._labor_accrual_log_analytic_resolution(
                        batch_line, ts, project, aa, "project.other_plan", [], proj_ids
                    )
                    return aa, "project.other_plan"

        self._labor_accrual_log_analytic_resolution(
            batch_line, ts, project, empty_aa, "none", [], proj_ids
        )
        return empty_aa, "none"

    def _get_analytic_distribution_for_batch_line(self, batch_line):
        """Return ``{str(account_id): 100.0}`` for **one** analytic account, or ``None``.

        Never returns composite keys (e.g. ``\"54,55\"``) or multiple top-level keys.
        """
        aa, _src = self._get_single_analytic_account_for_labor_accrual_line(batch_line)
        if aa:
            return {str(aa.id): 100.0}
        return None

    def _prepare_labor_accrual_move_vals(self, debit_account, credit_account, journal, total):
        """Build vals for one miscellaneous entry.

        Debit side: one line per unique analytic distribution group (grouped from batch lines).
        Credit side: one aggregated offset line without analytic (clearing/WIP account).
        Rounding: last debit group absorbs any cent difference so debit total == credit total.
        """
        self.ensure_one()
        company = self.company_id
        currency = company.currency_id
        ref = _("Labor accrual - %(name)s (%(period)s)") % {
            "name": self.name,
            "period": self.period_key or self.period_start,
        }
        narration = _(
            "Labor accrual batch %(batch_id)s.\n"
            "Name: %(name)s\n"
            "Company: %(company)s\n"
            "Period: %(start)s → %(end)s (key: %(key)s)\n"
            "Total labor amount from batch lines: %(total)s %(cur)s"
        ) % {
            "batch_id": self.id,
            "name": self.name,
            "company": company.display_name,
            "start": self.period_start,
            "end": self.period_end,
            "key": self.period_key or "",
            "total": total,
            "cur": currency.name if currency else "",
        }
        line_common = {
            "currency_id": currency.id if currency else False,
        }

        # Group batch lines by analytic distribution key so each analytic gets its own debit line.
        # key: tuple of sorted distribution items (hashable) → [running_amount, dist_dict_or_None]
        analytic_groups = {}
        for batch_line in self.line_ids:
            dist = self._get_analytic_distribution_for_batch_line(batch_line)
            group_key = tuple(sorted(dist.items())) if dist else None
            if group_key not in analytic_groups:
                analytic_groups[group_key] = [0.0, dist]
            analytic_groups[group_key][0] += batch_line.amount

        # Round each group amount; adjust the last group to guarantee debit == credit.
        group_entries = list(analytic_groups.values())
        if currency:
            for entry in group_entries:
                entry[0] = currency.round(entry[0])
            rounded_sum = sum(e[0] for e in group_entries)
            if rounded_sum != total and group_entries:
                group_entries[-1][0] = currency.round(
                    group_entries[-1][0] + (total - rounded_sum)
                )

        line_ids = []
        for group_amount, dist in group_entries:
            debit_line = {
                **line_common,
                "account_id": debit_account.id,
                "name": _("Labor accrual expense (batch total)"),
                "debit": group_amount,
                "credit": 0.0,
            }
            if dist:
                debit_line["analytic_distribution"] = dist
            if self._labor_accrual_analytic_debug_enabled():
                _logger.info(
                    "Labor accrual draft JE debit line vals | batch_id=%s amount=%s "
                    "analytic_distribution=%s group_key=%s",
                    self.id,
                    group_amount,
                    debit_line.get("analytic_distribution"),
                    tuple(sorted(dist.items())) if dist else None,
                )
            line_ids.append((0, 0, debit_line))

        line_ids.append((
            0, 0, {
                **line_common,
                "account_id": credit_account.id,
                "name": _("Labor accrual offset (batch total)"),
                "debit": 0.0,
                "credit": total,
            }
        ))

        return {
            "move_type": "entry",
            "journal_id": journal.id,
            "company_id": company.id,
            "currency_id": currency.id if currency else False,
            "date": self.period_end,
            "ref": ref[:256] if len(ref) > 256 else ref,
            "narration": narration,
            "line_ids": line_ids,
        }

    def action_generate_draft_move(self):
        """Create a draft account.move from batch lines (no posting)."""
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft batches can generate a journal entry."))
        if not self.line_ids:
            raise UserError(
                _("Populate batch lines first (there must be at least one line with a positive amount).")
            )
        total = self._get_labor_accrual_move_total()
        if total <= 0.0:
            raise UserError(
                _("The batch total amount must be greater than zero to generate an entry.")
            )

        debit_account, credit_account, journal = self._get_company_labor_accrual_config()

        if self.move_id:
            move = self.move_id
            if move.state != "draft":
                raise UserError(
                    _("This batch already has a journal entry that is not in draft. Remove or reverse it before generating a new one.")
                )
            self.move_id = False
            move.unlink()

        vals = self._prepare_labor_accrual_move_vals(
            debit_account, credit_account, journal, total
        )
        if self._labor_accrual_analytic_debug_enabled():
            _logger.info(
                "Labor accrual draft move vals preview | batch_id=%s total=%s line_commands=%s",
                self.id,
                total,
                [
                    (cmd[2].get("debit"), cmd[2].get("credit"), cmd[2].get("analytic_distribution"))
                    for cmd in vals.get("line_ids", [])
                    if cmd[0] == 0 and isinstance(cmd[2], dict)
                ],
            )
        move = self.env["account.move"].create(vals)
        self.move_id = move
        return True

    def action_post_move(self):
        """Post the batch journal entry and mark the batch as posted."""
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft batches can post their journal entry."))
        move = self.move_id
        if not move:
            raise UserError(_("Generate a draft journal entry before posting."))
        if move.state != "draft":
            raise UserError(
                _("The journal entry is not in draft (current state: %s). It cannot be posted from this batch.")
                % (move.state,)
            )

        move.with_context(
            skip_tier_validation_state_on_write=True,
        )._post()

        self.write(
            {
                "state": "posted",
                "posted_at": fields.Datetime.now(),
                "posted_by": self.env.user.id,
            }
        )
        return True

    def action_reverse_for_regeneration(self):
        """Reverse the posted accrual move (standard Odoo), post the reversal, cancel this batch."""
        self.ensure_one()
        if self.state != "posted":
            raise UserError(_("Only posted batches can be reversed to release the period."))
        if self.reversal_move_id:
            raise UserError(_("This batch was already reversed."))
        move = self.move_id
        if not move:
            raise UserError(_("No journal entry to reverse."))
        if move.state != "posted":
            raise UserError(
                _("The journal entry must be posted to be reversed (current state: %s).")
                % (move.state,)
            )

        caller = "%s (uid=%s)" % (self.env.user.display_name, self.env.user.id)
        ref = (_("REV: labor accrual batch %s") % self.id)[:256]
        narration = _(
            "Standard reversal for labor accrual batch %(id)s, period %(period)s. %(caller)s"
        ) % {"id": self.id, "period": self.period_key or "", "caller": caller}

        reversals = move._reverse_moves(
            default_values_list=[
                {
                    "date": fields.Date.context_today(self),
                    "ref": ref,
                    "narration": narration,
                }
            ]
        )
        if not reversals:
            raise UserError(_("The reversal entry could not be created."))
        reversals.with_context(
            skip_tier_validation_state_on_write=True,
        )._post()

        self.write(
            {
                "state": "cancelled",
                "reversal_move_id": reversals[0].id,
                "reversed_at": fields.Datetime.now(),
                "reversed_by": self.env.user.id,
            }
        )
        return True
