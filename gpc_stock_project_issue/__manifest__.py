# Copyright 2026
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).
{
    "name": "GPC Stock Project Issue",
    "summary": "Phase 1 scaffold — project material issue from stock (Task 5)",
    "version": "19.0.1.0.0",
    "category": "Inventory/Accounting",
    "author": "GPC",
    "license": "LGPL-3",
    "depends": [
        "stock",
        "stock_account",
        "account",
        "project",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/res_company_views.xml",
        "views/stock_picking_type_views.xml",
        "views/stock_picking_views.xml",
        "wizard/project_issue_wizard_views.xml",
    ],
    "installable": True,
    "application": False,
}
