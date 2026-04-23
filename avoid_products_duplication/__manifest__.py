#############################################################################
# -*- coding: utf-8 -*-
###############################################################################
#
#    BeyonData Solutions Private Limited
#
#    Copyright (C) 2024-TODAY BeyonData Solutions Private Limited
#    Author:BeyonData Solutions Private Limited
#
#   
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  S
#
###############################################################################

{
    'name':'Avoid Products Duplication',
    'author': 'BeyonData Solutions Private Limited',
    'website': 'https://www.beyondatagroup.com/',
    
    'depends':['base','mail','sale_management'],
    'summary':"""
    Avoid Products Duplication enhances Odoo with powerful features to improve productivity, automation, and business efficiency.
    avoid product duplication odoo| prevent duplicate products| product validation odoo| inventory data accuracy| product master control| duplicate product restriction| odoo product management
    """,
    'description': """
   Avoid Products Duplication is a powerful Odoo module designed to prevent duplicate product records during product creation and updates.
    It helps businesses maintain clean, accurate, and consistent product data across Inventory, Sales, Purchase, and POS modules.
    Duplicate products often lead to inventory mismatches, pricing errors, and reporting issues. This module eliminates those problems by enforcing smart duplication control rules.
    """,
    'category':'sales',
    "license": "OPL-1",
    'version': '1.0',
    'live_test_url': 'https://www.beyondatagroup.com/contactus',
    'data':[
        'views/duplication_settings.xml',
    ],
    'images': ['static/description/banners.gif'],
    # 'images': ['static/description/sale_banner.gif'],
    
}
