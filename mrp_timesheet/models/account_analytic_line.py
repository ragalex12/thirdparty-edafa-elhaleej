# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools import float_round

# Fields whose change should trigger JE reversal + regeneration
_COST_TRIGGER_FIELDS = frozenset({
    'unit_amount',
    'employee_id',
    'product_id',
    'is_overtime',
    'is_holiday',
    'date',
    'mrp_production_id',
    'company_id',
})


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    # ── MO linkage ────────────────────────────────────────────────────────────
    mrp_production_id = fields.Many2one(
        comodel_name='mrp.production',
        string='Manufacturing Order',
        index=True,
        ondelete='set null',
        help='Manufacturing order this timesheet line is linked to.',
    )

    # ── Task 54 – Overtime / Holiday flags ───────────────────────────────────
    is_overtime = fields.Boolean(
        string='Overtime',
        default=False,
        help='Applies the company Overtime Rate Multiplier to the hourly cost.',
    )
    is_holiday = fields.Boolean(
        string='Holiday',
        default=False,
        help='Applies the company Holiday Rate Multiplier (takes precedence over overtime).',
    )

    # ── Task 55 – Stored computed labor cost ─────────────────────────────────
    labor_cost_currency_id = fields.Many2one(
        comodel_name='res.currency',
        related='company_id.currency_id',
        string='Labor Cost Currency',
        store=True,
    )
    labor_cost = fields.Monetary(
        string='Labor Cost',
        compute='_compute_labor_cost',
        store=True,
        currency_field='labor_cost_currency_id',
        help='hours × hourly rate × multiplier, in company currency.',
    )

    # ── Task 58 – Per-line JE link ────────────────────────────────────────────
    labor_move_id = fields.Many2one(
        comodel_name='account.move',
        string='Labor Cost Journal Entry',
        copy=False,
        readonly=True,
        ondelete='set null',
        help='Journal entry automatically generated for this timesheet line\'s labor cost.',
    )

    # ── Compute labor_cost ────────────────────────────────────────────────────
    @api.depends(
        'unit_amount',
        'employee_id', 'employee_id.hourly_cost',
        'product_id', 'product_id.standard_price',
        'is_overtime', 'is_holiday',
        'company_id',
        'company_id.overtime_rate_multiplier',
        'company_id.holiday_rate_multiplier',
        'date',
    )
    def _compute_labor_cost(self):
        for line in self:
            line.labor_cost = line._get_labor_cost_amount()

    # =========================================================================
    # Task 66 – create() trigger
    # =========================================================================
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if self.env.context.get('skip_labor_je'):
            return records
        for line in records:
            if line._should_generate_labor_je():
                line._generate_labor_cost_move()
        return records

    # =========================================================================
    # Task 67 – write() trigger
    # =========================================================================
    def write(self, vals):
        if self.env.context.get('skip_labor_je'):
            return super().write(vals)

        cost_fields_changed = bool(_COST_TRIGGER_FIELDS & set(vals))
        if cost_fields_changed:
            # Reverse existing JEs before applying changes
            for line in self:
                if line.labor_move_id:
                    line._reverse_labor_cost_move()

        result = super().write(vals)

        if cost_fields_changed:
            # Regenerate JEs with new values
            for line in self:
                if line._should_generate_labor_je():
                    line._generate_labor_cost_move()

        return result

    # =========================================================================
    # Task 68 – unlink() trigger
    # =========================================================================
    def unlink(self):
        if not self.env.context.get('skip_labor_je'):
            for line in self:
                if line.labor_move_id:
                    line._reverse_labor_cost_move()
        return super().unlink()

    # =========================================================================
    # Helper: should this line generate a labor JE?
    # =========================================================================
    def _should_generate_labor_je(self):
        """Return True when this line qualifies for automatic JE generation.

        Conditions:
          - Not in skip_labor_je context
          - Line is linked to an MO  (always generate)
          - OR project has generate_labor_je=True
        """
        self.ensure_one()
        if self.env.context.get('skip_labor_je'):
            return False
        if self.mrp_production_id:
            return True
        project = self.project_id
        if project and getattr(project, 'generate_labor_je', False):
            return True
        return False

    # =========================================================================
    # Task 53 – Rate resolver
    # =========================================================================
    def _resolve_labor_rate(self):
        """Return (rate, rate_currency).

        Priority: employee.hourly_cost → employee.timesheet_cost → product.standard_price → 0
        """
        self.ensure_one()
        emp = self.employee_id
        if emp:
            rate = getattr(emp, 'hourly_cost', 0.0) or 0.0
            if rate:
                return rate, (emp.company_id.currency_id or self.company_id.currency_id)
            ts_cost = getattr(emp, 'timesheet_cost', 0.0) or 0.0
            if ts_cost:
                return ts_cost, (emp.company_id.currency_id or self.company_id.currency_id)
        if self.product_id:
            price = self.product_id.standard_price or 0.0
            if price:
                return price, (
                    getattr(self.product_id, 'currency_id', False)
                    or self.company_id.currency_id
                )
        return 0.0, self.company_id.currency_id

    # =========================================================================
    # Task 54 – Multiplier resolver
    # =========================================================================
    def _resolve_labor_multiplier(self):
        """Return rate multiplier: holiday > overtime > 1.0."""
        self.ensure_one()
        company = self.company_id
        if self.is_holiday:
            return getattr(company, 'holiday_rate_multiplier', 1.0) or 1.0
        if self.is_overtime:
            return getattr(company, 'overtime_rate_multiplier', 1.0) or 1.0
        return 1.0

    # =========================================================================
    # Task 55 + 56 – Core cost calculator
    # =========================================================================
    def _get_labor_cost_amount(self):
        """hours × rate × multiplier, converted to company currency."""
        self.ensure_one()
        hours = self.unit_amount or 0.0
        if hours <= 0.0:
            return 0.0
        rate, rate_currency = self._resolve_labor_rate()
        if not rate:
            return 0.0
        multiplier = self._resolve_labor_multiplier()
        raw_cost = hours * rate * multiplier
        company_currency = self.company_id.currency_id
        if rate_currency and rate_currency != company_currency and rate_currency.id:
            raw_cost = rate_currency._convert(
                raw_cost, company_currency,
                self.company_id,
                self.date or fields.Date.today(),
            )
        return float_round(raw_cost, precision_digits=company_currency.decimal_places or 2)

    # =========================================================================
    # Task 59 – Account resolver
    # =========================================================================
    def _resolve_labor_accounts(self):
        """Return (wip_account, clearing_account, journal).

        Priority: Project override → Workcenter override → Company default
        """
        self.ensure_one()
        company = self.company_id

        # WIP (Debit)
        wip_account = False
        project = self.project_id
        if project and getattr(project, 'labor_wip_account_id', False):
            wip_account = project.labor_wip_account_id
        if not wip_account and self.mrp_production_id:
            wo = self.mrp_production_id.workorder_ids[:1]
            if wo and getattr(wo.workcenter_id, 'labor_account_id', False):
                wip_account = wo.workcenter_id.labor_account_id
        if not wip_account:
            wip_account = company.labor_wip_account_id

        # Clearing (Credit)
        clearing_account = False
        if project and getattr(project, 'labor_clearing_account_id', False):
            clearing_account = project.labor_clearing_account_id
        if not clearing_account:
            clearing_account = company.labor_clearing_account_id

        # Journal
        journal = (
            getattr(company, 'labor_cost_journal_id', False)
            or getattr(company, 'account_stock_journal_id', False)
        )

        return wip_account, clearing_account, journal

    # =========================================================================
    # Task 59 – Analytic distribution builder
    # =========================================================================
    def _build_analytic_distribution(self):
        """Return {str(analytic_account_id): 100.0} or None."""
        self.ensure_one()
        analytic_account = False
        if self.mrp_production_id and self.mrp_production_id.analytic_account_id:
            analytic_account = self.mrp_production_id.analytic_account_id
        elif self.account_id:
            analytic_account = self.account_id
        if analytic_account:
            return {str(analytic_account.id): 100.0}
        return None

    # =========================================================================
    # Task 59 – JE generator  |  Task 78 – sudo()  |  Task 79 – audit log
    # =========================================================================
    def _generate_labor_cost_move(self):
        """Create and post: Debit WIP / Credit Clearing.

        Task 78: Uses sudo() for account.move creation so that manufacturing
        workers and HR employees who lack 'account.move' write rights can still
        trigger automatic JEs when logging timesheets.

        Task 79: The real caller's identity (uid + login) is captured BEFORE
        sudo() is applied and embedded in the JE narration as an audit trail,
        so the accounting team can trace who triggered each entry.

        Returns account.move or False (silently) when accounts missing.
        """
        self.ensure_one()

        # Task 63 guard
        if self.env.context.get('skip_labor_je'):
            return False

        cost = self._get_labor_cost_amount()
        if cost <= 0.0:
            return False

        wip_account, clearing_account, journal = self._resolve_labor_accounts()
        if not wip_account or not clearing_account or not journal:
            return False

        # Task 80 – multi-company guard: accounts must be accessible for this company
        # account.account uses company_ids (Many2many) in Odoo 17+; fall back to
        # company_id (Many2one) for earlier versions.
        company = self.company_id

        def _account_allows_company(account, co):
            # Odoo 17+: company_ids is a Many2many
            company_ids = getattr(account, 'company_ids', False)
            if company_ids:
                return not company_ids or co in company_ids
            # Odoo 16 and earlier: company_id is a Many2one
            acct_company = getattr(account, 'company_id', False)
            return not acct_company or acct_company == co

        if not _account_allows_company(wip_account, company) or \
                not _account_allows_company(clearing_account, company):
            return False

        analytic_dist = self._build_analytic_distribution()

        # Task 79 – capture real caller identity BEFORE sudo() for audit trail
        real_user = self.env.user
        caller_info = '{} (uid={})'.format(real_user.name or real_user.login, real_user.id)

        # Task 61 – audit trail ref & narration
        mo_ref = self.mrp_production_id.name if self.mrp_production_id else ''
        emp_name = self.employee_id.name if self.employee_id else ''
        rate_type = (
            'Holiday' if self.is_holiday
            else 'Overtime' if self.is_overtime
            else 'Regular'
        )
        ref = 'LABOR/{}{}'.format(
            '{}/'.format(mo_ref) if mo_ref else '',
            self.date or fields.Date.today(),
        )
        narration = (
            'Employee: {emp} | Hours: {hrs:.2f} | Type: {rt} | '
            'Cost: {cost:.2f} {cur} | Triggered by: {caller}'.format(
                emp=emp_name, hrs=self.unit_amount or 0.0,
                rt=rate_type, cost=cost, cur=company.currency_id.name,
                caller=caller_info,
            )
        )

        # Task 60 – move lines with analytic_distribution
        debit_vals = {
            'name': self.name or ref,
            'account_id': wip_account.id,
            'debit': cost, 'credit': 0.0,
            'currency_id': company.currency_id.id,
        }
        credit_vals = {
            'name': self.name or ref,
            'account_id': clearing_account.id,
            'debit': 0.0, 'credit': cost,
            'currency_id': company.currency_id.id,
        }
        if analytic_dist:
            debit_vals['analytic_distribution'] = analytic_dist
            credit_vals['analytic_distribution'] = analytic_dist

        # Task 78 – sudo() so manufacturing/HR users can create accounting entries
        move = self.env['account.move'].sudo().with_context(skip_labor_je=True).create({
            'move_type': 'entry',
            'date': self.date or fields.Date.context_today(self),
            'journal_id': journal.id,
            'company_id': company.id,
            'ref': ref,
            'narration': narration,
            'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)],
        })
        move._post()
        self.with_context(skip_labor_je=True).write({'labor_move_id': move.id})
        return move

    # =========================================================================
    # Task 62 – JE reversal  |  Task 78 – sudo()  |  Task 79 – audit log
    # =========================================================================
    def _reverse_labor_cost_move(self):
        """Reverse the linked labor JE and clear labor_move_id.

        Task 78: Uses sudo() for the same reason as _generate_labor_cost_move.
        Task 79: Captures real caller in reversal narration.
        """
        self.ensure_one()
        move = self.labor_move_id
        if not move:
            return False

        # Task 79 – real caller for audit trail
        real_user = self.env.user
        caller_info = '{} (uid={})'.format(real_user.name or real_user.login, real_user.id)

        # Task 78 – sudo() for reversal creation
        reversal = move.sudo()._reverse_moves(
            default_values_list=[{
                'ref': 'REV/{}'.format(move.ref or ''),
                'narration': 'Reversal of labor JE for timesheet: {} | Triggered by: {}'.format(
                    self.name or str(self.id), caller_info
                ),
                'date': fields.Date.context_today(self),
            }]
        )
        reversal._post()
        self.with_context(skip_labor_je=True).write({'labor_move_id': False})
        return reversal

    # =========================================================================
    # Legacy
    # =========================================================================
    def _get_timesheet_labor_cost_for_production(self):
        """Legacy wrapper."""
        self.ensure_one()
        return self._get_labor_cost_amount()
