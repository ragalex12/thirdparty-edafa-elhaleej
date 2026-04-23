# -*- coding: utf-8 -*-

from odoo import models, fields, api


class WorkersReportWizard(models.TransientModel):
    _name = 'workers.report.wizard'
    _description = 'Workers Report Wizard'

    employee_ids = fields.Many2many(
        'hr.employee',
        string='Workers',
        help='Leave empty to include all workers'
    )
    
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        help='Filter by department'
    )
    
    report_type = fields.Selection([
        ('cards', 'Worker Cards'),
        ('summary', 'Worker Summary'),
        ('list', 'Workers List'),
        ('timesheets', 'Worker Timesheets'),
    ], string='Report Type', required=True, default='list')
    
    def _get_employees(self):
        """Get employees based on wizard filters"""
        domain = []
        if self.employee_ids:
            domain.append(('id', 'in', self.employee_ids.ids))
        if self.department_id:
            domain.append(('department_id', '=', self.department_id.id))
        return self.env['hr.employee'].search(domain)
    
    def action_print_report(self):
        self.ensure_one()
        data = {
            'employee_ids': self.employee_ids.ids,
            'department_id': self.department_id.id if self.department_id else False,
            'report_type': self.report_type,
        }
        
        report_action = self.env.ref('workers_reports.action_report_worker')
        if report_action:
            return report_action.report_action(self.ids, data=data)
        return {'type': 'ir.actions.act_window_close'}

