# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProjectProject(models.Model):
    _inherit = 'project.project'

    # ── Task 49 – Per-project labor JE toggle & account overrides ─────────────
    generate_labor_je = fields.Boolean(
        string='Generate Labor Journal Entries',
        default=False,
        help='When enabled, timesheet lines on this project automatically '
             'generate labor cost journal entries using the accounts below '
             '(or the company defaults if left empty).',
    )
    labor_wip_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Labor WIP Account (Override)',
        check_company=True,
        help='Overrides the company Labor WIP Account for timesheets on this project.',
    )
    labor_clearing_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Labor Clearing Account (Override)',
        check_company=True,
        help='Overrides the company Labor Clearing Account for timesheets on this project.',
    )

    # =========================================================================
    # Task 72 – Per-project account sanity constraints
    # =========================================================================

    @api.constrains('labor_wip_account_id', 'labor_clearing_account_id')
    def _check_project_labor_accounts_not_same(self):
        """Per-project WIP and Clearing overrides must be different."""
        for project in self:
            if (project.labor_wip_account_id
                    and project.labor_clearing_account_id
                    and project.labor_wip_account_id == project.labor_clearing_account_id):
                raise ValidationError(
                    'Labor WIP Account and Labor Clearing Account overrides '
                    'must be different accounts on project "%s".' % project.name
                )

    @api.constrains('labor_clearing_account_id')
    def _check_project_clearing_account_type(self):
        """Per-project clearing account should be a liability type."""
        VALID_TYPES = {
            'liability_current',
            'liability_payable',
            'liability_non_current',
        }
        for project in self:
            acct = project.labor_clearing_account_id
            if not acct:
                continue
            account_type = getattr(acct, 'account_type', None)
            if account_type and account_type not in VALID_TYPES:
                raise ValidationError(
                    'Labor Clearing Account Override "%s" on project "%s" '
                    'has account type "%s". The clearing account should be a '
                    'liability account for the two-step payroll reconciliation '
                    'flow to work correctly.' % (acct.name, project.name, account_type)
                )
