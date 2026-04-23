# -*- coding: utf-8 -*-

from odoo import models, api, _
from odoo.exceptions import AccessError


class AccountAccount(models.Model):
    _inherit = 'account.account'

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to restrict account creation to COA Creator group only"""
        # Skip check if in module installation mode or running as superuser
        if not self.env.context.get('install_mode') and not self.env.su:
            # Check if user is in COA Creator group
            if not self.env.user.has_group('itech_account_coa_creator.group_account_coa_creator'):
                raise AccessError(_('Only users in the "COA Creator" group can create accounts in the Chart of Accounts. Please contact your administrator to be added to this group.'))
        
        return super(AccountAccount, self).create(vals_list)

    def write(self, vals):
        """Override write to restrict account modification to COA Creator group only"""
        # Skip check if in module installation mode or running as superuser
        if not self.env.context.get('install_mode') and not self.env.su:
            # Check if user is in COA Creator group
            if not self.env.user.has_group('itech_account_coa_creator.group_account_coa_creator'):
                raise AccessError(_('Only users in the "COA Creator" group can modify accounts in the Chart of Accounts. Please contact your administrator to be added to this group.'))
        
        return super(AccountAccount, self).write(vals)

    def unlink(self):
        """Override unlink to restrict account deletion to COA Creator group only"""
        # Skip check if in module installation mode or running as superuser
        if not self.env.context.get('install_mode') and not self.env.su:
            # Check if user is in COA Creator group
            if not self.env.user.has_group('itech_account_coa_creator.group_account_coa_creator'):
                raise AccessError(_('Only users in the "COA Creator" group can delete accounts from the Chart of Accounts. Please contact your administrator to be added to this group.'))
        
        return super(AccountAccount, self).unlink()

