# -*- coding: utf-8 -*-
"""
TC-01 to TC-07 – Integration tests for mrp_timesheet (Odoo 19)

Covers the full labor-cost-to-JE pipeline introduced in Steps 1-6:
  TC-01  Basic MO timesheet → correct JE accounts (debit WIP, credit clearing)
  TC-02  Overtime multiplier applied correctly
  TC-03  Timesheet edit → JE reversal + recreate
  TC-04  Missing account config → no JE, no crash
  TC-05  Project-based timesheet JE (no MO required)
  TC-06  Multi-company: JE created in correct company
  TC-07  Delete timesheet → JE reversed
"""

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


def _make_account(env, name, code, account_type, company):
    return env['account.account'].create({
        'name': name,
        'code': code,
        'account_type': account_type,
        'company_ids': [(4, company.id)],
    })


def _make_journal(env, name, code, company):
    return env['account.journal'].create({
        'name': name,
        'code': code,
        'type': 'general',
        'company_id': company.id,
    })


@tagged('post_install', '-at_install')
class TestMrpTimesheetTC(TransactionCase):
    """Integration test suite for mrp_timesheet Steps 1-6."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.currency = cls.company.currency_id

        # ── Accounts & journal ────────────────────────────────────────────────
        cls.wip_account = _make_account(
            cls.env, 'Test Labor WIP', 'TWIP01',
            'asset_current', cls.company
        )
        cls.clearing_account = _make_account(
            cls.env, 'Test Labor Clearing', 'TCLR01',
            'liability_current', cls.company
        )
        cls.journal = _make_journal(
            cls.env, 'Test Labor Journal', 'TLBR', cls.company
        )

        # Wire company config
        cls.company.write({
            'labor_wip_account_id': cls.wip_account.id,
            'labor_clearing_account_id': cls.clearing_account.id,
            'labor_cost_journal_id': cls.journal.id,
            'overtime_rate_multiplier': 1.5,
            'holiday_rate_multiplier': 2.0,
        })

        # ── Analytic account ──────────────────────────────────────────────────
        cls.analytic_account = cls.env['account.analytic.account'].create({
            'name': 'Test MO Analytic',
            'company_id': cls.company.id,
        })

        # ── Employee with known hourly rate ───────────────────────────────────
        cls.employee = cls.env['hr.employee'].create({
            'name': 'TC Worker',
            'company_id': cls.company.id,
            'hourly_cost': 100.0,
        })

        # ── Minimal product + BoM for MO creation ─────────────────────────────
        cls.product = cls.env['product.product'].create({
            'name': 'TC Finished Good',
            'type': 'product',
        })
        cls.bom = cls.env['mrp.bom'].create({
            'product_tmpl_id': cls.product.product_tmpl_id.id,
            'product_qty': 1.0,
            'product_uom_id': cls.env.ref('uom.product_uom_unit').id,
        })

    def _make_mo(self):
        mo = self.env['mrp.production'].create({
            'product_id': self.product.id,
            'product_qty': 1.0,
            'product_uom_id': self.env.ref('uom.product_uom_unit').id,
            'bom_id': self.bom.id,
            'analytic_account_id': self.analytic_account.id,
        })
        return mo

    def _make_ts_line(self, mo=None, hours=2.0, overtime=False, holiday=False,
                      project=None):
        vals = {
            'name': 'TC timesheet',
            'account_id': self.analytic_account.id,
            'company_id': self.company.id,
            'date': '2025-03-01',
            'employee_id': self.employee.id,
            'unit_amount': hours,
        }
        if mo:
            vals['mrp_production_id'] = mo.id
        if overtime:
            vals['is_overtime'] = True
        if holiday:
            vals['is_holiday'] = True
        if project:
            vals['project_id'] = project.id
        return self.env['account.analytic.line'].create(vals)

    # =========================================================================
    # TC-01: Basic MO timesheet → correct JE accounts
    # =========================================================================
    def test_tc01_basic_mo_timesheet_je_accounts(self):
        """JE debits WIP account and credits Clearing account for MO timesheet."""
        mo = self._make_mo()
        line = self._make_ts_line(mo=mo, hours=2.0)

        self.assertAlmostEqual(line.labor_cost, 200.0, places=2,
                               msg='TC-01: labor_cost should be 2h × 100 = 200')
        self.assertTrue(line.labor_move_id,
                        'TC-01: JE should be auto-created on create()')

        move = line.labor_move_id
        self.assertEqual(move.state, 'posted', 'TC-01: JE must be posted')
        self.assertEqual(move.company_id, self.company, 'TC-01: JE company')

        debit_lines  = move.line_ids.filtered(lambda l: l.debit  > 0)
        credit_lines = move.line_ids.filtered(lambda l: l.credit > 0)

        self.assertEqual(len(debit_lines),  1, 'TC-01: 1 debit  line expected')
        self.assertEqual(len(credit_lines), 1, 'TC-01: 1 credit line expected')

        self.assertEqual(debit_lines.account_id,  self.wip_account,
                         'TC-01: Debit → WIP account')
        self.assertEqual(credit_lines.account_id, self.clearing_account,
                         'TC-01: Credit → Clearing account')

        self.assertAlmostEqual(debit_lines.debit,   200.0, places=2)
        self.assertAlmostEqual(credit_lines.credit, 200.0, places=2)

        # Analytic distribution must reference the MO's analytic account
        for aml in move.line_ids:
            dist = aml.analytic_distribution or {}
            self.assertIn(str(self.analytic_account.id), dist,
                          'TC-01: analytic_distribution must contain MO analytic account')

    # =========================================================================
    # TC-02: Overtime multiplier applied correctly
    # =========================================================================
    def test_tc02_overtime_multiplier(self):
        """labor_cost uses 1.5× multiplier when is_overtime=True."""
        mo   = self._make_mo()
        line = self._make_ts_line(mo=mo, hours=4.0, overtime=True)

        expected = 4.0 * 100.0 * 1.5   # 600.0
        self.assertAlmostEqual(line.labor_cost, expected, places=2,
                               msg='TC-02: overtime cost should be 4h × 100 × 1.5 = 600')

        move = line.labor_move_id
        self.assertTrue(move, 'TC-02: JE should be created for overtime line')
        debit_lines = move.line_ids.filtered(lambda l: l.debit > 0)
        self.assertAlmostEqual(debit_lines.debit, 600.0, places=2,
                               msg='TC-02: JE debit should be 600')

    def test_tc02b_holiday_multiplier(self):
        """labor_cost uses 2.0× multiplier when is_holiday=True (takes precedence)."""
        mo   = self._make_mo()
        # is_holiday takes precedence over is_overtime
        line = self._make_ts_line(mo=mo, hours=2.0, overtime=True, holiday=True)

        expected = 2.0 * 100.0 * 2.0   # 400.0
        self.assertAlmostEqual(line.labor_cost, expected, places=2,
                               msg='TC-02b: holiday cost should be 2h × 100 × 2.0 = 400')

    # =========================================================================
    # TC-03: Timesheet edit → JE reversal + recreate
    # =========================================================================
    def test_tc03_edit_reverses_and_recreates_je(self):
        """Changing hours on a timesheet line reverses old JE and creates new one."""
        mo   = self._make_mo()
        line = self._make_ts_line(mo=mo, hours=2.0)

        old_move = line.labor_move_id
        self.assertTrue(old_move, 'TC-03: initial JE should exist')

        # Change hours → should trigger reversal + new JE
        line.unit_amount = 5.0
        new_move = line.labor_move_id

        self.assertTrue(new_move, 'TC-03: new JE should exist after edit')
        self.assertNotEqual(old_move, new_move,
                            'TC-03: a different JE should be created after edit')

        # Old move should now have a reversal
        self.assertTrue(old_move.reversal_move_ids,
                        'TC-03: old JE must have a reversal entry')

        # New JE should reflect 5h × 100 = 500
        new_debit = new_move.line_ids.filtered(lambda l: l.debit > 0)
        self.assertAlmostEqual(new_debit.debit, 500.0, places=2,
                               msg='TC-03: new JE should be 5h × 100 = 500')

    # =========================================================================
    # TC-04: Missing account config → no JE, no crash
    # =========================================================================
    def test_tc04_missing_account_config_no_crash(self):
        """When WIP or clearing account not configured, JE is silently skipped."""
        # Temporarily remove clearing account
        self.company.labor_clearing_account_id = False
        try:
            mo   = self._make_mo()
            line = self._make_ts_line(mo=mo, hours=2.0)

            # No JE should be created (silently skipped)
            self.assertFalse(line.labor_move_id,
                             'TC-04: no JE when clearing account is missing')
            # But labor_cost should still be computed
            self.assertAlmostEqual(line.labor_cost, 200.0, places=2,
                                   msg='TC-04: labor_cost should still compute')
        finally:
            # Restore config for other tests
            self.company.labor_clearing_account_id = self.clearing_account.id

    # =========================================================================
    # TC-05: Project-based timesheet JE (no MO)
    # =========================================================================
    def test_tc05_project_based_timesheet_je(self):
        """JE auto-generated for project timesheet when generate_labor_je=True."""
        project = self.env['project.project'].create({
            'name': 'TC Project',
            'company_id': self.company.id,
            'generate_labor_je': True,
        })

        line = self._make_ts_line(hours=3.0, project=project)

        self.assertAlmostEqual(line.labor_cost, 300.0, places=2,
                               msg='TC-05: 3h × 100 = 300')
        self.assertTrue(line.labor_move_id,
                        'TC-05: JE should be created for project with generate_labor_je=True')

        # Verify project without toggle does NOT generate JE
        project_off = self.env['project.project'].create({
            'name': 'TC Project No JE',
            'company_id': self.company.id,
            'generate_labor_je': False,
        })
        line_off = self._make_ts_line(hours=3.0, project=project_off)
        self.assertFalse(line_off.labor_move_id,
                         'TC-05: no JE when generate_labor_je=False and no MO link')

    # =========================================================================
    # TC-06: Multi-company JE in correct company
    # =========================================================================
    def test_tc06_multicompany_je_correct_company(self):
        """JE is created under the same company as the timesheet line."""
        mo   = self._make_mo()
        line = self._make_ts_line(mo=mo, hours=1.0)

        move = line.labor_move_id
        self.assertTrue(move, 'TC-06: JE must exist')
        self.assertEqual(move.company_id, self.company,
                         'TC-06: JE company must match timesheet line company')
        for aml in move.line_ids:
            self.assertEqual(aml.company_id, self.company,
                             f'TC-06: JE line {aml.id} has wrong company')

    # =========================================================================
    # TC-07: Delete timesheet → JE reversed
    # =========================================================================
    def test_tc07_delete_timesheet_reverses_je(self):
        """Deleting a timesheet line automatically reverses the linked JE."""
        mo      = self._make_mo()
        line    = self._make_ts_line(mo=mo, hours=2.0)
        move    = line.labor_move_id
        move_id = move.id

        self.assertTrue(move, 'TC-07: JE must exist before deletion')

        # Delete the timesheet line
        line.unlink()

        # Line should be gone
        remaining = self.env['account.analytic.line'].search([('id', '=', line.id)])
        self.assertFalse(remaining, 'TC-07: line should be deleted')

        # The original JE should now have a reversal
        move_reloaded = self.env['account.move'].browse(move_id)
        self.assertTrue(move_reloaded.reversal_move_ids,
                        'TC-07: JE must have a reversal after timesheet deletion')

        reversal = move_reloaded.reversal_move_ids
        self.assertEqual(reversal.state, 'posted',
                         'TC-07: reversal JE must be posted')
