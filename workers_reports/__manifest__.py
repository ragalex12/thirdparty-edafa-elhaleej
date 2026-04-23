# -*- coding: utf-8 -*-
{
    'name': 'Workers Reports',
    'version': '19.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Comprehensive reports for workers, projects, timesheets, and payroll',
    'description': """
Workers Reports Module
======================
This module provides comprehensive reporting functionality for construction workers:

Worker Reports:
- Worker Cards
- Worker Summary
- Workers List
- Worker Timesheets

Project Reports:
- Project Workers
- Project Hours
- Project Payroll

Timesheet Reports:
- Day Works Report
- Works by Project
- Works by Status

Payroll Reports:
- Payroll by Project
- Payroll by Worker
- Payroll Summary
    """,
    'author': 'Company1',
    'website': '',
    'depends': [
        'base',
        'hr',
        'project',
        'hr_timesheet',
        'workers_project_sheets',
        'workers_timesheet',
        'hr_payroll_community',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/worker_report_wizard_views.xml',
        'wizard/project_report_wizard_views.xml',
        'wizard/timesheet_report_wizard_views.xml',
        'wizard/payroll_report_wizard_views.xml',
        'reports/report_actions.xml',
        'reports/worker_reports.xml',
        'reports/project_reports.xml',
        'reports/timesheet_reports.xml',
        'reports/payroll_reports.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

