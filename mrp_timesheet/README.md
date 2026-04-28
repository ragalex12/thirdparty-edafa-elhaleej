# Manufacturing Timesheet

Adds a **Timesheet** tab on the Manufacturing Order form to view and log time spent on each MO, and **posts timesheet labor cost to production cost** when the MO is done.

## Dependencies

- **mrp** (Manufacturing)
- **hr_timesheet** (Timesheets)
- **stock_account** (Inventory valuation, for labor cost journal entry)

## Installation

1. Copy this folder into your Odoo addons path (e.g. `addons` or `localaddons`).
2. Update the app list and install **Manufacturing Timesheet**.

## Configuration

1. **Production labor expense account**  
   Go to **Settings → Companies → [Your company]** and set **Production Labor Expense Account**. This account is **credited** when timesheet labor cost is posted (inventory is debited). Use an expense account (e.g. “Production labor” or “WIP labor”).

2. **Stock journal**  
   Required for posting labor (same as for inventory valuation). Set **Stock Journal** on the company or on the product category if not already set.

3. **Employee hourly cost** (optional)  
   This module adds **Hourly Cost** on the **Employee** form (after Job Position) because it is not in Community by default. Set it per employee for labor cost calculation. If not set, the timesheet line’s **Product** cost or **amount** is used.

## Features

### 1. Timesheet tracking on Manufacturing Orders
1. Open a Manufacturing Order.
2. Set **Analytic Account** on the MO (optional; required to log time).
3. Open the **Timesheets** tab: add lines (date, user/employee, description, hours).
4. **Timesheet Labor Cost** is computed automatically (hours × employee/product hourly cost or line amount).
5. When you **Mark as Done** (Produce All), a **journal entry** is created once:  
   - **Debit** Stock Valuation (finished product category)  
   - **Credit** Production Labor Expense Account  
   So the time consumed **affects production cost** (inventory value increases by labor).

### 2. Update product cost from BoM (Materials + Labor)
1. Go to **Manufacturing → Configuration → Bills of Materials**.
2. Open a BoM.
3. Click the **"Update Cost (Materials + Labor)"** button (top-right, calculator icon).
4. The system:
   - Explodes the BoM to calculate **total material cost** from all components.
   - Queries past completed MOs to calculate **average labor cost per unit** from timesheets.
   - Updates the product's **Cost** (`standard_price`) = (material + labor) / quantity.
   - Posts a detailed breakdown to the product's chatter (material breakdown, labor average, old vs new cost).
5. Use this to keep product costs accurate based on actual production data.

## Documentation

- **[User Guide](docs/USER_GUIDE.md)** – Configuration, daily use, where to find settings and fields, troubleshooting.
- **[Use case examples](docs/USE_CASES.md)** – Typical scenarios (custom assembly, different rates per employee, mixing work-center and timesheet labor, reviewing cost before closing, etc.).

## Technical

- **Models:** 
  - `mrp.production`: analytic_account_id, timesheet_ids, timesheet_labor_cost, timesheet_cost_posted, timesheet_labor_move_id
  - `mrp.bom`: action_update_cost_from_bom_and_labor()
  - `account.analytic.line`: mrp_production_id, _get_timesheet_labor_cost_for_production()
  - `hr.employee`: hourly_cost (added for Community)
  - `res.company`: production_labor_expense_account_id
- **Labor cost:** Sum over lines of `amount` (if set) or `unit_amount ×` (employee hourly cost or product cost).
- **MO posting:** Override of `_post_inventory`; creates one posted account.move for timesheet labor.
- **BoM cost update:** Uses `bom.explode()` for materials + query past MOs for avg labor, updates `product.standard_price`.
