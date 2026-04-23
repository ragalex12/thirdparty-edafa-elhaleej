# -*- coding: utf-8 -*-
#############################################################################
#                                                                           #
#    iTech Co.                                                              #
#                                                                           #
#    Copyright (C) 2020-iTech Technologies(<https://www.iTech.com.eg>).     #
#                                                                           #
#############################################################################
{
    "name": "iTech Construction Project",
    "summary": "Construction Project integration between modules",
    "version": "19.0.1.0",
    "category": "Project Management",
    'author': 'iTech',
    'company': 'iTech',
    'website': "https://www.itech.com.eg",
    "installable": True,
    "depends": [
        'base',
        'hr',
        'project',
        'stock',
        'sale',
        'sale_management',
        'purchase',
        'project_todo',
        'account',
        'product',
        'hr_timesheet',
    ],
    "data": [
        # Security
        "security/security.xml",
        "security/ir.model.access.csv",
        # Sequences
        "sequences/projects_seq.xml",
        # Data
        "data/project_data.xml",
        # Views - Main
        "views/project_view.xml",
        "views/project_type_views.xml",
        # Views - Cost Management
        "views/cost_header_view.xml",
        "views/cost_code_view.xml",
        # Views - Project Management
        "views/bill_of_quantity_view.xml",
        "views/work_package_view.xml",
        "views/construction_management.xml",
        "views/construction_snag_list_view.xml",
    ],
    "images": [
        'static/description/images/main_screenshot.png'
        ],
    "demo": [
        "demo/project_demo.xml",
    ],
}
