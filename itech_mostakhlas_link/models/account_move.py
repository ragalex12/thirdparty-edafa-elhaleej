# -*- coding: utf-8 -*-
"""
iTech Mostakhlas Link - Account Move Extension
===============================================
Validates vendor bill quantities against BOQ allocations
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    """Extended Account Move with BOQ Quantity Validation"""
    _inherit = "account.move"

    def button_draft(self):
        """Remove invoice links when unposting"""
        result = super(AccountMove, self).button_draft()
        vendor_bills = self.filtered(
            lambda m: m.move_type in ['in_invoice', 'in_refund'] and 
            m.project_id
        )
        for bill in vendor_bills:
            self._remove_boq_invoice_links(bill)
        return result

    def _remove_boq_invoice_links(self, bill):
        """Remove invoice links from BOQ lines when unposting"""
        for line in bill.invoice_line_ids:
            if line.boq_line_id:
                line.boq_line_id.invoice_line_ids = [(3, line.id)]

    def action_post(self):
        """Post invoice and validate against BOQ quantities"""
        # التحقق من فواتير الموردين فقط
        vendor_bills = self.filtered(
            lambda m: m.move_type in ['in_invoice', 'in_refund'] and 
            m.project_id and 
            m.state == 'draft'
        )
        
        for bill in vendor_bills:
            self._validate_boq_quantities(bill)
            # Update BOQ line invoice links after validation
            self._update_boq_invoice_links(bill)
        
        result = super(AccountMove, self).action_post()
        return result

    def _validate_boq_quantities(self, bill):
        """Validate vendor bill quantities against BOQ"""
        errors = []
        warnings = []
        
        for line in bill.invoice_line_ids:
            if not line.boq_line_id:
                # تحذير إذا كان البند غير مربوط بـ BOQ
                if line.product_id and bill.project_id:
                    warnings.append(
                        _("Line '%s': Not linked to BOQ. Please link to BOQ line for validation.") % 
                        (line.name or line.product_id.name)
                    )
                continue
            
            boq_line = line.boq_line_id
            
            # التحقق من أن المورد صحيح
            if boq_line.partner_id.id != bill.partner_id.id:
                errors.append(
                    _("Line '%s': Vendor mismatch.\n"
                      "BOQ line is assigned to: %s\n"
                      "Invoice is for: %s\n"
                      "Please select correct BOQ line or update vendor.") % (
                        line.name or line.product_id.name,
                        boq_line.partner_id.name,
                        bill.partner_id.name
                    )
                )
                continue
            
            # التحقق من أن المنتج صحيح
            if boq_line.product_id.id != line.product_id.id:
                errors.append(
                    _("Line '%s': Product mismatch.\n"
                      "BOQ line product: %s\n"
                      "Invoice line product: %s") % (
                        line.name or line.product_id.name,
                        boq_line.product_id.name,
                        line.product_id.name
                    )
                )
                continue
            
            # حساب الكمية المفوترة الحالية (بما في ذلك هذه الفاتورة)
            current_qty = line.quantity
            if bill.move_type == 'in_refund':
                current_qty = -current_qty  # Credit note reduces quantity
            
            # حساب الكمية المفوترة سابقاً (من فواتير أخرى)
            # نستثني الفاتورة الحالية من الحساب
            previous_invoiced = boq_line.invoiced_qty
            
            # إذا كانت هذه الفاتورة مكتملة مسبقاً، نطرح كمية هذه الفاتورة
            if bill.state == 'posted':
                # البحث عن بنود هذه الفاتورة في BOQ
                bill_lines = boq_line.invoice_line_ids.filtered(
                    lambda l: l.move_id.id == bill.id
                )
                if bill_lines:
                    for bl in bill_lines:
                        if bl.move_id.move_type == 'in_invoice':
                            previous_invoiced -= bl.quantity
                        elif bl.move_id.move_type == 'in_refund':
                            previous_invoiced += bl.quantity
            
            # التحقق من عدم تجاوز الكمية المخصصة
            total_after = previous_invoiced + current_qty
            if total_after > boq_line.qty:
                excess = total_after - boq_line.qty
                errors.append(
                    _("Line '%s': Quantity exceeds BOQ allocation.\n\n"
                      "BOQ Allocated: %s %s\n"
                      "Previously Invoiced: %s %s\n"
                      "Current Invoice: %s %s\n"
                      "Total After: %s %s\n"
                      "Excess: %s %s\n\n"
                      "Please reduce quantity or update BOQ allocation.") % (
                        line.name or line.product_id.name,
                        boq_line.qty, boq_line.uom_id.name or '',
                        previous_invoiced, boq_line.uom_id.name or '',
                        current_qty, line.product_uom_id.name or '',
                        total_after, boq_line.uom_id.name or '',
                        excess, boq_line.uom_id.name or ''
                    )
                )
        
        if errors:
            error_message = _("Cannot post vendor bill. BOQ validation errors:\n\n%s") % '\n\n'.join(errors)
            raise ValidationError(error_message)
        
        if warnings:
            # يمكن إضافة تحذيرات بدون منع التأكيد
            pass

    def _update_boq_invoice_links(self, bill):
        """Update BOQ line invoice links after validation"""
        for line in bill.invoice_line_ids:
            if line.boq_line_id:
                # إضافة بند الفاتورة إلى قائمة فواتير بند BOQ
                line.boq_line_id.invoice_line_ids = [(4, line.id)]

