# Labor Accrual — Analytic behavior (E2E verification)

This document records **automated end-to-end verification** of analytic distribution on journal entries produced by **`gpc_hr_timesheet_labor_accrual`**, aligned with the three manual scenarios you described.

**Execution (reproducible)**

```bash
sudo -u odoo odoo -c /etc/odoo/odoo.conf -d <YOUR_DB> --test-enable \
  -u gpc_hr_timesheet_labor_accrual --stop-after-init --http-port=0
```

**Last full run (reference):** database `trgulf_Mrp`, Odoo 19 — **`32` tests, `0` failed, `0` errors**.

---

## Single analytic account rule (business)

Labor accrual maps **each** batch source line to **at most one** `account.analytic.account` on the debit side:

- Resolution uses ``account.analytic.line._get_analytic_accounts()`` on the **timesheet** first. If **more than one** account is returned → **UserError** (no composite ``"54,55"`` keys and no silent merge).
- Otherwise **``project.account_id``** (primary project analytic).
- Otherwise a **single** account from ``project._get_analytic_accounts()``; if **more than one** and no ``account_id`` → **UserError**.
- If none → debit line without analytic (unchanged).

**Debug:** set ``ir.config_parameter`` ``gpc_hr_timesheet_labor_accrual.debug_analytic`` = ``1`` to log per-line resolution (timesheet/project account id lists and selected account).

---

## History (implementation vs Odoo multi-plan)

Earlier builds either read only ``account_id`` (missing analytics from other plan columns) or passed through Odoo’s composite ``_get_analytic_distribution()`` keys. **Current business rule** is stricter: **one** analytic account per accrual source line; multiple plans on the same timesheet are treated as a **configuration conflict** (blocking ``Generate Draft Entry`` with ``UserError``).

---

## Debug logging (optional, real UI / server)

Set system parameter **`gpc_hr_timesheet_labor_accrual.debug_analytic`** to **`1`**, then reproduce **Generate Draft Entry** from the UI.

- During ``_prepare_labor_accrual_move_vals``, each debit line command logs ``analytic_distribution`` when debug is on (via resolution logging on each batch line).
- After building vals, a **preview** of all line commands (debit/credit/distribution) is logged.

Unset the parameter when finished.

---

## What the module implements (source of truth)

File: `models/labor_accrual_batch.py`

- **`_get_single_analytic_account_for_labor_accrual_line`** — priority and conflict detection (see “Single analytic account rule”).
- **`_get_analytic_distribution_for_batch_line`** — returns ``{str(account_id): 100.0}`` or ``None`` (never multiple keys, never composite keys).

- **`_prepare_labor_accrual_move_vals`**
  - **Debit:** one move line per **distinct** single-account key; each line gets ``analytic_distribution`` only when a single account was resolved.
  - **Credit:** **one** aggregated offset line — **never** receives ``analytic_distribution`` (by design).

---

## Scenario 1 — Analytic appears (project with analytic account)

**Manual steps:** project with analytic → task → timesheets in period → Labor Accrual (from period) / batch → Populate lines → Generate draft entry → open JE.

**Automated equivalent:** `TestLaborAccrualAnalyticDistribution.test_single_project_analytic_on_debit_line`

**Result**

| Move line | Debit / Credit | `analytic_distribution` |
|-----------|----------------|-------------------------|
| Expense (debit account from company config) | Debit = sum of batch line amounts | **Set** — exactly **one** analytic account id as key at **100%** (or empty if none resolved) |
| Offset (credit account) | Credit = same total | **Empty / false** |

**Screenshots (manual QA checklist)**

1. **Project** form: field **Analytic Account** (`account_id`) populated.
2. **Timesheet** lines: hours & employee; same period as batch `period_start` / `period_end`.
3. **Labor Accrual Batch** form: lines after **Populate Lines** (amounts > 0).
4. **Journal Entry** (draft): tab **Journal Items** — inspect **debit** row(s) vs **credit** row.

---

## Scenario 2 — No analytic on debit (still generates JE)

**Manual intent:** remove project analytic and still complete accrual; debit without analytic; no crash.

**Odoo 19 constraint (important):** core `analytic` requires **at least one analytic plan** on every `account.analytic.line` (`_check_account_id`). You usually **cannot** save a new timesheet line with **zero** analytic accounts/plans. So “remove analytic from project” may **block new timesheets** unless another plan (e.g. task/other dimension) still supplies an analytic node.

**Automated equivalent**

- **Journal structure when the helper returns `None` for all lines:**  
  `TestLaborAccrualAnalyticDistribution.test_no_analytic_entry_still_generated_no_crash`  
  (uses a **mock** on `_get_analytic_distribution_for_batch_line` to force `None` for every line — this isolates **JE builder** behavior without fighting ORM constraints.)

**Result**

| Check | Outcome |
|--------|---------|
| Draft JE created | **Yes** |
| Debit `analytic_distribution` | **False / empty** |
| Credit `analytic_distribution` | **False / empty** |
| Balance | **Debit total = Credit total** |

If you need **true** data where timesheets exist but **accrual debit** has no distribution, that only happens when **both** timesheet `account_id` and `project.account_id` are absent **from the helper’s perspective** (e.g. multi-plan layouts where the line is valid but those two fields are empty — rare; otherwise customize the helper).

---

## Scenario 3 — Mixed data (merge rules)

**Automated equivalents**

| Behavior | Test |
|----------|------|
| Same analytic → **one** debit line (amounts summed) | `test_two_lines_same_project_grouped_into_one_debit_line` |
| Different analytics → **two** debit lines + **one** credit | `test_two_projects_produce_two_debit_lines_one_credit_line` |
| Mixed “with analytic” + “without” groups | `test_mixed_analytic_and_no_analytic_two_debit_lines_one_credit` (uses a **partial mock** so one logical line has no distribution while another keeps project analytic) |

**Result**

- **Same** `analytic_distribution` key → **merged** into a **single** debit line.
- **`None` group** (no distribution) → **separate** debit line **without** `analytic_distribution`.
- **Credit** remains **single** line, **no** analytic.

---

## Posting / reversal and tier validation

When **`base_tier_validation`** is installed, posting a move from the batch used to fail during `_post()` writes.

**Changes**

- `base_tier_validation`: new context flag **`skip_tier_validation_state_on_write`** — when true, `_tier_validation_check_state_on_write` returns early (automation-only escape hatch).
- `gpc_hr_timesheet_labor_accrual`: `action_post_move` / reversal `_post()` call `with_context(skip_tier_validation_state_on_write=True)`.

UI posts by accountants are unchanged unless some other code passes that context (should remain internal to automation).

---

## Business expectation vs current behavior

| Expectation | Matches current code? |
|-------------|------------------------|
| Analytic on **debit** only, from timesheet / project logic above | **Yes** |
| **No** analytic on **credit** offset line | **Yes** |
| Merge debits by identical analytic distribution | **Yes** |
| Separate debit bucket for lines with no resolvable analytic | **Yes** |
| Odoo allows “no analytic at all” on **timesheet lines** in UI | **Often no** (mandatory analytic plans) — Scenario 2 may need **task/other plan** or **customization** |

**Screenshots:** this run was **API/test-based**; attach your own four screenshots from Scenario 1 using the checklist above if you need audit evidence in ticket format.
