# -*- coding: utf-8 -*-

from odoo import models, fields, api


class WorkersProjectReportWizard(models.TransientModel):
    _name = 'workers.report.project.wizard'
    _description = 'Workers Project Report Wizard'

    project_ids = fields.Many2many(
        'project.project',
        string='Projects',
        domain="[('use_for_payroll', '=', True)]",
        help='Leave empty to include all payroll projects'
    )
    
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        help='Filter by department'
    )
    
    def _get_projects(self):
        """Get projects based on wizard filters"""
        domain = [('use_for_payroll', '=', True)]
        if self.project_ids:
            domain.append(('id', 'in', self.project_ids.ids))
        if self.department_id:
            domain.append(('department_id', '=', self.department_id.id))
        return self.env['project.project'].search(domain)
    
    def action_print_report(self):
        self.ensure_one()
        data = {
            'project_ids': self.project_ids.ids,
            'department_id': self.department_id.id if self.department_id else False,
        }
        
        report_action = self.env.ref('workers_reports.action_report_project')
        if report_action:
            return report_action.report_action(self.ids, data=data)
        return {'type': 'ir.actions.act_window_close'}

