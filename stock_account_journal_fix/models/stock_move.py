# -*- coding: utf-8 -*-
"""
Fix: resolve stock journal from product category then company when creating
account move for stock valuation (MO completion, receipts, etc.).
Compatible with Odoo 19.
"""
from odoo import Command, _, models
from odoo.exceptions import UserError


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _get_stock_journal_for_account_move(self):
        """
        Resolve the journal to use for the stock valuation account move.
        Order: first valued move's product category stock journal, then company stock journal.
        Matches product.get_product_accounts()['stock_journal'] resolution.
        """
        self.ensure_one()
        company = self.company_id
        # Resolve in move's company context (company-dependent fields)
        categ = self.product_id.categ_id.with_company(company)
        journal = (
            categ.property_stock_journal
            or categ._fields['property_stock_journal'].get_company_dependent_fallback(categ)
            or company.account_stock_journal_id
        )
        return journal

    def _create_account_move(self):
        """ Create account move for specific location or analytic. """
        aml_vals_list = []
        move_to_link = set()
        for move in self:
            if move._should_create_account_move():
                aml_vals_list += move._get_account_move_line_vals()
                move_to_link.add(move.id)
        if not aml_vals_list:
            return self.env['account.move']
        # Resolve journal: first valued move's product category or company (fix for missing company journal)
        first_valued = self.env['stock.move'].browse(next(iter(move_to_link)))
        journal = first_valued._get_stock_journal_for_account_move()
        if not journal:
            raise UserError(
                _("No Stock Journal found for company '%s'. "
                  "Set Inventory > Configuration > Settings > Journal for Inventory Valuation, "
                  "or set Stock Journal on the product category.")
                % self.company_id.name
            )
        account_move = self.env['account.move'].create({
            'journal_id': journal.id,
            'line_ids': [Command.create(aml_vals) for aml_vals in aml_vals_list],
        })
        self.env['stock.move'].browse(move_to_link).account_move_id = account_move.id
        account_move._post()
        return account_move
