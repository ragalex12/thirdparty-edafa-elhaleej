# Edafa Legacy Asset Import

Adds auditable migration fields to `account.asset.asset` and provides an
idempotent staging importer for the historical Nadi Kitchens asset workbook.

## Source interpretation

- `Asset Name` → asset name
- purchase date embedded in `Asset Name` → asset acquisition `date`
- workbook `Date` (`2026-01-01`) → `legacy_cutover_date`
- `Gross Value` → `value`
- workbook `Salvage Value` → `legacy_accumulated_depreciation`
- `Force Salvage Value = 1` → `legacy_force_salvage_value_one`
- nominal current `salvage_value` → `1`
- `Category` → `category_id`
- `Number of Depreciations` → `method_number`
- `Analytic Account` → `account_analytic_id`

The importer leaves every asset in Draft and does not generate depreciation
lines or accounting entries.

## Staging result

Database: `trgulf_Mrp`

- 769 assets
- 5 asset models
- 20 analytic accounts
- gross value: `7,642,335.44`
- legacy accumulated depreciation: `5,903,764.76`
- legacy carrying value: `1,737,801.68`
- acquisition dates: `2016-01-11` through `2025-12-17`
- cutover date: `2026-01-01`
- state: 769 Draft
- generated depreciation lines: 0
- generated journal entries: 0

Backup before import:
`/tmp/trgulf_Mrp_pre_asset_import_20260718.dump`

## Run

Dry run:

```bash
ASSET_IMPORT_XLSX=/tmp/asset-import.xlsx \
ASSET_IMPORT_COMPANY_ID=1 \
ASSET_IMPORT_COMMIT=0 \
sudo -E -u odoo odoo shell -c /etc/odoo/odoo.conf -d trgulf_Mrp \
  < scripts/import_legacy_assets.py
```

Commit:

```bash
ASSET_IMPORT_XLSX=/tmp/asset-import.xlsx \
ASSET_IMPORT_COMPANY_ID=1 \
ASSET_IMPORT_COMMIT=1 \
sudo -E -u odoo odoo shell -c /etc/odoo/odoo.conf -d trgulf_Mrp \
  < scripts/import_legacy_assets.py
```
