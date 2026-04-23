# Testing guide — finished scope only

**Environment:** Odoo 19 Community  
**Staging / test database:** `trgulf_Mrp`  
**Last aligned with workspace:** April 2026  

This document covers **only** what is implemented and verified in scope. It does **not** include ZATCA / `l10n_sa_edi` (not installed) or deferred features (e.g. AML search filters for Task 1).

---

## Modules in scope

| Area | Module | Status |
|------|--------|--------|
| Task 1 — Journal line references | `gpc_account_move_line_reference_ext` | Installed |
| Task 2 — OCA financial reports account range | `account_financial_report` | Installed (GL / Open Items / Aged Partner wizards use string account-code bounds) |
| Task 6 — Invoice tier approval | `base_tier_validation` | Installed |
| Task 6 — Account moves | `account_move_tier_validation` | Installed |

---

## Task 1 — Journal line reference fields (`gpc_account_move_line_reference_ext`)

**What was built:** Three stored fields on `account.move.line`: `line_reference`, `line_reference_number`, `line_tax_number`. On the **invoice/move form**, they appear only for **Miscellaneous operations** (`move_type = entry`) on the **Journal Items** tab. Optional columns exist on the global **Journal Items** list view.  
**Not in scope:** Search filters on Journal Items for these fields are **disabled** in code (commented XML) — do not expect search/group-by until that is released.

### Tests

| ID | Scenario | Steps | Expected |
|----|----------|--------|----------|
| T1.1 | Columns on manual entry | Accounting → Journal Entries → create **Miscellaneous**; open **Journal Items** tab | **Line Reference**, **Reference Number**, **Tax Number** available (enable optional columns if hidden). |
| T1.2 | Hidden on customer invoice | Customer Invoice draft → **Journal Items** tab | Those three columns **not** shown on lines (entry-only). |
| T1.3 | Tax number from partner | On entry line: set partner with VAT, leave Tax Number empty, change field focus | **Tax Number** fills from partner VAT when blank. |
| T1.4 | No overwrite | Set **Tax Number** manually, then change partner | **Tax Number** stays as entered. |
| T1.5 | Persist | Post the misc entry, reopen | Values still present on lines. |
| T1.6 | Journal Items list | Accounting → **Journal Items** (if available); optional columns | Columns can be shown; values match line data. |

---

## Task 2 — OCA General Ledger (and related) From/To account range (`account_financial_report`)

**What was built:** Wizards (e.g. **General Ledger**, **Open Items**, **Aged Partner Balance**) use **string** account `code` bounds in `on_change` so the From/To range does not crash on Odoo 19 (no `int()` on account codes).

### Tests

| ID | Scenario | Steps | Expected |
|----|----------|--------|----------|
| T2.1 | General Ledger range | Open **General Ledger** wizard → set **Account code From** and **To** (numeric codes, valid order) | **Filter accounts** fills; **no** traceback. |
| T2.2 | Invalid range edge | Set From/To so range is empty or inverted (lexicographic) | **No** Python traceback; behaviour acceptable (empty or odd selection). |
| T2.3 | Other wizard | Repeat **From/To** change on **Open Items** or **Aged Partner Balance** | Same: **no** traceback on change. |
| T2.4 | Run report | Run General Ledger for a short date range | Report generates (PDF/HTML/XLSX per menu). |

---

## Task 6 — Customer invoice approval (`base_tier_validation` + `account_move_tier_validation`)

**What was built:** Tier validation on `account.move`; customer invoices can require validation before posting. Smoke-tested on `trgulf_Mrp`: request validation → waiting → approve → post.  
**Note:** `action_post()` passes `skip_validation_check` for field-level tier rules; **open validation** is still blocked by server checks on transition to posted — posting without approval must fail until tier is validated.

### Tests

| ID | Scenario | Steps | Expected |
|----|----------|--------|----------|
| T6.1 | Tier definition | Settings → Technical → **Tier Validations** → **Tier Definition**: model **Invoice** / `account.move`, domain for customer invoices (e.g. `out_invoice`), reviewer | Saves. |
| T6.2 | Request validation | Draft **customer invoice** matching domain → **Request Validation** (or equivalent) | Reviews created; status moves to waiting/pending as designed. |
| T6.3 | Block before approval | While validation not completed, attempt to **Post** / confirm | Posting **not** allowed (error or blocked). |
| T6.4 | Approve and post | Reviewer validates/approves tier → then **Post** | Invoice **posted**; `validation_status` **validated**. |
| T6.5 | Search filters (optional) | Invoices list: filters such as **Needs my Review**, **Validation status** (if shown) | Filters work without error. |

---

## Explicitly out of scope (not finished)

- **`l10n_sa_edi`** / ZATCA submit, CSID onboarding, EDI documents — module **not installed** on `trgulf_Mrp`.
- **`account_move_tier_validation_approver`** — not part of this guide.
- **AML search / filters** for Task 1 line reference fields — not deployed.

---

## Suggested run order

1. **Task 2** (read-only)  
2. **Task 1** (one misc entry)  
3. **Task 6** (tier + invoice)

---

## Document history

| Version | Note |
|---------|------|
| 1.0 | Finished-scope only: Tasks 1, 2, 6 approval; excludes ZATCA. |
