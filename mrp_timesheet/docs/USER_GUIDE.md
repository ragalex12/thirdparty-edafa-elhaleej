# Manufacturing Timesheet – User Guide

This guide explains how to configure and use the **Manufacturing Timesheet** module to log time on Manufacturing Orders and have that time affect production cost.

---

## 1. Prerequisites

- **Manufacturing** app installed (for Manufacturing Orders).
- **Timesheets** (or **HR Timesheet**) app installed.
- **Accounting** and **Inventory** with automatic valuation (so **Stock Journal** and valuation accounts are available).

---

## 2. Configuration

### 2.1 Production labor expense account

This account is **credited** when timesheet labor cost is posted (inventory is debited).

1. Go to **Settings**.
2. Open **Companies** and select your company.
3. Find **Production Labor Expense Account** (near **Currency** / **Stock Journal**).
4. Select an **expense** account (e.g. “Production labor”, “WIP labor”, or a dedicated cost account). Create one in **Accounting → Configuration → Chart of Accounts** if needed.

Without this, the module cannot post the labor journal entry when you mark an MO as done.

### 2.2 Stock journal

The labor journal entry uses the same **Stock Journal** as inventory valuation.

1. In **Settings → Companies**, set **Stock Journal** (or set it per product category if your setup uses that).
2. If you use the **Company Stock Journal (UI)** addon, the field is on the company form.

### 2.3 Employee hourly cost (optional but recommended)

The module adds **Hourly Cost** on the employee form (Odoo Community does not include it by default).

1. Go to **Employees**.
2. Open an employee.
3. Find **Hourly Cost** (after **Job Position**). Enter the cost per hour in company currency (e.g. 25.00).
4. Save.

This rate is used for timesheet lines linked to that employee when computing labor cost. If you leave it empty, the system uses the timesheet line’s **Product** cost or **Amount** when available.

### 2.4 Analytic account on the MO (optional)

To use the **Timesheets** tab and link lines to the MO:

1. In **Accounting**, create an **Analytic Account** (e.g. “Manufacturing” or per project).
2. On the Manufacturing Order, set **Analytic Account** (shown after **Product**). You can leave it empty if you only use work-center operations and do not use the timesheet tab.

---

## 3. Daily use

### 3.1 Updating product cost from BoM (Materials + Labor)

This feature calculates and updates a product's `standard_price` based on its Bill of Materials plus average labor from past completed MOs.

1. Go to **Manufacturing → Configuration → Bills of Materials**.
2. Open a BoM.
3. Click **"Update Cost (Materials + Labor)"** button (top-right, calculator icon).
4. The system:
   - Explodes the BoM to get all raw material costs.
   - Queries past completed MOs for that product to get average timesheet labor per unit.
   - Calculates: `Cost per unit = (total materials + avg labor) / BoM quantity`
   - Updates the product's **Cost** field.
   - Posts a message to the product with the breakdown.
5. Check the product form (**Products → Products → [Product]**) to see the updated **Cost**.
6. Check the product's **Chatter** to see the detailed breakdown (material components, labor average, old vs new cost).

**When to use:**
- After you've completed several MOs with timesheet data and want to update the product's standard cost to reflect real production cost (materials + labor).
- Before quoting or pricing: ensure the product cost includes both materials and labor.

**Note:** If no past MOs exist with timesheet labor, the cost will be materials only (labor = 0).

### 3.2 Logging time on a Manufacturing Order

1. Open **Manufacturing → Operations → Manufacturing Orders** and open an MO (or create one).
2. Set **Analytic Account** if you want to use the Timesheets tab.
3. Open the **Timesheets** tab.
4. Click **Add a line** (or use the editable list):
   - **Date**: day worked.
   - **User**: filled by default; change if needed.
   - **Employee**: select the employee (used for **Hourly Cost**).
   - **Description**: short note (e.g. “Assembly”, “Quality check”).
   - **Hours**: time spent (e.g. 2.5).
5. Save. You can add more lines for the same or other days/employees.

**Timesheet Labor Cost** (on the MO form) updates automatically: it is the sum of (hours × hourly cost) per line (or line amount if set).

### 3.3 Completing the order and posting labor cost

1. When the order is ready, click **Mark as Done** (or **Produce All** as in your flow).
2. The system:
   - Completes the MO and posts standard inventory moves/valuation.
   - If there are timesheet lines with a positive labor cost and labor has not been posted yet, it creates **one** journal entry:
     - **Debit**: Stock Valuation account (of the finished product’s category).
     - **Credit**: Production Labor Expense Account.
3. Labor is posted only **once** per MO. The link to the journal entry appears on the MO (**Timesheet Labor Journal Entry**).

### 3.4 Checking labor cost and accounting

- On the MO: **Timesheet Labor Cost** shows the total labor from timesheets; **Timesheet Labor Journal Entry** opens the posted move.
- In **Accounting**: find the journal entry by reference (e.g. “MO WH-MO00042 – Timesheet labor”) or via the link on the MO.

---

## 4. Where to find what

| What | Where |
|------|--------|
| Production Labor Expense Account | Settings → Companies → [Company] |
| Stock Journal | Settings → Companies → [Company] (or product category) |
| Hourly Cost (employee) | Employees → [Employee] → after Job Position |
| Analytic Account (per MO) | Manufacturing Order form → after Product |
| Timesheets tab | Manufacturing Order form → “Timesheets” tab |
| Timesheet Labor Cost | Manufacturing Order form → near Analytic Account |
| Timesheet Labor Journal Entry | Manufacturing Order form → link to the posted move |

---

## 5. Tips

- Set **Hourly Cost** for all employees who log time on MOs so labor cost is accurate.
- Use a **dedicated analytic account** per project or production line to analyze time and cost by MO.
- Labor is posted when you **Mark as Done**. To correct or re-post, you would need to reverse the labor move and reset the MO (or handle corrections in accounting); the module does not allow posting labor twice on the same MO.
- If you use **work orders** with work center costing, that cost is separate; this module adds **additional** cost from the **Timesheets** tab (e.g. for non-routed labor or overtime).

---

## 6. Troubleshooting

| Problem | What to check |
|---------|----------------|
| “Please set the Production labor expense account…” | Set **Production Labor Expense Account** on the company. |
| “No Stock Journal configured…” | Set **Stock Journal** on the company (or category). |
| “The product category … has no Stock Valuation Account” | Set **Stock Valuation Account** on the finished product’s category (Inventory valuation). |
| Timesheet Labor Cost is 0 | Ensure **Hourly Cost** is set on the employee (or **Amount** / **Product** on the line). |
| Labor not posted | Ensure the MO was **Marked as Done** and that **Timesheet Labor Cost** &gt; 0 before marking done. Labor is only posted once per MO. |
