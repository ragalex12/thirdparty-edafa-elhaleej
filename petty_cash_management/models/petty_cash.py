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

class HrPetty(models.Model):
    """
        Hr advance creation model.
        """
    _name = 'hr.petty'
    _description = 'Hr petty Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    read_only = fields.Boolean(string="check field")

    @api.onchange('employee')
    def _compute_read_only(self):
        """ Use this function to check weather the user has the permission to change the employee"""
        res_user = self.env['res.users'].search([('id', '=', self._uid)])
        print(res_user.has_group('hr.group_hr_user'))
        if res_user.has_group('hr.group_hr_user'):
            self.read_only = True
        else:
            self.read_only = False

    def mail_reminder(self):
        now = datetime.now() + timedelta(days=1)
        date_now = now.date()
        match = self.search([('state', '=', 'approved')])
        for i in match:
            if i.return_date:
                exp_date = fields.Date.from_string(i.return_date)
                if exp_date <= date_now:
                    base_url = self.env['ir.config_parameter'].get_param('web.base.url')
                    url = base_url + _('/web#id=%s&view_type=form&model=hr.petty&menu_id=') % i.id
                    mail_content = _('Hi %s,<br>As per the %s you ask %s on %s for the reason of %s. S0 here we '
                                     'remind you that you have to close the advance on or before %s. '
                                     'link.') % \
                                   (i.employee.name, i.name, i.petty_amount, i.date_request, i.purpose,
                                    date_now)
                    main_content = {
                        'subject': _('REMINDER On %s') % i.name,
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': i.employee.work_email,
                    }
                    mail_id = self.env['mail.mail'].create(main_content)
                    mail_id.mail_message_id.body = mail_content
                    mail_id.send()
                    if i.employee.user_id:
                        mail_id.mail_message_id.write(
                            {'needaction_partner_ids': [(4, i.employee.user_id.partner_id.id)]})
                        mail_id.mail_message_id.write({'partner_ids': [(4, i.employee.user_id.partner_id.id)]})

    @api.model
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hr.petty') or '/'
        return super(HrPetty, self).create(vals_list)

    def sent(self):
        self.state = 'to_approve'

    def send_mail(self):
        template = self.env.ref('petty_cash_management.petty_email_notification_template')
        self.env['mail.template'].browse(template.id).send_mail(self.id)
        self.mail_send = True

    def set_to_draft(self):
        self.state = 'draft'

    def approve(self):
        self.state = 'approved'

    def payment_register(self):
        
        # Initialize variables for petty account and journal
        s_petty_account = None
        s_petty__config_j = None
        s_petty_account_branch = None
        s_petty__config_branch_j = None

        if type == 'temporary':
            # Fetch settings for the main account
            s_petty_account = int(self.env['ir.config_parameter'].sudo().get_param('petty_cash_management.petty_account_id'))
            s_petty__config_j = int(self.env['ir.config_parameter'].sudo().get_param('petty_cash_management.petty_journal_id'))
            
            # Check if the settings are set
            if not s_petty_account or not s_petty__config_j:
                raise UserError(_("Please set the petty cash settings"))
            
            s_petty_account_id = s_petty_account
            s_petty_journal_id = s_petty__config_j
        else:
            # Fetch settings for the branch-specific account
            s_petty_account_branch = int(self.env['ir.config_parameter'].sudo().get_param('petty_cash_management.petty_account_branch_id'))
            s_petty__config_branch_j = int(self.env['ir.config_parameter'].sudo().get_param('petty_cash_management.petty_journal_branch_id'))
            
            # Check if the settings are set
            if not s_petty_account_branch or not s_petty__config_branch_j:
                raise UserError(_("Please set the petty cash settings"))
            
            s_petty_account_id = s_petty_account_branch
            s_petty_journal_id = s_petty__config_branch_j

        # Check if the payment journal is set
        if not self.journal_id:
            raise UserError(_("Please select the payment journal first"))

        # Prepare line items for account move
        line_ids = [
            (0, 0, {
                'journal_id': s_petty_journal_id,
                'account_id': self.journal_id.default_account_id.id,
                'name': self.name,
                'credit': self.petty_amount
            }),
            (0, 0, {
                'journal_id': s_petty_journal_id,
                'account_id': s_petty_account_id,
                'name': self.name,
                'partner_id': self.employee.user_id.partner_id.id,
                'debit': self.petty_amount
            })
        ]

        # Prepare values for the account move
        values = {
            'journal_id': s_petty_journal_id,
            'ref': self.name,
            'date': self.date_request,
            'line_ids': line_ids,
            'narration': 'Petty Reason: ' + self.purpose,
        }

        # Create and post the account move
        account_move = self.env['account.move'].create(values)
        account_move.action_post()

        # Update the state to paid
        self.state = 'paid'

    def reverse_payment_register(self):
        for each in self:
            # Search for the account move related to this record based on ref and narration
            journal_payment = self.env['account.move'].search([
                ('ref', '=', each.name),
                ('narration', '=', 'Petty Reason' + ': ' + each.purpose)  # Adjust the match criteria as needed
            ])

            if not journal_payment:
                raise UserError(_("No related journal entry found for reversal."))

            # Check if the move is already posted to ensure the reversal process is correct
            if journal_payment.state == 'posted':
                # Reverse the move using Odoo's reverse functionality
                reverse_move = journal_payment._reverse_moves(default_values_list=[{
                    'date': fields.Date.context_today(self),
                    'ref': 'Reversal of: ' + journal_payment.ref,
                }])

                # Post the reversed move to register it in the accounting records
                reverse_move.action_post()

            # Update the state to indicate that the payment has been returned
            each.state = 'returned'


    # return date validation
    @api.constrains('return_date')
    def validate_return_date(self):
        if self.return_date < self.date_request:
            raise UserError(_('Please Give Valid Return Date'))

    # Employee 
    def onchange_employee_id(self, employee, context=None):
        res = {}
        if employee:
            employee_rec = self.env['hr.employee'].browse(employee)
            res['job_id'] = employee_rec.job_id.id
            res['department_id'] = employee_rec.department_id.id
        return {'value': res}

    # Payment journal
    def journal_view(self):
        self.ensure_one()
        reverse_j = ('Reversal of: %s') % self.name
        domain = [
            '|',('ref', '=', self.name),('ref', '=', reverse_j)]
        return {
            'name': _('Jouranls'),
            'domain': domain,
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                                   Click to Create for journal
                                </p>'''),
        }

    journal_count = fields.Integer(compute='_journal_count', string='# Journals')

    def _journal_count(self):
        for each in self:
            reverse_j = ('Reversal of: %s') % each.name
            journal_ids = self.env['account.move'].search(['|',('ref', '=', each.name),('ref', '=', reverse_j)])
            each.journal_count = len(journal_ids)

    returned_advance_je = fields.Many2one('account.move', string="Journal Entry", readonly=True)

    name = fields.Char(string='Code', copy=False, help="Code",default = "ADV")
    company_id = fields.Many2one('res.company', 'Company', readonly=True, help="Company",
                                 default=lambda self: self.env.user.company_id)
    journal_id = fields.Many2one('account.journal', string='Payment Method',
                                 domain="[('type', 'in', ['cash', 'bank'])]")
    type = fields.Selection([('temporary', 'Temporary'), ('permanent', 'Permanent')], string='Please select the type',
                            required=True, default='temporary')
    rejected_reason = fields.Text(string='Rejected Reason', copy=False, readonly=True, help="Reason for the rejection")
    date_request = fields.Date(string='Requested Date', required=True, readonly=True,
                               help="Requested date",
                               default=datetime.now().strftime('%Y-%m-%d'))
    employee = fields.Many2one('hr.employee', string='Employee', required=True, readonly=True, help="Employee",
                               default=lambda self: self.env.user.employee_id.id)

    job_id = fields.Many2one('hr.job', string="Job Title", related='employee.job_id', readonly=True)
    department_id = fields.Many2one('hr.department', related='employee.department_id', string='Department',
                                    readonly=True)
    purpose = fields.Char(string='Reason', required=True, help="Reason")
    petty_amount = fields.Float("Petty Amount", required=True, readonly=True)
    return_date = fields.Date(string='Return Date', required=True,help="Return date")
    notes = fields.Html(string='Notes')
    state = fields.Selection([('draft', 'Draft'), ('to_approve', 'Waiting For Approval'), ('approved', 'Approved'),('paid', 'Paid'),
                              ('returned', 'Returned'), ('rejected', 'Refused'),('reconcile', 'Reconciled')], string='Status', default='draft',
                             tracking=True)
    mail_send = fields.Boolean(string="Mail Send")
    invoice_id = fields.Many2one('account.move', string="Bill")






