# -*- coding: utf-8 -*-
"""
iTech Construction Project Models
=================================
This module extends Odoo's project management with construction-specific features.
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    aec = fields.Char(string='Partner Code')

    # Fields for the partner when it acts as an agent
    agent = fields.Boolean(
        string="Creditor/Agent",
        help="Check this field if the partner is a creditor or an agent.",
    )
    agent_type = fields.Selection(
        selection=[("agent", "External agent"),("intagent", "Internal agent")],
        string="Type",
        default="agent",
    )

    settlement = fields.Selection(selection=[("monthly", "Monthly"),("quaterly", "Quarterly"),("semi", "Semi-annual"),("annual", "Annual"),],string="Settlement period",default="monthly",)
    is_customer = fields.Boolean(
        'Is Customer', help="""Check this field if the partner is a customer.""")
    is_vendor = fields.Boolean(
        'Is Vendor', help="""Check this field if the partner is a vendor.""")

class ProjectProject(models.Model):
    """Extended Project Model with Construction Features"""
    _inherit = 'project.project'

    # ========== Basic Fields ==========
    project_code = fields.Char(string='Project Code', readonly=True, store=True)
    project_location = fields.Char(string='Project Location')
    state = fields.Selection(
        [('draft', 'New'), ('assigned', 'Assigned'), ('approve', 'Approved'),
         ('inprogress', 'In Progress'), ('cancel', 'Cancelled'), ('finished', 'Finished')],
        tracking=True, default='draft'
    )
    
    # ========== Project Classification ==========
    type_id = fields.Many2one(
        comodel_name="project.type",
        string="Type",
        copy=False,
        domain="[('project_ok', '=', True)]",
    )
    project_purpose = fields.Many2many("project.purpose", string="Project Purpose")
    ownership = fields.Selection(
        [('mycompany', 'My Company'), ('sharingother', 'Sharing Other'), 
         ('bankfinansing', 'Bank Financing'), ('generalcontractor', 'General Contractor')],
        default='mycompany'
    )
    tag_ids = fields.Many2many("project.tags", string="Tags")
    privacy_visibility = fields.Selection(default="followers")
    
    # ========== Team & Members ==========
    members_ids = fields.Many2many(
        'hr.employee', 'project_employee_rel', 'project_id', 'employee_id',
        string='Project Members',
        help="Project's members are users who can have an access to the tasks related to this project."
    )
    p_assistant = fields.Many2one(
        'hr.employee',
        string="Project Assistant",
        default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1).id
    )
    
    # ========== Financial Fields ==========
    project_valuebvat = fields.Float(string='Total Amount before VAT')
    project_valueavat = fields.Float(string='Total Amount after VAT', compute="compute_pvat")
    
    # ========== Related Records ==========
    p_invoice_ids = fields.One2many('account.move', 'project_id', string='Invoices')
    p_so_ids = fields.One2many('sale.order', 'project_r_id', string='Sales Orders')
    p_po_ids = fields.One2many('purchase.order', 'project_id', string='Purchase Orders')
    
    # ========== Documents & Attachments ==========
    project_quote = fields.Binary(string='Quote', store=True, attachment=True)
    project_proposal = fields.Binary(string='Proposal', store=True, attachment=True)
    project_approval_mail = fields.Binary(string='Approval mail', store=True, attachment=True)
    project_contract = fields.Binary(string='Contract', required=True, store=True, attachment=True)
    project_contract_attachments = fields.Many2many(
        comodel_name="ir.attachment",
        relation="project_project_contract_attachment_rel",
        column1="project_project_id",
        column2="attachment_id",
        string="Contract Attachments"
    )
    attachment_dwg_other = fields.Many2many(
        comodel_name="ir.attachment",
        relation="project_project_ir_attachment_relation",
        column1="project_project_id",
        column2="attachment_id",
        string="Other DWGs"
    )
    image_medium = fields.Binary(related='partner_id.image_1920', store=True, attachment=True)
    
    # ========== DWG Attachments by Category ==========
    attachment_dwg_structural = fields.Many2many(
        comodel_name="ir.attachment",
        relation="project_project_dwg_structural_rel",
        column1="project_project_id",
        column2="attachment_id",
        string="انشائي (Structural)"
    )
    attachment_dwg_architectural = fields.Many2many(
        comodel_name="ir.attachment",
        relation="project_project_dwg_architectural_rel",
        column1="project_project_id",
        column2="attachment_id",
        string="معماري (Architectural)"
    )
    attachment_dwg_electrical = fields.Many2many(
        comodel_name="ir.attachment",
        relation="project_project_dwg_electrical_rel",
        column1="project_project_id",
        column2="attachment_id",
        string="كهرباء (Electrical)"
    )
    attachment_dwg_low_current = fields.Many2many(
        comodel_name="ir.attachment",
        relation="project_project_dwg_low_current_rel",
        column1="project_project_id",
        column2="attachment_id",
        string="تيار خفيف (Low Current)"
    )
    attachment_dwg_mechanical = fields.Many2many(
        comodel_name="ir.attachment",
        relation="project_project_dwg_mechanical_rel",
        column1="project_project_id",
        column2="attachment_id",
        string="ميكانيكا (Mechanical)"
    )
    attachment_dwg_hvac = fields.Many2many(
        comodel_name="ir.attachment",
        relation="project_project_dwg_hvac_rel",
        column1="project_project_id",
        column2="attachment_id",
        string="تكييف (HVAC)"
    )
    attachment_dwg_fire = fields.Many2many(
        comodel_name="ir.attachment",
        relation="project_project_dwg_fire_rel",
        column1="project_project_id",
        column2="attachment_id",
        string="حريق (Fire Fighting)"
    )
    attachment_dwg_general_site = fields.Many2many(
        comodel_name="ir.attachment",
        relation="project_project_dwg_general_site_rel",
        column1="project_project_id",
        column2="attachment_id",
        string="موقع عام (General Site)"
    )
    
    # ========== DWG Name Fields by Category ==========
    dwg_name_structural = fields.Char('انشائي (Structural) DWG Name')
    dwg_name_architectural = fields.Char('معماري (Architectural) DWG Name')
    dwg_name_electrical = fields.Char('كهرباء (Electrical) DWG Name')
    dwg_name_low_current = fields.Char('تيار خفيف (Low Current) DWG Name')
    dwg_name_mechanical = fields.Char('ميكانيكا (Mechanical) DWG Name')
    dwg_name_hvac = fields.Char('تكييف (HVAC) DWG Name')
    dwg_name_fire = fields.Char('حريق (Fire Fighting) DWG Name')
    dwg_name_general_site = fields.Char('موقع عام (General Site) DWG Name')
    dwg_name_other = fields.Char('Other DWGs Name')
    
    # ========== Count Fields ==========
    purchase_count = fields.Integer(compute='_purchase_count', string='# Purchase')
    sales_count = fields.Integer(compute='_sales_count', string='# Sales')
    invoices_count = fields.Integer(compute='_invoice_count', string='Invoices')
    vendor_bills_count = fields.Integer(compute='_vendor_bills_count', string='Vendor Bills')
    timesheets_count = fields.Integer(compute='_timesheets_count', string='# Timesheets')
    
    # ========== Computed Methods ==========
    @api.depends('project_valuebvat', 'company_id')
    def compute_pvat(self):
        """Compute total amount after VAT based on company country"""
        for rec in self:
            if rec.company_id and rec.company_id.country_code == 'SA':
                rec.project_valueavat = rec.project_valuebvat * 1.15
            else:
                rec.project_valueavat = rec.project_valuebvat * 1.14

    @api.depends()
    def _purchase_count(self):
        """Count purchase orders linked to this project"""
        for each in self:
            purchase_ids = self.env['purchase.order'].search([('project_id', '=', each.id)])
            each.purchase_count = len(purchase_ids)

    @api.depends()
    def _sales_count(self):
        """Count sales orders linked to this project"""
        for each in self:
            sales_ids = self.env['sale.order'].search([('project_r_id', '=', each.id)])
            each.sales_count = len(sales_ids)

    @api.depends()
    def _invoice_count(self):
        """Count customer invoices linked to this project"""
        for each in self:
            invoice_ids = self.env['account.move'].search([
                ('project_id', '=', each.id),
                ('move_type', 'in', ['out_invoice', 'out_refund'])
            ])
            each.invoices_count = len(invoice_ids)

    @api.depends()
    def _vendor_bills_count(self):
        """Count vendor bills linked to this project"""
        for each in self:
            vendor_bill_ids = self.env['account.move'].search([
                ('project_id', '=', each.id),
                ('move_type', 'in', ['in_invoice', 'in_refund'])
            ])
            each.vendor_bills_count = len(vendor_bill_ids)

    @api.depends()
    def _timesheets_count(self):
        """Count timesheets linked to this project"""
        for each in self:
            timesheets_ids = self.env['account.analytic.line'].search([('project_id', '=', each.id)])
            each.timesheets_count = len(timesheets_ids)

    # ========== CRUD Methods ==========
    def add_custom_followers(self, partner_ids):
        """Add followers to project, avoiding duplicates"""
        for record in self:
            # Check if partners are already followers to avoid duplicates
            existing_followers = record.message_follower_ids.mapped('partner_id').ids
            new_partners = [p for p in partner_ids if p not in existing_followers]
            
            if new_partners:
                record.message_subscribe(partner_ids=new_partners)
    
    @api.model_create_multi
    def create(self, vals_list):
        """Create project with auto-generated project code"""
        for vals in vals_list:
            if not vals.get('project_code'):
                sequence = self.env['ir.sequence'].next_by_code('project.req') or '/'
                vals['project_code'] = sequence or '/'
        
        result = super(ProjectProject, self).create(vals_list)
        
        # Add followers after creation
        for record in result:
            # Collect all followers
            partner_ids = []
            
            # Add project assistant as follower
            if record.p_assistant and record.p_assistant.user_id and record.p_assistant.user_id.partner_id:
                partner_ids.append(record.p_assistant.user_id.partner_id.id)
            
            # Add all team members as followers
            if record.members_ids:
                for member in record.members_ids:
                    if member.user_id and member.user_id.partner_id:
                        partner_id = member.user_id.partner_id.id
                        if partner_id not in partner_ids:
                            partner_ids.append(partner_id)
            
            # Subscribe all followers at once using custom method
            if partner_ids:
                record.add_custom_followers(partner_ids)
        return result
        
    def write(self, vals):
        """Update project and manage followers"""
        # Call super() to execute the default behavior of the write method
        result = super(ProjectProject, self).write(vals)
        
        # Perform any additional actions after calling super().write()
        # Always add project assistant and team members as followers when saving
        for project in self:
            # Collect all followers
            partner_ids = []
            
            # Add project assistant as follower (always check, not just when changed)
            if project.p_assistant and project.p_assistant.user_id and project.p_assistant.user_id.partner_id:
                partner_ids.append(project.p_assistant.user_id.partner_id.id)
            
            # Add project members as followers (always check, not just when changed)
            if project.members_ids:
                for member in project.members_ids:
                    if member.user_id and member.user_id.partner_id:
                        partner_id = member.user_id.partner_id.id
                        if partner_id not in partner_ids:
                            partner_ids.append(partner_id)
            
            # Subscribe all followers at once using custom method
            if partner_ids:
                project.add_custom_followers(partner_ids)
        
        return result

    def unlink(self):
        """Only allow deletion of projects in draft state"""
        for project in self:
            if project.state != 'draft':
                raise UserError(_('You can delete project in draft state only.'))
        return super(ProjectProject, self).unlink()

    # ========== State Management Methods ==========

    def action_assign(self, context=None):
        """Change project state to assigned"""
        return self.write({'state': 'assigned'})

    def action_validate(self, context=None):
        """Approve project - only project manager can approve"""
        if not (self.env.uid in [self.user_id.id, 2]):
            raise ValidationError(_('You are not allowed to approve this project'))
        return self.write({'state': 'approve'})

    def action_inprogress(self, context=None):
        """Change project state to in progress"""
        return self.write({'state': 'inprogress'})

    def action_done(self, context=None):
        """Mark project as finished"""
        return self.write({'state': 'finished'})

    def action_cancel(self, context=None):
        """Cancel project"""
        return self.write({'state': 'cancel'})

    # ========== View Actions ==========

    def invoice_view(self):
        """Open customer invoices view for this project"""
        self.ensure_one()
        return {
            'name': _('Invoices'),
            'domain': [('project_id', '=', self.id)],
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('account.view_out_invoice_tree').id,
            'views': [
                (self.env.ref('account.view_out_invoice_tree').id, 'list'),
                (self.env.ref('account.view_move_form').id, 'form'),
            ],
            'view_mode': 'list,form',
            'help': _('''<p class="oe_view_nocontent_create">
                                   Click to Create for New Invoices
                                </p>'''),
            'context': {
                'default_project_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_move_type': 'out_invoice',
                'move_type': 'out_invoice',
                'journal_type': 'sale'
            }
        }

    def vendor_bills_view(self):
        """Open vendor bills view for this project"""
        self.ensure_one()
        return {
            'name': _('Vendor Bills'),
            'domain': [
                ('project_id', '=', self.id),
                ('move_type', 'in', ['in_invoice', 'in_refund'])
            ],
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('account.view_in_invoice_tree').id,
            'views': [
                (self.env.ref('account.view_in_invoice_tree').id, 'list'),
                (self.env.ref('account.view_move_form').id, 'form'),
            ],
            'view_mode': 'list,form',
            'help': _('''<p class="oe_view_nocontent_create">
                                   Click to Create for New Vendor Bills
                                </p>'''),
            'context': {
                'default_project_id': self.id,
                'default_move_type': 'in_invoice',
                'move_type': 'in_invoice',
                'journal_type': 'purchase'
            }
        }

    def timesheets_view(self):
        """Open timesheets view for this project"""
        self.ensure_one()
        return {
            'name': _('Timesheets'),
            'domain': [('project_id', '=', self.id)],
            'res_model': 'account.analytic.line',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('hr_timesheet.timesheet_view_tree_user').id,
            'views': [(self.env.ref('hr_timesheet.timesheet_view_tree_user').id, 'list')],
            'help': _('''<p class="oe_view_nocontent_create">
                                   Click to Create for New Supervisor timesheets
                                </p>'''),
            'context': {
                'default_project_id': self.id,
                'default_partner_id': self.partner_id.id
            }
        }

    def sales_view(self):
        """Open sales orders view for this project"""
        self.ensure_one()
        return {
            'name': _('Sales'),
            'domain': [('project_r_id', '=', self.id)],
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('sale.view_order_tree').id,
            'views': [
                (self.env.ref('sale.view_order_tree').id, 'list'),
                (self.env.ref('sale.view_order_form').id, 'form'),
            ],
            'view_mode': 'list,form',
            'help': _('''<p class="oe_view_nocontent_create">
                                   Click to Create for New Sale
                                </p>'''),
            'context': {
                'default_project_r_id': self.id,
                'default_partner_id': self.partner_id.id
            }
        }

    def purchase_view(self):
        """Open purchase orders view for this project"""
        self.ensure_one()
        return {
            'name': _('Purchase'),
            'domain': [('project_id', '=', self.id)],
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('purchase.purchase_order_view_tree').id,
            'views': [
                (self.env.ref('purchase.purchase_order_view_tree').id, 'list'),
                (self.env.ref('purchase.purchase_order_form').id, 'form'),
            ],
            'view_mode': 'list,form',
            'help': _('''<p class="oe_view_nocontent_create">
                                   Click to Create for New purchase
                                </p>'''),
            'context': {'default_project_id': self.id}
        }

    def customers_view(self):
        """Open customers view for this project"""
        self.ensure_one()
        return {
            'name': _('Customers'),
            'domain': [('is_customer', '=', True)],
            'res_model': 'res.partner',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form,kanban',
            'help': _('''<p class="oe_view_nocontent_create">
                                   Click to Create for New Customer
                                </p>'''),
            'context': {
                'default_is_customer': True,
                'default_customer_rank': 1,
            }
        }
    
    def snag_list_view(self):
        """Open snag list view for this project"""
        self.ensure_one()
        return {
            'name': _('Construction Snag List / Change Orders'),
            'domain': [('project_id', '=', self.id)],
            'res_model': 'construction.snag.list',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'context': {
                'default_project_id': self.id,
            }
        }
    

# ========== Project Type Model ==========
class ProjectType(models.Model):
    """Project Type with hierarchical structure"""
    _name = "project.type"
    _description = "Project Type"
    _rec_name = "complete_name"

    parent_id = fields.Many2one(comodel_name="project.type", string="Parent Type")
    child_ids = fields.One2many(
        comodel_name="project.type", inverse_name="parent_id", string="Subtypes"
    )
    name = fields.Char(string="Name", required=True, translate=True)
    complete_name = fields.Char(
        string="Complete Name", compute="_compute_complete_name", store=True
    )
    description = fields.Text(translate=True)
    project_ok = fields.Boolean(string="Can be applied for projects", default=True)
    task_ok = fields.Boolean(string="Can be applied for tasks")

    @api.constrains("parent_id")
    def check_parent_id(self):
        if not self._check_recursion():
            raise ValidationError(_("You cannot create recursive project types."))

    @api.depends("name", "parent_id.complete_name")
    def _compute_complete_name(self):
        for project_type in self:
            if project_type.parent_id:
                project_type.complete_name = "{} / {}".format(
                    project_type.parent_id.complete_name, project_type.name
                )
            else:
                project_type.complete_name = project_type.name

# ========== Project Purpose Model ==========
class ProjectPurpose(models.Model):
    """Project Purpose Classification"""
    _name = "project.purpose"
    _description = "Project Purpose"

    name = fields.Char(string='Name', required=True, translate=True)

# ========== Sale Order Extension ==========
class SaleOrder(models.Model):
    """Extended Sale Order with Project Link"""
    _inherit = "sale.order"

    project_r_id = fields.Many2one('project.project', string='Project')

# ========== Purchase Order Extension ==========
class PurchaseOrder(models.Model):
    """Extended Purchase Order with Project Link"""
    _inherit = "purchase.order"

    project_id = fields.Many2one('project.project', string='Project')

    def _prepare_invoice(self):
        """Add project to invoice when creating from purchase order"""
        invoice_vals = super(PurchaseOrder, self)._prepare_invoice()
        if self.project_id:
            invoice_vals.update({'project_id': self.project_id.id})
        return invoice_vals

    @api.depends("project_id")
    def add_project_analytic_id(self):
        """Add project analytic account to purchase order lines"""
        for po in self:
            if po.project_id and po.project_id.analytic_account_id:
                for line in po.order_line:
                    line.account_analytic_id = po.project_id.analytic_account_id

# ========== Account Move (Invoice) Extension ==========
class AccountMove(models.Model):
    """Extended Account Move with Project Link"""
    _inherit = "account.move"

    project_id = fields.Many2one('project.project', string='Project')
    approved_pg = fields.Boolean(string='Approved By PM')

    def action_post(self):
        """Post invoice and handle project-related logic"""
        result = super(AccountMove, self).action_post()
        return result

