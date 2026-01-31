# -*- coding: utf-8 -*-
{
    'name': 'Stock Account Journal Fix & Debug',
    'version': '19.0.1.0',
    'category': 'Inventory/Inventory',
    'summary': 'Fix missing journal_id on account.move when completing MO; optional debug logging.',
    'description': """
Stock Account Journal Fix & Debug (Odoo 19)
============================================
- **Root cause**: stock_account's stock.move._create_account_move() uses only
  company_id.account_stock_journal_id. If the company has no Stock Journal set,
  account.move.create gets journal_id=False → ValidationError.
- **Fix**: Override _create_account_move to resolve journal from product category
  (property_stock_journal) then company fallback, matching get_product_accounts().
- **Debug**: Set config parameter stock_account_journal_fix.debug = True to log
  and raise when any account.move.create is called without journal_id (stack + vals).
    """,
    'author': 'Local',
    'license': 'LGPL-3',
    'depends': ['stock_account'],
    'installable': True,
    'auto_install': False,
}
