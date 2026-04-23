# -*- coding: utf-8 -*-
#############################################################################
#                                                                           #
#    iTech Co.                                                              #
#                                                                           #
#    Copyright (C) 2020-iTech Technologies(<https://www.iTech.com.eg>).     #
#                                                                           #
#############################################################################
from datetime import datetime, timedelta, date
from odoo import models, fields, _, api
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta


class HrEmployeeFamilyInfo(models.Model):
    _name = 'hr.employee.family'
    _description = 'HR Employee Family'

    employee_id = fields.Many2one(
        'hr.employee',
        string="Employee",
        help='Select corresponding Employee',
    )
    relation_id = fields.Many2one('hr.employee.relation', string="Relation")
    member_name = fields.Char(string='Name')
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ], string="Gender")
    member_contact = fields.Char(string='Contact No')
    birth_date = fields.Date(string="DOB")
    blood_type = fields.Selection([
        ('o_p', 'O Positive'),
        ('o_n', 'O Negative'),
        ('a_p', 'A Positive'),
        ('a_n', 'A Negative'),
        ('b_p', 'B Positive'),
        ('b_n', 'B Negative'),
        ('ab_p', 'AB Positive'),
        ('ab_n', 'AB Negative'),
    ], string="Blood Type")
    medical = fields.Char(string='Medical Company')
    medical_percent = fields.Float(string='Medical Percentage')
    religion = fields.Selection([
        ('m1', 'Muslim'),
        ('c2', 'Christian'),
        ('o3', 'Other'),
    ], string='Religion')


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    #_sql_constraints = [('no_employee_uniq', 'unique(no_employee)', 'The Employee Code must be unique!'), ]
    emp_no = fields.Char(string='Employee No.')
    no_employee = fields.Char(string='Employee Code', required=False)
    name_ar = fields.Char(string="Arabic Name", required=False)
    salary_type = fields.Selection([
        ('cash', 'Cash'),
        ('bank', 'Bank'),
    ], string="Receiving Salary By", required=True, default='cash')

    id_attachment_id = fields.Many2many(
        'ir.attachment',
        'id_attachment_rel',
        'id_ref',
        'attach_ref',
        string="ID Attachments"
    )
    id_expiry_date = fields.Date(string='Expiry Date', help='Expiry date of Identification ID')

    passport_attachment_id = fields.Many2many(
        'ir.attachment',
        'passport_attachment_rel',
        'passport_ref',
        'attach_ref1',
        string="Passport Attachments"
    )
    issued = fields.Date(string='ID issued date')
    passport_issued = fields.Date("Passport Issued date")
    joining_date = fields.Date(string='Joining Date', help="Employee joining date related to the contract start date")

    fam_ids = fields.One2many('hr.employee.family', 'employee_id', string='Family')
    ptraining_ids = fields.One2many('hr.ptraining', 'hr_employee_id', string='Employee Training Card')
    miscellaneous_receiving_ids = fields.One2many('hr.miscellaneous.receiving', 'hr_employee_id', string="Miscellaneous Receiving")

    experience_period = fields.Char(string='Experience period', compute='_compute_experience_period')
    age = fields.Char(string='Age', compute='_compute_age')

    whatsapp = fields.Char('WhatsApp')
    signal = fields.Char('Signal')
    facebook = fields.Char('Facebook')
    instagram = fields.Char('Instagram')
    linkedin = fields.Char('LinkedIn Profile')
    twitter = fields.Char('Twitter')
    behance = fields.Char('Behance Profile')

    military = fields.Selection([
        ('no', 'Does not apply'),
        ('exemption', 'Exemption'),
        ('complete', 'Complete the Military service'),
        ('postponed', 'Postponed'),
        ('current', 'Currently serving')
    ], string="Military")
    religion = fields.Selection([
        ('m1', 'Muslim'),
        ('c2', 'Christian'),
        ('o3', 'Other'),
    ], string='Religion')

    # Medical Care
    medical_care = fields.Boolean(string='Medical Care')
    mc_no = fields.Char(string='Medical Card Code', size=20)
    medical_care_handover = fields.Boolean(string='Medical Handed Over')

    # ATM
    atm = fields.Boolean(string='ATM')
    atm_receiving = fields.Date(string='ATM Receiving Date')

    # Business Card
    business_card = fields.Boolean(string='Business Card')
    business_card_receiving = fields.Date(string='Business Card Receiving Date')
    bc_no = fields.Integer(string='Number of Packages')

    # Access Card
    access_card = fields.Boolean(string='Access Card')
    access_card_handover = fields.Boolean(string='Access Card Handed Over')
    sr_access_card = fields.Char(string='Access Card Serial No.', size=25)

    # Premium Card
    premium_card = fields.Boolean(string='Premium Card')
    pc_limit = fields.Float(string='Premium Card Limit')
    pc_closed = fields.Boolean(string='Premium Card Closed')

    # Uniform
    uniform_check = fields.Boolean(string='Uniform')
    uniform_check_handover = fields.Boolean(string='Uniform Handed Over')

    # Mobile
    mobile = fields.Boolean(string='Mobile')
    mobile_model = fields.Char(string='Mobile Model')
    mobile_serial = fields.Char(string='Mobile Serial No')
    mobile_handed = fields.Boolean(string='Mobile Handed Over')
    mobile_receiving_date = fields.Date(string='Mobile Receiving Date')

    # SIM
    sim = fields.Boolean(string='SIM')
    sim_number = fields.Char(string='SIM Number')
    sim_package_limit = fields.Float(string='SIM Package Limit')
    sim_handed = fields.Boolean(string='SIM Handed Over')
    sim_receiving_date = fields.Date(string='SIM Receiving Date')

    # Car
    car = fields.Boolean(string='Car')
    car_model = fields.Char(string='Car Model')
    car_serial = fields.Char(string='Car Serial No')
    car_handed = fields.Boolean(string='Car Handed Over')
    car_receiving_date = fields.Date(string='Car Receiving Date')

    # Laptop
    laptop = fields.Boolean(string='Laptop')
    laptop_model = fields.Char(string='Laptop Model')
    laptop_serial = fields.Char(string='Laptop Serial No')
    laptop_handed = fields.Boolean(string='Laptop Handed Over')
    laptop_receiving_date = fields.Date(string='Laptop Receiving Date')

    # Tablet
    tablet = fields.Boolean(string='Tablet')
    tablet_model = fields.Char(string='Tablet Model')
    tablet_serial = fields.Char(string='Tablet Serial No')
    tablet_handed = fields.Boolean(string='Tablet Handed Over')
    tablet_receiving_date = fields.Date(string='Tablet Receiving Date')

    @api.model_create_multi
    def create(self, vals_list):
        res = super(HrEmployee, self).create(vals_list)
        for data in res:
            seq = self.env['ir.sequence'].next_by_code('hr.employee')
            data.emp_no = seq
        return res

    def action_create_sequence(self):
        if not self.emp_no:
            seq = self.env['ir.sequence'].next_by_code('hr.employee')
            self.emp_no = seq
    
    def action_generate(self):
        for rec in self:
            if not rec.emp_no:
                seq = self.env['ir.sequence'].next_by_code('hr.employee')
                rec.emp_no = seq

    @api.depends('joining_date')
    def _compute_experience_period(self):
        for record in self:
            if record.joining_date:
                delta = relativedelta(fields.Date.today(), record.joining_date)
                record.experience_period = f"{delta.years} Year/s {delta.months} Month/s"
            else:
                record.experience_period = ""

    @api.depends('birthday')
    def _compute_age(self):
        for record in self:
            if record.birthday:
                delta = relativedelta(fields.Date.today(), record.birthday)
                record.age = str(delta.years)
            else:
                record.age = ""


