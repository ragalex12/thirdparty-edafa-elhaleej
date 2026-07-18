# Copyright 2026 GPC
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).
{
    "name": "GPC Gulf Project Extensions",
    "summary": "Project dashboard description/contract amount and dimension-based quotation pricing",
    "version": "19.0.1.0.0",
    "category": "Project",
    "author": "GPC",
    "license": "LGPL-3",
    "depends": [
        "project",
        "sale_management",
        "account",
        "itech_construction_project",
        "order_line_sequences",
        "retention_performance_bond",
    ],
    "data": [
        "views/project_project_views.xml",
        "views/sale_order_views.xml",
        "report/report_saleorder.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "gpc_gulf_project_ext/static/src/components/**/*",
        ],
    },
    "installable": True,
    "application": False,
}