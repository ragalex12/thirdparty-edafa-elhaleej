# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HrPayslip(models.Model):
    """Extend payslip model to integrate with construction projects"""
    _inherit = 'hr.payslip'

    # Project-related fields
    project_id = fields.Many2one(
        'project.project',
        string='Project',
        help='Construction project related to this payslip'
    )
    
    project_hours = fields.Float(
        string='Project Hours',
        compute='_compute_project_hours',
        help='Total hours worked on project for this payslip period'
    )
    
    # Link to timesheets
    timesheet_ids = fields.Many2many(
        'account.analytic.line',
        'payslip_timesheet_rel',
        'payslip_id',
        'timesheet_id',
        string='Related Timesheets',
        help='Timesheets included in this payslip calculation'
    )
    
    # Related field for day work
    employee_day_work = fields.Boolean(
        string='Day Work Employee',
        related='employee_id.day_work',
        readonly=True,
        help='Indicates if this employee uses daily work timesheets'
    )
    
    @api.depends('employee_id', 'date_from', 'date_to', 'project_id')
    def _compute_project_hours(self):
        """Compute project hours for the payslip period"""
        for payslip in self:
            if payslip.employee_id and payslip.date_from and payslip.date_to:
                domain = [
                    ('employee_id', '=', payslip.employee_id.id),
                    ('date', '>=', payslip.date_from),
                    ('date', '<=', payslip.date_to),
                ]
                if payslip.project_id:
                    domain.append(('project_id', '=', payslip.project_id.id))
                else:
                    # Get all payroll projects for this employee
                    payroll_projects = payslip.employee_id.project_payroll_ids
                    if payroll_projects:
                        domain.append(('project_id', 'in', payroll_projects.ids))
                
                timesheets = self.env['account.analytic.line'].search(domain)
                payslip.project_hours = sum(timesheets.mapped('unit_amount'))
                payslip.timesheet_ids = [(6, 0, timesheets.ids)]
            else:
                payslip.project_hours = 0.0
                payslip.timesheet_ids = [(5, 0, 0)]
    
    @api.model_create_multi
    def create(self, vals_list):
        """Auto-set payroll structure for day work employees"""
        payslips = super().create(vals_list)
        for payslip in payslips:
            if payslip.employee_id and payslip.employee_id.day_work:
                # Set structure to Workers Daily Cost
                structure = self.env.ref('workers_project_sheets.structure_workers_daily_cost', False)
                if structure and not payslip.struct_id:
                    payslip.struct_id = structure
        return payslips
    
    def write(self, vals):
        """Update payroll structure when employee day_work changes"""
        result = super().write(vals)
        # If employee_id is changed, check day_work status
        if 'employee_id' in vals:
            for payslip in self:
                if payslip.employee_id and payslip.employee_id.day_work:
                    structure = self.env.ref('workers_project_sheets.structure_workers_daily_cost', False)
                    if structure:
                        payslip.struct_id = structure
        return result
    
    @api.onchange('employee_id')
    def onchange_employee(self):
        """Override to auto-set payroll structure for day work employees"""
        result = super().onchange_employee()
        if self.employee_id and self.employee_id.day_work:
            structure = self.env.ref('workers_project_sheets.structure_workers_daily_cost', False)
            if structure:
                # Override struct_id for day work employees
                self.struct_id = structure
                # Also update timesheets when employee changes
                if self.date_from and self.date_to:
                    self._compute_project_hours()
        return result

