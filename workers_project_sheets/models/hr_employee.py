# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HrEmployee(models.Model):
    """Extend employee model to integrate with construction projects and payroll"""
    _inherit = 'hr.employee'

    # Project-related fields for payroll integration
    project_payroll_ids = fields.Many2many(
        'project.project',
        'employee_project_payroll_rel',
        'employee_id',
        'project_id',
        string='Payroll Projects',
        help='Projects that affect this employee\'s payroll calculations'
    )
    
    # Payroll statistics from projects
    total_project_hours = fields.Float(
        string='Total Project Hours',
        compute='_compute_project_hours',
        help='Total hours worked on projects for payroll calculation'
    )
    
    # Link to payroll structure based on project
    project_payroll_structure_id = fields.Many2one(
        'hr.payroll.structure',
        string='Project Payroll Structure',
        help='Payroll structure specific to construction projects'
    )
    
    # Day work option
    day_work = fields.Boolean(
        string='Day Work',
        default=False,
        help='If checked, this employee uses daily work timesheets for payroll calculation with "Workers Daily Cost" structure'
    )
    
    @api.depends('project_payroll_ids')
    def _compute_project_hours(self):
        """Compute total hours worked on payroll projects"""
        for employee in self:
            if employee.project_payroll_ids:
                timesheets = self.env['account.analytic.line'].search([
                    ('employee_id', '=', employee.id),
                    ('project_id', 'in', employee.project_payroll_ids.ids)
                ])
                employee.total_project_hours = sum(timesheets.mapped('unit_amount'))
            else:
                employee.total_project_hours = 0.0

