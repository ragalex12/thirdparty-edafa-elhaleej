# -*- coding: utf-8 -*-
"""
Unit tests for stock_account_journal_fix (Odoo 19).
Tests journal resolution: product category then company, and UserError when none set.
"""
from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.stock_account.tests.common import TestStockValuationCommon
from odoo.addons.stock_account.tests.test_stockvaluation import _create_accounting_data


@tagged('post_install', '-at_install')
class TestStockAccountJournalFix(TestStockValuationCommon):
    """Tests for stock move account move journal resolution (category then company)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.ref('base.EUR').active = True
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.customer_location = cls.env.ref('stock.stock_location_customers')
        cls.supplier_location = cls.env.ref('stock.stock_location_suppliers')
        cls.uom_id = cls.env.ref('uom.product_uom_unit')
        # Accounting data
        (cls.stock_valuation_account, cls.expense_account, cls.income_account,
         cls.stock_journal) = _create_accounting_data(cls.env)
        cls.stock_valuation_account.account_stock_variation_id = cls.expense_account
        # Ensure stock location has valuation account so _should_create_account_move is True
        cls.stock_location.valuation_account_id = cls.stock_valuation_account
        # Dedicated category and product (avoid modifying shared product_category_goods)
        cls.test_categ = cls.env['product.category'].create({
            'name': 'Test Stock Journal Category',
            'property_stock_valuation_account_id': cls.stock_valuation_account.id,
            'property_valuation': 'real_time',
        })
        cls.product1 = cls.env['product.product'].create({
            'name': 'Product A',
            'is_storable': True,
            'default_code': 'prda',
            'categ_id': cls.test_categ.id,
        })
        cls.product1.write({
            'property_account_income_id': cls.income_account.id,
            'property_account_expense_id': cls.expense_account.id,
        })
        # Second journal for "category only" tests
        cls.category_journal = cls.env['account.journal'].create({
            'name': 'Category Stock Journal',
            'code': 'CATSTK',
            'type': 'general',
        })

    def test_get_stock_journal_company_only(self):
        """Company has stock journal, category has none -> returns company journal."""
        self.env.company.account_stock_journal_id = self.stock_journal
        self.test_categ.property_stock_journal = False
        move = self.env['stock.move'].create({
            'product_id': self.product1.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
            'product_uom': self.uom_id.id,
            'product_uom_qty': 1.0,
            'company_id': self.company.id,
        })
        journal = move._get_stock_journal_for_account_move()
        self.assertEqual(journal, self.stock_journal)

    def test_get_stock_journal_category_overrides(self):
        """Company has no journal, category has journal -> returns category journal (fix)."""
        self.env.company.account_stock_journal_id = False
        self.test_categ.property_stock_journal = self.category_journal
        move = self.env['stock.move'].create({
            'product_id': self.product1.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
            'product_uom': self.uom_id.id,
            'product_uom_qty': 1.0,
            'company_id': self.company.id,
        })
        journal = move._get_stock_journal_for_account_move()
        self.assertEqual(journal, self.category_journal)

    def test_get_stock_journal_category_first(self):
        """Both company and category have journal -> category wins (resolution order)."""
        self.env.company.account_stock_journal_id = self.stock_journal
        self.test_categ.property_stock_journal = self.category_journal
        move = self.env['stock.move'].create({
            'product_id': self.product1.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
            'product_uom': self.uom_id.id,
            'product_uom_qty': 1.0,
            'company_id': self.company.id,
        })
        journal = move._get_stock_journal_for_account_move()
        self.assertEqual(journal, self.category_journal)

    def test_create_account_move_uses_category_journal_when_company_unset(self):
        """In move creates account move with category journal when company journal is unset."""
        self.env.company.account_stock_journal_id = False
        self.test_categ.property_stock_journal = self.category_journal
        self.product1.standard_price = 10.0
        move = self._make_in_move(self.product1, 2, 10)
        self.assertTrue(move.account_move_id, 'Account move should be created')
        self.assertEqual(
            move.account_move_id.journal_id,
            self.category_journal,
            'Account move should use category journal',
        )

    def test_create_account_move_uses_company_journal_when_category_unset(self):
        """In move creates account move with company journal when category has no journal."""
        self.env.company.account_stock_journal_id = self.stock_journal
        self.test_categ.property_stock_journal = False
        self.product1.standard_price = 10.0
        move = self._make_in_move(self.product1, 2, 10)
        self.assertTrue(move.account_move_id, 'Account move should be created')
        self.assertEqual(
            move.account_move_id.journal_id,
            self.stock_journal,
            'Account move should use company journal',
        )

    def test_create_account_move_no_journal_raises_user_error(self):
        """When neither company nor category has stock journal, UserError is raised."""
        self.env.company.account_stock_journal_id = False
        self.test_categ.property_stock_journal = False
        self.product1.standard_price = 10.0
        with self.assertRaises(UserError) as cm:
            self._make_in_move(self.product1, 2, 10)
        self.assertIn('No Stock Journal found', str(cm.exception))
        self.assertIn(self.company.name, str(cm.exception))
