# Copyright 2026
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import api, fields, models
from odoo.tools import float_compare


class AnalyticProjectStatementWizard(models.TransientModel):
    _name = "analytic.project.statement.wizard"
    _description = "Analytic Project Statement Wizard"

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    date_from = fields.Date(
        string="Date from",
        required=True,
        default=lambda self: self._default_date_from(),
    )
    date_to = fields.Date(
        string="Date to",
        required=True,
        default=lambda self: self._default_date_to(),
    )
    target_move = fields.Selection(
        selection=[
            ("posted", "All posted entries"),
            ("all", "All entries"),
        ],
        string="Target moves",
        required=True,
        default="posted",
    )
    journal_ids = fields.Many2many(
        comodel_name="account.journal",
        string="Journals",
        help="Leave empty to include all journals.",
    )
    account_ids = fields.Many2many(
        comodel_name="account.account",
        string="Accounts",
        help="Leave empty to include all accounts.",
    )
    analytic_account_ids = fields.Many2many(
        comodel_name="account.analytic.account",
        string="Projects / analytic accounts",
        help="Leave empty to include all analytic accounts present on lines.",
    )

    @api.model
    def _default_date_from(self):
        today = fields.Date.context_today(self)
        return today.replace(month=1, day=1)

    @api.model
    def _default_date_to(self):
        return fields.Date.context_today(self)

    def _get_aml_domain(self):
        """Search domain for candidate journal items (no analytic slicing yet).

        Do **not** put ``analytic_distribution`` in the domain: on JSON fields,
        ``("analytic_distribution", "!=", False)`` does not reliably exclude
        empty values in SQL, while :meth:`_get_aml_source_recordset` filters in
        Python to lines with a non-empty distribution map.

        Optional wizard filters narrow further; analytic account matching is
        applied in :meth:`_get_aml_source_recordset`.
        """
        self.ensure_one()
        domain = [
            ("company_id", "=", self.company_id.id),
            ("date", ">=", self.date_from),
            ("date", "<=", self.date_to),
            ("display_type", "not in", ("line_section", "line_note")),
        ]
        if self.target_move == "posted":
            domain.append(("move_id.state", "=", "posted"))
        else:
            domain.append(("move_id.state", "in", ("draft", "posted")))
        if self.journal_ids:
            domain.append(("journal_id", "in", self.journal_ids.ids))
        if self.account_ids:
            domain.append(("account_id", "in", self.account_ids.ids))
        return domain

    def _aml_line_matches_analytic_filter(self, line):
        """Return whether ``line`` should be kept for selected analytic accounts.

        When no analytic filter is set, any line with a non-empty distribution
        matches. Otherwise at least one key in ``analytic_distribution`` must
        resolve to a selected analytic account (supports compound keys ``a,b``).
        """
        self.ensure_one()
        if not self.analytic_account_ids:
            return True
        wanted = frozenset(self.analytic_account_ids.ids)
        distribution = line.analytic_distribution
        if not distribution:
            return False
        for key in distribution:
            for part in key.split(","):
                part = part.strip()
                if not part:
                    continue
                try:
                    account_id = int(part)
                except ValueError:
                    continue
                if account_id in wanted:
                    return True
        return False

    def _distribution_key_matches_analytic_filter(self, distribution_key):
        """Whether a single ``analytic_distribution`` map key passes the filter."""
        self.ensure_one()
        if not self.analytic_account_ids:
            return True
        wanted = frozenset(self.analytic_account_ids.ids)
        for part in distribution_key.split(","):
            part = part.strip()
            if not part:
                continue
            try:
                account_id = int(part)
            except ValueError:
                continue
            if account_id in wanted:
                return True
        return False

    def _get_aml_source_recordset(self):
        """Candidate ``account.move.line`` records for the report (pre-slicing).

        Applies :meth:`_get_aml_domain` then drops lines without usable
        distribution and applies the optional analytic account filter.
        """
        self.ensure_one()
        MoveLine = self.env["account.move.line"]
        aml = MoveLine.search(self._get_aml_domain())
        aml = aml.filtered(lambda line: bool(line.analytic_distribution))
        if self.analytic_account_ids:
            aml = aml.filtered(lambda line: self._aml_line_matches_analytic_filter(line))
        return aml

    def _aal_matches_wizard_filters(self, aal):
        """Whether an analytic line passes optional wizard filters."""
        self.ensure_one()
        ml = aal.move_line_id
        if self.journal_ids:
            if not ml or ml.journal_id not in self.journal_ids:
                return False
        if self.account_ids:
            gacc = aal.general_account_id
            if not gacc or gacc not in self.account_ids:
                return False
        if self.target_move == "posted" and ml and ml.move_id.state != "posted":
            return False
        if self.target_move == "all" and ml and ml.move_id.state not in ("draft", "posted"):
            return False
        return True

    def _aal_amount_to_debit_credit(self, amount, currency):
        """Map ``account.analytic.line`` ``amount`` to debit/credit columns.

        Analytic amounts are signed: **negative** is an outflow / cost on the
        project; show that as **debit** so the statement mirrors GL-style
        expense debits. **Positive** amounts go to **credit**.
        """
        if currency.is_zero(amount):
            return 0.0, 0.0
        if amount < 0:
            return currency.round(-amount), 0.0
        return 0.0, currency.round(amount)

    def _get_aal_source_recordset(self):
        """``account.analytic.line`` rows that are not already covered by AML explosion.

        Many databases post journal lines **without** ``analytic_distribution`` on
        ``account.move.line`` while analytic planning exists only on analytic
        lines (often with no ``move_line_id``). Those lines would otherwise
        yield an empty export for an otherwise active project/company.
        """
        self.ensure_one()
        Aal = self.env["account.analytic.line"]
        domain = [
            ("company_id", "=", self.company_id.id),
            ("date", ">=", self.date_from),
            ("date", "<=", self.date_to),
        ]
        if self.analytic_account_ids:
            domain.append(("account_id", "in", self.analytic_account_ids.ids))
        lines = Aal.search(domain)
        kept_ids = []
        for aal in lines:
            if not self._aal_matches_wizard_filters(aal):
                continue
            ml = aal.move_line_id
            if ml and ml.analytic_distribution:
                continue
            kept_ids.append(aal.id)
        return Aal.browse(kept_ids)

    def _line_currency(self, line):
        """Company currency for rounding allocated amounts."""
        return line.company_id.currency_id

    def _normalize_distribution_ratios(self, ratios, amount, currency):
        """Scale ratios to Odoo’s percentage convention (each weight 0–100, sum ~100).

        Imports or integrations sometimes store **fractional** weights summing to
        ``1`` (e.g. ``0.6`` / ``0.4``). Treating those as ``6%`` / ``4%`` makes
        tiny slices that round to **zero** in Excel.

        Also coerce JSON values to ``float`` (they may arrive as strings).
        """
        if not ratios:
            return ratios
        ratios = [float(r) for r in ratios]
        total = sum(ratios)
        if not total:
            return ratios
        # Fractional multipliers (sum ~1) → same shape as UI percentages (~100).
        # (Single-key ``{id: 1}`` can mean 1% on a percentage scale — do not remap.)
        if len(ratios) > 1 and float_compare(total, 1.0, 6) <= 0:
            return [r * 100.0 for r in ratios]
        return ratios

    def _split_line_amount_by_distribution_percentages(self, amount, percentages, currency):
        """Split a column total using Odoo-style analytic percentages (0–100 each).

        Each slice is ``amount * (p / 100)``. Percentages are **always** taken
        against 100 (not renormalized when only some keys are kept after the
        analytic filter). The last slice absorbs rounding drift so the parts
        sum to ``currency.round(amount)``.
        """
        if not percentages:
            return []
        percentages = self._normalize_distribution_ratios(percentages, amount, currency)
        if len(percentages) == 1:
            return [currency.round(amount * (percentages[0] / 100.0))]
        rounded_total = currency.round(amount)
        parts = []
        allocated = 0.0
        for p in percentages[:-1]:
            part = currency.round(amount * (p / 100.0))
            parts.append(part)
            allocated += part
        parts.append(currency.round(rounded_total - allocated))
        return parts

    def _iter_sorted_distribution_items(self, distribution):
        """Yield ``(key, weight)`` in deterministic key order."""
        if not distribution:
            return
        for key in sorted(distribution.keys(), key=lambda k: (len(k), k)):
            yield key, distribution[key]

    def _filtered_distribution_keys_and_ratios(self, line):
        """Ordered keys and weights used for explosion (respects analytic filter)."""
        distribution = line.analytic_distribution or {}
        keys = []
        ratios = []
        for key, weight in self._iter_sorted_distribution_items(distribution):
            if self.analytic_account_ids and not self._distribution_key_matches_analytic_filter(
                key
            ):
                continue
            keys.append(key)
            ratios.append(weight)
        return keys, ratios

    def _format_project_label(self, distribution_key):
        """Value for the *project* column for one ``analytic_distribution`` key."""
        raw_ids = []
        for part in distribution_key.split(","):
            part = part.strip()
            if not part:
                continue
            try:
                raw_ids.append(int(part))
            except ValueError:
                continue
        if not raw_ids:
            return distribution_key
        accounts = self.env["account.analytic.account"].browse(raw_ids).exists()
        by_id = {a.id: a.display_name for a in accounts}
        labels = [by_id[i] for i in raw_ids if i in by_id]
        return " / ".join(labels) if labels else distribution_key

    def _aml_debit_credit_base(self, line, currency):
        """Debit/credit amounts to explode; use ``balance`` if both legs are zero."""
        debit = line.debit or 0.0
        credit = line.credit or 0.0
        if currency.is_zero(debit) and currency.is_zero(credit):
            bal = getattr(line, "balance", None)
            if bal is not None and not currency.is_zero(bal):
                if float_compare(bal, 0.0, currency.decimal_places) > 0:
                    return bal, 0.0
                return 0.0, -bal
        return debit, credit

    def _explode_line_to_row_dicts(self, line):
        """Return ``(distribution_key, row_dict)`` per analytic slice on ``line``.

        ``row_dict`` keys are exactly: date, move_name, project, account, debit,
        credit.
        """
        self.ensure_one()
        keys, ratios = self._filtered_distribution_keys_and_ratios(line)
        if not keys:
            return []

        currency = self._line_currency(line)
        base_debit, base_credit = self._aml_debit_credit_base(line, currency)
        debits = self._split_line_amount_by_distribution_percentages(
            base_debit, ratios, currency
        )
        credits = self._split_line_amount_by_distribution_percentages(
            base_credit, ratios, currency
        )
        move = line.move_id
        account_label = line.account_id.display_name or ""

        out = []
        for key, debit_amt, credit_amt in zip(keys, debits, credits):
            out.append(
                (
                    key,
                    {
                        "date": line.date,
                        "move_name": move.name or "",
                        "project": self._format_project_label(key),
                        "account": account_label,
                        "debit": debit_amt,
                        "credit": credit_amt,
                    },
                )
            )
        return out

    def _report_row_sort_key(self, line, distribution_key):
        """Stable ordering: date, move, line id, then distribution key."""
        return (
            line.date or fields.Date.from_string("1900-01-01"),
            line.move_id.id,
            line.id,
            len(distribution_key),
            distribution_key,
        )

    def _get_report_phase1_rows(self):
        """Ordered list of Phase 1 row dicts (six columns), one per slice.

        Combines exploded ``account.move.line`` rows (analytic distribution) with
        supplementary ``account.analytic.line`` rows when journal items carry no
        distribution map. Each dict has keys: ``date``, ``move_name``,
        ``project``, ``account``, ``debit``, ``credit``.
        """
        self.ensure_one()
        aml = self._get_aml_source_recordset().sorted(
            lambda l: (l.date, l.move_id.id, l.id)
        )
        staged = []
        for line in aml:
            for dist_key, row in self._explode_line_to_row_dicts(line):
                staged.append((self._report_row_sort_key(line, dist_key), row))
        currency = self.company_id.currency_id
        for aal in self._get_aal_source_recordset().sorted(lambda a: (a.date, a.id)):
            debit, credit = self._aal_amount_to_debit_credit(aal.amount, currency)
            gacc = aal.general_account_id
            account_label = gacc.display_name if gacc else ""
            project_label = aal.account_id.display_name if aal.account_id else ""
            if aal.move_line_id and aal.move_line_id.move_id:
                move_name = aal.move_line_id.move_id.name or ""
            elif aal.name:
                move_name = aal.name
            else:
                move_name = ""
            row = {
                "date": aal.date,
                "move_name": move_name,
                "project": project_label,
                "account": account_label,
                "debit": debit,
                "credit": credit,
            }
            # Sort after AML rows on the same day (AML keys use move_id as 2nd part).
            sort_key = (
                aal.date or fields.Date.from_string("1900-01-01"),
                10**9,
                aal.id,
                "",
            )
            staged.append((sort_key, row))
        staged.sort(key=lambda t: t[0])
        return [t[1] for t in staged]

    def action_export_xlsx(self):
        """Launch XLSX report (data building to be implemented later)."""
        self.ensure_one()
        return self.env.ref(
            "gpc_analytic_project_statement.action_report_analytic_project_statement_xlsx"
        ).report_action(self)
