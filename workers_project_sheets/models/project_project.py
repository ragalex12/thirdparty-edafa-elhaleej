# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProjectProject(models.Model):
    """Extend project model to integrate with payroll"""
    _inherit = 'project.project'

    # Payroll integration fields
    use_for_payroll = fields.Boolean(
        string='Use for Payroll',
        default=False,
        help='If checked, timesheets from this project will be included in payroll calculations'
    )
    
    payroll_structure_id = fields.Many2one(
        'hr.payroll.structure',
        string='Payroll Structure',
        help='Payroll structure to apply for workers on this project'
    )
    
    # Payroll statistics
    payroll_hours = fields.Float(
        string='Total Payroll Hours',
        compute='_compute_payroll_hours',
        help='Total hours worked on this project for payroll'
    )
    
    payroll_workers_count = fields.Integer(
        string='Payroll Workers',
        compute='_compute_payroll_workers',
        help='Number of workers assigned to this project for payroll'
    )
    
    # Link to salary rules
    payroll_rule_ids = fields.Many2many(
        'hr.salary.rule',
        'project_salary_rule_rel',
        'project_id',
        'rule_id',
        string='Payroll Rules',
        help='Salary rules applicable to this project'
    )
    
    # Worker sheet code statistics
    worker_sheet_w_count = fields.Integer(
        string='W (حراسه) Count',
        compute='_compute_worker_sheet_stats',
        help='Number of timesheets with code W (Security/Guards)'
    )
    
    worker_sheet_c_count = fields.Integer(
        string='C (By Metre) Count',
        compute='_compute_worker_sheet_stats',
        help='Number of timesheets with code C (By Metre)'
    )
    
    worker_sheet_g_count = fields.Integer(
        string='G (Dept Cost) Count',
        compute='_compute_worker_sheet_stats',
        help='Number of timesheets with code G (Worker Cost Over Company Department)'
    )
    
    worker_sheet_h_count = fields.Integer(
        string='H (Direct Cost) Count',
        compute='_compute_worker_sheet_stats',
        help='Number of timesheets with code H (Worker Cost for Worker Direct)'
    )
    
    @api.depends('timesheet_ids')
    def _compute_worker_sheet_stats(self):
        """Compute statistics for each worker sheet code"""
        for project in self:
            timesheets = project.timesheet_ids
            project.worker_sheet_w_count = len(timesheets.filtered(lambda t: t.worker_sheet_code == 'W'))
            project.worker_sheet_c_count = len(timesheets.filtered(lambda t: t.worker_sheet_code == 'C'))
            project.worker_sheet_g_count = len(timesheets.filtered(lambda t: t.worker_sheet_code == 'G'))
            project.worker_sheet_h_count = len(timesheets.filtered(lambda t: t.worker_sheet_code == 'H'))
    
    @api.depends('timesheet_ids', 'use_for_payroll')
    def _compute_payroll_hours(self):
        """Compute total hours for payroll calculation"""
        for project in self:
            if project.use_for_payroll:
                project.payroll_hours = sum(
                    project.timesheet_ids.filtered(
                        lambda t: t.work_status in ['normal', 'overtime', 'holiday']
                    ).mapped('unit_amount')
                )
            else:
                project.payroll_hours = 0.0
    
    @api.depends('members_ids', 'use_for_payroll')
    def _compute_payroll_workers(self):
        """Count workers assigned to this project for payroll"""
        for project in self:
            if project.use_for_payroll:
                project.payroll_workers_count = len(project.members_ids)
            else:
                project.payroll_workers_count = 0

