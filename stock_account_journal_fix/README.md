# Stock Account Journal Fix & Debug (Odoo 19)

Fixes **ValidationError: Missing required value for field 'Journal' (journal_id)** when clicking "Produce All" on a Manufacturing Order (or completing any valued stock move). Designed for **Odoo 19**.

## Root cause

In Odoo core `stock_account`, `stock.move._create_account_move()` uses **only**:

```python
'journal_id': self.company_id.account_stock_journal_id.id
```

If the company has no **Stock Journal** set (Settings → Inventory → Journal for Inventory Valuation), `journal_id` is False and `account.move.create` raises.

Product category **Stock Journal** (e.g. "Manufacturing Valuation") is **not** used by this code path, even if you set it.

## Fix (this module)

- Overrides `stock.move._create_account_move()` to resolve the journal in this order:
  1. Product category `property_stock_journal` (for the move’s company)
  2. Company-dependent fallback for that category
  3. Company `account_stock_journal_id`
- If no journal is found, raises a clear error indicating company and category.

## Debug mode

To see **who** calls `account.move.create` without `journal_id`:

1. Create system parameter: **Key** `stock_account_journal_fix.debug`, **Value** `True`.
2. Reproduce (e.g. Produce All on MO). The server will log `vals` and full stack, then raise.
3. To only log without raising: set **Key** `stock_account_journal_fix.debug_raise`, **Value** `False`.

See **MO_JOURNAL_DIAGNOSIS.md** for full diagnosis, SQL queries, and config checklist.

## Unit tests

Run the module tests (Odoo 19, with database and addons path set):

```bash
odoo -d YOUR_DB --addons-path=... -i stock_account_journal_fix --test-enable --stop-after-init
# or run only this module's tests:
odoo -d YOUR_DB --addons-path=... --test-enable --test-tags stock_account_journal_fix --stop-after-init
```
