# OpenProject handoff — OCA account code range onchange fix (Odoo 19)

**Automation status:** Not executed against OpenProject API from build environment (API returned `401 Unauthenticated` / host configuration errors). **Create or update the work package manually** in your OpenProject project, or run when API credentials and base URL are valid.

---

## Duplicate check (before create)

Search work packages for subject containing:

`Fix OCA account code range onchange crash in Odoo 19 reports`

If a match exists with the same scope, **add the closure comment** to that WP and set status to **Closed / Done** instead of creating a duplicate.

---

## Work package fields

| Field | Value |
|-------|--------|
| **Type** | Bug (or Task if your process prefers tasks for fixes) |
| **Subject / title** | Fix OCA account code range onchange crash in Odoo 19 reports |
| **Priority** | Normal |

### Description (paste as body)

**Root cause:**

In Odoo 19, `account.account` code search goes through `_search_code` → `code_store` using string semantics. Some OCA report wizards were building account range domains using numeric/int bounds, which caused domain evaluation to compare string account codes against integer values and crash with:

`TypeError: '<=' not supported between instances of 'str' and 'int'`

**Affected files:**

- `account_financial_report/wizard/open_items_wizard.py`
- `account_financial_report/wizard/general_ledger_wizard.py`
- `account_financial_report/wizard/aged_partner_balance_wizard.py`

**Reference file already safe:**

- `account_financial_report/wizard/trial_balance_wizard.py`

**Implemented fix:**

Replaced numeric account code range bounds with string bounds only:

```
start_range = self.account_code_from.code or ""
end_range = self.account_code_to.code or ""
```

Kept domain behavior unchanged:

- `("code", ">=", start_range)`
- `("code", "<=", end_range)`

**Tests:**

- `test_open_items_account_range_onchange_string_domain`
- `test_aged_partner_balance_account_range_onchange_string_domain`
- `test_general_ledger_account_range_onchange_string_domain`

**Validation:**

- Reproduced pre-fix crash with int-based code bounds
- Verified post-fix onchange works with string-based bounds
- Confirmed no remaining int-based account code handling in affected onchange methods
- `trial_balance_wizard.py` already string-safe and required no change

**Residual note:**

Lexical/string ordering of account codes remains unchanged and is out of scope for this fix.

---

## Status

Set to the team’s **Done / Closed / Resolved** equivalent immediately after creation (work is already completed).

---

## Final comment (paste as last activity / note)

Implemented and verified Odoo 19 compatibility fix for OCA `account_financial_report` account range onchange crash. Open Items, General Ledger, and Aged Partner Balance now use string-only account code bounds, preventing the str/int TypeError during onchange domain evaluation. Trial Balance was reviewed and already safe. Focused tests were added/confirmed. Lexical account code ordering remains unchanged and is out of scope for this bugfix.

---

*End of handoff.*
