"""Import the Nadi Kitchens legacy asset workbook into an Odoo staging database.

Run through ``odoo shell`` so the global ``env`` is available:

    ASSET_IMPORT_XLSX=/path/to/assets.xlsx \
    ASSET_IMPORT_COMPANY_ID=1 \
    ASSET_IMPORT_COMMIT=0 \
    odoo shell -d DATABASE < import_legacy_assets.py

The default is a dry run. Set ``ASSET_IMPORT_COMMIT=1`` to commit.
"""

import os
import re
from collections import Counter
from datetime import datetime
from decimal import Decimal

from openpyxl import load_workbook


EXPECTED_HEADERS = [
    "Asset Name",
    "Date",
    "Gross Value",
    "Salvage Value",
    "Category",
    "Company",
    "Number of Depreciations",
    "Force Salvage Value = 1",
    "Analytic Account",
]
EXPECTED_ROW_COUNT = 769
EXPECTED_SOURCE_COMPANY = "شركة نادي المطابخ المحدوده"
PURCHASE_DATE_RE = re.compile(r"شراء\s*:\s*(\d{1,2}/\d{1,2}/\d{4})")

CATEGORY_ACCOUNTS = {
    "أثاث وتجهيزات مكتبية": ("106002", "106007", "400064"),
    "الكترونيات وبرمجيات": ("106003", "106008", "400065"),
    "الات ومعدات وادوات": ("124005", "106007", "421125"),
    "مركبات ووسائل نقل": ("106004", "106009", "400066"),
    "تحسينات وديكور": ("106001", "106007", "400064"),
}


def text(value):
    return str(value or "").strip()


def money(value):
    return float(Decimal(str(value)).quantize(Decimal("0.01")))


def source_purchase_date(asset_name):
    match = PURCHASE_DATE_RE.search(asset_name)
    if not match:
        raise ValueError(f"Missing purchase date in asset name: {asset_name}")
    return datetime.strptime(match.group(1), "%d/%m/%Y").date()


def get_one(model, domain, description):
    record = env[model].search(domain, limit=1)
    if not record:
        raise ValueError(f"Missing {description}: {domain}")
    return record


def account_by_code(company, code):
    return get_one(
        "account.account",
        [("code", "=", code), ("company_ids", "in", company.id)],
        f"account {code} for {company.display_name}",
    )


def load_rows(path):
    workbook = load_workbook(path, data_only=True, read_only=True)
    sheet = workbook[workbook.sheetnames[0]]
    values = list(sheet.iter_rows(values_only=True))
    headers = [text(value) for value in values[0]]
    if headers != EXPECTED_HEADERS:
        raise ValueError(f"Unexpected workbook headers: {headers}")
    rows = [
        dict(zip(headers, row))
        for row in values[1:]
        if any(value is not None for value in row)
    ]
    if len(rows) != EXPECTED_ROW_COUNT:
        raise ValueError(f"Expected {EXPECTED_ROW_COUNT} rows, found {len(rows)}")
    return rows


def validate_rows(rows):
    errors = []
    for row_number, row in enumerate(rows, start=2):
        name = text(row["Asset Name"])
        gross = money(row["Gross Value"])
        accumulated = money(row["Salvage Value"])
        periods = int(row["Number of Depreciations"])
        category = text(row["Category"])
        company = text(row["Company"])
        if not name:
            errors.append(f"row {row_number}: empty Asset Name")
        if company != EXPECTED_SOURCE_COMPANY:
            errors.append(f"row {row_number}: unexpected company {company!r}")
        if category not in CATEGORY_ACCOUNTS:
            errors.append(f"row {row_number}: unknown category {category!r}")
        if gross <= 0:
            errors.append(f"row {row_number}: Gross Value must be positive")
        if accumulated < 0 or accumulated > gross:
            errors.append(f"row {row_number}: invalid accumulated depreciation")
        if periods < 0:
            errors.append(f"row {row_number}: negative Number of Depreciations")
        if row["Force Salvage Value = 1"] is not True:
            errors.append(f"row {row_number}: unsupported force-salvage flag")
        try:
            source_purchase_date(name)
        except ValueError as error:
            errors.append(f"row {row_number}: {error}")
    if errors:
        raise ValueError("\n".join(errors[:50]))


def ensure_analytic_accounts(rows, company):
    plan = get_one("account.analytic.plan", [("id", "=", 1)], "analytic plan 1")
    result = {}
    for name in sorted({text(row["Analytic Account"]) for row in rows}):
        account = env["account.analytic.account"].search(
            [
                ("name", "=", name),
                ("company_id", "=", company.id),
                ("plan_id", "=", plan.id),
            ],
            limit=1,
        )
        if not account:
            account = env["account.analytic.account"].create(
                {
                    "name": name,
                    "company_id": company.id,
                    "plan_id": plan.id,
                }
            )
        result[name] = account
    return result


