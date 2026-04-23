# -*- coding: utf-8 -*-
"""
iTech Mostakhlas Link - Account Move Line Extension
===================================================
Links invoice lines to BOQ lines for validation
"""

from odoo import models, fields, api, _


class AccountMoveLine(models.Model):
    """Extended Account Move Line with BOQ Link"""
    _inherit = 'account.move.line'

    boq_line_id = fields.Many2one(
        'bill.quantity.line',
        string='BOQ Line',
        help="Link this invoice line to BOQ line for validation",
        ondelete='restrict'
    )
    boq_allocated_qty = fields.Float(
        string='BOQ Allocated Qty',
        related='boq_line_id.qty',
        readonly=True,
        help="Quantity allocated in BOQ for this vendor"
    )
    boq_invoiced_qty = fields.Float(
        string='BOQ Invoiced Qty',
        related='boq_line_id.invoiced_qty',
        readonly=True,
        help="Previously invoiced quantity from BOQ"
    )
    boq_remaining_qty = fields.Float(
        string='BOQ Remaining Qty',
        related='boq_line_id.remaining_qty',
        readonly=True,
        help="Remaining quantity available in BOQ"
    )

    @api.onchange('boq_line_id')
    def _onchange_boq_line_id(self):
        """Auto-fill product and validate when BOQ line is selected"""
        if self.boq_line_id:
            # تعيين المنتج إذا لم يكن محدداً
            if not self.product_id:
                self.product_id = self.boq_line_id.product_id
            
            # تعيين وحدة القياس
            if self.boq_line_id.uom_id:
                self.product_uom_id = self.boq_line_id.uom_id
            
            # تحذير إذا كانت الكمية المتبقية قليلة
            if self.boq_line_id.remaining_qty < self.quantity:
                return {
                    'warning': {
                        'title': _('Quantity Warning'),
                        'message': _(
                            'Remaining quantity in BOQ is %s %s. '
                            'You are trying to invoice %s %s.'
                        ) % (
                            self.boq_line_id.remaining_qty,
                            self.boq_line_id.uom_id.name or '',
                            self.quantity,
                            self.product_uom_id.name or ''
                        )
                    }
                }

    @api.onchange('product_id', 'move_id.partner_id')
    def _onchange_product_boq_domain(self):
        """Update BOQ line domain based on product and vendor"""
        if self.product_id and self.move_id.partner_id:
            return {
                'domain': {
                    'boq_line_id': [
                        ('partner_id', '=', self.move_id.partner_id.id),
                        ('product_id', '=', self.product_id.id),
                        ('bill_quantity_id.project_id', '=', self.move_id.project_id.id if self.move_id.project_id else False)
                    ]
                }
            }

