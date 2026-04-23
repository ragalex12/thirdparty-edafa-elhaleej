# -*- coding: utf-8 -*-
"""
Construction Snag List / Change Orders Model
===========================================
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ConstructionSnagList(models.Model):
    """Construction Snag List / Change Orders"""
    _name = 'construction.snag.list'
    _description = 'Construction Snag List / Change Orders'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        tracking=True
    )
    project_id = fields.Many2one(
        'project.project',
        string='Project',
        required=True,
        tracking=True,
        ondelete='cascade'
    )
    date = fields.Date(
        string='Date',
        required=True,
        default=fields.Date.context_today,
        tracking=True
    )
    description = fields.Text(
        string='Description',
        required=True,
        tracking=True
    )
    category = fields.Selection(
        [
            ('structural', 'Structural'),
            ('architectural', 'Architectural'),
            ('electrical', 'Electrical'),
            ('mechanical', 'Mechanical'),
            ('hvac', 'HVAC'),
            ('fire', 'Fire Fighting'),
            ('other', 'Other'),
        ],
        string='Category',
        required=True,
        tracking=True
    )
    priority = fields.Selection(
        [
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('urgent', 'Urgent'),
        ],
        string='Priority',
        default='medium',
        tracking=True
    )
    status = fields.Selection(
        [
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('completed', 'Completed'),
        ],
        string='Status',
        default='draft',
        tracking=True,
        required=True
    )
    assigned_to = fields.Many2one(
        'res.users',
        string='Assigned To',
        tracking=True
    )
    estimated_cost = fields.Float(
        string='Estimated Cost',
        digits='Account',
        tracking=True
    )
    actual_cost = fields.Float(
        string='Actual Cost',
        digits='Account',
        tracking=True
    )
    notes = fields.Text(
        string='Notes'
    )
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'construction_snag_attachment_rel',
        'snag_id',
        'attachment_id',
        string='Attachments'
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Generate sequence number for snag list"""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                sequence = self.env['ir.sequence'].next_by_code('construction.snag.list') or '/'
                vals['name'] = sequence or '/'
        return super(ConstructionSnagList, self).create(vals_list)

    def action_submit(self):
        """Submit snag list for approval"""
        self.write({'status': 'submitted'})

    def action_approve(self):
        """Approve snag list"""
        self.write({'status': 'approved'})

    def action_reject(self):
        """Reject snag list"""
        self.write({'status': 'rejected'})

    def action_complete(self):
        """Mark snag list as completed"""
        self.write({'status': 'completed'})

    def action_reset_to_draft(self):
        """Reset snag list to draft"""
        self.write({'status': 'draft'})

    def action_view_project(self):
        """Open the related project"""
        self.ensure_one()
        if not self.project_id:
            return False
        return {
            'name': _('Project'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.project',
            'res_id': self.project_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
