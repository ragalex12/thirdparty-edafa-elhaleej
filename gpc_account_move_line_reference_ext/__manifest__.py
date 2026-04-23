# -*- coding: utf-8 -*-
{
    "name": "GPC Account Move Line Reference Extension",
    "version": "19.0.1.0.0",
    "category": "Accounting",
    "summary": "Journal item reference fields for manual journal entries.",
    "description": "Phase 1 scaffold for journal item reference fields on account.move.line.",
    "author": "GPC",
    "license": "LGPL-3",
    "depends": ["account"],
    "data": [
        "views/account_move_views.xml",
        "views/account_move_line_search_views.xml"
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
