# -*- coding: utf-8 -*-
#############################################################################
#                                                                           #
#    iTech Co.                                                              #
#                                                                           #
#    Copyright (C) 2020-iTech Technologies(<https://www.iTech.com.eg>).     #
#                                                                           #
#############################################################################

from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta
from odoo import models, fields, api, exceptions
import math
import logging

_logger = logging.getLogger(__name__)


class HrAdvanceConfig(models.TransientModel):
    _inherit = 'res.config.settings'

    petty_account_id = fields.Many2one('account.account', 'Petty Account Temporary', config_parameter='petty_cash_management.petty_account_id')

    petty_journal_id = fields.Many2one('account.journal', 'Petty Journal Temporary', config_parameter='petty_cash_management.petty_journal_id')
    
    petty_account_branch_id = fields.Many2one('account.account', 'Petty Account Permanent', config_parameter='petty_cash_management.petty_account_branch_id')

    petty_journal_branch_id = fields.Many2one('account.journal', 'Petty Journal Permanent', config_parameter='petty_cash_management.petty_journal_branch_id')

