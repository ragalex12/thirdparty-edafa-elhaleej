\# -*- coding: utf-8 -*-
"""
Unit tests for mrp_timesheet (Odoo 19).
Tests labor cost computation on analytic lines and MO, and UserError when labor account missing.
"""
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestMrpTimesheet(TransactionCase):
    """Tests for timesheet labor cost computation and posting."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.currency = cls.company.currency_id
        # Analytic account for timesheet lines
        cls.analytic_account = cls.env['account.analytic.account'].create({
            'name': 'Test MO Analytic',
            'company_id': cls.company.id,
        })
        # Employee with hourly cost (our module adds this field)
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Test Worker',
            'company_id': cls.company.id,
            'hourly_cost': 25.0,
        })
        # Service product with cost (for lines without employee)
        cls.product_service = cls.env['product.product'].create({
            'name': 'Labor Service',
            'type': 'service',
            'standard_price': 30.0,
        })

    def test_analytic_line_cost_from_amount(self):
        """Line with amount set returns abs(amount) as labor cost."""
        line = self.env['account.analytic.line'].create({
            'name': 'Test',
            'account_id': self.analytic_account.id,
            'company_id': self.company.id,
            'date': '2025-01-15',
            'amount': -120.0,  # credit
            'unit_amount': 0,
        })
        cost = line._get_timesheet_labor_cost_for_production()
        self.assertEqual(cost, 120.0)

    def test_analytic_line_cost_from_hours_and_employee(self):
        """Line with unit_amount and employee hourly_cost returns hours * rate."""
        line = self.env['account.analytic.line'].create({
            'name': 'Assembly',
            'account_id': self.analytic_account.id,
            'company_id': self.company.id,
            'date': '2025-01-15',
            'employee_id': self.employee.id,
            'unit_amount': 4.0,
            'amount': 0,
        })
        cost = line._get_timesheet_labor_cost_for_production()
        self.assertAlmostEqual(cost, 4.0 * 25.0, places=2)

    def test_analytic_line_cost_from_hours_and_product(self):
        """Line with unit_amount and product (no employee rate) uses product cost."""
        line = self.env['account.analytic.line'].create({
            'name': 'Labor',
            'account_id': self.analytic_account.id,
            'company_id': self.company.id,
            'date': '2025-01-15',
            'product_id': self.product_service.id,
            'unit_amount': 2.0,
            'amount': 0,
        })
        cost = line._get_timesheet_labor_cost_for_production()
        self.assertAlmostEqual(cost, 2.0 * 30.0, places=2)

    def test_analytic_line_cost_zero_hours(self):
        """Line with zero unit_amount returns 0."""
        line = self.env['account.analytic.line'].create({
            'name': 'No time',
            'account_id': self.analytic_account.id,
            'company_id': self.company.id,
            'date': '2025-01-15',
            'employee_id': self.employee.id,
            'unit_amount': 0.0,
        })
        cost = line._get_timesheet_labor_cost_for_production()
        self.assertEqual(cost, 0.0)

    def test_mrp_production_timesheet_labor_total(self):
        """MO with several timesheet lines has correct total labor cost."""
        # Create minimal MO (required fields depend on Odoo version; use search or create minimal)
        product_finished = self.env['product.product'].create({
            'name': 'Finished Good',
            'type': 'product',
            'categ_id': self.env.ref('product.product_category_all').id,
        })
        bom = self.env['mrp.bom'].create({
            'product_tmpl_id': product_finished.product_tmpl_id.id,
            'product_qty': 1.0,
            'product_uom_id': self.env.ref('uom.product_uom_unit').id,
        })
        production = self.env['mrp.production'].create({
            'product_id': product_finished.id,
            'product_qty': 1.0,
            'product_uom_id': self.env.ref('uom.product_uom_unit').id,
            'bom_id': bom.id,
        })
        # Add timesheet lines
        self.env['account.analytic.line'].create([
            {
                'name': 'Line 1',
                'account_id': self.analytic_account.id,
                'company_id': self.company.id,
                'date': '2025-01-15',
                'mrp_production_id': production.id,
                'employee_id': self.employee.id,
                'unit_amount': 2.0,
                'amount': 0,
            },
            {
                'name': 'Line 2',
                'account_id': self.analytic_account.id,
                'company_id': self.company.id,
                'date': '2025-01-15',
                'mrp_production_id': production.id,
                'amount': 50.0,
                'unit_amount': 0,
            },
        ])
        total = production._get_timesheet_labor_total()
        # 2 * 25 + 50 = 100
        self.assertAlmostEqual(total, 100.0, places=2)
        self.assertAlmostEqual(production.timesheet_labor_cost, 100.0, places=2)

    def test_post_timesheet_labor_raises_without_labor_account(self):
        """Posting labor cost raises UserError when company has no production labor expense account."""
        self.company.production_labor_expense_account_id = False
        product_finished = self.env['product.product'].create({
            'name': 'Finished Good 2',
            'type': 'product',
            'categ_id': self.env.ref('product.product_category_all').id,
        })
        bom = self.env['mrp.bom'].create({
            'product_tmpl_id': product_finished.product_tmpl_id.id,
            'product_qty': 1.0,
            'product_uom_id': self.env.ref('uom.product_uom_unit').id,
        })
        production = self.env['mrp.production'].create({
            'product_id': product_finished.id,
            'product_qty': 1.0,
            'product_uom_id': self.env.ref('uom.product_uom_unit').id,
            'bom_id': bom.id,
        })
        self.env['account.analytic.line'].create({
            'name': 'Labor',
            'account_id': self.analytic_account.id,
            'company_id': self.company.id,
            'date': '2025-01-15',
            'mrp_production_id': production.id,
            'employee_id': self.employee.id,
            'unit_amount': 1.0,
            'amount': 0,
        })
        with self.assertRaises(UserError) as cm:
            production._post_timesheet_labor_cost_if_any()
        self.assertIn('Production labor expense account', str(cm.exception))

    def test_bom_cost_calculation_materials_only(self):
        """BoM with components but no past MOs calculates material cost only."""
        # Create component products with costs
        component1 = self.env['product.product'].create({
            'name': 'Component A',
            'type': 'product',
            'standard_price': 10.0,
        })
        component2 = self.env['product.product'].create({
            'name': 'Component B',
            'type': 'product',
            'standard_price': 5.0,
        })
        # Create finished product
        finished = self.env['product.product'].create({
            'name': 'Finished Product',
            'type': 'product',
            'standard_price': 0.0,
        })
        # Create BoM: 2 units of finished = 3x A + 4x B
        bom = self.env['mrp.bom'].create({
            'product_tmpl_id': finished.product_tmpl_id.id,
            'product_qty': 2.0,
            'product_uom_id': self.env.ref('uom.product_uom_unit').id,
        })
        self.env['mrp.bom.line'].create([
            {
                'bom_id': bom.id,
                'product_id': component1.id,
                'product_qty': 3.0,
            },
            {
                'bom_id': bom.id,
                'product_id': component2.id,
                'product_qty': 4.0,
            },
        ])
        # Call action (no past MOs, so labor = 0)
        bom.action_update_cost_from_bom_and_labor()
        
        # Material cost = 3*10 + 4*5 = 30 + 20 = 50 for 2 units = 25/unit
        self.assertAlmostEqual(finished.standard_price, 25.0, places=2)

    def test_bom_cost_calculation_with_labor(self):
        """BoM cost includes avg labor from past completed MOs."""
        # Create component and finished product
        component = self.env['product.product'].create({
            'name': 'Component C',
            'type': 'product',
            'standard_price': 20.0,
        })
        finished = self.env['product.product'].create({
            'name': 'Finished Product 2',
            'type': 'product',
            'standard_price': 0.0,
        })
        # Create BoM: 1 unit finished = 2x component
        bom = self.env['mrp.bom'].create({
            'product_tmpl_id': finished.product_tmpl_id.id,
            'product_qty': 1.0,
            'product_uom_id': self.env.ref('uom.product_uom_unit').id,
        })
        self.env['mrp.bom.line'].create({
            'bom_id': bom.id,
            'product_id': component.id,
            'product_qty': 2.0,
        })
        # Create 2 completed MOs with timesheet labor
        for i in range(2):
            mo = self.env['mrp.production'].create({
                'product_id': finished.id,
                'product_qty': 1.0,
                'product_uom_id': self.env.ref('uom.product_uom_unit').id,
                'bom_id': bom.id,
                'state': 'done',  # Manually set to done for test
            })
            # Add timesheet: 2 hours @ 25/h = 50 per MO
            self.env['account.analytic.line'].create({
                'name': f'Labor MO {i+1}',
                'account_id': self.analytic_account.id,
                'company_id': self.company.id,
                'date': '2025-01-15',
                'mrp_production_id': mo.id,
                'employee_id': self.employee.id,
                'unit_amount': 2.0,
                'amount': 0,
            })
        
        # Call action: material = 2*20 = 40, labor = avg 50/unit, total = 90/unit
        bom.action_update_cost_from_bom_and_labor()
        
        # Expected: (40 materials + 50 labor) / 1 = 90/unit
        self.assertAlmostEqual(finished.standard_price, 90.0, places=2)
