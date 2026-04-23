# -*- coding: utf-8 -*-
{
    'name': 'Petty Expenses and bill invoice',
    'version': '19.0.1.0.0',
    'summary': """Manage the expenses""",
    'description': 'Manage the expenses',
    'category': 'Generic Modules/Human Resources',
    'author': 'iTech',
    'company': 'iTech',
    'maintainer': 'iTech',
    'website': "https://www.itech.com.eg",
    'depends': ['hr', 'mail', 'hr_expense','petty_cash_management','account'],
    'data': [
        'security/ir.model.access.csv',
        'views/expenses_view.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}

