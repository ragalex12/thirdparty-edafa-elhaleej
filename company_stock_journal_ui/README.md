# Company Stock Journal (UI)

Odoo Community addon that exposes the **Stock Journal** company field on the company form so it can be set without Studio or code.

## Why

- **ValidationError** on **Produce All** (MO): *Missing required value for field 'Journal' (journal_id)* on `account.move`.
- Cause: `res.company.account_stock_journal_id` is not set; `stock_account` uses it when creating stock valuation moves.
- The field exists on `res.company` (from `stock_account`) but is not shown on the company form in standard Community.

## What this module does

- Inherits **base** company form (`base.view_company_form`).
- Adds **Stock Journal** (`account_stock_journal_id`) after the **Currency** field.
- Field is editable, restricted to **Settings** users (`base.group_system`).
- Domain: journals of the current company and type **General** only.

No new menu or action; the field appears on **Settings → Companies → [Company]**.

## Dependencies

- base, account, stock, stock_account (Odoo Community with Inventory Valuation / wms_accounting).

## Install / upgrade

1. Put the addon in your addons path (e.g. `/opt/localaddons`).
2. Update Apps: **Apps → Update Apps List**.
3. Search **Company Stock Journal**, then **Install** (or **Upgrade** if already installed).

## Verify

1. **Settings → Companies** → open a company.
2. On the **General Information** tab, confirm **Stock Journal** appears after **Currency**.
3. Set **Stock Journal** to a **General** journal (e.g. "Miscellaneous" or a dedicated "Stock Valuation" journal).
4. Save.
5. Run **Produce All** on a Manufacturing Order that uses real-time valuation; a journal entry should be created and the error should disappear.

## Version

- Target: **Odoo 19** Community; view inheritance is compatible with **Odoo 18** (same `base.view_company_form` and field name).
