# -*- coding: utf-8 -*-
{
    'name': 'Workers Project Sheets',
    'version': '19.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Construction project management with payroll integration for workers',
    'description': """
Workers Project Sheets
=======================
This module integrates construction project management with employee tracking and payroll:
- Inherits from iTech Construction Project
- Inherits from HR Employee Enhance
- Integrates with HR Payroll Community for payroll rules
- Links timesheets to payroll calculations
- Project-based worker management
    """,
    'author': 'Company1',
    'depends': [
        'base',
        'hr',
        'project',
        'hr_timesheet',
        'workers_timesheet',
        'itech_construction_project',
        'hr_employee_enhance',
        'hr_payroll_community',
        'hr_payroll_account_community',
    ],
    'data': [
        'data/payroll_structure_data.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/hr_employee_views.xml',
        'views/project_views.xml',
        'views/hr_payslip_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}

