# -*- coding: utf-8 -*-
{
    'name': 'Manufacturing Timesheet',
    'version': '19.0.1.0',
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
    'depends': ['mrp', 'hr_timesheet', 'stock_account', 'hr'],
    'post_init_hook': 'post_init_hook',
    'data': [
        'views/hr_employee_views.xml',
        'views/mrp_bom_views.xml',
        'views/mrp_production_views.xml',
        'views/res_company_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
