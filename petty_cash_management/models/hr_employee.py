# -*- coding: utf-8 -*-
#############################################################################
#                                                                           #
#    iTech Co.                                                              #
#                                                                           #
#    Copyright (C) 2020-iTech Technologies(<https://www.iTech.com.eg>).     #
#                                                                           #
#############################################################################

from odoo import models, fields, api, _

class HrAdvanceV(models.Model):
    _inherit = 'hr.employee'

    petty_count = fields.Integer(compute='_petty_count', string='# Advance')

    # count of all advance contracts (optimized with read_group)
    def _petty_count(self):
        petty_data = self.env['hr.petty'].read_group(
            [('employee', 'in', self.ids)],
            ['employee'],
            ['employee']
        )
        mapped_data = {data['employee'][0]: data['employee_count'] for data in petty_data}
        for employee in self:
            employee.petty_count = mapped_data.get(employee.id, 0)

    # smart button action for returning the view of all HR advance related to the current employee
    def petty_view(self):
        self.ensure_one()
        return {
            'name': _('Petty Cash'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.petty',
            'view_mode': 'list,form',
            'domain': [('employee', '=', self.id)],
            'context': {'default_employee': self.id},
        }
