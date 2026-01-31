# -*- coding: utf-8 -*-
"""
Debug: intercept account.move.create when journal_id is missing.
Compatible with Odoo 19.
Enable via: Settings > Technical > Parameters > System Parameters
  Key: stock_account_journal_fix.debug  Value: True
"""
import logging
import traceback

from odoo import api, models

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model_create_multi
    def create(self, vals_list):
        debug = self.env['ir.config_parameter'].sudo().get_param('stock_account_journal_fix.debug', 'False').lower() == 'true'
        for vals in vals_list:
            if not vals.get('journal_id') and debug:
                _logger.error(
                    "account.move.create called WITHOUT journal_id. vals keys=%s",
                    list(vals.keys()),
                )
                _logger.error("vals (no line_ids detail)=%s", {k: v for k, v in vals.items() if k != 'line_ids'})
                _logger.error("STACK:\n%s", ''.join(traceback.format_stack()))
                # Set stock_account_journal_fix.debug_raise = False to only log, not raise
                if self.env['ir.config_parameter'].sudo().get_param('stock_account_journal_fix.debug_raise', 'True').lower() == 'true':
                    raise ValueError(
                        "account.move.create without journal_id (debug mode). "
                        "Check logs for vals and stack. Set company Stock Journal or product category Stock Journal."
                    )
        return super().create(vals_list)
