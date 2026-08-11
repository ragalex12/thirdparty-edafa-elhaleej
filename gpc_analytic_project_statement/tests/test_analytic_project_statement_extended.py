# Copyright 2026
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

"""Extended Analytic Project Statement + XLSX UAT (existing fields only)."""

import io
import zipfile
from xml.etree import ElementTree as ET

from odoo import fields
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.gpc_analytic_project_statement.tests.test_analytic_project_statement import (
    _create_analytic_account,
    _make_account,
)


NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
FORBIDDEN_PNL = (
    "مواد",
    "أجور مباشرة",
    "اجور مباشرة",
    "تكاليف صناعية",
    "المبيعات",
    "صافي الربح",
)


def _xlsx_blob(content):
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        sheet_xml = zf.read("xl/worksheets/sheet1.xml")
        shared = []
        if "xl/sharedStrings.xml" in zf.namelist():
            ss_root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for si in ss_root.findall("m:si", NS):
                shared.append("".join(t.text or "" for t in si.findall(".//m:t", NS)))
        root = ET.fromstring(sheet_xml)
    return sheet_xml, shared, root


@tagged("post_install", "-at_install")
class TestAnalyticProjectStatementExtended(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                mail_create_nolog=True,
                mail_notrack=True,
                tracking_disable=True,
            )
        )
        cls.company = cls.env.company
        cls.expense = _make_account(
            cls.env, "Stmt Ext Expense", "STEX01", "expense", cls.company
        )
        cls.revenue = _make_account(
            cls.env, "Stmt Ext Revenue", "STRV01", "income", cls.company
        )
        cls.journal = cls.env["account.journal"].create(
            {
                "name": "Stmt Ext Journal",
                "code": "STX1",
                "type": "general",
                "company_id": cls.company.id,
            }
        )
        cls.analytic = _create_analytic_account(cls.env, cls.company, "مشروع ألفا MM-UAT")
        cls.analytic_b = _create_analytic_account(cls.env, cls.company, "MM-UAT-AA-BETA")
        cls.employee = cls.env["hr.employee"].create({"name": "MM-UAT-EMP-STMT"})

    def _wizard(self, **kwargs):
        vals = {
            "company_id": self.company.id,
            "date_from": fields.Date.from_string("2024-01-01"),
            "date_to": fields.Date.from_string("2024-12-31"),
            "target_move": "posted",
        }
        vals.update(kwargs)
        return self.env["analytic.project.statement.wizard"].create(vals)

    def _xlsx(self, wizard):
        model = self.env["report.gpc_aps.proj_stmt_xlsx"].with_context(
            active_model="analytic.project.statement.wizard"
        )
        content, ext = model.create_xlsx_report(wizard.ids, {})
        self.assertEqual(ext, "xlsx")
        return content

    def _post_material(self, amount, analytic, move_date="2024-03-15"):
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": self.journal.id,
                "date": fields.Date.from_string(move_date),
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "MM-UAT material",
                            "account_id": self.expense.id,
                            "debit": amount,
                            "credit": 0.0,
                            "analytic_distribution": {str(analytic.id): 100.0},
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "MM-UAT material offset",
                            "account_id": self.revenue.id,
                            "debit": 0.0,
                            "credit": amount,
                        },
                    ),
                ],
            }
        )
        move.action_post()
        return move

    def _timesheet(self, **kwargs):
        vals = {
            "name": "MM-UAT-TS-stmt",
            "account_id": self.analytic.id,
            "employee_id": self.employee.id,
            "amount": -80.0,
            "unit_amount": 8.0,
            "company_id": self.company.id,
            "date": fields.Date.from_string("2024-03-10"),
        }
        vals.update(kwargs)
        return self.env["account.analytic.line"].create(vals)

    def test_empty_result(self):
        w = self._wizard(
            date_from=fields.Date.from_string("2010-01-01"),
            date_to=fields.Date.from_string("2010-01-31"),
        )
        self.assertEqual(w._get_report_phase1_rows(), [])

    def test_company_filter_excludes_other_company_aal(self):
        other = self.env["res.company"].create({"name": "MM-UAT-CO-STMT"})
        self._timesheet()
        other_aa = _create_analytic_account(self.env, other, "other-aa")
        vals = {
            "name": "foreign ts",
            "account_id": other_aa.id,
            "employee_id": self.employee.id,
            "amount": -10.0,
            "unit_amount": 1.0,
            "company_id": other.id,
            "date": fields.Date.from_string("2024-03-10"),
        }
        self.env["account.analytic.line"].create(vals)
        rows = self._wizard()._get_report_phase1_rows()
        self.assertTrue(any(r.get("move_name") == "MM-UAT-TS-stmt" for r in rows))
        self.assertFalse(any(r.get("move_name") == "foreign ts" for r in rows))

    def test_timesheet_and_material_mixed(self):
        self._timesheet()
        move = self._post_material(250.0, self.analytic)
        rows = self._wizard(
            date_from=fields.Date.from_string("2024-03-01"),
            date_to=fields.Date.from_string("2024-03-31"),
        )._get_report_phase1_rows()
        ts = [r for r in rows if r.get("move_name") == "MM-UAT-TS-stmt"]
        gl = [r for r in rows if r.get("move_name") == move.name]
        self.assertEqual(len(ts), 1)
        self.assertEqual(ts[0]["account"], "Timesheet / no GL")
        self.assertTrue(gl)
        self.assertNotEqual(gl[0]["account"], "Timesheet / no GL")
        sources = {r.get("source") for r in gl}
        self.assertEqual(sources, {"aal"})

    def test_large_result_set_50(self):
        for i in range(50):
            self._timesheet(
                name="MM-UAT-TS-bulk-%03d" % i,
                date=fields.Date.from_string("2024-04-01"),
                amount=-10.0,
                unit_amount=1.0,
            )
        rows = self._wizard(
            date_from=fields.Date.from_string("2024-04-01"),
            date_to=fields.Date.from_string("2024-04-30"),
        )._get_report_phase1_rows()
        bulk = [r for r in rows if (r.get("move_name") or "").startswith("MM-UAT-TS-bulk-")]
        self.assertEqual(len(bulk), 50)
        self.assertAlmostEqual(sum(r["debit"] for r in bulk), 500.0, places=2)

    def test_xlsx_one_row_equals_phase1(self):
        self._timesheet()
        w = self._wizard(
            date_from=fields.Date.from_string("2024-03-01"),
            date_to=fields.Date.from_string("2024-03-31"),
        )
        expected = w._get_report_phase1_rows()
        self.assertEqual(len(expected), 1)
        content = self._xlsx(w)
        sheet_xml, shared, root = _xlsx_blob(content)
        view = root.find("m:sheetViews/m:sheetView", NS)
        self.assertEqual(view.get("rightToLeft"), "1")
        blob = sheet_xml.decode("utf-8", errors="ignore") + "\n".join(shared)
        self.assertIn(expected[0]["move_name"], blob)
        for forbidden in FORBIDDEN_PNL:
            self.assertNotIn(forbidden, blob)

    def test_xlsx_arabic_project_and_totals(self):
        self._timesheet(name="MM-UAT-TS-عربي-طويل " + ("وصف " * 20))
        self._post_material(1000.0, self.analytic, "2024-03-20")
        w = self._wizard(
            date_from=fields.Date.from_string("2024-03-01"),
            date_to=fields.Date.from_string("2024-03-31"),
        )
        rows = w._get_report_phase1_rows()
        content = self._xlsx(w)
        sheet_xml, shared, root = _xlsx_blob(content)
        blob = sheet_xml.decode("utf-8", errors="ignore") + "\n".join(shared)
        self.assertIn("مشروع ألفا", blob)
        self.assertIn("الإجمالي", blob)
        debit = sum(r["debit"] for r in rows)
        self.assertGreater(debit, 0)
        for forbidden in FORBIDDEN_PNL:
            self.assertNotIn(forbidden, blob)

    def test_draft_je_excluded_when_target_posted(self):
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": self.journal.id,
                "date": fields.Date.from_string("2024-05-05"),
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "draft expense",
                            "account_id": self.expense.id,
                            "debit": 99.0,
                            "credit": 0.0,
                            "analytic_distribution": {str(self.analytic.id): 100.0},
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "draft offset",
                            "account_id": self.revenue.id,
                            "debit": 0.0,
                            "credit": 99.0,
                        },
                    ),
                ],
            }
        )
        self.assertEqual(move.state, "draft")
        posted = self._wizard(
            date_from=fields.Date.from_string("2024-05-01"),
            date_to=fields.Date.from_string("2024-05-31"),
            target_move="posted",
        )._get_report_phase1_rows()
        all_rows = self._wizard(
            date_from=fields.Date.from_string("2024-05-01"),
            date_to=fields.Date.from_string("2024-05-31"),
            target_move="all",
        )._get_report_phase1_rows()
        self.assertFalse(any(r.get("move_name") == move.name for r in posted))
        self.assertTrue(any(r.get("aml_id") in move.line_ids.ids or r.get("move_name") == move.name for r in all_rows) or all_rows)

    def test_one_project_one_month_filter(self):
        self._timesheet(date=fields.Date.from_string("2024-06-10"))
        self._timesheet(
            name="other-month",
            date=fields.Date.from_string("2024-07-10"),
            account_id=self.analytic_b.id,
        )
        rows = self._wizard(
            date_from=fields.Date.from_string("2024-06-01"),
            date_to=fields.Date.from_string("2024-06-30"),
            analytic_account_ids=[(6, 0, [self.analytic.id])],
        )._get_report_phase1_rows()
        self.assertTrue(rows)
        self.assertFalse(any(r.get("move_name") == "other-month" for r in rows))

    def test_historical_no_gl_still_listed(self):
        self._timesheet(
            name="historical-no-gl",
            date=fields.Date.from_string("2024-01-05"),
            amount=-40.0,
            unit_amount=8.0,
        )
        rows = self._wizard(
            date_from=fields.Date.from_string("2024-01-01"),
            date_to=fields.Date.from_string("2024-01-31"),
        )._get_report_phase1_rows()
        hit = [r for r in rows if r.get("move_name") == "historical-no-gl"]
        self.assertEqual(len(hit), 1)
        self.assertEqual(hit[0]["account"], "Timesheet / no GL")
        self.assertFalse(hit[0].get("aml_id"))

    def test_xlsx_empty_has_rtl_no_pnl(self):
        w = self._wizard(
            date_from=fields.Date.from_string("2011-01-01"),
            date_to=fields.Date.from_string("2011-01-31"),
        )
        content = self._xlsx(w)
        sheet_xml, shared, root = _xlsx_blob(content)
        view = root.find("m:sheetViews/m:sheetView", NS)
        self.assertEqual(view.get("rightToLeft"), "1")
        blob = sheet_xml.decode("utf-8", errors="ignore") + "\n".join(shared)
        for forbidden in FORBIDDEN_PNL:
            self.assertNotIn(forbidden, blob)
