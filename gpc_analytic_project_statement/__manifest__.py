# Copyright 2026
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).
{
    "name": "GPC Analytic Project Statement",
    "summary": "Analytic / project statement XLSX (AAL-primary; Excel template style only)",
    "version": "19.0.1.8.0",
    "category": "Accounting/Reporting",
    "author": "GPC",
    "license": "LGPL-3",
    "depends": [
        "account",
        "report_xlsx",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizard/analytic_project_statement_wizard_views.xml",
        "report/analytic_project_statement_reports.xml",
        "menuitems.xml",
    ],
    "installable": True,
    "application": False,
}
