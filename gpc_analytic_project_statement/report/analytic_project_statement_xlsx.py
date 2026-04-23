# Copyright 2026
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from datetime import datetime, time as time_cls

from odoo import _, models


class ReportAnalyticProjectStatementXlsx(models.AbstractModel):
    # Short technical name: PG identifier limit 63 chars on derived table name.
    _name = "report.gpc_aps.proj_stmt_xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "Analytic Project Statement XLSX"

    def generate_xlsx_report(self, workbook, data, objects):
        wizard = objects[:1]
        wizard.ensure_one()
        rows = wizard._get_report_phase1_rows()
        currency = wizard.company_id.currency_id

        sheet = workbook.add_worksheet("Project Statement")
        sheet.set_column(0, 0, 12)
        sheet.set_column(1, 1, 22)
        sheet.set_column(2, 3, 40)
        sheet.set_column(4, 5, 16)

        fmt_header = workbook.add_format({"bold": True})
        fmt_date = workbook.add_format({"num_format": "yyyy-mm-dd"})
        # Plain decimal format — avoids Excel/viewers treating values as serial dates
        # (e.g. 300 shown as a “time” or 1900-date). Currency symbol is omitted here;
        # amounts are in company currency (see wizard Company field).
        places = max(0, int(currency.decimal_places or 2))
        fmt_amount = workbook.add_format(
            {"num_format": "#,##0." + ("0" * places)}
        )

        headers = [
            _("Date"),
            _("Transaction / Move Number"),
            _("Project"),
            _("Account"),
            _("Debit"),
            _("Credit"),
        ]
        for col, title in enumerate(headers):
            sheet.write(0, col, title, fmt_header)

        row_pos = 1
        for rec in rows:
            line_date = rec["date"]
            if line_date:
                sheet.write_datetime(
                    row_pos,
                    0,
                    datetime.combine(line_date, time_cls.min),
                    fmt_date,
                )
            else:
                sheet.write(row_pos, 0, "", fmt_date)

            sheet.write(row_pos, 1, rec["move_name"] or "")
            sheet.write(row_pos, 2, rec["project"] or "")
            sheet.write(row_pos, 3, rec["account"] or "")
            sheet.write_number(row_pos, 4, rec["debit"], fmt_amount)
            sheet.write_number(row_pos, 5, rec["credit"], fmt_amount)
            row_pos += 1
