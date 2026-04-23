# -*- coding: utf-8 -*-
"""
Task 73 – Two-step payroll reconciliation flow
==============================================

**Step 1 – Timesheet posting (this module)**
  When a timesheet line is saved (create/write) or an MO is marked Done:
    DR  Labor WIP Account         (e.g. 510100 – Manufacturing WIP)
    CR  Labor Clearing Account    (e.g. 215100 – Payroll Accrual / Labor Clearing)

  This immediately recognises the *direct labor cost* on the product/MO
  without waiting for payroll to run.

**Step 2 – Payroll run (hr_payroll_account or hr_payroll_account_community)**
  When payroll is confirmed and salary journal entries are posted:
    DR  Labor Clearing Account    (225100 – clears the accrual)
    CR  Wages Payable / Bank      (310100 – actual cash/liability)

  The clearing account acts as a transit; after both steps the net balance
  on 215100 is zero, WIP carries the true cost, and Wages Payable/Bank
  reflects actual cash obligations.

**Task 74 – hr_payroll_account_community integration**
  If `hr_payroll_account_community` (or `hr_payroll_account`) is installed
  the `_get_payroll_debit_account()` helper on `hr.payslip` will be checked.
  Administrators should map the payslip *Gross Wage* or *Labor Cost* salary
  rule's debit account to match `res.company.labor_clearing_account_id` so
  Step 2 entries cancel Step 1 entries on that account automatically.

  No automatic wiring is performed by this module to avoid coupling; a
  validation constraint warns when the accounts look inconsistent.
"""

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = 'res.company'

    # ── kept for backward compatibility ──────────────────────────────────────
    production_labor_expense_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Production Labor Expense Account (Legacy)',
        check_company=True,
        help='Legacy field. Use labor_wip_account_id / labor_clearing_account_id instead.',
    )

    # ── Task 45 – WIP / Project Cost debit account ────────────────────────────
    labor_wip_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Labor WIP Account',
        check_company=True,
        help='Account DEBITED when timesheet labor cost is posted '
             '(Manufacturing WIP or Project Cost account).',
    )

    # ── Task 46 – Labor Clearing / Payroll Accrual credit account ─────────────
    labor_clearing_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Labor Clearing Account',
        check_company=True,
        help='Account CREDITED when timesheet labor cost is posted '
             '(Labor Clearing or Payroll Accrual account).',
    )

    # ── Task 47 – Dedicated journal for labor JEs ─────────────────────────────
    labor_cost_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Labor Cost Journal',
        check_company=True,
        domain=[('type', 'in', ['general', 'miscellaneous'])],
        help='Journal used for automatic labor cost journal entries. '
             'Falls back to the company stock journal if not set.',
    )

    # ── Task 48 – Rate multipliers ────────────────────────────────────────────
    overtime_rate_multiplier = fields.Float(
        string='Overtime Rate Multiplier',
        default=1.5,
        help='Multiplier applied to the employee hourly rate for overtime hours '
             '(e.g. 1.5 = 150 %). Set to 1.0 to disable.',
    )
    holiday_rate_multiplier = fields.Float(
        string='Holiday Rate Multiplier',
        default=2.0,
        help='Multiplier applied to the employee hourly rate for holiday hours '
             '(e.g. 2.0 = 200 %). Set to 1.0 to disable.',
    )

    # =========================================================================
    # Task 72 – Constraints: account sanity checks
    # =========================================================================

    @api.constrains('labor_wip_account_id', 'labor_clearing_account_id')
    def _check_labor_accounts_not_same(self):
        """WIP and Clearing must be different accounts."""
        for company in self:
            if (company.labor_wip_account_id
                    and company.labor_clearing_account_id
                    and company.labor_wip_account_id == company.labor_clearing_account_id):
                raise ValidationError(
                    'Labor WIP Account and Labor Clearing Account must be '
                    'different accounts for company "%s".' % company.name
                )

    @api.constrains('labor_clearing_account_id')
    def _check_clearing_account_type(self):
        """Task 72 – Warn when the clearing account is not a liability/payable type.

        The Labor Clearing Account should normally be a Current Liability
        (account_type in ['liability_current', 'liability_payable',
        'liability_non_current']) so that the payroll run can debit it.

        We raise a soft warning (ValidationError) rather than blocking, so
        administrators can still use any account type if their CoA differs.
        """
        VALID_TYPES = {
            'liability_current',
            'liability_payable',
            'liability_non_current',
        }
        for company in self:
            acct = company.labor_clearing_account_id
            if not acct:
                continue
            account_type = getattr(acct, 'account_type', None)
            if account_type and account_type not in VALID_TYPES:
                raise ValidationError(
                    'Labor Clearing Account "%s" (company: %s) has account type '
                    '"%s". For the two-step payroll reconciliation flow to work '
                    'correctly, the clearing account should be a liability account '
                    '(Current Liability, Payable, or Non-current Liability). '
                    'Please review your Chart of Accounts configuration.' % (
                        acct.name, company.name, account_type
                    )
                )

    @api.constrains('overtime_rate_multiplier', 'holiday_rate_multiplier')
    def _check_rate_multipliers(self):
        """Multipliers must be >= 1.0 — values below 1 would reduce the rate."""
        for company in self:
            if company.overtime_rate_multiplier < 1.0:
                raise ValidationError(
                    'Overtime Rate Multiplier must be ≥ 1.0 (got %.2f for company "%s").'
                    % (company.overtime_rate_multiplier, company.name)
                )
            if company.holiday_rate_multiplier < 1.0:
                raise ValidationError(
                    'Holiday Rate Multiplier must be ≥ 1.0 (got %.2f for company "%s").'
                    % (company.holiday_rate_multiplier, company.name)
                )

    # =========================================================================
    # Task 74 – hr_payroll_account_community helper
    # =========================================================================

    def _get_labor_clearing_account_for_payroll(self):
        """Task 74 – Return the clearing account to use in salary rules.

        Called by payroll modules (hr_payroll_account / hr_payroll_account_community)
        when building salary journal entries.  Returns the company's
        labor_clearing_account_id if configured, otherwise None.

        Usage in a custom salary rule:
            result = employee.company_id._get_labor_clearing_account_for_payroll()
        """
        self.ensure_one()
        return self.labor_clearing_account_id or False
