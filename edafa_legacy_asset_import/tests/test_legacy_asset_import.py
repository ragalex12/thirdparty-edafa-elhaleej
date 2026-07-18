from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestLegacyAssetImport(TransactionCase):
    def test_migration_fields_are_stored_and_writable(self):
        model_fields = self.env["account.asset.asset"]._fields
        for field_name in (
            "legacy_import_key",
            "legacy_cutover_date",
            "legacy_accumulated_depreciation",
            "legacy_force_salvage_value_one",
        ):
            field = model_fields[field_name]
            self.assertTrue(field.store)
            self.assertFalse(field.compute)

    def test_fields_are_available_to_generic_import(self):
        field_tree = self.env["base_import.import"].get_fields_tree(
            "account.asset.asset",
            depth=1,
        )
        importable_names = {field["id"] for field in field_tree}
        self.assertTrue(
            {
                "name",
                "date",
                "value",
                "category_id",
                "company_id",
                "method_number",
                "account_analytic_id",
                "legacy_cutover_date",
                "legacy_accumulated_depreciation",
                "legacy_force_salvage_value_one",
            }.issubset(importable_names)
        )

    def test_legacy_carrying_value_matches_source_behavior(self):
        asset = self.env["account.asset.asset"].new(
            {
                "value": 2600.0,
                "legacy_accumulated_depreciation": 652.07,
                "salvage_value": 1.0,
            }
        )
        asset._compute_legacy_carrying_value()
        self.assertAlmostEqual(asset.legacy_carrying_value, 1946.93, places=2)
