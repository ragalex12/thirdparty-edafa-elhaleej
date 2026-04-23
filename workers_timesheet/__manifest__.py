# -*- coding: utf-8 -*-
{
    'name': 'Workers Timesheet',
    'version': '19.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Timesheet management for construction workers',
    'description': """
Workers Timesheet
=================
This module provides timesheet management specifically for construction workers:
- Daily work hour recording
- Project assignment
- Work status tracking (Normal, Overtime, Holiday)
- Integration with payroll calculations
- Department/Group assignment
    """,
    'author': 'Company1',
    'website': '',
    'depends': [
        'base',
        'hr',
        'project',
        'hr_timesheet',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_timesheet_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}

