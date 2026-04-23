# Dr. Hatem Plan: BoM Cost Calculation with Timesheet Labor

## Goal
Add a button on the Bill of Materials (BoM) that calculates and updates the product's `standard_price` (cost) by combining:
1. **Material cost** from BoM components (using `explode()`)
2. **Average labor cost** from past Manufacturing Orders' timesheet data

---

## Overview

Currently:
- Our module posts timesheet labor cost to accounting when MO is done (journal entry).
- Dr. Hatem's code calculates product cost from BoM materials only.

After implementation:
- The BoM will have a button **"Update Cost from BoM + Labor"**
- When clicked, it will:
  - Sum material costs (via `bom.explode()`)
  - Query past completed MOs to get average labor per unit
  - Update `product.standard_price = (material_cost + avg_labor) / bom.product_qty`

---

## Implementation Steps

### Step 1: Add model extension for `mrp.bom`

**File:** `models/mrp_bom.py`

- Inherit `mrp.bom`
- Add method `action_update_cost_from_bom_and_labor()`
- Logic:
  1. Determine the product to update (bom.product_id or single variant)
  2. Call `bom.explode(product, bom.product_qty)` to get raw materials
  3. Sum material cost: `Σ(component.standard_price × qty)`
  4. Query completed MOs for that product:
     ```python
     past_mos = self.env['mrp.production'].search([
         ('product_id', '=', product.id),
         ('state', '=', 'done'),
         ('timesheet_labor_cost', '>', 0),
     ])
     ```
  5. Calculate average labor per unit:
     ```python
     if past_mos:
         total_labor = sum(mo.timesheet_labor_cost for mo in past_mos)
         total_qty = sum(mo.product_qty for mo in past_mos)
         avg_labor_per_unit = total_labor / total_qty if total_qty > 0 else 0
     else:
         avg_labor_per_unit = 0
     ```
  6. Compute final cost:
     ```python
     material_cost = total_material_cost
     labor_cost = avg_labor_per_unit * bom.product_qty
     total_cost = material_cost + labor_cost
     cost_per_unit = total_cost / bom.product_qty
     ```
  7. Update `product.standard_price = cost_per_unit`
  8. Post message on product chatter with breakdown (material, labor, total)

**Error handling:**
- Catch `UserError` from `explode()` if BoM is incomplete
- Warn if no past MOs found (labor = 0)
- Skip if `bom.product_qty` is 0

---

### Step 2: Add button on BoM form view

**File:** `views/mrp_bom_views.xml`

- Inherit `mrp.bom` form view (likely `mrp.mrp_bom_form_view`)
- Add button in header or button_box:
  ```xml
  <button name="action_update_cost_from_bom_and_labor"
          string="Update Cost (Materials + Labor)"
          type="object"
          class="oe_highlight"
          groups="mrp.group_mrp_manager"/>
  ```
- Place near existing buttons (if any) or in the header statusbar area

---

### Step 3: Add computed fields for visibility (optional)

**File:** `models/mrp_bom.py`

Add fields to show on BoM form:
- `estimated_material_cost` (Monetary, computed) — sum from explode()
- `estimated_labor_cost` (Monetary, computed) — avg labor from past MOs
- `estimated_total_cost` (Monetary, computed) — material + labor

These give the user a **preview** before clicking the button.

**Computation:**
- Same logic as step 1 but in a `@api.depends` method
- Depends on: `product_id`, `product_qty`, `bom_line_ids`, and past MO data (might need periodic recompute)

---

### Step 4: Update manifest dependencies

**File:** `__manifest__.py`

Already depends on `mrp` — no change needed.

---

### Step 5: Add models/__init__.py import

**File:** `models/__init__.py`

Add:
```python
from . import mrp_bom
```

---

### Step 6: Logging and user feedback

