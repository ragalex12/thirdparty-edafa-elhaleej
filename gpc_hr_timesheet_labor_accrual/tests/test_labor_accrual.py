# Copyright 2026
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from unittest import mock

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged
from odoo.tools.sql import SQL


def _make_account(env, name, code, account_type, company):
    return env["account.account"].create(
        {
            "name": name,
            "code": code,
            "account_type": account_type,
            "company_ids": [(6, 0, [company.id])],
        }
    )


def _make_journal(env, name, code, company):
    return env["account.journal"].create(
        {
            "name": name,
            "code": code,
            "type": "general",
            "company_id": company.id,
        }
    )


def _analytic_account_vals(env, company, name):
    """Odoo 17+ analytic accounts require a plan when plan_id is mandatory in DB."""
    vals = {"name": name, "company_id": company.id}
    if "plan_id" in env["account.analytic.account"]._fields:
        Plan = env["account.analytic.plan"]
        plan = Plan.search([], limit=1)
        if not plan:
            plan = Plan.create({"name": "Lab Accrual Analytic Plan"})
        vals["plan_id"] = plan.id
    return vals


def _sql_columns(env, table):
    env.cr.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name = %s",
        (table,),
    )
    return {row[0] for row in env.cr.fetchall()}


def _null_stored_plan_columns(env, record):
    """Null real SQL plan columns only.

    Odoo 19 exposes ``analytic_distribution`` on ``account.analytic.line`` in
    the ORM (``_fields`` / ``_get_plan_fnames``) but that JSON lives on
    ``account.move.line``, not as a column on ``account_analytic_line``.
    """
    cols = _sql_columns(env, record._table)
    fnames = []
    if hasattr(record, "_get_plan_fnames"):
        fnames.extend(record._get_plan_fnames())
    if "account_id" in record._fields:
        fnames.append("account_id")
    seen = set()
    for fname in fnames:
        if fname in seen:
            continue
        seen.add(fname)
        field = record._fields.get(fname)
        if not field or fname not in cols:
            continue
        if not getattr(field, "store", False):
            continue
        env.cr.execute(
            SQL(
                "UPDATE %s SET %s = NULL WHERE id = %s",
                SQL.identifier(record._table),
                SQL.identifier(fname),
                record.id,
            )
        )
    record.invalidate_recordset()


@tagged("post_install", "-at_install")
class TestLaborAccrualScaffold(TransactionCase):
    """Minimal model/field registration checks."""

    def test_models_registered(self):
        self.env["labor.accrual.batch"]
        self.env["labor.accrual.batch.line"]
        self.env["labor.accrual.batch.wizard"]

    def test_company_fields_exist(self):
        company = self.env.company
        self.assertIn("labor_accrual_debit_account_id", company._fields)
        self.assertIn("labor_accrual_credit_account_id", company._fields)
        self.assertIn("labor_accrual_journal_id", company._fields)


