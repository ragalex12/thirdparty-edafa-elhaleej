# -*- coding: utf-8 -*-
{
    'name': "Tax Details Report",

    'summary': """
        Print Tax Report""",

    'description': """
        Print Tax Report
    """,

    'author': "iTech Co.",
    'website': "http://www.itech.com.eg",

    'category': 'account',
    'version': '19.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base','base_accounting_kit'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/tax_report_views.xml',
        'views/tax_report_template.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}