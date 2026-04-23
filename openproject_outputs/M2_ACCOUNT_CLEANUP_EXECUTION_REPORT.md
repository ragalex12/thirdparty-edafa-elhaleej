# Account code cleanup — execution report (test/training)

**Date:** 2026-04-09  
**Environment:** Stated **test/training** by operator.  
**Database:** `trgulf_Mrp` @ `127.0.0.1` (PostgreSQL), user `odoo`.  
**Effective code field:** `trim(account_account.code_store->>'1')` (Odoo 19 `jsonb` company key `1`).

---

## 1. Recoverability / backup

| Item | Detail |
|------|--------|
| **Backup taken before changes** | Yes — custom format (`pg_dump -Fc`) |
| **Path** | `/tmp/trgulf_Mrp_pre_account_cleanup_20260409_155843.dump` |
| **Restore (example)** | `pg_restore -h 127.0.0.1 -U odoo -d <target_db> --clean --if-exists /tmp/trgulf_Mrp_pre_account_cleanup_20260409_155843.dump` |

**Production:** This run did **not** target any host/database other than the above. **Do not** replay these SQL updates on production without a separate plan and approval.

---

## 2. Pre-check — records reviewed

### 2.1 Snapshot (before changes)

| id | `code_store['1']` | `active` | `account_type` | `name` (en_US) | `company_ids` (res_company) |
|----|---------------------|----------|----------------|----------------|-----------------------------|
| **755** | 105001 | true | asset_cash | نقدية الصندوق | {3} |
| **788** | 105001 | true | asset_cash | صندوق | {2} |
| **790** | TCWIP01 | true | asset_current | TC WIP Test | {1} |
| **791** | TCCLR01 | true | liability_current | TC CLR Test | {1} |
| **748** | 1260006 | true | asset_current | المخزون الخام | {2} |

### 2.2 Usage summary (before)

| id | `account_move_line` lines | `account_analytic_line` | Notes |
|----|---------------------------|-------------------------|--------|
| 755 | **0** | 0 | Default on journals **63**, **97** (`default_account_id`) |
| 788 | **0** | 0 | Default on journal **96** (`default_account_id`) |
| 790 | **16** (16 moves) | **16** | Posted usage — **no delete** |
| 791 | **16** (16 moves) | **16** | Posted usage — **no delete** |
| 748 | **28** (11 moves) | (not summarized in detail) | Inventory — **no change** |

Other spot-checks for **755/788**: `account_payment`, `account_bank_statement_line`, `account_tax_repartition_line`, `mrp_workcenter`, `stock_location` — **0** rows referencing these accounts.

`ir_default`: no rows matching account ids in the quick text scan.

---

## 3. Actions taken

### 3.1 Duplicate code **105001** (ids **755**, **788**)

- **Issue:** Same display code under key `"1"` for two rows; **no** `account_move_line` on either id.
- **Journals still reference by `id`** (not by code string): **755** → journals **63**, **97**; **788** → journal **96**.
- **Action chosen:** **Recode** account **788** only to a **unique** numeric code (**no delete**, **no archive** — avoids breaking journal defaults).
- **Change:** `788`: **`105001` → `105002`** in `code_store->'1'`.
- **755:** **unchanged** (`105001`).

### 3.2 Alphanumeric **TCWIP01** (id **790**) and **TCCLR01** (id **791**)

- **Issue:** Posted **move lines** and **analytic lines** on both — **cannot** archive without business impact.
- **Action chosen:** **Temporary numeric recoding** in test only (same `account.id`, so existing lines stay valid).
- **Changes:**
  - **790:** **`TCWIP01` → `990101`**
  - **791:** **`TCCLR01` → `990102`**

### 3.3 Review-only **1260006** (id **748**)

- **Action:** **None** (no technical reason to change).
- **Confirmed:** **active** = true; **used** in **28** move lines; **seven-digit numeric** code is **acceptable** as a valid chart-of-accounts pattern; only remaining **length-7** code after cleanup (see metrics below).

---

## 4. SQL confirmation — before vs after

Metrics use non-empty `code_store->>'1'`.

| Metric | Before | After |
|--------|--------|--------|
| Total `account_account` rows | **470** | **470** |
| Distinct codes | **469** | **470** |
| Duplicate code values (`GROUP BY` count > 1) | **1** (`105001` → ids 755, 788) | **0** |
| Rows with letters in code (`[A-Za-z]`) | **2** (790, 791) | **0** |
| Codes containing `.` | **0** | **0** |
| Length distribution | 6: **467**, 7: **3** | 6: **469**, 7: **1** |

**After cleanup, the only length-7 code** is **`1260006`** (id **748**).

---

## 5. Were suspicious anomalies removed?

| Item | Result |
|------|--------|
| **Duplicate `105001`** | **Resolved** — distinct codes; **788** is now **`105002`**. |
| **Alphanumeric test codes** | **Resolved** as codes — now **numeric** `990101` / `990102` (historical moves unchanged on same ids). |
| **`1260006`** | **Unchanged** — still valid **numeric** extended code; usage unchanged. |

---

## 6. Recommendation

1. **Rerun the General Ledger (range / filter) test now** on this database — duplicate code and non-digit codes that motivated the data-quality check are **cleared** for the `code_store['1']` view used in analysis.
2. **No further data cleanup is required** for the items above before that test; optional follow-up is **business confirmation** of **`1260006`** and whether journals **63/96/97** should eventually align naming after any future COA policy.

---

## 7. SQL applied (audit)

```sql
-- 788: duplicate resolution
UPDATE account_account
SET code_store = jsonb_set(COALESCE(code_store, '{}'::jsonb), '{1}', '"105002"'::jsonb, true),
    write_date = NOW() AT TIME ZONE 'UTC'
WHERE id = 788;

-- 790 / 791: temporary numeric codes (test)
UPDATE account_account
SET code_store = jsonb_set(COALESCE(code_store, '{}'::jsonb), '{1}', '"990101"'::jsonb, true),
    write_date = NOW() AT TIME ZONE 'UTC'
WHERE id = 790;

UPDATE account_account
SET code_store = jsonb_set(COALESCE(code_store, '{}'::jsonb), '{1}', '"990102"'::jsonb, true),
    write_date = NOW() AT TIME ZONE 'UTC'
WHERE id = 791;
```

---

*End of execution report.*
