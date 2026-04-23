# Final SQL-only data confirmation — Account codes (`trgulf_Mrp`)

**Date:** April 9, 2026  
**Method:** Read-only PostgreSQL `SELECT` only (no UI, no ORM required for this document, **no data changes**).  
**Database:** `trgulf_Mrp`  
**Effective account code analyzed:** `trim(account_account.code_store->>'1')` — Odoo 19 stores per-company codes in **`code_store` (jsonb)**; company key **`1`** used for this confirmation.

---

## 1. Executive outcome

| Question | Answer |
|----------|--------|
| **SQL/data investigation** | **PARTIAL** confirmation of format risk: **no dotted codes**; **non-uniform length**; **duplicate code**; **two alphanumeric** codes. |
| **Are anomalies enough to recommend data cleanup?** | **Yes** — at minimum **duplicate `105001`** and **suspicious test codes** warrant cleanup **before** any future reporting or range-logic work. |
| **Code implementation (OCA wizard fix)** | **Postpone decision** — not part of this report; **clean data first**, then reassess need for software change with stakeholders. |

---

## 2. Global counts

| Metric | Value |
|--------|--------|
| Total rows `account_account` | **470** |
| Rows with non-empty company-1 code | **470** |
| Distinct company-1 codes | **469** |
| **Gap (duplicates)** | **470 − 469 = 1** duplicate code value |

---

## 3. Confirmed findings (SQL)

### 3.1 No dotted account codes

```sql
WHERE code_store->>'1' LIKE '%.%'
```

**Result:** **0 rows.**

**Conclusion:** On this database, **no** account code contains a **dot** (`.`). Lexical/range issues **cannot** be attributed to dotted notation **here**.

---

### 3.2 Duplicate code (critical data anomaly)

**Duplicate value:** **`105001`** — **2** active account rows:

| id | code | name (en_US) | active | account_type |
|----|------|----------------|--------|----------------|
| **755** | 105001 | نقدية الصندوق | true | asset_cash |
| **788** | 105001 | صندوق | true | asset_cash |

**Conclusion:** **Same code** attached to **two** different `account.account` records (both **cash**, both **active**). This breaks the expectation of **one row per code** for reporting, range filters, and reconciliations.

---

### 3.3 Alphanumeric / non–strict-numeric codes (suspicious)

**Pattern:** `[A-Za-z]` in code

| id | code | name (en_US) | active |
|----|------|----------------|--------|
| **790** | **TCWIP01** | TC WIP Test | true |
| **791** | **TCCLR01** | TC CLR Test | true |

**Conclusion:** **Two** accounts use **letters**; names read as **test** entries. These are **suspicious** for production hygiene and for any logic that assumes **digits-only** codes.

---

### 3.4 Code length not perfectly uniform

**Distribution:**

| Length (characters) | Count |
|---------------------|-------|
| **6** | **467** |
| **7** | **3** |

**All rows with length ≠ 6:**

| id | code | len | name (en_US) | Notes |
|----|------|-----|----------------|--------|
| **748** | **1260006** | 7 | المخزون الخام | **Seven-digit numeric** — likely legitimate COA extension |
| **790** | **TCWIP01** | 7 | TC WIP Test | Alphanumeric / test |
| **791** | **TCCLR01** | 7 | TC CLR Test | Alphanumeric / test |

**Strict pattern “exactly six digits”** (`^[0-9]{6}$`):

- **Fails for 3 rows:** `1260006`, `TCWIP01`, `TCCLR01`.

**Conclusion:** Lengths are **mostly** uniform (6). **Non-uniformity** comes from **one** extra-long **numeric** code and **two** alphanumeric codes — not from random noise across hundreds of rows.

---

### 3.5 Other checks (SQL)

| Check | Result |
|--------|--------|
| Codes with characters outside `[A-Za-z0-9._/-]` | **0** |
| Rows missing company-1 code | **0** |

---

## 4. Suspicious account codes — summary table

| Priority | Code | id(s) | Issue |
|----------|------|-------|--------|
| **P1 — Duplicate** | **105001** | **755, 788** | Two active accounts, same code, both cash — **must be resolved** (merge, deactivate duplicate, or renumber). |
| **P2 — Test / non-production style** | **TCWIP01** | **790** | Alphanumeric; name “TC WIP Test” — **candidate removal or renumber** after validation. |
| **P2 — Test / non-production style** | **TCCLR01** | **791** | Alphanumeric; name “TC CLR Test” — same as above. |
| **P3 — Review only** | **1260006** | **748** | Length 7, **all digits**; Arabic name “raw inventory” — **likely valid**; confirm with finance before any change. |

**Not suspicious on this DB:** dotted codes (**none**).

---

## 5. Is data cleanup justified?

**Yes — with scope:**

| Justification | Strength |
|---------------|----------|
| **Duplicate active code `105001`** | **Strong** — uniqueness of account code is a standard COA rule; duplicates skew any code-based filter or export. |
| **Test-like alphanumeric codes** | **Medium** — remove or rename after confirming unused in moves. |
| **Single 7-digit numeric `1260006`** | **Weak alone** — treat as **business confirmation**, not automatic cleanup. |

**Recommendation:** **Proceed with a data-cleanup initiative** focused on **P1 (mandatory)** and **P2 (after move/balance check)**. **Do not** conflate this with a decision to change OCA report code — **that remains a separate, postponed decision.**

---

## 6. Final recommendation (no UI testing; no code change)

1. **First — data**
   - **Resolve duplicate `105001`** (ids **755** vs **788**): merge into one account **or** assign a **new unique code** to one row after checking journal items / payments.
   - **Address `TCWIP01` / `TCCLR01`**: confirm no posted moves; then archive, merge, or renumber.
   - **Confirm `1260006`** with finance (intentional 7-digit vs migration artifact).

2. **Postpone — implementation decision**
   - **Do not** start OCA wizard / `isdigit()` implementation work **as a consequence of this SQL report alone**.
   - After cleanup, **re-run the same SQL** (duplicate count = 0; suspicious codes cleared or accepted) and **then** decide whether a **code** fix is still required for this tenant.

3. **This report does not require UI testing** to stand; conclusions are **SQL-only**.

---

## 7. Queries used (reproducible)

```sql
-- Counts
SELECT COUNT(*), COUNT(DISTINCT trim(code_store->>'1'))
FROM account_account
WHERE trim(COALESCE(code_store->>'1','')) <> '';

-- Duplicates
SELECT trim(code_store->>'1') AS code, COUNT(*), array_agg(id)
FROM account_account
WHERE trim(COALESCE(code_store->>'1','')) <> ''
GROUP BY 1 HAVING COUNT(*) > 1;

-- Dots / letters / length / strict 6-digit
-- (see sections 3.1–3.4 in body)
```

---

*End of SQL-only confirmation report.*