def ensure_categories(company, journal):
    result = {}
    for name, codes in CATEGORY_ACCOUNTS.items():
        asset_account, depreciation_account, expense_account = (
            account_by_code(company, code) for code in codes
        )
        values = {
            "name": name,
            "company_id": company.id,
            "price": 0.0,
            "currency_id": company.currency_id.id,
            "account_asset_id": asset_account.id,
            "account_depreciation_id": depreciation_account.id,
            "account_depreciation_expense_id": expense_account.id,
            "journal_id": journal.id,
            "method": "linear",
            "method_time": "number",
            "method_number": 1,
            "method_period": 1,
            "prorata": False,
            "open_asset": False,
            "group_entries": False,
            "type": "purchase",
        }
        category = env["account.asset.category"].search(
            [("name", "=", name), ("company_id", "=", company.id)],
            limit=1,
        )
        if category:
            category.write(values)
        else:
            category = env["account.asset.category"].create(values)
        result[name] = category
    return result


def import_assets(rows, company, categories, analytics, journal):
    model = env["account.asset.asset"]
    created = updated = 0
    source_totals = {
        "gross": Decimal("0"),
        "accumulated": Decimal("0"),
        "carrying": Decimal("0"),
    }
    period_counts = Counter()
    for index, row in enumerate(rows, start=1):
        key = f"NADI-ASSET-{index:04d}"
        gross = money(row["Gross Value"])
        accumulated = money(row["Salvage Value"])
        nominal_salvage = 1.0
        periods = int(row["Number of Depreciations"])
        values = {
            "legacy_import_key": key,
            "code": key,
            "name": text(row["Asset Name"]),
            "date": source_purchase_date(text(row["Asset Name"])),
            "legacy_cutover_date": row["Date"].date(),
            "value": gross,
            "legacy_accumulated_depreciation": accumulated,
            "legacy_force_salvage_value_one": True,
            "salvage_value": nominal_salvage,
            "category_id": categories[text(row["Category"])].id,
            "company_id": company.id,
            "currency_id": company.currency_id.id,
            "account_analytic_id": analytics[text(row["Analytic Account"])].id,
            "method": "linear",
            "method_time": "number",
            "method_number": periods,
            "method_period": 1,
            "prorata": False,
            "journal_id": journal.id,
            "account_asset_id": categories[
                text(row["Category"])
            ].account_asset_id.id,
            "account_depreciation_id": categories[
                text(row["Category"])
            ].account_depreciation_id.id,
            "account_depreciation_expense_id": categories[
                text(row["Category"])
            ].account_depreciation_expense_id.id,
            "open_asset": False,
            "group_entries": False,
            "type": "purchase",
            "state": "draft",
        }
        asset = model.search([("legacy_import_key", "=", key)], limit=1)
        if asset:
            if asset.state != "draft":
                raise ValueError(f"Refusing to update non-draft asset {key}")
            asset.write(values)
            updated += 1
        else:
            model.create(values)
            created += 1
        source_totals["gross"] += Decimal(str(gross))
        source_totals["accumulated"] += Decimal(str(accumulated))
        source_totals["carrying"] += Decimal(
            str(round(gross - accumulated - nominal_salvage, 2))
        )
        period_counts[periods] += 1
    return created, updated, source_totals, period_counts


xlsx_path = os.environ.get("ASSET_IMPORT_XLSX", "/tmp/asset-import.xlsx")
company_id = int(os.environ.get("ASSET_IMPORT_COMPANY_ID", "1"))
commit = os.environ.get("ASSET_IMPORT_COMMIT", "0") == "1"

rows = load_rows(xlsx_path)
validate_rows(rows)
company = get_one("res.company", [("id", "=", company_id)], "target company")
journal = get_one(
    "account.journal",
    [("company_id", "=", company.id), ("code", "=", "MISC")],
    "MISC journal",
)
analytics = ensure_analytic_accounts(rows, company)
categories = ensure_categories(company, journal)
created, updated, totals, period_counts = import_assets(
    rows,
    company,
    categories,
    analytics,
    journal,
)

imported = env["account.asset.asset"].search(
    [("legacy_import_key", "=like", "NADI-ASSET-%")]
)
print(f"validated_rows={len(rows)}")
print(f"created={created} updated={updated} imported={len(imported)}")
print(f"categories={len(categories)} analytics={len(analytics)}")
print(f"gross_total={totals['gross']}")
print(f"accumulated_total={totals['accumulated']}")
print(f"legacy_carrying_total={totals['carrying']}")
print(f"zero_remaining_periods={period_counts[0]}")
print(f"state_counts={Counter(imported.mapped('state'))}")

if commit:
    env.cr.commit()
    print("RESULT=COMMITTED")
else:
    env.cr.rollback()
    print("RESULT=DRY_RUN_ROLLED_BACK")
