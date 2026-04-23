# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # --- References ---
    contract_ref = fields.Char(string="Contract No")
    po_ref = fields.Char(string="PO No")
    invoice_ref = fields.Char(string="Inv Ref")
    covered_period = fields.Char(string="Covered Period")

    # --- Deduction inputs (monetary in order currency) ---
    performance_bond_percent = fields.Float(
        string="Performance Bond %",
        default=0.0,
    )
    performance_bond_amount = fields.Monetary(
        string="Performance Bond",
        currency_field="currency_id",
        compute="_compute_performance_bond_amount",
        store=True,
        readonly=False,
    )
    retention_percent = fields.Float(
        string="Retention %",
        default=0.0,
    )
    retention_amount = fields.Monetary(
        string="Retention Amount",
        currency_field="currency_id",
        compute="_compute_retention_amount",
        store=True,
        readonly=False,
    )

    # --- Computed (for display) ---
    gross_untaxed = fields.Monetary(
        string="Gross (Untaxed)",
        currency_field="currency_id",
        compute="_compute_deduction_totals",
        store=True,
    )
    deductions_total = fields.Monetary(
        string="Total Deductions",
        currency_field="currency_id",
        compute="_compute_deduction_totals",
        store=True,
    )
    tax_base_after_deductions = fields.Monetary(
        string="Tax Base After Deductions",
        currency_field="currency_id",
        compute="_compute_deduction_totals",
        store=True,
    )
    net_collect_now = fields.Monetary(
        string="Net Collect Now",
        currency_field="currency_id",
        compute="_compute_deduction_totals",
        store=True,
    )

    def _has_order_lines(self):
        self.ensure_one()
        return bool(self.order_line)

    @api.depends(
        "order_line",
        "order_line.price_subtotal",
        "performance_bond_percent",
        "performance_bond_amount",
        "retention_percent",
        "retention_amount",
        "amount_total",
    )
    def _compute_deduction_totals(self):
        for order in self:
            if not order.order_line:
                order.gross_untaxed = 0
                order.deductions_total = 0
                order.tax_base_after_deductions = 0
                order.net_collect_now = 0
                continue
            gross = order.amount_untaxed or 0
            bond = order.performance_bond_amount or 0
            retention = order.retention_amount or 0
            # All deductions are calculated from gross untaxed amount (amount_untaxed)
            # Performance Bond and Retention are calculated from gross_untaxed but do NOT affect VAT calculation
            order.gross_untaxed = gross
            order.deductions_total = 0
            order.tax_base_after_deductions = gross
            # Net collect = total after VAT - retention - bond (what customer pays now)
            order.net_collect_now = abs(order.amount_total or 0) - retention - bond

    @api.depends(
        "order_line",
        "order_line.price_subtotal",
        "performance_bond_percent",
        "amount_untaxed",
        "currency_id",
    )
    def _compute_performance_bond_amount(self):
        for order in self:
            if not order.order_line:
                order.performance_bond_amount = 0
                continue
            if not order.performance_bond_percent:
                order.performance_bond_amount = 0
                continue
            if not order.currency_id:
                order.performance_bond_amount = 0
                continue
            # Calculate from gross untaxed amount (amount_untaxed)
            base = abs(order.amount_untaxed or 0)
            if base <= 0:
                order.performance_bond_amount = 0
                continue
            # Calculate: Performance Bond = Gross Untaxed * (Percentage / 100)
            calculated_amount = base * (order.performance_bond_percent / 100.0)
            order.performance_bond_amount = order.currency_id.round(calculated_amount)

    @api.depends("amount_untaxed", "retention_percent", "currency_id")
    def _compute_retention_amount(self):
        for order in self:
            if not order.order_line:
                order.retention_amount = 0
                continue
            if not order.retention_percent:
                order.retention_amount = 0
                continue
            if not order.currency_id:
                order.retention_amount = 0
                continue
            # Calculate from gross untaxed amount (amount_untaxed)
            base = abs(order.amount_untaxed or 0)
            if base <= 0:
                order.retention_amount = 0
                continue
            # Calculate: Retention = Gross Untaxed * (Percentage / 100)
            calculated_amount = base * (order.retention_percent / 100.0)
            order.retention_amount = order.currency_id.round(calculated_amount)

    @api.onchange("retention_percent")
    def _onchange_retention_percent(self):
        if self.retention_percent and not self._has_order_lines():
            self.retention_percent = 0.0
            return {
                "warning": {
                    "title": "No Order Lines",
                    "message": "Add order lines before setting Retention %.",
                }
            }

    @api.onchange("performance_bond_percent")
    def _onchange_performance_bond_percent(self):
        if self.performance_bond_percent and not self._has_order_lines():
            self.performance_bond_percent = 0.0
            return {
                "warning": {
                    "title": "No Order Lines",
                    "message": "Add order lines before setting Performance Bond %.",
                }
            }

    @api.onchange("order_line")
    def _onchange_order_line(self):
        if not self.order_line:
            if self.retention_percent:
                self.retention_percent = 0.0
            if self.performance_bond_percent:
                self.performance_bond_percent = 0.0

    @api.constrains("performance_bond_amount", "retention_amount")
    def _check_deductions_non_negative(self):
        for order in self:
            if (order.performance_bond_amount or 0) < 0:
                raise ValidationError(_("Performance Bond cannot be negative."))
            if (order.retention_amount or 0) < 0:
                raise ValidationError(_("Retention Amount cannot be negative."))

    @api.constrains("performance_bond_percent")
    def _check_performance_bond_percent(self):
        for order in self:
            if order.performance_bond_percent < 0 or order.performance_bond_percent > 100:
                raise ValidationError(_("Performance Bond % must be between 0 and 100."))

    @api.constrains(
        "performance_bond_amount",
        "retention_amount",
        "amount_total",
    )
    def _check_deductions_not_exceed_total(self):
        for order in self:
            total = order.amount_total or 0
            reduce_total = (
                (order.performance_bond_amount or 0)
                + (order.retention_amount or 0)
            )
            if total and reduce_total > total:
                raise ValidationError(
                    _("Sum of deductions (performance bond + retention) cannot exceed total.")
                )
