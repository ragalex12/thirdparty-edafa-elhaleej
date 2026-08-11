# Copyright 2026
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from datetime import datetime, time as time_cls

from odoo import _, models


# Visual styling only. Column set is the existing Phase-1 report fields.
# Do not add Industrial P&L categories (مواد / أجور / overhead / مبيعات).
_HEADER_FILL = "#5B9BD5"
_HEADER_FONT = "#FFFFFF"
_TITLE_FONT = "#1F4E79"
_ALT_FILL = "#D6EAF8"
_TOTAL_FILL = "#BDD7EE"
_BORDER = "#2E75B6"
_FONT = "Calibri"


class ReportAnalyticProjectStatementXlsx(models.AbstractModel):
    # Short technical name: PG identifier limit 63 chars on derived table name.
    _name = "report.gpc_aps.proj_stmt_xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "Analytic Project Statement XLSX"

    def _phase1_xlsx_headers(self):
        """Display labels for existing row keys only (Arabic visual + English key)."""
        return [
            (_("Date"), "التاريخ"),
            (_("Transaction / Move Number"), "رقم الحركة"),
            (_("Project"), "المشروع"),
            (_("Account"), "الحساب"),
            (_("Debit"), "مدين"),
            (_("Credit"), "دائن"),
        ]

    def generate_xlsx_report(self, workbook, data, objects):
        wizard = objects[:1]
        wizard.ensure_one()
        rows = wizard._get_report_phase1_rows()
        currency = wizard.company_id.currency_id
        places = max(0, int(currency.decimal_places or 2))
        amount_fmt = "#,##0." + ("0" * places)

        sheet = workbook.add_worksheet(_("Project Statement"))
        sheet.right_to_left()
        sheet.set_landscape()
        sheet.set_paper(9)
        sheet.fit_to_pages(1, 0)
        sheet.set_margins(left=0.6, right=0.6, top=0.7, bottom=0.7)
        sheet.hide_gridlines(2)
        sheet.set_default_row(18)

        # Column 0 is the rightmost column when right_to_left is on.
        sheet.set_column(0, 0, 14)
        sheet.set_column(1, 1, 28)
        sheet.set_column(2, 2, 36)
        sheet.set_column(3, 3, 38)
        sheet.set_column(4, 5, 16)

        common = {
            "font_name": _FONT,
            "font_size": 11,
            "border": 1,
            "border_color": _BORDER,
            "valign": "vcenter",
            "reading_order": 2,
        }
        fmt_title = workbook.add_format(
            {
                "font_name": _FONT,
                "font_size": 18,
                "bold": True,
                "font_color": _TITLE_FONT,
                "align": "center",
                "valign": "vcenter",
                "reading_order": 2,
            }
        )
        fmt_meta = workbook.add_format(
            {
                "font_name": _FONT,
                "font_size": 11,
                "italic": True,
                "font_color": "#5B5B5B",
                "align": "center",
                "valign": "vcenter",
                "reading_order": 2,
            }
        )
        fmt_header = workbook.add_format(
            {
                **common,
                "bold": True,
                "font_color": _HEADER_FONT,
                "bg_color": _HEADER_FILL,
                "align": "center",
                "text_wrap": True,
            }
        )
        fmt_text = workbook.add_format({**common, "align": "right", "text_wrap": True})
        fmt_text_alt = workbook.add_format(
            {**common, "align": "right", "text_wrap": True, "bg_color": _ALT_FILL}
        )
        fmt_date = workbook.add_format(
            {**common, "num_format": "yyyy-mm-dd", "align": "center"}
        )
        fmt_date_alt = workbook.add_format(
            {
                **common,
                "num_format": "yyyy-mm-dd",
                "align": "center",
                "bg_color": _ALT_FILL,
            }
        )
        fmt_amount = workbook.add_format(
            {**common, "num_format": amount_fmt, "align": "center"}
        )
        fmt_amount_alt = workbook.add_format(
            {
                **common,
                "num_format": amount_fmt,
                "align": "center",
                "bg_color": _ALT_FILL,
            }
        )
        fmt_total_label = workbook.add_format(
            {
                **common,
                "bold": True,
                "bg_color": _TOTAL_FILL,
                "align": "center",
            }
        )
        fmt_total_amt = workbook.add_format(
            {
                **common,
                "bold": True,
                "num_format": amount_fmt,
                "bg_color": _TOTAL_FILL,
                "align": "center",
            }
        )

        title = _("Analytic Project Statement")
        period = "%s  →  %s" % (wizard.date_from or "", wizard.date_to or "")
        meta = "%s  |  %s  |  %s" % (
            wizard.company_id.display_name or "",
            period,
            currency.display_name or currency.name or "",
        )

        sheet.set_row(0, 28)
        sheet.set_row(1, 20)
        sheet.set_row(2, 8)
        sheet.merge_range(0, 0, 0, 5, title, fmt_title)
        sheet.merge_range(1, 0, 1, 5, meta, fmt_meta)

        headers = self._phase1_xlsx_headers()
        sheet.set_row(3, 28)
        for col, (en_label, ar_label) in enumerate(headers):
            sheet.write(3, col, "%s\n%s" % (ar_label, en_label), fmt_header)

        sheet.freeze_panes(4, 0)
        sheet.repeat_rows(0, 3)

        row_pos = 4
        total_debit = 0.0
        total_credit = 0.0
        for rec in rows:
            alt = (row_pos - 4) % 2 == 1
            text_fmt = fmt_text_alt if alt else fmt_text
            date_fmt = fmt_date_alt if alt else fmt_date
            amt_fmt = fmt_amount_alt if alt else fmt_amount
            sheet.set_row(row_pos, 20)

            line_date = rec["date"]
            if line_date:
                sheet.write_datetime(
                    row_pos,
                    0,
                    datetime.combine(line_date, time_cls.min),
                    date_fmt,
                )
            else:
                sheet.write(row_pos, 0, "", date_fmt)

            sheet.write(row_pos, 1, rec["move_name"] or "", text_fmt)
            sheet.write(row_pos, 2, rec["project"] or "", text_fmt)
            sheet.write(row_pos, 3, rec["account"] or "", text_fmt)
            debit = rec["debit"] or 0.0
            credit = rec["credit"] or 0.0
            sheet.write_number(row_pos, 4, debit, amt_fmt)
            sheet.write_number(row_pos, 5, credit, amt_fmt)
            total_debit += debit
            total_credit += credit
            row_pos += 1

        if rows:
            sheet.set_row(row_pos, 22)
            sheet.merge_range(
                row_pos, 0, row_pos, 3, _("Total") + " / الإجمالي", fmt_total_label
            )
            sheet.write_number(row_pos, 4, total_debit, fmt_total_amt)
            sheet.write_number(row_pos, 5, total_credit, fmt_total_amt)

        sheet.set_print_scale(100)
        last_row = max(row_pos, 4)
        sheet.print_area(0, 0, last_row, 5)