class HrPTraining(models.Model):
    _name = "hr.ptraining"
    _description = "Employee Previous Training"

    ptrain_id = fields.Char(string='SR.', size=32)
    ptraining_program = fields.Char(string='Training Program', required=True)
    ptraining_center = fields.Char(string='Training Center')
    pperiod_from = fields.Date(string='Period From', required=True)
    pperiod_to = fields.Date(string='Period To', required=True)
    ptraining_officer = fields.Char(string='Trainer')
    presults = fields.Selection([
        ('failed', 'Failed'),
        ('passed', 'Passed'),
        ('good', 'Good'),
        ('vgood', 'Very Good'),
        ('excellent', 'Excellent')
    ], string='Results')

    hr_employee_id = fields.Many2one('hr.employee', 'Employee Name', required=True)


class EmployeeRelationInfo(models.Model):
    _name = 'hr.employee.relation'
    _description = 'Employee Relation'

    name = fields.Char(string="Relationship", required=True)

class MiscellaneousReceiving(models.Model):
    _name = "hr.miscellaneous.receiving"
    _description = "Miscellaneous Receiving"

    product_id = fields.Many2one('product.product', string="Item", required=True)
    description = fields.Text(related='product_id.description_purchase', string='Description', readonly=True)
    quantity = fields.Float(string="Quantity", required=True)
    receiving_date = fields.Date(string="Receiving Date")
    handed_over = fields.Boolean(string="Handed Over")
    mho_date = fields.Date(string="Handed Over Date")

    hr_employee_id = fields.Many2one('hr.employee', string="Employee Profile Ref.")

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.description = self.product_id.description_purchase
