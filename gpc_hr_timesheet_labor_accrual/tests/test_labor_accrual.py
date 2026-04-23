# Copyright 2026
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import fields
from odoo.exceptions import UserError, ValidationError
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
        cls.project = cls.env["project.project"].create(
            {
                "name": "Lab Accrual Project",
                "company_id": cls.company.id,
                "generate_labor_je": False,
            }
        )

        # Minimal MO stack for Non-MO exclusion (mrp_timesheet)
        cls.product = cls.env["product.product"].create(
            {
                "name": "LabAccr FG",
                # Odoo 19: product.template.type uses consu/service/combo (not legacy "product")
                "type": "consu",
            }
        )
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
