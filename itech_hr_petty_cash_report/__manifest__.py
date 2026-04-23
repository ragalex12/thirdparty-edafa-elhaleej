# -*- coding: utf-8 -*-
{
    'name': "Petty Cash report",

    'summary': """
        Print T/P advanced and putty cash report""",

    'description': """
        Print T/P advanced and putty cash report
    """,

    'author': "iTech Co.",
    'website': "http://www.itech.com.eg",

    'category': 'HR',
    'version': '19.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'petty_cash_management','account'],
    'license': 'AGPL-3',

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/hr_advance_report_views.xml',
        'views/hr_advance_report_template.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
