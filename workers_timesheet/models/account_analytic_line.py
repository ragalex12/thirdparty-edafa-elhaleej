# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime


class AccountAnalyticLine(models.Model):
    """Extend timesheet model for construction workers"""
    _inherit = 'account.analytic.line'

    # Additional fields for timesheet (DayWorks)
    work_note = fields.Text(
        string='Work Note', 
        help='Additional notes about the work performed'
    )
    
    work_status = fields.Selection([
        ('normal', 'Normal'),
        ('overtime', 'Overtime'),
        ('holiday', 'Holiday'),
    ], string='Work Status', default='normal', required=True)
    
    # Date fields (similar to VB6 app)
    work_date_day = fields.Integer(
        string='Day', 
        compute='_compute_date_parts', 
        store=True
    )
    
    work_date_month = fields.Integer(
        string='Month', 
        compute='_compute_date_parts', 
        store=True
    )
    
    work_date_year = fields.Integer(
        string='Year', 
        compute='_compute_date_parts', 
        store=True
    )
    
    # Department relation
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        related='employee_id.department_id',
        store=True,
        readonly=True
    )
    
    # Payroll integration
    include_in_payroll = fields.Boolean(
        string='Include in Payroll',
        default=True,
        help='If checked, this timesheet entry will be included in payroll calculations'
    )
    
    # Worker Sheet Coding (from Company1)
    worker_sheet_code = fields.Selection([
        ('W', 'W - حراسه (Security/Guards)'),
        ('C', 'C - By Metre'),
        ('G', 'G - Worker Cost Over Company Department'),
        ('H', 'H - Worker Cost for Worker Direct'),
    ], string='Worker Sheet Code', 
       help='Coding system for worker sheet classification:\n'
            'W: حراسه (Security/Guards)\n'
            'C: By Metre\n'
            'G: Worker Cost Over Company Department\n'
            'H: Worker Cost for Worker Direct')
    
    # Metre quantity (for C type)
    metre_quantity = fields.Float(
        string='Metre Quantity',
        help='Quantity in metres (used when Worker Sheet Code is C)'
    )
    
    @api.depends('date')
    def _compute_date_parts(self):
        """Compute day, month, year from date"""
        for line in self:
            if line.date:
                line.work_date_day = line.date.day
                line.work_date_month = line.date.month
                line.work_date_year = line.date.year
            else:
                line.work_date_day = 0
                line.work_date_month = 0
                line.work_date_year = 0
    
    def _include_in_payroll_from_project(self, project):
        """Default payroll flag: eligible unless the project explicitly opts out.

        Do **not** copy ``project.use_for_payroll`` (that field defaults False and
        would silently uncheck Include in Payroll when selecting a normal project).
        """
        if not project:
            return True
        return not bool(getattr(project, "exclude_from_payroll", False))

    @api.onchange("project_id")
    def _onchange_project_id(self):
        """Keep timesheets payroll-eligible unless the project opts out."""
        for rec in self:
            rec.include_in_payroll = rec._include_in_payroll_from_project(rec.project_id)

    @api.model_create_multi
    def create(self, vals_list):
        Project = self.env["project.project"]
        for vals in vals_list:
            if "include_in_payroll" not in vals:
                project = (
                    Project.browse(vals["project_id"])
                    if vals.get("project_id")
                    else Project.browse()
                )
                vals["include_in_payroll"] = self._include_in_payroll_from_project(project)
        return super().create(vals_list)

    def write(self, vals):
        vals = dict(vals)
        res = super().write(vals)
        if "project_id" in vals and "include_in_payroll" not in vals:
            for rec in self:
                rec.include_in_payroll = rec._include_in_payroll_from_project(rec.project_id)
        return res
    
    @api.onchange('worker_sheet_code')
    def _onchange_worker_sheet_code(self):
        """Reset metre_quantity when code is not C"""
        if self.worker_sheet_code != 'C':
            self.metre_quantity = 0.0

