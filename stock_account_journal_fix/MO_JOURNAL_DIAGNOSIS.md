# MO Produce All – Missing journal_id (account.move) – Diagnosis & Fix (Odoo 19)

## A) Likely root causes (ranked, with evidence)

### 1. **Company Stock Journal not set (most likely)**  
**Evidence:**  
- `addons/stock_account/models/stock_move.py` line 155:  
  `'journal_id': self.company_id.account_stock_journal_id.id`  
- The code uses **only** `company_id.account_stock_journal_id`. It does **not** use product category `property_stock_journal`.  
- If `account_stock_journal_id` is False, `.id` is False → `account.move.create(vals)` gets `journal_id=False` → ValidationError.

### 2. **Product category Stock Journal set but company one not set**  
- You configured “Product Category Stock Journal” (e.g. “Manufacturing Valuation”).  
- `product.get_product_accounts()` uses category then company (see `addons/stock_account/models/product.py` lines 113–117).  
- `stock.move._create_account_move()` does **not** use that logic; it only uses `company_id.account_stock_journal_id`.  
- So category journal alone is not used for the move created on MO completion.

### 3. **Multi-company / wrong company**  
- If the move’s `company_id` is not the one where you set the Stock Journal, `company_id.account_stock_journal_id` can be empty for that company.

### 4. **Custom “Production” location / WIP**  
- You have an Inventory Location “Production” with a “Cost of Production” account (WIP).  
- `_get_account_move_line_vals()` uses `location_id.valuation_account_id` / `location_dest_id.valuation_account_id` for debits/credits.  
- Journal resolution is still only `company_id.account_stock_journal_id` (same code path as above).

---

## B) What to print/log and where

### 1. Debug module (this addon) – `account.move.create`  
**File:** `stock_account_journal_fix/models/account_move.py`  
**Method:** `create()`  
**When:** Only if system parameter `stock_account_journal_fix.debug` is `True`.  
**Logs:**  
- `vals` keys and vals without full `line_ids`  
- Full stack: `traceback.format_stack()`  
**Then:** Raises `ValueError` so you get a clear traceback and can see the caller.

### 2. Optional: log inside `stock.move._create_account_move` (core)  
**File (core):** `odoo/addons/stock_account/models/stock_move.py` (or addons/stock_account)  
**Method:** `_create_account_move`  
**Add before `account.move.create`:**  
```python
import logging
_logger = logging.getLogger(__name__)
# before: account_move = self.env['account.move'].create({...})
_logger.error(
    "stock.move._create_account_move company=%s account_stock_journal_id=%s move_ids=%s",
    self.company_id.name, self.company_id.account_stock_journal_id.id, self.ids
)
```  
Use only if you prefer not to use the debug module.

---

## C) Results to paste back

After enabling debug and reproducing (Produce All on MO):

1. **Log lines**  
   - The two `_logger.error` lines from `account_move.create` (vals keys + STACK).  
   - If you added the optional log in `_create_account_move`: the line with `company=`, `account_stock_journal_id=`, `move_ids=`.

2. **Traceback**  
   - Full traceback when `ValueError` is raised (so we see the exact call chain: e.g. `_action_done` → `_create_account_move` → `account.move.create`).

3. **SQL query results** (run the 3 queries below and paste the result sets).

---

## D) Final patch (code) and config checklist

### Config checklist (try first)

- [ ] **Company Stock Journal**  
  Settings → Inventory → Configuration → Settings → **Journal for Inventory Valuation** (or company form: **Stock Journal**) set for the company of the MO/warehouse.
- [ ] **Inventory valuation**  
  Valuation = **Perpetual (real time)** for products you want to post moves on completion.
- [ ] **Stock valuation account**  
  Company: **Stock Valuation Account** set.  
  Product category: **Stock Valuation Account** and/or **Stock Input/Output** if used.
- [ ] **Production location**  
  If using a “Production” location with WIP: **Valuation Account** (or your custom “Cost of Production”) set on that location.
- [ ] **Journals**  
  At least one journal of type **General** (or the one used for inventory) exists for the company and is set as Stock Journal.

### Code fix (this module)

The module `stock_account_journal_fix` overrides `stock.move._create_account_move()` to resolve the journal in this order:

1. Product category `property_stock_journal` (for move’s company)  
2. Company-dependent fallback for that category  
3. Company `account_stock_journal_id`  

If none is set, it raises a clear `ValueError` pointing to company and category.

**Diff-style (conceptual) – in your override:**

- Replace the single line  
  `'journal_id': self.company_id.account_stock_journal_id.id`  
  with resolution via a helper that uses category then company (see `models/stock_move.py`).
- Add a clear raise when no journal is found.

No change to core is required if you use this addon.

---

## SQL queries to run

### Query 1: Products/categories missing stock journal (per company)

```sql
-- Companies and their stock journal
SELECT c.id AS company_id, c.name AS company_name,
       c.account_stock_journal_id AS company_stock_journal_id,
       j.code AS journal_code
FROM res_company c
LEFT JOIN account_journal j ON j.id = c.account_stock_journal_id
WHERE c.account_stock_journal_id IS NULL;

-- Product categories: company-dependent property_stock_journal is in ir_property
SELECT ip.id, ip.name, ip.res_id, ip.company_id, ip.value_reference,
       c.name AS company_name
FROM ir_property ip
LEFT JOIN res_company c ON c.id = ip.company_id
WHERE ip.name = 'property_stock_journal'
  AND ip.res_id LIKE 'product.category,%';
```

### Query 2: Stock valuation layers without account_move_id or company mismatch

```sql
SELECT svl.id AS svl_id, svl.product_id, svl.quantity, svl.value,
       svl.account_move_id, svl.company_id,
       sm.id AS move_id, sm.picking_id, sm.origin
FROM stock_valuation_layer svl
LEFT JOIN stock_move sm ON sm.id = svl.stock_move_id
WHERE svl.account_move_id IS NULL
   OR svl.company_id != (SELECT company_id FROM account_move WHERE id = svl.account_move_id)
LIMIT 50;
```

### Query 3: Journals per company that can be used as stock journal fallback

```sql
SELECT j.id, j.company_id, c.name AS company_name, j.name, j.code, j.type
FROM account_journal j
JOIN res_company c ON c.id = j.company_id
WHERE j.type IN ('general', 'bank')
ORDER BY j.company_id, j.type;
```

---

## How to reproduce with the debug module

1. Install `stock_account_journal_fix` and upgrade.
2. Create system parameter: **Key** `stock_account_journal_fix.debug`, **Value** `True`  
   (Settings → Technical → Parameters → System Parameters).
3. Clear company Stock Journal for the company used by the MO (to reproduce the error).
4. Open a Manufacturing Order and click **Produce All** (or Mark as Done).
5. Check server logs for the two `_logger.error` lines and the full traceback; paste them plus the 3 SQL results.

To only log without raising, comment out the `raise ValueError(...)` in `models/account_move.py` and run again.
