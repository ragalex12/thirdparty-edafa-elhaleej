# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime


class WorkersPayrollReportWizard(models.TransientModel):
    _name = 'workers.report.payroll.wizard'
    _description = 'Workers Payroll Report Wizard'

    employee_ids = fields.Many2many(
        'hr.employee',
        string='Workers',
        help='Leave empty to include all workers'
    )
    
    project_ids = fields.Many2many(
        'project.project',
        string='Projects',
        domain="[('use_for_payroll', '=', True)]",
        help='Filter by payroll projects'
    )
    
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        help='Filter by department'
    )
    
    date_from = fields.Date(string='Date From', required=True)
    date_to = fields.Date(string='Date To', default=fields.Date.today, required=True)
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'date_from' in fields_list:
            # Default to start of current month
            today = datetime.now()
            res['date_from'] = today.replace(day=1).date()
        if 'date_to' in fields_list:
            res['date_to'] = fields.Date.today()
        return res
    
    def _get_timesheets(self):
        """Get timesheets based on wizard filters"""
        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('include_in_payroll', '=', True),
        ]
        if self.employee_ids:
            domain.append(('employee_id', 'in', self.employee_ids.ids))
        if self.project_ids:
            domain.append(('project_id', 'in', self.project_ids.ids))
        if self.department_id:
            domain.append(('department_id', '=', self.department_id.id))
        return self.env['account.analytic.line'].search(domain)
    
    def action_print_report(self):
        self.ensure_one()
        data = {
            'employee_ids': self.employee_ids.ids,
            'project_ids': self.project_ids.ids,
            'department_id': self.department_id.id if self.department_id else False,
            'date_from': self.date_from,
            'date_to': self.date_to,
        }
        
        report_action = self.env.ref('workers_reports.action_report_payroll')
        if report_action:
            return report_action.report_action(self.ids, data=data)
        return {'type': 'ir.actions.act_window_close'}

