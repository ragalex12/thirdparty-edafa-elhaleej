# -*- coding: utf-8 -*-
#############################################################################
#                                                                           #
#    iTech Co.                                                              #
#                                                                           #
#    Copyright (C) 2020-iTech Technologies(<https://www.iTech.com.eg>).     #
#                                                                           #
#############################################################################
{
    "name": "iTech Mostakhlas Link",
    "summary": "Link Vendor Bills to BOQ Lines with Quantity Validation",
    "version": "19.0.1.0",
    "category": "Project Management",
    'author': 'iTech',
    'company': 'iTech',
    'website': "https://www.itech.com.eg",
    "installable": True,
    "depends": [
        'itech_construction_project',
        'account',
    ],
    "data": [
        # Security
        "security/ir.model.access.csv",
        # Views
        "views/bill_of_quantity_view.xml",
        "views/account_move_view.xml",
    ],
    "auto_install": False,
    "application": False,
}

