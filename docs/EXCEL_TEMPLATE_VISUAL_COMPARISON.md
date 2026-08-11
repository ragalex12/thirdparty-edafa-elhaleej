# Excel template visual comparison

Mode: **`EXCEL_TEMPLATE_STYLE_ONLY`**

Original file: `/opt/uploads/excel_assign_proof/تقرير الصناعي.xlsx`  
Generated file: `/home/sabry/evidence/gulf_mm_uat_20260811/xlsx/gulf_mm_analytic_statement.xlsx`  
Database: `trgcc_mm_uat` · wizard 2026-02-01 → 2026-09-30 · posted entries

Screenshots: `screenshots/43_*.png` … `47_excel_visual_comparison.png`

## Original template screenshot

`screenshots/43_original_excel_template.png`

RTL table with Industrial P&L headers: م، اسم المشروع، مواد، اجور مباشرة، تكاليف صناعية غير مباشرة، اجمالي التكاليف، المبيعات، صافي الربح. Sample projects only.

## Generated report screenshot

`screenshots/44_odoo_xlsx_new_design.png`

Same visual language (blue header, borders, alt rows, totals, RTL, Arabic labels) applied to the **existing** Analytic Project Statement columns.

## Similarities achieved

- RTL worksheet (`rightToLeft=1`)
- Arabic-friendly headers (Arabic line + existing English field name)
- Calibri-family font, 11pt body, 18pt title
- Dark-blue header, white text, thin blue borders
- Alternating row fill
- Totals row styling (`الاجمالي`) using **sum of displayed Debit/Credit**
- Landscape / fit-to-width print, frozen header, column widths
- Company + period in the title block (wizard fields already on the report)

## Remaining visual differences (unavoidable)

| Difference | Reason |
|------------|--------|
| No مواد / أجور مباشرة / overhead / مبيعات / صافي الربح columns | Not in the current report dataset. Explicitly out of scope (`EXCEL_TEMPLATE_STYLE_ONLY`, not Industrial P&L). |
| Six columns instead of eight | Current Phase-1 fields are Date, Move, Project, Account, Debit, Credit. |
| No serial column `م` | Not an existing report field. |
| Dates as `yyyy-mm-dd` | Existing report date field; Excel serial is formatting only. |
| Bilingual header cells | Keep the existing English field identity visible. |
| Data rows are live GCC UAT AALs, not Mohammad’s two sample projects | Presentation of the real statement, not dummy P&L numbers. |

## Accounting logic impact

**Accounting/business logic changes from Excel template: NONE**

- `_get_report_phase1_rows()` unchanged
- AAL-primary, Timesheet / no GL, JE-once, no AML/AAL double count unchanged
- Totals row = arithmetic sum of the same debit/credit cells already written
- Generated XLSX totals **7700.00 debit / 106000.00 credit** equal Phase-1 JSON sums

## Existing field mapping

| Current report field (`_get_report_phase1_rows`) | XLSX column (RTL: A is rightmost) |
|--------------------------------------------------|-----------------------------------|
| `date` | التاريخ / Date |
| `move_name` | رقم الحركة / Transaction / Move Number |
| `project` | المشروع / Project |
| `account` | الحساب / Account (includes `Timesheet / no GL`) |
| `debit` | مدين / Debit |
| `credit` | دائن / Credit |
| wizard `company_id`, `date_from`, `date_to`, currency | title/meta row |
| sum(`debit`), sum(`credit`) | Total / الإجمالي |

Not mapped (not in dataset): مواد، أجور مباشرة، تكاليف صناعية غير مباشرة، المبيعات، صافي الربح.
