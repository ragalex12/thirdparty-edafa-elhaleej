{
    'name': "Company Header Footer",
    'summary': 'Custom Header and Footer Images for Reports per Company',
    'description': """
Company Header Footer
=====================
This module allows each company to have custom header and footer images (JPG) for reports
instead of using the default Odoo settings.

Features:
* Custom JPG header image per company
* Custom JPG footer image per company
* Enable/disable custom header and footer independently
* Works with all Odoo reports
    """,
    'author': "iTech Co.",
    'website': 'http://www.iTech.com.eg',
    'category': 'Reporting',
    'version': "19.0.1.0.0",
    'license': 'LGPL-3',
    'depends': ['base', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_company_views.xml',
        'report/custom_external_layout.xml',
    ],
    'assets': {},
    'installable': True,
    'auto_install': False,
    'application': False,
    'post_init_hook': None,
    'uninstall_hook': None,
}

