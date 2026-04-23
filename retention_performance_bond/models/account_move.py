# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    # --- References ---
    contract_ref = fields.Char(string="Contract No")
    po_ref = fields.Char(string="PO No")
    invoice_ref = fields.Char(string="Inv Ref")
    covered_period = fields.Char(string="Covered Period")

    # --- Deduction inputs (monetary, company currency for storage; use currency_id for display) ---
    performance_bond_percent = fields.Float(
        string="Performance Bond %",
        default=0.0,
    )
    performance_bond_amount = fields.Monetary(
        string="Performance Bond",
        currency_field="company_currency_id",
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
        currency_field="company_currency_id",
        compute="_compute_retention_amount",
        store=True,
        readonly=False,
    )

    # --- Computed (for display and journal logic) ---
    gross_untaxed = fields.Monetary(
        string="Gross (Untaxed)",
        currency_field="company_currency_id",
        compute="_compute_deduction_totals",
        store=True,
    )
    deductions_total = fields.Monetary(
        string="Total Deductions",
        currency_field="company_currency_id",
        compute="_compute_deduction_totals",
        store=True,
    )
    tax_base_after_deductions = fields.Monetary(
        string="Tax Base After Deductions",
        currency_field="company_currency_id",
        compute="_compute_deduction_totals",
        store=True,
    )
    net_collect_now = fields.Monetary(
        string="Net Collect Now",
        currency_field="company_currency_id",
        compute="_compute_deduction_totals",
        store=True,
    )
    has_deduction_lines = fields.Boolean(
        string="Has Deduction Lines",
        compute="_compute_has_deduction_lines",
        store=False,
        help="Indicates if deduction journal lines have been created for this invoice",
    )
    deduction_line_ids = fields.Many2many(
        'account.move.line',
        string="Deduction Journal Lines",
        compute="_compute_deduction_line_ids",
        store=False,
        help="Journal lines created for deductions (performance bond, retention)",
    )
    deduction_lines_count = fields.Integer(
        string="Deduction Lines Count",
        compute="_compute_deduction_line_ids",
        store=False,
    )
    deduction_journal_id = fields.Many2one(
        'account.move',
        string="Deduction Journal Entry",
        readonly=True,
        help="MISC journal entry created for deductions related to this invoice",
    )

    def _has_invoice_lines(self):
        self.ensure_one()
        return bool(self.invoice_line_ids)

    @api.depends("deduction_journal_id", "deduction_journal_id.line_ids", "state")
    def _compute_deduction_line_ids(self):
        """Compute deduction journal lines for this invoice."""
        for move in self:
            if move.move_type != "out_invoice" or move.state != "posted":
                move.has_deduction_lines = False
                move.deduction_line_ids = False
                move.deduction_lines_count = 0
                continue
            
            # Check if deduction journal entry exists
            if move.deduction_journal_id and move.deduction_journal_id.line_ids:
                move.has_deduction_lines = True
                move.deduction_line_ids = move.deduction_journal_id.line_ids
                move.deduction_lines_count = len(move.deduction_journal_id.line_ids)
            else:
                move.has_deduction_lines = False
                move.deduction_line_ids = False
                move.deduction_lines_count = 0
    
    @api.depends("line_ids", "line_ids.account_id", "line_ids.name", "state")
    def _compute_has_deduction_lines(self):
        """Compute whether deduction journal lines exist and store them."""
        self._compute_deduction_line_ids()

    @api.depends(
        "invoice_line_ids",
        "invoice_line_ids.price_subtotal",
        "performance_bond_percent",
        "performance_bond_amount",
        "retention_percent",
        "retention_amount",
        "amount_total",
    )
    def _compute_deduction_totals(self):
        for move in self:
            if move.move_type != "out_invoice":
                move.gross_untaxed = 0
                move.deductions_total = 0
                move.tax_base_after_deductions = 0
                move.net_collect_now = move.amount_total or 0
                continue
            if not move.invoice_line_ids:
                move.gross_untaxed = 0
                move.deductions_total = 0
                move.tax_base_after_deductions = 0
                move.net_collect_now = 0
                continue
            gross = move.amount_untaxed_signed or 0
            bond = move.performance_bond_amount or 0
            retention = move.retention_amount or 0
            # All deductions are calculated from gross untaxed amount (amount_untaxed_signed)
            # Performance Bond and Retention are calculated from gross_untaxed but do NOT affect VAT calculation
            move.gross_untaxed = gross
            move.deductions_total = 0
            move.tax_base_after_deductions = gross
            # Net collect = total after VAT - retention - bond (what customer pays now)
            move.net_collect_now = abs(move.amount_total_signed or 0) - retention - bond

    @api.depends(
        "invoice_line_ids",
        "invoice_line_ids.price_subtotal",
        "performance_bond_percent",
        "amount_untaxed_signed",
        "currency_id",
    )
    def _compute_performance_bond_amount(self):
        for move in self:
            if move.move_type != "out_invoice":
                move.performance_bond_amount = 0
                continue
            if not move.invoice_line_ids:
                move.performance_bond_amount = 0
                continue
            if not move.performance_bond_percent:
                move.performance_bond_amount = 0
                continue
            if not move.currency_id:
                move.performance_bond_amount = 0
                continue
            # Calculate from gross untaxed amount (amount_untaxed_signed)
            base = abs(move.amount_untaxed_signed or 0)
            if base <= 0:
                move.performance_bond_amount = 0
                continue
            # Calculate: Performance Bond = Gross Untaxed * (Percentage / 100)
            calculated_amount = base * (move.performance_bond_percent)
            move.performance_bond_amount = move.currency_id.round(calculated_amount)

    @api.depends("amount_untaxed_signed", "retention_percent", "currency_id")
    def _compute_retention_amount(self):
        for move in self:
            if move.move_type != "out_invoice":
                move.retention_amount = 0
                continue
            if not move.invoice_line_ids:
                move.retention_amount = 0
                continue
            if not move.retention_percent:
                move.retention_amount = 0
                continue
            if not move.currency_id:
                move.retention_amount = 0
                continue
            # Calculate from gross untaxed amount (amount_untaxed_signed)
            base = abs(move.amount_untaxed_signed or 0)
            if base <= 0:
                move.retention_amount = 0
                continue
            # Calculate: Retention = Gross Untaxed * (Percentage / 100)
            calculated_amount = base * (move.retention_percent)
            move.retention_amount = move.currency_id.round(calculated_amount)

    @api.onchange("retention_percent")
    def _onchange_retention_percent(self):
        if self.retention_percent and not self._has_invoice_lines():
            self.retention_percent = 0.0
            return {
                "warning": {
                    "title": "No Invoice Lines",
                    "message": "Add invoice lines before setting Retention %.",
                }
            }

    @api.onchange("performance_bond_percent")
    def _onchange_performance_bond_percent(self):
        if self.performance_bond_percent and not self._has_invoice_lines():
            self.performance_bond_percent = 0.0
            return {
                "warning": {
                    "title": "No Invoice Lines",
                    "message": "Add invoice lines before setting Performance Bond %.",
                }
            }

    @api.onchange("invoice_line_ids")
    def _onchange_invoice_line_ids(self):
        # Only reset percentages in draft state to avoid issues with posted invoices
        if self.state == "draft" and not self.invoice_line_ids:
            if self.retention_percent:
                self.retention_percent = 0.0
            if self.performance_bond_percent:
                self.performance_bond_percent = 0.0

    @api.constrains("performance_bond_amount", "retention_amount")
    def _check_deductions_non_negative(self):
        for move in self:
            if move.move_type != "out_invoice":
                continue
            if (move.performance_bond_amount or 0) < 0:
                raise ValidationError(_("Performance Bond cannot be negative."))
            if (move.retention_amount or 0) < 0:
                raise ValidationError(_("Retention Amount cannot be negative."))

    @api.constrains("performance_bond_percent")
    def _check_performance_bond_percent(self):
        for move in self:
            if move.move_type != "out_invoice":
                continue
            if move.performance_bond_percent < 0 or move.performance_bond_percent > 100:
                raise ValidationError(_("Performance Bond % must be between 0 and 100."))

    @api.constrains("performance_bond_amount", "retention_amount", "amount_total")
    def _check_deductions_not_exceed_total(self):
        for move in self:
            if move.move_type != "out_invoice" or not move.amount_total:
                continue
            total = abs(move.amount_total_signed or 0)
            reduce_total = (move.performance_bond_amount or 0) + (move.retention_amount or 0)
            if reduce_total > total:
                raise ValidationError(_(
                    "Sum of deductions (performance bond + retention) cannot exceed invoice total."
                ))

    def _get_deduction_amounts(self):
        """Return amounts in company currency for journal lines. Only for out_invoice with deductions."""
        self.ensure_one()
        if self.move_type != "out_invoice":
            return None
        bond = self.performance_bond_amount or 0
        ret = self.retention_amount or 0
        if bond == 0 and ret == 0:
            return None
        # Convert to company currency if invoice is in other currency
        company_currency = self.company_id.currency_id
        if self.currency_id != company_currency:
            date = self.invoice_date or self.date
            bond = self.currency_id._convert(bond, company_currency, self.company_id, date)
            ret = self.currency_id._convert(ret, company_currency, self.company_id, date)
        return {"performance_bond": bond, "retention": ret}

    def _get_gcc_report_amounts(self):
        """Return GCC amounts converted to document currency for printing."""
        self.ensure_one()
        company_currency = self.company_currency_id or self.company_id.currency_id
        document_currency = self.currency_id or company_currency
        date = self.invoice_date or self.date or fields.Date.context_today(self)

        def _convert(amount):
            amount = amount or 0.0
            if not company_currency or not document_currency:
                return amount
            if company_currency == document_currency:
                return amount
            return company_currency._convert(amount, document_currency, self.company_id, date)

        return {
            "gross_untaxed": _convert(self.gross_untaxed),
            "tax_base_after_deductions": _convert(self.tax_base_after_deductions),
            "net_collect_now": _convert(self.net_collect_now),
            "performance_bond_amount": _convert(self.performance_bond_amount),
            "retention_amount": _convert(self.retention_amount),
        }

    def _validate_deduction_accounts(self):
        """Block posting if any deduction amount > 0 but corresponding account not set."""
        self.ensure_one()
        amounts = self._get_deduction_amounts()
        if not amounts:
            return
        company = self.company_id
        if amounts["performance_bond"] > 0 and not company.performance_bond_receivable_account_id:
            raise ValidationError(
                "Performance Bond is set but company has no 'Performance Bonds Receivable' account. "
                "Configure it in Accounting Settings."
            )
        if amounts["retention"] > 0 and not company.retention_receivable_account_id:
            raise ValidationError(
                "Retention is set but company has no 'Retention Receivable' account. "
                "Configure it in Accounting Settings."
            )

    def _create_deduction_move_lines(self):
        """
        Create a separate MISC journal entry for deductions related to the invoice.
        The journal entry will contain:
        - Debit Retention receivable / Credit Sales/Revenue
        - Debit Performance bond receivable / Credit Sales/Revenue
        
        This creates a separate journal entry instead of modifying the invoice directly.
        """
        for move in self:
            if move.move_type != "out_invoice" or move.state != "posted":
                continue
            
            # Check if deduction journal already exists
            if move.deduction_journal_id:
                _logger.debug(
                    "Deduction journal entry already exists for invoice %s: %s",
                    move.name or move.id,
                    move.deduction_journal_id.name
                )
                continue
            
            amounts = move._get_deduction_amounts()
            if not amounts:
                continue

            company = move.company_id
            partner = move.partner_id
            company_currency = company.currency_id

            # Get balance account from company settings
            balance_account = company.deduction_balance_account_id
            
            # If not configured in settings, try to find from invoice lines as fallback
            if not balance_account:
                for invoice_line in move.invoice_line_ids:
                    if invoice_line.account_id:
                        # Odoo 16+: account_type; older: user_type_id.type
                        atype = getattr(invoice_line.account_id, "account_type", None)
                        if not atype and hasattr(invoice_line.account_id, "user_type_id"):
                            atype = getattr(invoice_line.account_id.user_type_id, "type", None)
                        # Check if it's an income/revenue account
                        if atype in ("income", "income_other", "revenue", "revenue_other"):
                            balance_account = invoice_line.account_id
                            break
                
                # If still not found, try to get from product's default income account
                if not balance_account and move.invoice_line_ids:
                    for invoice_line in move.invoice_line_ids:
                        if invoice_line.product_id:
                            product = invoice_line.product_id
                            # Try to get income account from product
                            if hasattr(product, 'property_account_income_id') and product.property_account_income_id:
                                balance_account = product.property_account_income_id
                                break
                            # Or from product category
                            if product.categ_id and hasattr(product.categ_id, 'property_account_income_categ_id') and product.categ_id.property_account_income_categ_id:
                                balance_account = product.categ_id.property_account_income_categ_id
                                break
            
            if not balance_account:
                raise ValidationError(
                    _("Balance account for deductions is not configured. Please set 'Balance Account for Deductions' in Accounting Settings.")
                )
            date = move.date
            invoice_ref = move.ref or move.name or ""
            
            # Get MISC journal (search for journal with code 'MISC')
            misc_journal = self.env['account.journal'].search([
                ('company_id', '=', company.id),
                ('code', '=', 'MISC'),
            ], limit=1)
            
            if not misc_journal:
                raise ValidationError(
                    _("No journal with code 'MISC' found for company %s. Please create a journal with code 'MISC' first.") % company.name
                )

            lines_vals = []

            # 1. Retention: Dr Retention receivable, Cr Sales/Revenue
            if amounts["retention"] > 0:
                lines_vals.append((0, 0, {
                    "name": _("Retention (%.2f%%) - Invoice: %s") % (move.retention_percent or 0, invoice_ref),
                    "account_id": company.retention_receivable_account_id.id,
                    "partner_id": partner.id,
                    "debit": amounts["retention"],
                    "credit": 0,
                    "date": date,
                }))
                lines_vals.append((0, 0, {
                    "name": _("Retention (%.2f%%) - Invoice: %s") % (move.retention_percent or 0, invoice_ref),
                    "account_id": balance_account.id,
                    "partner_id": partner.id,
                    "debit": 0,
                    "credit": amounts["retention"],
                    "date": date,
                }))

            # 2. Performance bond: Dr Performance bond receivable, Cr Sales/Revenue
            if amounts["performance_bond"] > 0:
                lines_vals.append((0, 0, {
                    "name": _("Performance Bond - Invoice: %s") % invoice_ref,
                    "account_id": company.performance_bond_receivable_account_id.id,
                    "partner_id": partner.id,
                    "debit": amounts["performance_bond"],
                    "credit": 0,
                    "date": date,
                }))
                lines_vals.append((0, 0, {
                    "name": _("Performance Bond - Invoice: %s") % invoice_ref,
                    "account_id": balance_account.id,
                    "partner_id": partner.id,
                    "debit": 0,
                    "credit": amounts["performance_bond"],
                    "date": date,
                }))

            if lines_vals:
                try:
                    # Create MISC journal entry
                    # Build journal reference based on which deductions are present
                    has_performance_bond = amounts.get("performance_bond", 0) > 0
                    has_retention = amounts.get("retention", 0) > 0
                    
                    if has_performance_bond and has_retention:
                        journal_ref = _("Performance Bond and Retention for Invoice: %s") % invoice_ref
                    elif has_performance_bond:
                        journal_ref = _("Performance Bond for Invoice: %s") % invoice_ref
                    elif has_retention:
                        journal_ref = _("Retention for Invoice: %s") % invoice_ref
                    else:
                        journal_ref = _("Deductions for Invoice: %s") % invoice_ref
                    
                    deduction_move = self.env['account.move'].create({
                        'move_type': 'entry',
                        'journal_id': misc_journal.id,
                        'date': date,
                        'ref': journal_ref,
                        'narration': _("Deduction journal entry related to invoice %s") % invoice_ref,
                        'line_ids': lines_vals,
                        'currency_id': company_currency.id,
                    })
                    
                    # Post the journal entry
                    deduction_move.action_post()
                    
                    # Link the journal entry to the invoice
                    move.deduction_journal_id = deduction_move.id
                    
                    # Recompute has_deduction_lines to update button visibility
                    move._compute_has_deduction_lines()
                    
                    # Invalidate cache to ensure the field is updated in the UI
                    move.invalidate_recordset(['deduction_journal_id', 'has_deduction_lines'])
                    
                    _logger.info(
                        "Successfully created deduction journal entry %s for invoice %s",
                        deduction_move.name,
                        move.name or move.id
                    )
                except Exception as e:
                    _logger.error(
                        "Error creating deduction journal entry for invoice %s: %s",
                        move.name or move.id,
                        str(e),
                        exc_info=True
                    )
                    raise ValidationError(
                        _("Error creating deduction journal entry: %s") % str(e)
                    )

    def _remove_deduction_move_lines(self, move):
        """Remove existing deduction lines if amounts are zero.
        
        Note: This can only remove lines if the invoice is in draft state.
        For posted invoices, lines cannot be deleted.
        
        IMPORTANT: This method should NEVER be called for posted invoices.
        """
        # Strict check - only work on draft invoices
        if move.state != "draft":
            _logger.debug(
                "Skipping _remove_deduction_move_lines for invoice %s: state is %s (must be draft)",
                move.name or move.id,
                move.state
            )
            return
        
        company = move.company_id
        deduction_accounts = []
        if company.retention_receivable_account_id:
            deduction_accounts.append(company.retention_receivable_account_id.id)
        if company.performance_bond_receivable_account_id:
            deduction_accounts.append(company.performance_bond_receivable_account_id.id)
        
        if not deduction_accounts:
            return
        
        # Find and remove deduction lines (only in draft state)
        deduction_names = [
            _("Retention"),
            _("Performance Bond"),
        ]
        deduction_lines = move.line_ids.filtered(
            lambda l: l.account_id.id in deduction_accounts and
                     any(name in (l.name or "") for name in deduction_names)
        )
        
        # Triple-check: state must be draft, lines must belong to draft move
        if deduction_lines:
            # Only unlink if ALL safety checks pass
            safe_to_delete = (
                move.state == "draft" and
                all(not line.move_id or line.move_id.state == "draft" for line in deduction_lines)
            )
            
            if safe_to_delete:
                try:
                    deduction_lines.unlink()
                except Exception as e:
                    _logger.error(
                        "Error removing deduction lines from invoice %s: %s",
                        move.name or move.id,
                        str(e)
                    )
            else:
                _logger.warning(
                    "Cannot remove deduction lines from invoice %s: safety checks failed (state=%s)",
                    move.name or move.id,
                    move.state
                )

    def action_generate_deduction_lines(self):
        """Manual action to generate deduction journal lines for posted invoices.
        
        This button allows users to manually create deduction journal lines
        if they weren't created automatically during posting.
        """
        self.ensure_one()
        if self.move_type != "out_invoice":
            raise ValidationError(_("This action is only available for customer invoices."))
        if self.state != "posted":
            raise ValidationError(_("Invoice must be posted before generating deduction lines."))
        
        # Check if deduction amounts are set
        amounts = self._get_deduction_amounts()
        if not amounts:
            raise ValidationError(_("No deduction amounts set. Please set performance bond or retention before generating journal lines."))
        
        # Validate accounts are configured
        self._validate_deduction_accounts()
        
        # Check if deduction journal entry already exists
        if self.deduction_journal_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Deduction Journal Already Exists'),
                    'message': _('Deduction journal entry already exists for this invoice: %s') % self.deduction_journal_id.name,
                    'type': 'warning',
                    'sticky': False,
                }
            }
        
        # Create the deduction lines (this method only creates, never deletes)
        # It has built-in duplicate detection to prevent creating lines twice
        try:
            self._create_deduction_move_lines()
            # Recompute has_deduction_lines to hide the button
            self._compute_has_deduction_lines()
            
            # Refresh the form to show the created journal entry
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
        except Exception as e:
            _logger.error(
                "Error generating deduction lines for invoice %s: %s",
                self.name or self.id,
                str(e),
                exc_info=True
            )
            raise ValidationError(
                _("Error generating deduction lines: %s") % str(e)
            )
    
    def action_view_deduction_lines(self):
        """Action to view deduction journal entry."""
        self.ensure_one()
        if not self.deduction_journal_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Deduction Journal'),
                    'message': _('No deduction journal entry found for this invoice.'),
                    'type': 'warning',
                    'sticky': False,
                }
            }
        
        return {
            'name': _('Deduction Journal Entry'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': self.deduction_journal_id.id,
            'view_mode': 'form',
            'context': {
                'create': False,
                'edit': False,
            },
        }

    def _post(self, soft=True):
        # Validate accounts before posting (only if deduction amounts are set)
        # Don't block posting if accounts are missing - user can add lines manually later
        for move in self:
            if move.move_type == "out_invoice":
                amounts = move._get_deduction_amounts()
                if amounts and any(amounts.values()):
                    # Only validate if there are deduction amounts set
                    try:
                        move._validate_deduction_accounts()
                    except ValidationError:
                        # Log warning but don't block posting
                        _logger.warning(
                            "Invoice %s has deduction amounts but accounts are not configured. "
                            "User can add deduction lines manually after posting.",
                            move.name or move.id
                        )
        res = super()._post(soft=soft)
        # Don't automatically create deduction lines - user will click button to create them
        # This allows invoice to be validated first, then deduction lines added manually
        return res
