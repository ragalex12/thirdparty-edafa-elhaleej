# M2 / M3 / M4 closure summary

**Purpose:** Single handoff memo for the account-code General Ledger thread: data work (M2), report-logic analysis (M3), and test-environment patch (M4).

**Environment context:** Work was performed against a **test/training** Odoo database (`trgulf_Mrp`) unless stated otherwise. **Production** was not modified by M2–M4 execution described here.

---

## M2 closure — COA data investigation and cleanup

### Investigation (SQL-only, read-only)

- **Effective code analyzed:** `trim(account_account.code_store->>'1')` (Odoo 19 stores per-company codes in `code_store` JSON).
- **Findings (pre-cleanup):**
  - No account codes containing a **dot** (`.`).
  - **One duplicate code:** `105001` on two active cash accounts (ids **755**, **788**).
  - **Two alphanumeric codes:** `TCWIP01`, `TCCLR01` (test-style names).
  - **Length not uniform:** mostly 6-character numeric codes; one legitimate **7-digit** numeric `1260006`; the two alphanumeric codes were length 7.
  - **470** account rows, **469** distinct codes (duplicate explained the gap).

**Reference:** [`M2_SQL_DATA_CONFIRMATION_FINAL.md`](M2_SQL_DATA_CONFIRMATION_FINAL.md).

### Cleanup (test DB only)

- **Recoverability:** PostgreSQL `pg_dump` backup taken before updates (`/tmp/trgulf_Mrp_pre_account_cleanup_*.dump`).
- **Actions:**
  - **Duplicate `105001`:** Recoded **788** → **`105002`** (journals reference accounts by **id**; no move lines on either duplicate row).
  - **TCWIP01 / TCCLR01:** Recoded to temporary numerics **`990101`** / **`990102`** (accounts were posted — recode only, not delete).
  - **`1260006`:** Reviewed; **no change** (valid extended numeric code; in use).

**Reference:** [`M2_ACCOUNT_CLEANUP_EXECUTION_REPORT.md`](M2_ACCOUNT_CLEANUP_EXECUTION_REPORT.md).

### M2 outcome

- Duplicate and alphanumeric **code-string** anomalies **removed** for the analyzed `code_store['1']` view.
- **SQL** and **ORM** string-range checks on `code` were aligned after cleanup for verification ranges.
- **Data investigation closed:** no remaining evidence that “dirty COA” was the **primary** root cause for the General Ledger range symptom.

---

## M3 closure — report logic investigation and root cause

### Scope

- **Module:** `account_financial_report` (OCA-style), under `account_financial_report` in the addons path.
- **Focus:** `general.ledger.report.wizard` — **From code / To code** (`account_code_from` / `account_code_to`) and how `account_ids` is filled.

### Behavior

- The **printed report** consumes **`account_ids`** prepared by the wizard; it does **not** re-apply a separate code-range filter on move lines.
- **Auto-fill** of `account_ids` from the from/to pickers is implemented in **`on_change_account_range`** on the wizard.

### Root cause (confirmed)

- **General Ledger**, **Open Items**, and **Aged Partner Balance** wizards used **`int(self.account_code_from.code)`** and **`int(self.account_code_to.code)`** in the search domain for **`account.account`** / field **`code`**.
- In **Odoo 19**, account **code** is a **Char**-backed field (via `code_store`); **integer** bounds in the domain are **not type-safe** and led to **`TypeError`** (str/int comparison) and/or incorrect behavior during search.
- **Trial Balance** in the **same** addon already used **string** bounds for the same pattern — correct alignment target.

### M3 outcome

- **Report-logic investigation closed:** primary defect identified as **wizard onchange domain typing**, not residual COA duplication/alphanumeric noise after M2.

---

## M4 closure — test patch, files, validation

### Implemented fix

- Replaced **int-based** range bounds with **string-based** bounds in **`on_change_account_range`**, consistent with **Trial Balance**.
- **Company scoping** preserved:
  - **General Ledger:** `('company_ids', 'in', self.company_id.ids)` remains in the search domain when `company_id` is set.
  - **Open Items / Aged Partner Balance:** existing **filter** on `company_id in account.company_ids` after search is unchanged.

### Changed files

| File | Role |
|------|------|
| `account_financial_report/wizard/general_ledger_wizard.py` | GL wizard `on_change_account_range` |
| `account_financial_report/wizard/open_items_wizard.py` | Same int→string fix |
| `account_financial_report/wizard/aged_partner_balance_wizard.py` | Same int→string fix |
| `account_financial_report/tests/test_general_ledger.py` | New test: `test_general_ledger_account_range_onchange_string_domain` |

### Validation (test environment)

- **No `TypeError`** when running `on_change_account_range` with digit-only from/to accounts for the active company.
- **`account_ids`** populated consistently with a direct `account.account` search using the **same** string `code` domain and company filter (**shell validation** on test DB).
- **Automated test** added to guard regression (wizard `new()` + onchange + non-empty `account_ids` when the chart has at least two digit-code accounts).

### M4 outcome

- **Test-environment patch completed** for GL, Open Items, and Aged Partner Balance wizards.

---

## Open note — out of scope for this bugfix

**Lexical string behavior for mixed-length account codes** (e.g. **6-digit** vs **7-digit** numerics in the same chart) **remains**:

- Range filters on `code` use **string** ordering (`>=` / `<=` on character data), which is **not** the same as **numeric** ordering for all pairs of codes.
- Addressing that (padding rules, numeric comparison, UX copy, or chart policy) is a **separate product semantics / decision** task, **not** part of the int/string wizard fix.

---

## Next step

- **Production rollout planning:** review, backup, deploy the addon changes, and smoke-test GL / Open Items / Aged Partner **from/to** in a staging mirror before production.
- **Optional parallel track:** open a **product decision** task if stakeholders want explicit rules for **mixed-length** numeric codes (beyond lexical string behavior).

---

*End of closure memo.*
