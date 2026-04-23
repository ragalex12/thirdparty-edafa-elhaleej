from odoo import fields, models


class BaseDocumentLayout(models.TransientModel):
    _inherit = 'base.document.layout'

    use_custom_header = fields.Boolean(related='company_id.use_custom_header', readonly=False)
    use_custom_footer = fields.Boolean(related='company_id.use_custom_footer', readonly=False)
    report_header_image = fields.Binary(related='company_id.report_header_image', readonly=False)
    report_footer_image = fields.Binary(related='company_id.report_footer_image', readonly=False)
