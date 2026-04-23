import time

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class TaxReport(models.TransientModel):
    _name = 'itech.tax.report'

    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)
    tax_ids = fields.Many2many("account.tax", string="Tax", domain="[('active', '=', True), ('company_id', '=', company_id)]", required=True )

    @api.constrains('date_from', 'date_to')
    def print_report(self):
        self.ensure_one()
        if self.filtered(lambda c: c.date_to and c.date_from > c.date_to):
            raise ValidationError(_('start date must be less than end date.'))
        [data] = self.read()
        datas = {
            'ids': [],
            'model': 'account.move.line',
            'form': data
        }
        return self.env.ref('itech_tax_report.report_tax').report_action(self, data=datas)


class tax_details_report(models.AbstractModel):
    _name = 'report.itech_tax_report.tax_report_template'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model'):
            raise UserError("Form content is missing, this report cannot be printed.")

        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_ids', []))

        company = self.env['res.company'].search([('id', '=', data['form'].get('company_id')[0])], limit=1)

        taxes = self.env['account.tax'].search([('id', '=', data['form'].get('tax_ids'))])
        accs = []
        for t in taxes:
            accs.append(int(t.invoice_repartition_line_ids.account_id))
            accs.append(int(t.refund_repartition_line_ids.account_id))
        
        if data['form'].get('tax_ids'):
            if data['form'].get('date_from') and data['form'].get('date_to'):
                lines = self.env['account.move.line'].search(
                    [('date', '>=', data['form'].get('date_from')),
                     ('date', '<=', data['form'].get('date_to')),
                     ('company_id', '=', company.id),
                     ('parent_state', '=', 'posted'),
                     ('account_id', 'in', accs)])

            elif data['form'].get('date_from'):
                lines = self.env['account.move.line'].search(
                    [('date', '>=', data['form'].get('date_from')),
                     ('company_id', '=', company.id),
                     ('parent_state', '=', 'posted'),
                     ('account_id', 'in', accs)])

            elif data['form'].get('date_to'):
                lines = self.env['account.move.line'].search(
                    [('date', '<=', data['form'].get('date_to')),
                     ('company_id', '=', company.id),
                     ('parent_state', '=', 'posted'),
                     ('account_id', 'in', accs)])

            elif data['form'].get('tax_ids'):
                lines = self.env['account.move.line'].search(
                    [('company_id', '=', company.id),
                    ('parent_state', '=', 'posted'),
                    ('account_id', 'in', accs)])

            else:
                lines = self.env['account.move.line'].search([
                    ('company_id', '=', company.id),
                    ('parent_state', '=', 'posted'),
                    ('account_id', 'in', accs)])
        else:
            if data['form'].get('date_from') and data['form'].get('date_to'):
                lines = self.env['account.move.line'].search(
                     [('date', '>=', data['form'].get('date_from')),
                     ('date', '<=', data['form'].get('date_to')),
                     ('company_id', '=', company.id),
                     ('parent_state', '=', 'posted'),
                     ('account_id', 'in', accs)])

                     
            elif data['form'].get('date_to'):
                lines = self.env['account.move.line'].search([('date', '<=', data['form'].get('date_to')),
                                                              ('company_id', '=', company.id),
                                                              ('parent_state', '=', 'posted'),
                                                              ('account_id', 'in', accs)])

            elif data['form'].get('date_from'):
                lines = self.env['account.move.line'].search([('date', '>=', data['form'].get('date_from')),
                                                              ('company_id', '=', company.id),
                                                              ('parent_state', '=', 'posted'),
                                                              ('account_id', 'in', accs)])

            else:
                lines = self.env['account.move.line'].search([
                     ('company_id', '=', company.id),
                     ('parent_state', '=', 'posted'),
                     ('account_id', 'in', accs)])

        all_taxes = []

        if data['form'].get('tax_ids'):
            for t in data['form'].get('tax_ids'):
                all_taxes.append(t)
            tax_ids = self.env['account.tax'].search([('id', 'in', all_taxes)])
        else:
            tax_ids = self.env['account.tax'].search([])


        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'docs': lines,
            'docss': tax_ids,
            'tax_ids': tax_ids,
            'data': data['form']
        }
        

