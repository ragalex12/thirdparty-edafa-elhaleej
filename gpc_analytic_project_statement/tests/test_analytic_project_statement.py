# Copyright 2026
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


def _make_account(env, name, code, account_type, company):
    return env["account.account"].create(
        {
            "name": name,
            "code": code,
            "account_type": account_type,
            "company_ids": [(6, 0, [company.id])],
        }
    )


def _create_analytic_account(env, company, name):
    """Minimal Odoo 19 analytic account: plan has no company_id on this schema."""
    vals = {"name": name}
    if "company_id" in env["account.analytic.account"]._fields:
        vals["company_id"] = company.id
    if "plan_id" in env["account.analytic.account"]._fields:
        Plan = env["account.analytic.plan"]
        domain = []
        if "company_id" in Plan._fields:
            domain = [("company_id", "in", [False, company.id])]
        plan = Plan.search(domain, limit=1)
        if not plan:
            plan_vals = {"name": "GPC Test Analytic Plan"}
            if "company_id" in Plan._fields:
                plan_vals["company_id"] = company.id
            plan = Plan.create(plan_vals)
        vals["plan_id"] = plan.id
    return env["account.analytic.account"].create(vals)


@tagged("post_install", "-at_install")
class TestAnalyticProjectStatementPhase1(TransactionCase):
    """Phase 1 tests for wizard domain, row builder, and XLSX wiring."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                mail_create_nolog=True,
                mail_create_nosubscribe=True,
                mail_notrack=True,
                no_reset_password=True,
                tracking_disable=True,
            )
        )
        cls.company = cls.env.company
        cls.expense = _make_account(
            cls.env, "GPC Stmt Expense", "GPSEX99", "expense", cls.company
        )
        cls.revenue = _make_account(
            cls.env, "GPC Stmt Revenue", "GPSRV99", "income", cls.company
        )
        cls.journal_a = cls.env["account.journal"].create(
            {
                "name": "GPC Test Journal A",
                "code": "GPSA",
                "type": "general",
                "company_id": cls.company.id,
            }
        )
        cls.journal_b = cls.env["account.journal"].create(
            {
                "name": "GPC Test Journal B",
                "code": "GPSB",
                "type": "general",
                "company_id": cls.company.id,
            }
        )
        cls.analytic_aa = _create_analytic_account(cls.env, cls.company, "GPC Proj A")
        cls.analytic_bb = _create_analytic_account(cls.env, cls.company, "GPC Proj B")

    def _wizard(self, **kwargs):
        vals = {
            "company_id": self.company.id,
            "date_from": fields.Date.from_string("2020-01-01"),
            "date_to": fields.Date.from_string("2020-12-31"),
            "target_move": "posted",
            "journal_ids": [(6, 0, [self.journal_a.id, self.journal_b.id])],
            "analytic_account_ids": [
                (6, 0, [self.analytic_aa.id, self.analytic_bb.id])
            ],
        }
        vals.update(kwargs)
        return self.env["analytic.project.statement.wizard"].create(vals)

    def _create_balanced_move(
        self,
        journal,
        move_date,
        expense_line_debit,
        analytic_distribution,
        line_date=None,
        skip_analytic_on_expense=False,
    ):
        """Create a draft misc entry: debit expense, credit revenue."""
        exp_vals = {
            "name": "gpc test expense",
            "account_id": self.expense.id,
            "debit": expense_line_debit,
            "credit": 0.0,
        }
        if not skip_analytic_on_expense and analytic_distribution is not None:
            exp_vals["analytic_distribution"] = analytic_distribution
        if line_date and "date" in self.env["account.move.line"]._fields:
            exp_vals["date"] = line_date
        return self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": journal.id,
                "date": move_date,
                "line_ids": [
                    (0, 0, exp_vals),
                    (
                        0,
                        0,
                        {
                            "name": "gpc test revenue",
                            "account_id": self.revenue.id,
                            "debit": 0.0,
                            "credit": expense_line_debit,
                        },
                    ),
                ],
            }
        )

    def _post_balanced_move(self, *args, **kwargs):
        """Create a posted misc entry: debit expense, credit revenue."""
        move = self._create_balanced_move(*args, **kwargs)
        move._post(soft=False)
        self.assertEqual(move.state, "posted")
        return move

    # ── Registration / smoke ─────────────────────────────────────────────────

    def test_wizard_model_registered(self):
        self.env["analytic.project.statement.wizard"]

    def test_xlsx_report_model_registered(self):
        self.env["report.gpc_aps.proj_stmt_xlsx"]

    # ── Domain / source ───────────────────────────────────────────────────────

    def test_domain_includes_company_and_date_and_posted(self):
        self._post_balanced_move(
            self.journal_a,
            fields.Date.from_string("2020-06-15"),
            100.0,
            {str(self.analytic_aa.id): 100.0},
        )
        w = self._wizard(
            date_from=fields.Date.from_string("2020-06-01"),
            date_to=fields.Date.from_string("2020-06-30"),
            target_move="posted",
        )
        dom = w._get_aml_domain()
        self.assertIn(("company_id", "=", self.company.id), dom)
        self.assertIn(("date", ">=", w.date_from), dom)
        self.assertIn(("date", "<=", w.date_to), dom)
        self.assertIn(("move_id.state", "=", "posted"), dom)
        aml = w._get_aml_source_recordset()
        self.assertTrue(aml)
        for line in aml:
            self.assertEqual(line.company_id, self.company)
            self.assertTrue(line.date >= w.date_from)
            self.assertTrue(line.date <= w.date_to)
            self.assertEqual(line.move_id.state, "posted")

    def test_date_range_excludes_outside_lines(self):
        self._post_balanced_move(
            self.journal_a,
            fields.Date.from_string("2020-03-10"),
            50.0,
            {str(self.analytic_aa.id): 100.0},
        )
        w = self._wizard(
            date_from=fields.Date.from_string("2020-01-01"),
            date_to=fields.Date.from_string("2020-02-29"),
        )
        self.assertFalse(w._get_aml_source_recordset())

    def test_target_move_posted_excludes_draft(self):
        move = self._post_balanced_move(
            self.journal_a,
            fields.Date.from_string("2020-05-01"),
            80.0,
            {str(self.analytic_aa.id): 100.0},
        )
        move.button_draft()
        w = self._wizard(target_move="posted")
        self.assertFalse(w._get_aml_source_recordset())

    def test_target_move_all_includes_draft(self):
        move = self._post_balanced_move(
            self.journal_a,
            fields.Date.from_string("2020-05-01"),
            80.0,
            {str(self.analytic_aa.id): 100.0},
        )
        move.button_draft()
        w = self._wizard(target_move="all")
        aml = w._get_aml_source_recordset()
        self.assertTrue(aml.filtered(lambda l: l.move_id.id == move.id))

    def test_journal_filter(self):
        self._post_balanced_move(
            self.journal_a,
            fields.Date.from_string("2020-04-01"),
            10.0,
            {str(self.analytic_aa.id): 100.0},
        )
        self._post_balanced_move(
            self.journal_b,
            fields.Date.from_string("2020-04-01"),
            20.0,
            {str(self.analytic_aa.id): 100.0},
        )
        w = self._wizard(journal_ids=[(6, 0, [self.journal_b.id])])
        aml = w._get_aml_source_recordset()
        self.assertTrue(aml)
        self.assertEqual(set(aml.mapped("journal_id")), {self.journal_b})

    def test_account_filter(self):
        self._post_balanced_move(
            self.journal_a,
            fields.Date.from_string("2020-04-01"),
            10.0,
            {str(self.analytic_aa.id): 100.0},
        )
        w = self._wizard(account_ids=[(6, 0, [self.revenue.id])])
        self.assertFalse(w._get_aml_source_recordset())
        w2 = self._wizard(account_ids=[(6, 0, [self.expense.id])])
        self.assertTrue(w2._get_aml_source_recordset())

    def test_excludes_lines_without_analytic_distribution(self):
        self._post_balanced_move(
            self.journal_a,
            fields.Date.from_string("2020-07-01"),
            33.0,
            None,
            skip_analytic_on_expense=True,
        )
        w = self._wizard()
        self.assertFalse(w._get_aml_source_recordset())

    def test_supplementary_rows_from_standalone_analytic_lines(self):
        """AML without analytic_distribution still exports rows when AAL exist (training DB case)."""
        self._post_balanced_move(
            self.journal_a,
            fields.Date.from_string("2020-06-10"),
            40.0,
            None,
            skip_analytic_on_expense=True,
        )
        self.env["account.analytic.line"].create(
            {
                "name": "gpc standalone aal",
                "account_id": self.analytic_aa.id,
                "amount": -50.0,
                "company_id": self.company.id,
                "date": fields.Date.from_string("2020-06-10"),
            }
        )
        w = self._wizard(
            date_from=fields.Date.from_string("2020-06-01"),
            date_to=fields.Date.from_string("2020-06-30"),
            journal_ids=[(5, 0, 0)],
        )
        rows = w._get_report_phase1_rows()
        self.assertTrue(
            any(r.get("move_name") == "gpc standalone aal" for r in rows),
            "Standalone analytic lines must appear when journal items have no distribution",
        )
        self.assertAlmostEqual(
            sum(r["debit"] for r in rows if r.get("move_name") == "gpc standalone aal"),
            50.0,
            places=2,
            msg="Negative analytic amount is shown as debit (cost)",
        )

    def test_analytic_filter_lines_and_slices(self):
        self._post_balanced_move(
            self.journal_a,
            fields.Date.from_string("2020-08-01"),
            100.0,
            {
                str(self.analytic_aa.id): 40.0,
                str(self.analytic_bb.id): 60.0,
            },
        )
        w_all = self._wizard()
        rows_all = w_all._get_report_phase1_rows()
        self.assertEqual(len(rows_all), 2)

        w_aa = self._wizard(
            analytic_account_ids=[(6, 0, [self.analytic_aa.id])],
        )
        aml_aa = w_aa._get_aml_source_recordset()
        self.assertTrue(aml_aa)
        rows_aa = w_aa._get_report_phase1_rows()
        self.assertEqual(len(rows_aa), 1)
        self.assertAlmostEqual(rows_aa[0]["debit"], 40.0, places=2)

    # ── Row builder ───────────────────────────────────────────────────────────

    def test_one_key_one_row(self):
        self._post_balanced_move(
            self.journal_a,
            fields.Date.from_string("2020-09-01"),
            25.0,
            {str(self.analytic_aa.id): 100.0},
        )
        rows = self._wizard()._get_report_phase1_rows()
        self.assertEqual(len(rows), 1)

    def test_multiple_keys_multiple_rows(self):
        self._post_balanced_move(
            self.journal_a,
            fields.Date.from_string("2020-09-02"),
            100.0,
            {
                str(self.analytic_aa.id): 50.0,
                str(self.analytic_bb.id): 50.0,
            },
        )
        rows = self._wizard()._get_report_phase1_rows()
        self.assertEqual(len(rows), 2)

    def test_fractional_weights_sum_to_one_not_treated_as_one_percent(self):
        """0.5+0.5 on AML are proportions, not 0.5%% (AML fallback path).

        Posted JEs create AAL; Odoo 19 may persist 0.5 as 0.5% on those AAL.
        This assertion is for the AML explosion fallback, so the move stays
        draft and any auto-created AAL are removed.
        """
        move = self._create_balanced_move(
            self.journal_a,
            fields.Date.from_string("2020-09-21"),
            200.0,
            {
                str(self.analytic_aa.id): 0.5,
                str(self.analytic_bb.id): 0.5,
            },
        )
        self.assertEqual(move.state, "draft")
        aals = self.env["account.analytic.line"].search(
            [("move_line_id", "in", move.line_ids.ids)]
        )
        if aals:
            aals.unlink()
        rows = self._wizard(target_move="all")._get_report_phase1_rows()
        self.assertEqual(len(rows), 2)
        self.assertAlmostEqual(
            sum(r["debit"] for r in rows), 200.0, places=2
        )
        for r in rows:
            self.assertAlmostEqual(r["debit"], 100.0, places=2)
            self.assertEqual(r["credit"], 0.0)
            self.assertEqual(r.get("source"), "aml")

    def test_allocated_debit_credit_sum_matches_line(self):
        move = self._post_balanced_move(
            self.journal_a,
            fields.Date.from_string("2020-09-03"),
            123.45,
            {
                str(self.analytic_aa.id): 30.0,
                str(self.analytic_bb.id): 70.0,
            },
        )
        exp_line = move.line_ids.filtered(lambda l: l.account_id == self.expense)
        self.assertEqual(len(exp_line), 1)
        currency = self.company.currency_id
        rows = self._wizard()._get_report_phase1_rows()
        self.assertEqual(len(rows), 2)
        total_debit = currency.round(sum(r["debit"] for r in rows))
        total_credit = currency.round(sum(r["credit"] for r in rows))
        self.assertEqual(total_debit, currency.round(exp_line.debit))
        self.assertEqual(total_credit, currency.round(exp_line.credit))

    def test_row_move_name_and_line_date(self):
        move = self._post_balanced_move(
            self.journal_a,
            fields.Date.from_string("2020-10-01"),
            15.0,
            {str(self.analytic_aa.id): 100.0},
        )
        exp_line = move.line_ids.filtered(lambda l: l.account_id == self.expense)
        rows = self._wizard()._get_report_phase1_rows()
        self.assertEqual(rows[0]["move_name"], move.name)
        self.assertEqual(rows[0]["date"], exp_line.date)

    def test_line_specific_date_when_supported(self):
        line_date = fields.Date.from_string("2020-11-20")
        move_date = fields.Date.from_string("2020-11-01")
        if "date" not in self.env["account.move.line"]._fields:
            self.skipTest("AML has no independent date field in this Odoo version")
        move = self._post_balanced_move(
            self.journal_a,
            move_date,
            12.0,
            {str(self.analytic_aa.id): 100.0},
            line_date=line_date,
        )
        exp_line = move.line_ids.filtered(lambda l: l.account_id == self.expense)
        aal = self.env["account.analytic.line"].search(
            [("move_line_id", "in", exp_line.ids)], limit=1
        )
        if aal and aal.date != line_date:
            self.skipTest(
                "AAL-primary statement uses account.analytic.line.date; "
                "this Odoo 19 schema stores the journal date (%s) on AAL, "
                "not the AML line_date (%s)." % (aal.date, line_date)
            )
        rows = self._wizard(
            date_from=line_date,
            date_to=line_date,
        )._get_report_phase1_rows()
        self.assertTrue(rows)
        self.assertEqual(rows[0]["date"], exp_line.date if not aal else aal.date)

    # ── XLSX ─────────────────────────────────────────────────────────────────

    def test_xlsx_render_from_wizard_without_error(self):
        self._post_balanced_move(
            self.journal_a,
            fields.Date.from_string("2020-12-01"),
            9.0,
            {str(self.analytic_aa.id): 100.0},
        )
        wizard = self._wizard()
        self.env.ref(
            "gpc_analytic_project_statement.action_report_analytic_project_statement_xlsx"
        )
        xlsx_model = self.env[
            "report.gpc_aps.proj_stmt_xlsx"
        ].with_context(active_model="analytic.project.statement.wizard")
        content, ext = xlsx_model.create_xlsx_report(wizard.ids, {})
        self.assertEqual(ext, "xlsx")
        self.assertTrue(content)
        self.assertGreater(len(content), 500)

    def test_timesheet_without_gl_uses_label(self):
        employee = self.env["hr.employee"].create({"name": "Stmt TS Emp"})
        self.env["account.analytic.line"].create(
            {
                "name": "uat timesheet no gl",
                "account_id": self.analytic_aa.id,
                "employee_id": employee.id,
                "amount": -80.0,
                "unit_amount": 8.0,
                "company_id": self.company.id,
                "date": fields.Date.from_string("2020-06-15"),
            }
        )
        w = self._wizard(
            date_from=fields.Date.from_string("2020-06-01"),
            date_to=fields.Date.from_string("2020-06-30"),
            journal_ids=[(5, 0, 0)],
        )
        rows = w._get_report_phase1_rows()
        ts_rows = [r for r in rows if r.get("move_name") == "uat timesheet no gl"]
        self.assertEqual(len(ts_rows), 1)
        self.assertEqual(ts_rows[0]["account"], "Timesheet / no GL")
        self.assertAlmostEqual(ts_rows[0]["debit"], 80.0, places=2)

    def test_no_duplicate_when_aal_represents_aml(self):
        move = self._post_balanced_move(
            self.journal_a,
            fields.Date.from_string("2020-09-11"),
            70.0,
            {str(self.analytic_aa.id): 100.0},
        )
        exp = move.line_ids.filtered(lambda l: l.account_id == self.expense)[:1]
        posted_aal = self.env["account.analytic.line"].search(
            [("move_line_id", "in", exp.ids)]
        )
        self.assertTrue(
            posted_aal,
            "Posted JE with analytic_distribution must create AAL (AAL-primary source).",
        )
        w = self._wizard(
            date_from=fields.Date.from_string("2020-09-01"),
            date_to=fields.Date.from_string("2020-09-30"),
        )
        rows = w._get_report_phase1_rows()
        related = [
            r
            for r in rows
            if r.get("aml_id") == exp.id or r.get("move_name") == move.name
        ]
        sources = {r.get("source") for r in related}
        self.assertLessEqual(
            len(sources), 1, "AML and AAL must not both emit the same JE line"
        )
        self.assertEqual(
            len(related),
            1,
            "Posted JE must appear once (no AML/AAL double counting).",
        )
        self.assertEqual(related[0].get("source"), "aal")
        self.assertNotEqual(related[0].get("account"), "Timesheet / no GL")
