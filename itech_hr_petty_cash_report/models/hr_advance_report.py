import time

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class HRAdvanceReport(models.TransientModel):
    _name = 'hr.advance.report'
    _description = "HR Advance Report"

    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)
    partner_ids = fields.Many2many(
        comodel_name='res.partner',
        relation='hr_advance_report_res_partner_rel',
        column1='hr_advance_report_id',
        column2='partner_id',
        string='Partners'
    )
    initial_balance = fields.Boolean('Include Initial Balances', default=True)
    amount_currency = fields.Boolean("With Currency",
                                     help="It adds the currency column on report if the "
                                          "currency differs from the company currency.")
    cumulated_amount_currency = fields.Boolean("Cumulated Amount Currency")

    @api.constrains('date_from', 'date_to')
    def _check_date_range(self):
        for rec in self:
            if rec.date_to and rec.date_from and rec.date_from > rec.date_to:
                raise ValidationError(_('Start date must be less than end date.'))

    def print_report(self):
        self.ensure_one()
        [data] = self.read()
        datas = {
            'ids': [],
            'model': 'account.move.line',
            'form': data
        }
        return self.env.ref('itech_hr_petty_cash_report.report_hr_advance').report_action(self, data=datas)

class HrAdvanceReport(models.AbstractModel):
    _name = 'report.itech_hr_petty_cash_report.hr_advance_report_template'
    _description = "HR Advance Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model'):
            raise UserError("Form content is missing, this report cannot be printed.")

        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_ids', []))
        company = self.env['res.company'].browse(data['form'].get('company_id')[0])

        # Account IDs
        accs = [int(self.env['ir.config_parameter'].sudo().get_param('petty_cash_management.petty_account_id'))]

        # Build search domain
        domain = [
            ('company_id', '=', company.id),
            ('parent_state', '=', 'posted'),
            ('account_id', 'in', accs),
        ]

        if data['form'].get('partner_ids'):
            domain.append(('partner_id', 'in', data['form'].get('partner_ids')))
        if data['form'].get('date_from'):
            domain.append(('date', '>=', data['form'].get('date_from')))
        if data['form'].get('date_to'):
            domain.append(('date', '<=', data['form'].get('date_to')))

        # Main lines (sorted in Python for QWeb)
        lines = self.env['account.move.line'].search(domain).sorted(lambda l: l.date)

        # Initial balance lines
        intbalance_domain = [
            ('account_id', 'in', accs),
            ('company_id', '=', company.id),
            ('parent_state', '=', 'posted'),
            ('date', '<', data['form'].get('date_from')),
        ]
        intbalance_lines = self.env['account.move.line'].search(intbalance_domain)

        # Group by partner for easier template loop
        partner_ids = lines.mapped('partner_id')
        grouped_data = {}
        for partner in partner_ids:
            grouped_data[partner.id] = {
                'partner': partner,
                'lines': lines.filtered(lambda l: l.partner_id.id == partner.id),
                'initial_balance': intbalance_lines.filtered(lambda l: l.partner_id.id == partner.id),
            }

        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data['form'],
            'partners': partner_ids,
            'grouped_data': grouped_data,  # partner → lines + initial_balance
        }

