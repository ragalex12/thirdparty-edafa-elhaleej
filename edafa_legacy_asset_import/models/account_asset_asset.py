from odoo import api, fields, models


class AccountAssetAsset(models.Model):
    _inherit = "account.asset.asset"

    legacy_import_key = fields.Char(
        string="Legacy Import Key",
        copy=False,
        index=True,
        help="Stable source key used to make the historical asset migration idempotent.",
    )
    legacy_cutover_date = fields.Date(
        string="Legacy Cutover Date",
        index=True,
        help="As-of date supplied by the legacy export; this is not the acquisition date.",
    )
    legacy_accumulated_depreciation = fields.Monetary(
        string="Legacy Accumulated Depreciation",
        currency_field="currency_id",
        help="Accumulated depreciation exported by the legacy asset system.",
    )
    legacy_force_salvage_value_one = fields.Boolean(
        string="Force Salvage Value = 1",
        help="Legacy migration flag that preserves a nominal non-depreciable value of one.",
    )
    legacy_carrying_value = fields.Monetary(
        string="Legacy Carrying Value",
        currency_field="currency_id",
        compute="_compute_legacy_carrying_value",
        store=True,
        help="Gross value less legacy accumulated depreciation and the nominal salvage value.",
    )

    _legacy_import_key_unique = models.Constraint(
        "unique(legacy_import_key)",
        "Legacy import key must be unique.",
    )

    @api.depends(
        "value",
        "legacy_accumulated_depreciation",
        "salvage_value",
    )
    def _compute_legacy_carrying_value(self):
        for asset in self:
            asset.legacy_carrying_value = (
                asset.value
                - asset.legacy_accumulated_depreciation
                - asset.salvage_value
            )
