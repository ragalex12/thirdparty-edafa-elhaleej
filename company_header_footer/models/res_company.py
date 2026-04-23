from odoo import models, fields, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    report_header_image = fields.Binary(
        string='Report Header Image',
        help='Custom header image (JPG) for reports. This will be used instead of the default Odoo header.',
        attachment=True,
    )
    report_footer_image = fields.Binary(
        string='Report Footer Image',
        help='Custom footer image (JPG) for reports. This will be used instead of the default Odoo footer.',
        attachment=True,
    )
    report_header_image_filename = fields.Char(
        string='Header Image Filename',
        compute='_compute_header_image_filename',
    )
    report_footer_image_filename = fields.Char(
        string='Footer Image Filename',
        compute='_compute_footer_image_filename',
    )
    use_custom_header = fields.Boolean(
        string='Use Custom Header',
        default=False,
        help='Enable to use custom header image instead of default Odoo header'
    )
    use_custom_footer = fields.Boolean(
        string='Use Custom Footer',
        default=False,
        help='Enable to use custom footer image instead of default Odoo footer'
    )

    def _compute_header_image_filename(self):
        for record in self:
            record.report_header_image_filename = f'header_{record.id}.jpg' if record.id else 'header.jpg'

    def _compute_footer_image_filename(self):
        for record in self:
            record.report_footer_image_filename = f'footer_{record.id}.jpg' if record.id else 'footer.jpg'

