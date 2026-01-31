# -*- coding: utf-8 -*-
{
    'name': 'Company Stock Journal (UI)',
    'version': '19.0.1.0',
    'category': 'Inventory/Inventory',
    'summary': 'Expose Stock Journal on company form for inventory valuation.',
    'description': """
Company Stock Journal (UI)
==========================
Makes the company field **Stock Journal** (account_stock_journal_id) visible and
editable on the company form (Settings > Companies). Required for automated
inventory valuation and MO Produce All when creating stock valuation journal entries.

- Inherits base company form; no new menus or actions.
- Compatible with Odoo Community stock_account / wms_accounting.
    """,
    'author': 'Local',
    'license': 'LGPL-3',
    'depends': ['base', 'account', 'stock', 'stock_account'],
    'data': [
        'views/res_company_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
