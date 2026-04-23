# M2 Investigation Report — Phase 2 & Live Data Verification (Updated)

**Date:** April 9, 2026  
**Last updated:** April 9, 2026 (live DB + ORM evidence)  
**Scope:** OCA **account_financial_report** — **Accounts From / To** (and related wizards)  
**Odoo target:** 19.0-20251019  

---

## Executive summary

| Layer | Status | Notes |
|-------|--------|--------|
| **Code defect (`isdigit()`)** | **Confirmed** | Four wizards skip range logic when `account.account.code` is not entirely numeric (`str.isdigit()` is **False** for dots, letters, spaces, etc.). |
| **Live database (`trgulf_Mrp`)** | **Verified (read-only)** | **470** accounts; **no dotted codes**; **mostly 6-character numeric strings**; **2** alphanumeric test codes; **1 duplicate code**; length **6 vs 7** for three accounts. |
| **“Dotted SAR COA” hypothesis** | **Not supported on `trgulf_Mrp`** | Earlier **Gulf_Cons** / industry assumptions **were not validated by SQL** in this update. **Per-database** checks are required. |
| **Risk for From/To filter** | **Medium (data)** + **High (code path)** | Duplicate code and rare alphanumeric codes affect ranges; `isdigit()` still blocks non-numeric patterns on **any** DB that uses them. |

**Conclusion:** The **code issue remains real and should be fixed in design**. **Data-format root cause for the *current* tenant is only PARTIALLY confirmed** on `trgulf_Mrp` (no dots; issue would **not** trigger for typical **pure numeric** codes there, except for the **2** letter accounts and **int-vs-string domain** quirks — see §6).

---

## 1. Environment verified (executed)

| Item | Value |
|------|--------|
| **Database inspected** | **`trgulf_Mrp`** (PostgreSQL `127.0.0.1`, user `odoo`) |
| **Odoo version** | **19.0-20251019** |
| **Companies** | **4** (`res_company` ids 1–4) |
| **Account code storage (Odoo 19)** | **`code_store` (jsonb)** on `account_account`; effective code for analysis: **`code_store->>'1'`** (company id `1`). All inspected rows used key **`"1"`** only. |
| **Production vs training** | **Not encoded in DB.** Treat as **the inspected tenant** unless PM labels it. |

**Methods used (read-only):**  
- `SELECT` SQL on `account_account` / `res_company`  
- `odoo shell` ORM: `env['account.account'].search([...])` with DB credentials (one-off process; **no** change to running Odoo service or data).

---

## 2. SQL findings (`trgulf_Mrp`, company 1 code)

| Metric | Result |
|--------|--------|
| Total `account_account` rows | **470** |
| Rows with non-empty `code_store->>'1'` | **470** |
| Distinct codes | **469** |
| **Duplicate code** | **Yes:** **`105001`** → two rows (**ids 755, 788**) |
| Codes containing **`.`** | **0** |
| Codes matching `[A-Za-z]` | **2** (`TCWIP01`, `TCCLR01` — test-style names) |
| Codes matching `[^A-Za-z0-9._/-]` | **0** |
| Length distribution | **467 × length 6**, **3 × length 7** |
| Lexical `min` / `max` (string) | **`100001`** … **`TCWIP01`** |

**Sample (first 20 by string sort):** from `100001` (Liquidity Transfer) through `103018` (Shipment Other Charges) — consistent **numeric string** pattern.

**Lexical range checks (SQL):**

- Between **`100001`** and **`101010`**: **11** accounts.  
- Between **`TCCLR01`** and **`TCWIP01`**: **2** accounts.  
- Between **`999999`** and **`ZZZZZZ`**: includes **`999999`**, **`TCWIP01`**, **`TCCLR01`** (string ordering).

---

## 3. Odoo shell / ORM findings (same database)

| Check | ORM result |
|--------|------------|
| `search([])` count | **470** |
| `order='code asc'`, limit 20 | Aligns with SQL sample |
| `('code','ilike','%.%')` | **0** |
| Codes with letters (Python `re`) | **2** (ids **790**, **791**) |
| Length distribution | `{6: 467, 7: 3}` |
| `('code','>=','100001'),('code','<=','101010')` | **11** |
| `('code','>=','TCCLR01'),('code','<=','TCWIP01')` | **2** |

**Conclusion:** ORM **`code`** behaves as a **string** for domains; lexical filters are **consistent** with SQL on **`trgulf_Mrp`**.

---

## 4. Code analysis (OCA `account_financial_report`) — unchanged facts

**File:** `account_financial_report/wizard/general_ledger_wizard.py`

```python
@api.onchange("account_code_from", "account_code_to")
def on_change_account_range(self):
    if (
        self.account_code_from
        and self.account_code_from.code.isdigit()
        and self.account_code_to
        and self.account_code_to.code.isdigit()
    ):
        start_range = int(self.account_code_from.code)
        end_range = int(self.account_code_to.code)
        domain = [("code", ">=", start_range), ("code", "<=", end_range)]
        ...
        self.account_ids = self.env["account.account"].search(domain)
```

**Same `isdigit()` gate appears in:**

- `trial_balance_wizard.py` (lines 85, 87)  
- `aged_partner_balance_wizard.py` (lines 51, 53)  
- `open_items_wizard.py` (lines 71, 73)  

