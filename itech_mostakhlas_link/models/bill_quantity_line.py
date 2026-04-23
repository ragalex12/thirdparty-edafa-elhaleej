# -*- coding: utf-8 -*-
"""
iTech Mostakhlas Link - Bill Quantity Line Extension
====================================================
Extends bill.quantity.line to track invoiced quantities
"""

from odoo import models, fields, api, _


class BillQuantityLine(models.Model):
    """Extended Bill Quantity Line with Invoice Tracking"""
    _inherit = 'bill.quantity.line'

    # ========== Invoice Tracking Fields ==========
    invoice_line_ids = fields.Many2many(
        'account.move.line',
        'boq_line_invoice_line_rel',
        'boq_line_id',
        'invoice_line_id',
        string='Invoice Lines',
        readonly=True,
        help="Invoice lines linked to this BOQ line"
    )
    invoiced_qty = fields.Float(
        string='Invoiced Quantity',
        compute='_compute_invoiced_qty',
        store=True,
        digits='Account',
        help="Total quantity invoiced to vendor for this line"
    )
    remaining_qty = fields.Float(
        string='Remaining Quantity',
        compute='_compute_remaining_qty',
        store=True,
        digits='Account',
        help="Remaining quantity available for invoicing"
    )
    assigned_to_vendor = fields.Boolean(
        string='Assigned to Vendor',
        compute='_compute_assigned_to_vendor',
        store=True,
        help="Whether this line is assigned to a vendor"
    )

    # ========== Computed Methods ==========
    @api.depends('partner_id')
    def _compute_assigned_to_vendor(self):
        """Check if line is assigned to a vendor"""
        for line in self:
            line.assigned_to_vendor = bool(line.partner_id)

    @api.depends('invoice_line_ids.quantity', 'invoice_line_ids.move_id.state', 'invoice_line_ids.move_id.move_type')
    def _compute_invoiced_qty(self):
        """Calculate total invoiced quantity from vendor bills"""
        for line in self:
            if not line.partner_id:
                line.invoiced_qty = 0.0
                continue

            # جمع الكميات من فواتير المورد المكتملة
            invoiced_lines = line.invoice_line_ids.filtered(
                lambda l: l.move_id.move_type in ['in_invoice', 'in_refund'] and
                l.move_id.state == 'posted' and
                l.move_id.partner_id.id == line.partner_id.id
            )
            
            total_qty = 0.0
            for inv_line in invoiced_lines:
                if inv_line.move_id.move_type == 'in_invoice':
                    total_qty += inv_line.quantity
                elif inv_line.move_id.move_type == 'in_refund':
                    total_qty -= inv_line.quantity  # Credit note reduces quantity
            
            line.invoiced_qty = total_qty

    @api.depends('qty', 'invoiced_qty')
    def _compute_remaining_qty(self):
        """Calculate remaining quantity"""
        for line in self:
            line.remaining_qty = max(0.0, line.qty - line.invoiced_qty)