In `action_update_cost_from_bom_and_labor`:
- Log material breakdown (component by component) like Dr. Hatem's code
- Log labor calculation (# of past MOs, total labor, avg per unit)
- Post chatter message on **product** with summary:
  ```
  Cost updated from BoM:
  - Material cost: 44.00 (from 3 components)
  - Labor cost: 6.00/unit (avg from 12 past MOs)
  - Total: 50.00/unit
  Old cost: 45.00 → New cost: 50.00
  ```
- Return a user notification (optional):
  ```python
  return {
      'type': 'ir.actions.client',
      'tag': 'display_notification',
      'params': {
          'title': 'Cost Updated',
          'message': f'Product {product.name} cost updated to {cost_per_unit:.2f}',
          'type': 'success',
      }
  }
  ```

---

### Step 7: Handling edge cases

**Multiple BoMs for one product:**
- Each BoM can have different costs (different components)
- The button updates the product's cost based on **that specific BoM**
- If multiple BoMs exist, the last one clicked wins (standard Odoo behavior)
- Alternative: add a `default_bom` checkbox and only allow cost update from default BoM

**No past MOs:**
- Labor cost = 0
- Warn the user: "No completed MOs with timesheet labor found. Cost includes materials only."

**Product variants:**
- If BoM is for template (no specific variant), and template has multiple variants → skip or choose one
- Dr. Hatem's code handles this: use `product_tmpl_id.product_variant_id` if only one variant

**Archived products:**
- Use `with_context(active_test=False)` when querying products/MOs

**Multi-company:**
- Filter past MOs by company: `('company_id', '=', bom.company_id.id)`

---

## File Structure (new/modified)

```
mrp_timesheet/
├── models/
│   ├── __init__.py                    # ADD import mrp_bom
│   ├── mrp_bom.py                     # NEW: BoM cost calculation with labor
│   ├── mrp_production.py              # existing
│   ├── account_analytic_line.py       # existing
│   ├── hr_employee.py                 # existing
│   └── res_company.py                 # existing
├── views/
│   ├── mrp_bom_views.xml              # NEW: button on BoM form
│   ├── mrp_production_views.xml       # existing
│   ├── hr_employee_views.xml          # existing
│   └── res_company_views.xml          # existing
├── __manifest__.py                    # UPDATE: add mrp_bom_views.xml to data
└── DRHATEM_PLAN.md                    # this file
```

---

## Testing Steps

1. Create a BoM with 2-3 components (e.g. Table = 4x Wood + 8x Screw)
2. Set cost on each component
3. Create and complete 2-3 MOs for that product with timesheet lines (log hours)
4. Open the BoM and click **"Update Cost (Materials + Labor)"**
5. Check product's `standard_price` = material + avg labor
6. Check chatter message on product with breakdown
7. Repeat with different BoM or no past MOs (labor = 0)

---

## Optional Enhancements

1. **Scheduled action:** Auto-update product costs weekly based on latest MO data
2. **Report:** Show cost breakdown (material vs labor) per product
3. **Historical tracking:** Store cost updates in a separate model (like product.price.history) so you can see how cost changed over time
4. **BoM cost field:** Add `computed_cost` on BoM (non-stored) so it shows the calculated cost without updating the product
5. **Wizard:** Instead of direct button, open a wizard showing material/labor breakdown and let user confirm before updating

---

## Checklist

- [x] Create `models/mrp_bom.py` with `action_update_cost_from_bom_and_labor()`
- [x] Add button in `views/mrp_bom_views.xml` (smart button with calculator icon)
- [x] Import `mrp_bom` in `models/__init__.py`
- [x] Add `mrp_bom_views.xml` to `__manifest__.py` data list
- [x] Update README/docs with new feature (README, USER_GUIDE, USE_CASES)
- [x] Add unit tests in `tests/test_mrp_timesheet.py` (material only, material + labor)
- [ ] Test with BoM + past MOs (user to test in production)
- [ ] Test edge cases (no MOs, no labor, archived product)

## Implementation Complete ✅

The BoM cost calculation feature is fully implemented:
- **Button:** Top-right of BoM form (calculator icon, smart button style)
- **Logic:** Explodes BoM for materials, queries past MOs for avg labor, updates product cost
- **Docs:** README, USER_GUIDE (section 3.1), USE_CASES (use case 8)
- **Tests:** Two unit tests added for cost calculation (materials only, materials + labor)

**User can now:**
1. Click the button on any BoM to update product cost
2. See detailed breakdown in product chatter
3. Product cost reflects both materials (from BoM design) and labor (from actual MO data)

---

## Timeline Estimate

- Step 1 (model): 2-3 hours
- Step 2 (view): 30 minutes
- Steps 3-5 (optional fields, manifest): 1 hour
- Step 6 (logging, messages): 1 hour
- Step 7 (edge cases): 1 hour
- Testing: 1-2 hours

**Total: ~7-9 hours**

---

## Notes

This plan integrates Dr. Hatem's BoM explosion approach with our timesheet labor tracking. The key difference:
- **Dr. Hatem's code:** Material cost only
- **Our addition:** Material cost + average labor from past MOs

Both use the same `explode()` method for materials; we just add a query for labor and combine them.