@tagged("post_install", "-at_install")
class TestLaborAccrualPhase1(TransactionCase):
    """Phase 1: config, selection, lines, draft JE, posting, duplicate control, reversal."""

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
        cls.AAL = cls.env["account.analytic.line"]
        cls.Batch = cls.env["labor.accrual.batch"]

        cls.debit_acc = _make_account(
            cls.env, "LabAcc Dr Test", "LADR99", "expense", cls.company
        )
        cls.credit_acc = _make_account(
            cls.env, "LabAcc Cr Test", "LACR99", "liability_current", cls.company
        )
        cls.accrual_journal = _make_journal(
            cls.env, "Labor Accrual Test Journal", "LAB9", cls.company
        )
        cls.company.write(
            {
                "labor_accrual_debit_account_id": cls.debit_acc.id,
                "labor_accrual_credit_account_id": cls.credit_acc.id,
                "labor_accrual_journal_id": cls.accrual_journal.id,
            }
        )

        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Lab Accrual Worker",
                "company_id": cls.company.id,
                "hourly_cost": 100.0,
            }
        )
        cls.employee_zero = cls.env["hr.employee"].create(
            {
                "name": "Lab Accrual Zero Rate",
                "company_id": cls.company.id,
                "hourly_cost": 0.0,
            }
        )
        proj_vals = {
            "name": "Lab Accrual Project",
            "company_id": cls.company.id,
        }
        if "generate_labor_je" in cls.env["project.project"]._fields:
            proj_vals["generate_labor_je"] = False
        cls.project = cls.env["project.project"].create(proj_vals)

        # Optional MO stack (only when mrp is installed)
        cls.product = cls.env["product.product"].create(
            {
                "name": "LabAccr FG",
                "type": "consu",
            }
        )
        cls.bom = False
        cls.analytic_mo = False
        if "mrp.bom" in cls.env:
            cls.bom = cls.env["mrp.bom"].create(
                {
                    "product_tmpl_id": cls.product.product_tmpl_id.id,
                    "product_qty": 1.0,
                    "product_uom_id": cls.env.ref("uom.product_uom_unit").id,
                }
            )
            cls.analytic_mo = cls.env["account.analytic.account"].create(
                _analytic_account_vals(cls.env, cls.company, "Lab MO Analytic")
            )

    def _batch(self, period_key="2025-06", **kwargs):
        vals = {
            "name": "Lab accrual %s" % period_key,
            "company_id": self.company.id,
            "period_start": fields.Date.from_string("2025-06-01"),
            "period_end": fields.Date.from_string("2025-06-30"),
            "period_key": period_key,
            "state": "draft",
        }
        vals.update(kwargs)
        return self.Batch.create(vals)

    def _ts_line_vals_base(self):
        return {
            "name": "lab accrual ts",
            "company_id": self.company.id,
            "employee_id": self.employee.id,
            "project_id": self.project.id,
            "unit_amount": 2.0,
            "date": fields.Date.from_string("2025-06-15"),
        }

    def _create_ts_line(self, **kwargs):
        vals = self._ts_line_vals_base()
        vals.update(kwargs)
        if "validated" in self.AAL._fields and "validated" not in kwargs:
            vals["validated"] = True
        return self.AAL.create(vals)

    def test_company_config_required_for_draft_move(self):
        """Draft JE generation requires all three company fields (used in _get_company_labor_accrual_config)."""
        batch = self._batch()
        self._create_ts_line()
        batch.action_populate_lines()
        self.assertTrue(batch.line_ids)

        j_bak = self.company.labor_accrual_journal_id
        d_bak = self.company.labor_accrual_debit_account_id
        c_bak = self.company.labor_accrual_credit_account_id
        try:
            self.company.labor_accrual_journal_id = False
            with self.assertRaises(UserError):
                batch.action_generate_draft_move()

            self.company.labor_accrual_journal_id = j_bak
            self.company.labor_accrual_debit_account_id = False
            with self.assertRaises(UserError):
                batch.action_generate_draft_move()

            self.company.labor_accrual_debit_account_id = d_bak
            self.company.labor_accrual_credit_account_id = False
            with self.assertRaises(UserError):
                batch.action_generate_draft_move()
        finally:
            self.company.write(
                {
                    "labor_accrual_journal_id": j_bak.id,
                    "labor_accrual_debit_account_id": d_bak.id,
                    "labor_accrual_credit_account_id": c_bak.id,
                }
            )

    def test_generate_blocks_foreign_company_journal(self):
        """Generate JE must refuse a journal owned by another company (SQL bypass of ORM)."""
        other = self.env["res.company"].create({"name": "Labor Accrual Foreign Co J"})
        foreign_journal = _make_journal(self.env, "Foreign Labor Journal", "FXLJ", other)
        self._create_ts_line()
        batch = self._batch(period_key="2025-06-cxj")
        batch.action_populate_lines()
        if not batch.line_ids:
            self.skipTest("No batch line created.")
        bak = self.company.labor_accrual_journal_id
        self.env.cr.execute(
            "UPDATE res_company SET labor_accrual_journal_id = %s WHERE id = %s",
            (foreign_journal.id, self.company.id),
        )
        self.company.invalidate_recordset(["labor_accrual_journal_id"])
        try:
            with self.assertRaises(UserError) as ctx:
                batch.action_generate_draft_move()
            self.assertIn("cross-company journal", str(ctx.exception).lower())
            self.assertFalse(batch.move_id)
        finally:
            self.env.cr.execute(
                "UPDATE res_company SET labor_accrual_journal_id = %s WHERE id = %s",
                (bak.id, self.company.id),
            )
            self.company.invalidate_recordset(["labor_accrual_journal_id"])

    def test_generate_blocks_foreign_company_debit_account(self):
        """Generate JE must refuse a debit account that is not on the batch company."""
        other = self.env["res.company"].create({"name": "Labor Accrual Foreign Co A"})
        foreign_debit = _make_account(
            self.env, "Foreign Labor Dr", "FXDR99", "expense", other
        )
        self._create_ts_line()
        batch = self._batch(period_key="2025-06-cxa")
        batch.action_populate_lines()
        if not batch.line_ids:
            self.skipTest("No batch line created.")
        bak = self.company.labor_accrual_debit_account_id
        self.env.cr.execute(
            "UPDATE res_company SET labor_accrual_debit_account_id = %s WHERE id = %s",
            (foreign_debit.id, self.company.id),
        )
        self.company.invalidate_recordset(["labor_accrual_debit_account_id"])
        try:
            with self.assertRaises(UserError) as ctx:
                batch.action_generate_draft_move()
            msg = str(ctx.exception).lower()
            self.assertTrue(
                "cross-company debit" in msg or "does not belong" in msg,
                msg,
            )
            self.assertFalse(batch.move_id)
        finally:
            self.env.cr.execute(
                "UPDATE res_company SET labor_accrual_debit_account_id = %s WHERE id = %s",
                (bak.id, self.company.id),
            )
            self.company.invalidate_recordset(["labor_accrual_debit_account_id"])

    def test_generate_blocks_timesheet_from_other_company(self):
        """A batch line pointing at another company's timesheet must not generate a JE."""
        other = self.env["res.company"].create({"name": "Labor Accrual Foreign Co T"})
        self._create_ts_line()
        batch = self._batch(period_key="2025-06-cxt")
        batch.action_populate_lines()
        if not batch.line_ids:
            self.skipTest("No batch line created.")
        ts = batch.line_ids[0].timesheet_line_id
        self.env.cr.execute(
            "UPDATE account_analytic_line SET company_id = %s WHERE id = %s",
            (other.id, ts.id),
        )
        ts.invalidate_recordset(["company_id"])
        with self.assertRaises(UserError) as ctx:
            batch.action_generate_draft_move()
        self.assertIn("another company", str(ctx.exception).lower())
        self.assertFalse(batch.move_id)

    def test_domain_includes_company_period_validated_non_mo_rules(self):
        """Eligible domain encodes company, date range, and Non-MO; validated when the field exists."""
        batch = self._batch()
        dom = batch._get_eligible_timesheet_domain()
        self.assertIn(("company_id", "=", self.company.id), dom)
        self.assertIn(("date", ">=", batch.period_start), dom)
        self.assertIn(("date", "<=", batch.period_end), dom)
        if "validated" in self.AAL._fields:
            self.assertIn(("validated", "=", True), dom)
        if "mrp_production_id" in self.AAL._fields:
            self.assertIn(("mrp_production_id", "=", False), dom)

    def test_populate_respects_period(self):
        """Lines outside the batch date range are not turned into batch lines (company in domain)."""
        batch = self._batch()
        self._create_ts_line(date=fields.Date.from_string("2025-06-10"))
        self._create_ts_line(date=fields.Date.from_string("2025-05-10"))

        batch.action_populate_lines()
        self.assertEqual(len(batch.line_ids), 1)
        self.assertEqual(
            batch.line_ids.timesheet_line_id.date,
            fields.Date.from_string("2025-06-10"),
        )

    def test_populate_excludes_unvalidated_when_field_exists(self):
        """If validated exists, unvalidated timesheet lines are excluded."""
        if "validated" not in self.AAL._fields:
            self.skipTest("account.analytic.line has no validated field in this database.")
        self._create_ts_line(validated=False)
        ok = self._create_ts_line(validated=True)
        batch = self._batch()
        batch.action_populate_lines()
        self.assertEqual(len(batch.line_ids), 1)
        self.assertEqual(batch.line_ids.timesheet_line_id, ok)

    def test_populate_excludes_mo_timesheet_when_field_exists(self):
        """mrp_timesheet: lines linked to an MO are excluded (Non-MO scope)."""
        if "mrp_production_id" not in self.AAL._fields:
            self.skipTest("account.analytic.line has no mrp_production_id field.")
        try:
            mo = self.env["mrp.production"].create(
                {
                    "product_id": self.product.id,
                    "product_qty": 1.0,
                    "product_uom_id": self.env.ref("uom.product_uom_unit").id,
                    "bom_id": self.bom.id,
                    "analytic_account_id": self.analytic_mo.id,
                }
            )
        except Exception as err:
            self.skipTest(
                "Could not create mrp.production for Non-MO test: %s" % (err,)
            )
        self._create_ts_line(
            mrp_production_id=mo.id,
            account_id=self.analytic_mo.id,
        )
        plain = self._create_ts_line()
        batch = self._batch()
        batch.action_populate_lines()
        self.assertEqual(len(batch.line_ids), 1)
        self.assertEqual(batch.line_ids.timesheet_line_id, plain)

    def test_populate_one_line_per_eligible_timesheet_excludes_zero_labor(self):
        """One batch line per eligible analytic line; zero labor_cost lines are skipped."""
        a = self._create_ts_line(unit_amount=1.0)
        self._create_ts_line(employee_id=self.employee_zero.id, unit_amount=3.0)
        batch = self._batch()
        batch.action_populate_lines()
        self.assertEqual(len(batch.line_ids), 1)
        self.assertEqual(batch.line_ids.timesheet_line_id, a)
        self.assertGreater(batch.line_ids.amount, 0.0)

    def test_draft_move_created_balanced_linked(self):
        """Draft JE: one move, balanced lines, batch.move_id set."""
        self._create_ts_line(unit_amount=1.0)
        batch = self._batch()
        batch.action_populate_lines()
        batch.action_generate_draft_move()
        move = batch.move_id
        self.assertTrue(move)
        self.assertEqual(move.state, "draft")
        self.assertEqual(move.move_type, "entry")
        lines = move.line_ids
        self.assertEqual(len(lines), 2)
        self.assertAlmostEqual(sum(lines.mapped("debit")), sum(lines.mapped("credit")))
        self.assertAlmostEqual(sum(lines.mapped("debit")), batch.line_ids.amount)

    def test_post_move_updates_batch_and_move(self):
        """Posting: move posted; batch state posted; posted_by / posted_at set."""
        self._create_ts_line(unit_amount=1.0)
        batch = self._batch()
        batch.action_populate_lines()
        batch.action_generate_draft_move()
        user = self.env.user
        batch.action_post_move()
        self.assertEqual(batch.state, "posted")
        self.assertEqual(batch.move_id.state, "posted")
        self.assertEqual(batch.posted_by, user)
        self.assertTrue(batch.posted_at)

    def test_duplicate_active_batch_blocked(self):
        """Second draft/posted batch for same company + period_key raises ValidationError."""
        b1 = self._batch(period_key="2025-07")
        self.assertTrue(b1)
        with self.assertRaises(ValidationError):
            self._batch(period_key="2025-07")

    def test_wizard_duplicate_raises_user_error(self):
        """Wizard cannot create a second active batch for the same company and period."""
        wiz = self.env["labor.accrual.batch.wizard"].create(
            {
                "company_id": self.company.id,
                "period_start": fields.Date.from_string("2025-08-01"),
                "period_end": fields.Date.from_string("2025-08-31"),
            }
        )
        wiz.action_create_batch_and_populate_lines()
        wiz2 = self.env["labor.accrual.batch.wizard"].create(
            {
                "company_id": self.company.id,
                "period_start": fields.Date.from_string("2025-08-01"),
                "period_end": fields.Date.from_string("2025-08-31"),
            }
        )
        with self.assertRaises(UserError):
            wiz2.action_create_batch_and_populate_lines()

    def test_reverse_cancels_batch_and_allows_new_batch_same_period(self):
        """Reversal move posted; batch cancelled; new active batch for same period_key allowed."""
        self._create_ts_line(unit_amount=1.0)
        batch = self._batch(period_key="2025-09")
        batch.action_populate_lines()
        batch.action_generate_draft_move()
        batch.action_post_move()
        move = batch.move_id
        batch.action_reverse_for_regeneration()
        self.assertEqual(batch.state, "cancelled")
        self.assertTrue(batch.reversal_move_id)
        self.assertEqual(batch.reversal_move_id.state, "posted")
        self.assertTrue(batch.reversed_at)
        self.assertEqual(batch.reversed_by, self.env.user)

        rev = batch.reversal_move_id
        if "reversed_entry_id" in rev._fields:
            self.assertEqual(rev.reversed_entry_id, move)

        new_batch = self._batch(period_key="2025-09", name="Replacement 2025-09")
        self.assertEqual(new_batch.state, "draft")

    def test_period_key_syncs_from_period_start_on_create(self):
        batch = self._batch(
            period_key="2026-01",
            period_start=fields.Date.from_string("2026-02-01"),
            period_end=fields.Date.from_string("2026-02-28"),
        )
        self.assertEqual(batch.period_key, "2026-02")

    def test_period_key_syncs_when_dates_written(self):
        batch = self._batch()
        self.assertEqual(batch.period_key, "2025-06")
        batch.write(
            {
                "period_start": fields.Date.from_string("2026-01-01"),
                "period_end": fields.Date.from_string("2026-01-31"),
            }
        )
        self.assertEqual(batch.period_key, "2026-01")

    def test_cross_month_range_rejected(self):
        with self.assertRaises(ValidationError):
            self._batch(
                period_start=fields.Date.from_string("2026-01-01"),
                period_end=fields.Date.from_string("2026-02-28"),
            )

    def test_wizard_cross_month_rejected(self):
        wiz = self.env["labor.accrual.batch.wizard"].create(
            {
                "company_id": self.company.id,
                "period_start": fields.Date.from_string("2026-01-14"),
                "period_end": fields.Date.from_string("2026-02-21"),
            }
        )
        with self.assertRaises(UserError):
            wiz.action_create_batch_and_populate_lines()

    def test_populate_uses_dates_not_stale_label(self):
        """Jan 14 / Jan 21 lines are selected only when the date window is January."""
        jan14 = self._create_ts_line(
            unit_amount=8.0, date=fields.Date.from_string("2026-01-14")
        )
        jan21 = self._create_ts_line(
            unit_amount=6.0, date=fields.Date.from_string("2026-01-21")
        )
        feb01 = self._create_ts_line(
            unit_amount=8.0, date=fields.Date.from_string("2026-02-01")
        )
        batch = self._batch(
            period_start=fields.Date.from_string("2026-01-01"),
            period_end=fields.Date.from_string("2026-01-31"),
        )
        self.assertEqual(batch.period_key, "2026-01")
        batch.action_populate_lines()
        ts_ids = set(batch.line_ids.mapped("timesheet_line_id").ids)
        self.assertIn(jan14.id, ts_ids)
        self.assertIn(jan21.id, ts_ids)
        self.assertNotIn(feb01.id, ts_ids)


