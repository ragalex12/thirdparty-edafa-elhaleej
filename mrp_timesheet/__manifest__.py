# -*- coding: utf-8 -*-
{
    'name': 'Manufacturing Timesheet',
    'version': '19.0.8.0',
    'category': 'Manufacturing/Manufacturing',
    'summary': 'Add a Timesheet tab on Manufacturing Orders to log and view time.',
    'description': """
Manufacturing Timesheet
======================
Adds a **Timesheets** tab on the Manufacturing Order form so you can:
- View timesheet lines linked to the MO (analytic account).
- Log time spent on the order (employee, hours, description).

Requires an analytic account on the MO (optional field). Time is stored
as standard analytic lines (account.analytic.line) for reporting and costing.
    """,
    'author': 'Local',
    'license': 'LGPL-3',
    'depends': ['mrp', 'hr_timesheet', 'stock_account', 'hr', 'project'],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/hr_employee_views.xml',
        'views/mrp_bom_views.xml',
        'views/mrp_production_views.xml',
        'views/res_company_views.xml',
        'views/mrp_workcenter_views.xml',
        'views/project_project_views.xml',
        'views/account_analytic_line_views.xml',
        'views/labor_clearing_check_wizard_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'post_init_hook': 'post_init_hook',
}
