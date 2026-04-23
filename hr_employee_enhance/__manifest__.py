# -*- coding: utf-8 -*-
#############################################################################
#                                                                           #
#    iTech Co.                                                              #
#                                                                           #
#    Copyright (C) 2020-iTech Technologies(<https://www.iTech.com.eg>).     #
#                                                                           #
#############################################################################
{
    'name': 'HR Employee Info',
    'version': '19.0.1.0',
    'summary': """Adding Advanced Fields In Employee Master""",
    'description': 'This module helps you to add more information in employee records.',
    'category': 'Generic Modules/Human Resources',
    'author': 'iTech',
    'company': 'iTech',
    'website': "https://www.itech.com.eg",
    'depends': ['base', 'hr', 'mail','product'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/hr_employee_view.xml',
        'views/hr_notification.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
