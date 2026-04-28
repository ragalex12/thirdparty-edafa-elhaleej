# Manufacturing Timesheet – Use Case Examples

This document describes typical use cases and how to achieve them with the **Manufacturing Timesheet** module.

---

## Use case 1: Track and cost labor on a custom assembly order

**Scenario:** You build custom furniture. Each order is a Manufacturing Order. Workers log actual hours on the MO; you want that labor to increase the cost of the finished product.

**Steps:**

1. **Configuration**
   - Set **Production Labor Expense Account** on the company (e.g. “Production labor”).
   - Set **Hourly Cost** for each workshop employee (e.g. 18.00 for assistants, 28.00 for senior assemblers).
   - Ensure **Stock Journal** and product category **Stock Valuation Account** are set.

2. **On each MO**
   - Create or open the MO for the custom piece.
   - Set **Analytic Account** (e.g. “Custom orders”).
   - In the **Timesheets** tab, add lines:
     - Employee: John (28.00/h), Description: “Assembly”, Hours: 3.0  
     - Employee: Maria (18.00/h), Description: “Sanding”, Hours: 1.5  

3. **Result**
   - **Timesheet Labor Cost** = 3.0×28 + 1.5×18 = 84 + 27 = **111.00**.
   - When you **Mark as Done**, a journal entry is created: inventory (finished product) is debited 111.00, Production labor expense is credited 111.00. The cost of the produced good includes this labor.

**Benefit:** You see real labor per order and it is reflected in inventory value and cost of goods.

---

## Use case 2: Different hourly rates per employee

**Scenario:** Technicians have different hourly costs; you want the MO labor cost to use each employee’s rate.

**Steps:**

1. In **Employees**, set **Hourly Cost** per person (e.g. Junior: 15.00, Senior: 35.00, Specialist: 50.00).
2. On the MO, in the **Timesheets** tab, always select the correct **Employee** for each line (and enter hours).
3. The module uses that employee’s **Hourly Cost** for that line. **Timesheet Labor Cost** is the sum over all lines.

**Benefit:** No need to maintain separate “labor products” per rate; one place (employee) defines the cost per hour.

---

## Use case 3: Mix work-center cost and manual timesheet labor

**Scenario:** Your BoM has operations with work centers (automatic cost), but some work is done off the routing (e.g. quality checks, rework). You want to add that extra time and cost on the MO.

**Steps:**

1. Configure work centers and BoM operations as usual (work center cost per hour, duration).
2. On the MO, open the **Timesheets** tab and add lines for the **non-routed** work (e.g. “Final QC”, “Rework”).
3. Set **Employee** and **Hours**; **Hourly Cost** comes from the employee.
4. When you **Mark as Done**, standard valuation posts component + work center cost; the module adds one extra journal entry for the **timesheet** labor only.

**Benefit:** You keep work-center costing and add real extra labor (e.g. overtime, rework) without changing the BoM.

---

## Use case 4: Review labor cost before closing the MO

**Scenario:** You want to see total labor cost before marking the MO as done, and optionally adjust time entries.

**Steps:**

1. On the MO, fill the **Timesheets** tab (date, employee, description, hours).
2. Check **Timesheet Labor Cost** on the form (updated automatically).
3. If the total is wrong, edit the timesheet lines (fix hours or employee) or add/remove lines.
4. When the total is correct, click **Mark as Done**. Labor is posted once with that total.

**Benefit:** No surprise after closing; you can correct time before posting.

---

## Use case 5: One MO, several workers and days

**Scenario:** One production order is worked on by several people over several days. You want one total labor cost for the MO.

**Steps:**

1. On the MO, set **Analytic Account**.
2. In **Timesheets**, add one line per person per day (or per task), e.g.:
   - Mon: Alice 4h, Bob 2h  
   - Tue: Alice 2h, Bob 4h  
   - Wed: Bob 3h  
3. **Timesheet Labor Cost** = sum of (hours × hourly cost) for all lines.
4. **Mark as Done** once when the order is finished; one journal entry posts the full labor cost.

**Benefit:** Full traceability (who, when, how many hours) and a single labor cost per MO for accounting.

---

## Use case 6: No employee hourly cost – use product or amount

**Scenario:** You do not set **Hourly Cost** on employees; you prefer to use a service product’s cost or the line amount.

**Steps:**

1. Leave **Hourly Cost** empty on employees (or set it only for some).
2. On the timesheet line you can:
   - Set **Product** to a service product with a **Cost** (standard price); the module uses **Hours × Product cost** when employee cost is 0.
   - Or ensure the line has **Amount** set (e.g. from another process); the module uses **|Amount|** for that line.
3. Labor cost is still summed and posted when you **Mark as Done**.

**Benefit:** Flexibility to drive cost from product or amount when employee rate is not used.

---

## Use case 7: Analyze time and cost by analytic account

**Scenario:** You use one analytic account per production line or project and want to see total time and cost per account.

**Steps:**

1. Create analytic accounts (e.g. “Line A”, “Line B”, “Project X”).
2. On each MO, set **Analytic Account** and log timesheet lines (they inherit the MO’s analytic account).
3. Use **Accounting** (or **Timesheets**) reports filtered by analytic account to see hours and cost per line/project.
4. The labor journal entry credits **Production Labor Expense Account** and the move is linked to the MO; you can still analyze by analytic account from the timesheet lines.

**Benefit:** Same MO timesheet data supports both production costing and analytic reporting.

---

## Use case 8: Update product cost from BoM with materials AND labor

**Scenario:** You want the product's `standard_price` (cost) to reflect both material cost (from BoM) and average labor (from past MOs with timesheets), so quotes and valuation are accurate.

**Steps:**

1. **Produce several MOs** with timesheet data:
   - Complete 3-5 MOs for the product.
   - Log timesheet hours on each MO (Timesheets tab).
   - Mark each as Done (labor is posted to inventory).

2. **Update cost from BoM:**
   - Go to **Manufacturing → Configuration → Bills of Materials**.
   - Open the BoM for that product.
   - Click **"Update Cost (Materials + Labor)"** button (top-right, calculator icon).

3. **Result:**
   - Material cost: calculated from BoM explosion (all components × costs).
   - Labor cost: average from the past completed MOs (total labor ÷ total qty).
   - Product's **Cost** is updated to: `(material + avg labor) / BoM qty`.
   - Chatter on product shows breakdown:
     - Material: 120.00 (from 5 components)
     - Labor: 8.50/unit (avg from 4 past MOs)
     - Old cost: 120.00 → New cost: 128.50

**Benefit:** Product cost now includes both materials (from BoM design) and labor (from actual production data). Use for pricing, profitability analysis, and accurate inventory valuation.

---

## Summary

| Use case | Main feature used |
|----------|-------------------|
| Custom assembly labor on MO | Timesheets tab + labor posting |
| Different rates per employee | Employee Hourly Cost |
| Extra labor beyond work centers | Timesheets tab alongside work orders |
| Check cost before closing | Timesheet Labor Cost on MO |
| Several workers/days on one MO | Multiple lines in Timesheets tab |
| Cost from product or amount | Product cost / line amount when no employee rate |
| Analyze by line/project | Analytic account on MO + reports |
| Update product cost from BoM + labor | BoM "Update Cost (Materials + Labor)" button |

For configuration and field locations, see the [User Guide](USER_GUIDE.md).