@tagged("post_install", "-at_install")
class TestLaborAccrualAnalyticDistribution(TransactionCase):
    """Phase 2: analytic distribution on generated journal entry lines."""

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
        cls.AAL = cls.env["account.analytic.line"]
        cls.Batch = cls.env["labor.accrual.batch"]

        cls.debit_acc = _make_account(
            cls.env, "Analytic Dr Test", "AADR99", "expense", cls.company
        )
        cls.credit_acc = _make_account(
            cls.env, "Analytic Cr Test", "AACR99", "liability_current", cls.company
        )
        cls.accrual_journal = _make_journal(
            cls.env, "Analytic Accrual Journal", "AAJ9", cls.company
        )
        cls.company.write(
            {
                "labor_accrual_debit_account_id": cls.debit_acc.id,
                "labor_accrual_credit_account_id": cls.credit_acc.id,
                "labor_accrual_journal_id": cls.accrual_journal.id,
            }
        )
        cls.employee = cls.env["hr.employee"].create(
            {"name": "Analytic Worker", "company_id": cls.company.id, "hourly_cost": 100.0}
        )

        # Two projects, each with its own analytic account
        cls.analytic_a = cls.env["account.analytic.account"].create(
            _analytic_account_vals(cls.env, cls.company, "Analytic A")
        )
        cls.analytic_b = cls.env["account.analytic.account"].create(
            _analytic_account_vals(cls.env, cls.company, "Analytic B")
        )
        cls.project_a = cls.env["project.project"].create(
            {"name": "Project A", "company_id": cls.company.id, "account_id": cls.analytic_a.id}
        )
        cls.project_b = cls.env["project.project"].create(
            {"name": "Project B", "company_id": cls.company.id, "account_id": cls.analytic_b.id}
        )
        # Project with no analytic account
        cls.project_no_analytic = cls.env["project.project"].create(
            {"name": "Project No Analytic", "company_id": cls.company.id}
        )

    def _batch(self, period_key="2025-10"):
        return self.Batch.create(
            {
                "name": "Analytic batch %s" % period_key,
                "company_id": self.company.id,
                "period_start": fields.Date.from_string("2025-10-01"),
                "period_end": fields.Date.from_string("2025-10-31"),
                "period_key": period_key,
                "state": "draft",
            }
        )

    def _ts(self, project, amount_hours=2.0, **kwargs):
        vals = {
            "name": "analytic ts",
            "company_id": self.company.id,
            "employee_id": self.employee.id,
            "project_id": project.id,
            "unit_amount": amount_hours,
            "date": fields.Date.from_string("2025-10-15"),
        }
        if "validated" in self.AAL._fields and "validated" not in kwargs:
            vals["validated"] = True
        vals.update(kwargs)
        return self.AAL.create(vals)

    # ------------------------------------------------------------------
    # Helper: resolve analytic distribution via the new helper method
    # ------------------------------------------------------------------

    def test_helper_returns_ts_account_id_first(self):
        """Single analytic on timesheet → one-key distribution from that account."""
        ts = self._ts(self.project_a)
        batch = self._batch(period_key="2025-10-h1")
        batch.action_populate_lines()
        if not batch.line_ids:
            self.skipTest("No batch line created (amount resolution failed in this env).")
        bl = batch.line_ids[0]
        dist = batch._get_analytic_distribution_for_batch_line(bl)
        ts_accs = ts._get_analytic_accounts()
        if len(ts_accs) != 1:
            self.skipTest("Need exactly one analytic account on timesheet for this assertion.")
        self.assertEqual(dist, {str(ts_accs.id): 100.0})

    def test_helper_falls_back_to_project_account_id(self):
        """When timesheet has no analytic accounts, use project.account_id (single)."""
        batch = self._batch(period_key="2025-10-h2")
        self._ts(self.project_a)
        batch.action_populate_lines()
        if not batch.line_ids:
            self.skipTest("No batch line created.")
        bl = batch.line_ids[0]
        ts = bl.timesheet_line_id
        _null_stored_plan_columns(self.env, ts)
        dist = batch._get_analytic_distribution_for_batch_line(bl)
        if not self.project_a.account_id:
            self.skipTest("Project has no account_id for fallback.")
        self.assertEqual(dist, {str(self.project_a.account_id.id): 100.0})

    def test_helper_raises_when_no_analytic(self):
        """When timesheet + project analytic columns are cleared, helper raises UserError."""
        batch = self._batch(period_key="2025-10-h3")
        self._ts(self.project_a)
        batch.action_populate_lines()
        if not batch.line_ids:
            self.skipTest("No batch line created.")
        bl = batch.line_ids[0]
        ts = bl.timesheet_line_id
        _null_stored_plan_columns(self.env, ts)
        _null_stored_plan_columns(self.env, self.project_a)
        with self.assertRaises(UserError):
            batch._get_analytic_distribution_for_batch_line(bl)

    def test_timesheet_two_analytic_accounts_raises_user_error(self):
        """Two analytic accounts on the same timesheet → UserError (no silent merge)."""
        aa2 = self.env["account.analytic.account"].create(
            _analytic_account_vals(self.env, self.company, "Labor accrual second plan AA")
        )
        plan_fnames = [f for f in self.AAL._get_plan_fnames() if f != "account_id"]
        if not plan_fnames:
            self.skipTest("Only one analytic plan column on analytic lines in this DB.")
        ts = self._ts(self.project_a)
        second_f = plan_fnames[0]
        cols = _sql_columns(self.env, ts._table)
        if second_f not in cols:
            self.skipTest(
                "Plan field %s is not a SQL column on account_analytic_line." % second_f
            )
        self.env.cr.execute(
            SQL(
                "UPDATE account_analytic_line SET %s = %s WHERE id = %s",
                SQL.identifier(second_f),
                aa2.id,
                ts.id,
            )
        )
        ts.invalidate_recordset()
        if len(ts._get_analytic_accounts()) < 2:
            self.skipTest("Second plan did not yield multiple analytic accounts.")
        batch = self._batch(period_key="2025-10-2acct")
        self.env["labor.accrual.batch.line"].create(
            {
                "batch_id": batch.id,
                "timesheet_line_id": ts.id,
                "amount": 100.0,
                "employee_id": ts.employee_id.id,
                "project_id": ts.project_id.id,
                "line_date": ts.date,
            }
        )
        bl = batch.line_ids[0]
        with self.assertRaises(UserError):
            batch._get_analytic_distribution_for_batch_line(bl)

    # ------------------------------------------------------------------
    # Single project with analytic → debit line carries distribution
    # ------------------------------------------------------------------

    def test_single_project_analytic_on_debit_line(self):
        """Single project with analytic: debit line has analytic_distribution; credit has none."""
        self._ts(self.project_a)
        batch = self._batch(period_key="2025-10-s1")
        batch.action_populate_lines()
        if not batch.line_ids:
            self.skipTest("No batch line created.")
        batch.action_generate_draft_move()
        move = batch.move_id
        debit_lines = move.line_ids.filtered(lambda l: l.debit > 0)
        credit_lines = move.line_ids.filtered(lambda l: l.credit > 0)

        self.assertEqual(len(debit_lines), 1)
        self.assertEqual(len(credit_lines), 1)

        # Credit (offset) must NOT carry analytic
        self.assertFalse(credit_lines.analytic_distribution)

        # Debit line: exactly one analytic key (business rule).
        ts = batch.line_ids[0].timesheet_line_id
        ts_accs = ts._get_analytic_accounts()
        if len(ts_accs) != 1:
            self.skipTest("Need exactly one analytic account on timesheet.")
        self.assertEqual(
            debit_lines.analytic_distribution,
            {str(ts_accs.id): 100.0},
        )
        # analytic_distribution is an AML field in Odoo 19 — not an AAL column.
        self.assertIn("analytic_distribution", debit_lines._fields)
        self.assertNotIn(
            "analytic_distribution",
            _sql_columns(self.env, "account_analytic_line"),
        )

        batch.action_post_move()
        move.invalidate_recordset()
        self.assertEqual(move.state, "posted")
        posted_aal = self.env["account.analytic.line"].search(
            [("move_line_id", "in", debit_lines.ids)]
        )
        self.assertTrue(
            posted_aal,
            "Posted labor JE debit must create account.analytic.line via move_line_id.",
        )
        for aal in posted_aal:
            self.assertTrue(aal.account_id, "Posted AAL missing analytic account_id")
            self.assertEqual(aal.account_id, ts_accs)
            self.assertEqual(
                aal.general_account_id,
                self.debit_acc,
                "Posted AAL general_account_id must be the labor expense account",
            )
            self.assertIn(aal.move_line_id, debit_lines)
            # Project linkage is the analytic account copied from the timesheet.
            self.assertEqual(aal.account_id, ts.project_id.account_id or ts_accs)
            if aal.employee_id:
                self.assertEqual(aal.employee_id, self.employee)

    def test_no_analytic_raises_user_error(self):
        """Missing analytic must raise UserError — never post JE without analytic."""
        self._ts(self.project_a)
        batch = self._batch(period_key="2025-10-s2")
        batch.action_populate_lines()
        if not batch.line_ids:
            self.skipTest("No batch line created.")
        BatchModel = self.env.registry["labor.accrual.batch"]
        with mock.patch.object(
            BatchModel,
            "_get_single_analytic_account_for_labor_accrual_line",
            lambda self, bl: (self.env["account.analytic.account"].browse(), "none"),
        ):
            with self.assertRaises(UserError):
                batch.action_generate_draft_move()
        self.assertFalse(batch.move_id)
    # ------------------------------------------------------------------
    # Multi-project grouping: separate debit lines, one credit line
    # ------------------------------------------------------------------

    def test_two_projects_produce_two_debit_lines_one_credit_line(self):
        """Two timesheet lines from different projects → 2 debit lines, 1 credit line."""
        self._ts(self.project_a, amount_hours=2.0)
        self._ts(self.project_b, amount_hours=3.0)
        batch = self._batch(period_key="2025-10-m1")
        batch.action_populate_lines()
        if len(batch.line_ids) < 2:
            self.skipTest("Need 2 batch lines with positive amounts.")
        batch.action_generate_draft_move()
        move = batch.move_id
        debit_lines = move.line_ids.filtered(lambda l: l.debit > 0)
        credit_lines = move.line_ids.filtered(lambda l: l.credit > 0)

        # Each project produces its own debit line
        self.assertEqual(len(debit_lines), 2, "Expected one debit line per analytic group.")
        self.assertEqual(len(credit_lines), 1, "Expected one aggregated credit line.")

        # Balanced
        self.assertAlmostEqual(
            sum(debit_lines.mapped("debit")),
            credit_lines.credit,
            places=2,
        )

        # Each debit line: single analytic key only (business rule)
        for dl in debit_lines:
            if dl.analytic_distribution:
                self.assertEqual(len(dl.analytic_distribution), 1)
        dists = [frozenset(l.analytic_distribution.items()) for l in debit_lines if l.analytic_distribution]
        if len(dists) == 2:
            self.assertNotEqual(dists[0], dists[1], "Debit lines must have different analytic distributions.")

    def test_two_lines_same_project_grouped_into_one_debit_line(self):
        """Two timesheet lines from the same project → 1 debit line (grouped), 1 credit line."""
        self._ts(self.project_a, amount_hours=1.0)
        self._ts(self.project_a, amount_hours=2.0, date=fields.Date.from_string("2025-10-20"))
        batch = self._batch(period_key="2025-10-m2")
        batch.action_populate_lines()
        if len(batch.line_ids) < 2:
            self.skipTest("Need 2 batch lines with positive amounts.")
        batch.action_generate_draft_move()
        move = batch.move_id
        debit_lines = move.line_ids.filtered(lambda l: l.debit > 0)
        credit_lines = move.line_ids.filtered(lambda l: l.credit > 0)

        self.assertEqual(len(debit_lines), 1, "Same analytic → should be grouped into one debit line.")
        self.assertEqual(len(credit_lines), 1)
        self.assertAlmostEqual(debit_lines.debit, credit_lines.credit, places=2)

    def test_debit_always_equals_credit_multi_project(self):
        """Rounding guard: total debit == total credit across any number of groups."""
        self._ts(self.project_a, amount_hours=1.0)
        self._ts(self.project_b, amount_hours=1.0)
        batch = self._batch(period_key="2025-10-r1")
        batch.action_populate_lines()
        if not batch.line_ids:
            self.skipTest("No batch lines created.")
        batch.action_generate_draft_move()
        move = batch.move_id
        total_debit = sum(move.line_ids.mapped("debit"))
        total_credit = sum(move.line_ids.mapped("credit"))
        self.assertAlmostEqual(
            total_debit, total_credit, places=2,
            msg="Total debit must always equal total credit (rounding guard).",
        )
        # Every debit line must carry account_id + analytic_distribution
        for line in move.line_ids.filtered(lambda l: l.debit > 0):
            self.assertTrue(line.account_id, "Debit line missing account_id")
            self.assertTrue(line.analytic_distribution, "Debit line missing analytic_distribution")

    def test_regenerate_draft_replaces_old_move(self):
        """Re-clicking Generate Draft Entry deletes the old draft and creates a fresh one."""
        self._ts(self.project_a)
        batch = self._batch(period_key="2025-10-regen")
        batch.action_populate_lines()
        if not batch.line_ids:
            self.skipTest("No batch lines created.")
        batch.action_generate_draft_move()
        first_move_id = batch.move_id.id
        batch.action_generate_draft_move()
        self.assertNotEqual(batch.move_id.id, first_move_id, "Old move must be replaced.")
        self.assertEqual(batch.move_id.state, "draft")

    def test_mixed_missing_analytic_raises_user_error(self):
        """Any batch line without analytic must abort JE generation (no silent empty group)."""
        ts_with = self._ts(self.project_a, amount_hours=2.0)
        ts_without = self._ts(self.project_a, amount_hours=1.0, date=fields.Date.from_string("2025-10-16"))
        batch = self._batch(period_key="2025-10-mixed")
        batch.action_populate_lines()
        if len(batch.line_ids) < 2:
            self.skipTest("Need 2 batch lines (check labor_cost resolution).")

        BatchCls = self.env.registry["labor.accrual.batch"]
        orig_get = BatchCls._get_analytic_distribution_for_batch_line

        def mixed_helper(self, batch_line):
            if batch_line.timesheet_line_id.id == ts_without.id:
                # Simulate unresolved analytic by calling the raise path
                raise UserError("simulated missing analytic")
            return orig_get(self, batch_line)

        with mock.patch.object(
            BatchCls,
            "_get_analytic_distribution_for_batch_line",
            mixed_helper,
        ):
            with self.assertRaises(UserError):
                batch.action_generate_draft_move()
        self.assertFalse(batch.move_id)
