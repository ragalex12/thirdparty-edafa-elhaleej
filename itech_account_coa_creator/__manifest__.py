# -*- coding: utf-8 -*-
{
    'name': "iTech Account COA Creator",
    'summary': """
        Restrict account creation to COA Creator group only""",
    'description': """
        Account COA Creator
        ===================
        
        This module restricts account management to a specific security group, 
        ensuring only authorized users can create, modify, or delete accounts 
        in the Chart of Accounts (COA).
        
        Features:
        ---------
        - New security group: "COA Creator"
        - Only users in this group can create, modify, or delete accounts
        - All other groups (including Accounting Managers) are restricted
        - Integrates with Odoo 19 Enterprise Accounting module
        
        Security:
        ---------
        - Account creation: Restricted to COA Creator group only
        - Account modification: Restricted to COA Creator group only
        - Account deletion: Restricted to COA Creator group only
        - Read access: Maintained for users with standard accounting access
    """,
    'author': "iTech",
    'website': "http://www.iTech.com.eg",
    'category': 'Accounting/Accounting',
    'version': '19.0.1.0.0',
    'depends': [
        'base',
        'account',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/account_menu_views.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}

