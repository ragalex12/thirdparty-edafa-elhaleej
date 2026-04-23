# -*- coding: utf-8 -*-
{
    "name": "Retention & Performance Bond",
    "version": "19.0.1.0.0",
    "category": "Accounting/Accounting",
    "summary": "Project invoicing with retention and performance bond ",
    "description": """
        Extends customer invoices with:
        - Contract/PO/Invoice references
        - Performance bond
        - Retention %
        Creates extra journal lines on post to split receivable (retention , performance bond).
    """,
    "author": "iTech",
    "website": "https://www.itech.com.eg",
    "license": "LGPL-3",
    "depends": ["account", "project", "mail", "sale"],
    "data": [
        "security/ir.model.access.csv",
        "views/account_move_views.xml",
        "views/res_config_settings_views.xml",
        "views/report_invoice.xml",
        "views/report_saleorder.xml",
    ],
    "installable": True,
    "application": False,
}
