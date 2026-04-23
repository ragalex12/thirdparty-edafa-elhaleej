# -*- coding: utf-8 -*-
#############################################################################
#                                                                           #
#    iTech Co.                                                              #
#                                                                           #
#    Copyright (C) 2020-iTech Technologies(<https://www.iTech.com.eg>).     #
#                                                                           #
#############################################################################

from datetime import date, datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HR_expense (models.Model):
    _inherit = 'hr.expense'

    expense_attachment = fields.Binary(string='Attachment', store=True, attachment=True)
    payment_mode = fields.Selection(
        selection_add=[('petty_cash', 'Petty Cash')],
        ondelete={'petty_cash': 'set default'},
    )
    type = fields.Selection([('temporary', 'Temporary'), ('permanent', 'Permanent')], string='Please select the type',
                            required=True, default='temporary')


    def confirm_advance_reconcile(self):
        # Initialize the petty journal variable
        s_petty__config_j = None

        # Check if the petty_branch is set and retrieve the journal configuration
        if self.type:
            if self.type == 'temporary':
                s_petty_account = int(self.env['ir.config_parameter'].sudo().get_param('petty_cash_management.petty_account_id'))
                s_petty__config_j = int(self.env['ir.config_parameter'].sudo().get_param('petty_cash_management.petty_journal_id'))
            else:
                s_petty_account_branch = int(self.env['ir.config_parameter'].sudo().get_param('petty_cash_management.petty_account_branch_id'))
                s_petty__config_j = int(self.env['ir.config_parameter'].sudo().get_param('petty_cash_management.petty_journal_branch_id'))

        # Ensure that the journal configuration is available
        if s_petty__config_j is None:
            raise UserError(_("Please set the petty cash journal settings."))

        # Determine the payment journal to use
        payment_journal = s_petty__config_j

        # Prepare line items for the account move
        line_ids = [
            (0, 0, {
                'journal_id': s_petty__config_j,
                'account_id': s_petty_account if self.petty_branch.code == 'OU1' else s_petty_account_branch,  # Conditional account_id
                'name': self.name,
                'credit': self.total_amount_currency,  # Ensure this is defined
                'partner_id': self.employee_id.user_id.partner_id.id,
            }),
            (0, 0, {
                'journal_id': s_petty__config_j,
                'account_id': self.account_id.id,  # Ensure account_id is properly defined
                'name': self.name,
                'tax_ids':[(6, 0,self.tax_ids.ids)],
                'analytic_distribution': self.analytic_distribution,  # Ensure line is defined correctly
                'partner_id': self.employee_id.user_id.partner_id.id,
                'debit': self.total_amount_currency - self.tax_amount  # Ensure petty_amount is defined
            })
        ]

        # Prepare values for the account move
        values = {
            'journal_id': payment_journal,
            'ref': self.name,
            'date': self.date,  # Ensure this date is valid
            'line_ids': line_ids,
        }

        # Create and post the account move
        account_move = self.env['account.move'].create(values)
        account_move.post()

        # Update the state to done
        self.state = 'done'

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    reconcile_partner = fields.Many2one('res.partner', string="Reconcile Partner")
        
    def action_post(self):
        res = super().action_post()

        for payment in self:
            if payment.journal_id.code == 'EADV' and payment.reconcile_partner and payment.move_id:
                journal_suspense_account = payment.journal_id.suspense_account_id

                # Find the credit line to reverse
                credit_lines = payment.move_id.line_ids.filtered(
                    lambda l: l.account_id == journal_suspense_account and l.credit > 0
                )

                target_journal = payment.journal_id
                create_journal = self.env['account.journal'].browse(3)
                
                if not target_journal.default_account_id:
                    raise UserError(_("Default account is missing in Journal, Please configure it."))

                new_move = self.env['account.move'].sudo().create({
                    'journal_id': create_journal.id,
                    'date': payment.move_id.date,
                    'ref': f'Advance Adjustment: {payment.name}',
                    'line_ids': [
                        (0, 0, {
                            'account_id': journal_suspense_account.id,
                            'partner_id': payment.reconcile_partner.id,
                            'name': payment.memo or 'Advance Credit (Adjust)',
                            'debit': 0.0,
                            'credit': payment.amount,
                        }),
                        (0, 0, {
                            'account_id': target_journal.default_account_id.id,
                            'partner_id': payment.partner_id.id,
                            'name': 'Offset Entry',
                            'debit': payment.amount,
                            'credit': 0.0,
                        }),
                    ]
                })
                new_move.action_post()

        return res

class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    reconcile_partner = fields.Many2one('res.partner', string="Reconcile Partner")

    def _create_payment_vals_from_wizard(self, batch_result):
        # Before creating vals, check reconcile_partner if journal is EADV
        if self.journal_id.code == 'EADV' and not self.reconcile_partner:
            raise UserError(_("You must specify a Reconcile Partner for journal with code 'EADV'."))

        vals = super()._create_payment_vals_from_wizard(batch_result)
        if self.reconcile_partner:
            vals['reconcile_partner'] = self.reconcile_partner.id
        return vals