**Additional technical note (Odoo 19):** The domain uses **`int` bounds** with field **`code`**. Depending on ORM coercion, this may differ from **pure string** lexical behaviour; on `trgulf_Mrp`, `code` is stored as **string-like** values in `code_store`. Any fix design should use **one consistent type** (string lexical vs numeric) and **avoid** `isdigit()` for real COAs.

---

## 5. Screen / PDF / XLSX behaviour (logic chain)

When `isdigit()` is **False**, the `if` body does not run → **`account_ids`** on the wizard may stay **empty / unchanged**. Downstream, if the report treats empty `account_ids` as “no account filter”, users can see **all accounts** in the period (same analysis as before; validate on UI when possible).

---

## 6. Revised root-cause assessment

| Question | Answer for **`trgulf_Mrp`** |
|----------|-----------------------------|
| Purely numeric uniform codes? | **Mostly yes** (467×6-char numeric style; 3×7-char). |
| Dotted codes? | **No** (0 rows). |
| Alphabetic / mixed? | **Yes, minimal** (2 test codes). |
| Inconsistent lengths? | **Yes** (6 vs 7). |
| Lexical From/To surprising? | Possible for **edge ranges** mixing **`999999`** with **`TC*`** codes; **duplicate `105001`** can duplicate or confuse selection. |
| Is root cause **only** data format on this DB? | **PARTIAL.** Dots are **not** the issue here; **code wizard logic** still defective for **any** future non-numeric code or wrong **int/string** domain. |

---

## 7. Confirmed / partial / not confirmed

| Statement | Status |
|-----------|--------|
| **`isdigit()` blocks non-numeric codes** | **Confirmed** (source) |
| **`trgulf_Mrp` uses dotted hierarchical codes** | **Not confirmed** — **contradicted** by SQL (**0** dots) |
| **Silent skip of range when `isdigit()` fails** | **Confirmed** (control flow) |
| **Live UI/PDF/XLSX identical to this analysis** | **Not confirmed** here — recommend **one** guided test on the same DB |

**Evidence summary**

- Dots found: **NO** (`trgulf_Mrp`)  
- Letters found: **YES** (2)  
- Mixed formats: **YES** (minimal)  
- Inconsistent lengths: **YES** (6 vs 7)  
- Duplicate code values: **YES** (`105001`)

**Likely impact on OCA GL From/To on `trgulf_Mrp`:** **medium** (data quirks + wizard logic), not “high because of dots” on this tenant.

---

## 8. Risk and recommendations

| Risk | Level | Action |
|------|--------|--------|
| **Wizard `isdigit()` + int domain** | **High** (design) | Implement **M2** fix: string-safe range (and company-aware `code_store` if multi-company codes differ). |
| **Duplicate code `105001`** | **Medium** (data) | Merge/archive duplicate accounts; retest ranges. |
| **Test accounts `TCWIP01` / `TCCLR01`** | **Low** | Remove or deactivate if obsolete. |
| **Other databases (e.g. Gulf_Cons)** | **Unknown** | Run the **same SQL/OR checklist** per database before assuming dotted COA. |

### Next step (aligned with investigation, not “implement blindly”)

1. **Proceed to M2 implementation design** for replacing `isdigit()` / int domain with a **documented** string (or numeric-padding) strategy + tests.  
2. **Data:** clean **duplicate** and **test** codes on affected DBs.  
3. **Optional:** run **one** real **General Ledger** wizard From/To on **`trgulf_Mrp`** to confirm UI matches SQL range behaviour.  
4. **Do not** rely on **Gulf_Cons** dotted-format assumptions until verified by query on that DB.

---

## 9. Status vs previous version of this report

| Old claim | Update |
|-----------|--------|
| “Unable to query DB / terminal blocked” | **Superseded** — **`trgulf_Mrp`** queried successfully. |
| “Gulf_Cons almost certainly uses dotted codes” | **Not evidenced** for **`trgulf_Mrp`**; **per-DB** verification required. |
| “~95% Gulf_Cons manifests defect” | **Replaced** by **evidence table** above; **tenant-specific**. |
| “Proceed immediately Phase 4 implementation” | **Softened** — **design + implementation** proceed with **data cleanup** and **optional UI confirmation**. |

---

## 10. Appendix — suggested read-only queries (other databases)

Use the same pattern; on **Odoo 19** adjust for **`code_store`**:

```sql
-- Effective code (company 1)
SELECT id, code_store->>'1' AS code, name->>'en_US' AS name
FROM account_account
WHERE code_store->>'1' IS NOT NULL
ORDER BY code_store->>'1'
LIMIT 20;

SELECT COUNT(*), COUNT(DISTINCT code_store->>'1')
FROM account_account
WHERE trim(COALESCE(code_store->>'1','')) <> '';

SELECT code_store->>'1' AS code, COUNT(*)
FROM account_account
WHERE code_store->>'1' IS NOT NULL
GROUP BY code_store->>'1'
HAVING COUNT(*) > 1;
```

---

*Report maintained for OpenProject M2. Source: code review + read-only `trgulf_Mrp` SQL/ORM (April 9, 2026).*
