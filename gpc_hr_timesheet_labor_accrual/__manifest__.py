# Copyright 2026
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).
{
    "name": "GPC HR Timesheet Labor Accrual",
    "summary": "Monthly labor accrual batches from validated non-MO timesheets (Phase 1 scaffold)",
    "version": "19.0.1.0.0",
    "category": "Human Resources/Accounting",
    "author": "GPC",
    "license": "LGPL-3",
    "depends": [
        "hr_timesheet",
        "account",
        "mrp_timesheet",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/res_company_views.xml",
        "views/labor_accrual_batch_views.xml",
        "wizard/labor_accrual_batch_wizard_views.xml",
        "menuitems.xml",
    ],
    "installable": True,
    "application": False,
}
