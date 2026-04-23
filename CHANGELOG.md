# Local Addons – Changelog & Project Summary

**Author:** Sabry Youssef  
**Workspace:** /opt/localaddons  
**Date:** January 2026

This document summarizes the custom Odoo modules and changes added to this workspace, notably the fix for the Manufacturing Order “Produce All” journal error and the Company Stock Journal UI.

---

## 1. stock_account_journal_fix (Odoo 19)

**Purpose:** Fix `ValidationError: Missing required value for field 'Journal' (journal_id)` when clicking **Produce All** on a Manufacturing Order (or completing any valued stock move).

### Root cause (documented)
- `stock_account`’s `stock.move._create_account_move()` uses only `company_id.account_stock_journal_id` for `journal_id`.
- If the company has no **Stock Journal** set, `account.move.create` receives `journal_id=False` and raises.
- Product category **Stock Journal** (e.g. “Manufacturing Valuation”) was not used by this code path.

### What was implemented
- **Override** `stock.move._create_account_move()` to resolve the journal in this order:
  1. Product category `property_stock_journal` (for the move’s company)
  2. Company-dependent fallback for that category
  3. Company `account_stock_journal_id`
- If no journal is found, raise a clear **UserError** with company name.
- **Debug mode:** Optional interception of `account.move.create` when `journal_id` is missing (system parameters `stock_account_journal_fix.debug` and `stock_account_journal_fix.debug_raise`).

### Files
- `__manifest__.py`, `__init__.py`
- `models/account_move.py` – debug hook
- `models/stock_move.py` – journal resolution and `_create_account_move` override
- `MO_JOURNAL_DIAGNOSIS.md` – diagnosis, code path, SQL queries, config checklist
- `README.md` – usage and debug
- `tests/` – unit tests for journal resolution and account move creation

### Version
- Target: **Odoo 19** Community.

---

## 2. company_stock_journal_ui (Odoo 19)

**Purpose:** Expose the company **Stock Journal** field (`account_stock_journal_id`) on the company form so users can set it without Studio or code.

### Why
- The field exists on `res.company` (from `stock_account`) but was not visible on the company form in standard Community.
- Without it set, MO Produce All (and other stock valuation moves) trigger the missing `journal_id` error.

### What was implemented
- **Inherited view** of `base.view_company_form` (res.company form).
- **Field** `account_stock_journal_id` added after **Currency** on the General Information tab.
- Label: “Stock Journal”; help text for inventory valuation.
- Domain: journals of the current company, type **General**.
- **Access:** `groups="base.group_system"` (Settings only).
- No new menu or action; field appears under **Settings → Companies → [Company]**.

### Files
- `__manifest__.py`, `__init__.py`
- `views/res_company_view.xml` – view inheritance
- `README.md` – install and verify

### Version
- Target: **Odoo 19** Community; compatible with Odoo 18.

---

## Recommended usage

1. **Install** `company_stock_journal_ui` so the Stock Journal is visible on the company form.
2. **Set** Stock Journal per company: **Settings → Companies → [Company] → Stock Journal** (e.g. “Miscellaneous” or a dedicated “Stock Valuation” journal).
3. **Optional:** Install `stock_account_journal_fix` if you want journal resolution from product category when company journal is not set, or to use the debug mode for missing `journal_id`.

---

## Verification (MO Produce All)

1. Ensure **Stock Journal** is set on the company (via company form or `stock_account_journal_fix`).
2. Open a Manufacturing Order and click **Produce All** (or Mark as Done).
3. A journal entry should be created and the “Missing required value for field 'Journal' (journal_id)” error should no longer appear.

---

## M0 / WP2 — Repository standards (2026-04)

Canonical conventions for module layout, naming (`gpc_*` prefix for new first-party code), Git branches, and manifest versioning are documented in **`REPOSITORY_STANDARDS.md`** at the root of this repository. New Phase 1 modules should follow that file.

---

## M0 — Phase 1 execution order revised (2026-04)

Backend-first implementation: **M2 → M1 → M3**, then **M4 → M5 → M6**. The **full security groups matrix** is deferred to a **pre-UAT hardening** step (not the next milestone after M0). See **`docs/phase1/PHASE1_EXECUTION_PLAN.md`**. OpenProject update instructions: **`openproject_outputs/M0_EXECUTION_ORDER_REVISED.md`**.

---

*Document maintained in the workspace root. Author: Sabry Youssef.*
