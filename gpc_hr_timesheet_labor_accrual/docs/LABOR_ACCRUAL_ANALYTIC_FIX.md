# Labor Accrual — Analytic Distribution Fix

**Module:** `gpc_hr_timesheet_labor_accrual`  
**Version:** `19.0.1.0.5`  
**Primary file:** `models/labor_accrual_batch.py`

This document describes the analytic-distribution fix for labor accrual journal entries: what was wrong, what changed, and how to verify it.

---

## Problem (before)

When generating a draft journal entry from a labor accrual batch, **debit lines** often had an **empty Analytic Distribution** column on the Journal Entry form, even though related timesheets or projects had analytics configured.

Root causes:

1. **Single-account-only logic** — Resolution tried to pick one `account.analytic.account` (via `_get_analytic_accounts()` or `project.account_id`). If more than one account was found, the code raised `UserError` or dropped analytics instead of using Odoo’s full distribution.
2. **Ignored `analytic_distribution` JSON** — When plan-column helpers returned nothing useful, the stored/computed `analytic_distribution` field on timesheets was not always read.
3. **Collapsed to `{id: 100}`** — Multi-plan layouts (composite keys like `"247,248": 100`) were not passed through to `account.move.line`.
4. **Empty keys from Odoo helpers** — `_get_analytic_distribution()` could return `{"": 100}` when no plan was set; treating that as valid left a non-empty dict that still produced **no visible** analytic tag in the UI.
5. **One debit line for the whole batch** — Even when batch lines had different analytics, amounts were sometimes rolled into a single “batch total” debit with no distribution.

**Credit (WIP/offset) lines** were already correct: no analytic on the credit side by design.

---

## Solution (after)

### Business behavior

| Area | Behavior |
|------|----------|
| **Resolution** | Each batch line gets the **full** `analytic_distribution` dict from its timesheet, or from the project if the timesheet has none. |
| **Debit JE lines** | One debit move line per **distinct** analytic distribution (amounts summed per group). Same project + same distribution → **one** debit; same project + **different** distributions → **multiple** debits. |
| **Credit JE line** | Still **one** aggregated offset line with **no** `analytic_distribution`. |
| **Multi-plan / composite keys** | Preserved (e.g. `{"247,248": 100.0}`) when that is what Odoo stores on the source record. |
| **No analytic** | Batch lines with no resolvable distribution form a separate debit group **without** `analytic_distribution`; entry still posts as balanced. |
| **Conflicts** | No longer blocks on “more than one analytic account” at accrual time; grouping uses the full distribution as the key. |

### Resolution priority (`_read_analytic_distribution_from_record`)

For a timesheet or project record:

1. **`analytic_distribution`** field (JSON), if present and non-empty after normalization.
2. **`_get_analytic_distribution()`** (Odoo native, all plans).
3. **`_get_analytic_accounts()`** → composite key via `_get_distribution_key()` or comma-separated account ids → `{key: 100.0}`.

Batch line helper **`_get_analytic_distribution_for_batch_line`**:

- Timesheet first → if empty, project fallback.
- Optional debug logging when `gpc_hr_timesheet_labor_accrual.debug_analytic` = `1`.

### Journal entry build (`_prepare_labor_accrual_move_vals`)

1. Loop all `labor.accrual.batch` lines.
2. Resolve `dist` per line.
3. **Group key:** `tuple(sorted(dist.items()))` if `dist` else `None`.
4. Sum `batch_line.amount` per group; currency-round; last group absorbs rounding so **Σ debit = credit**.
5. Emit one `(0, 0, debit_line_vals)` per group with `analytic_distribution=dist` when set.
6. Append one credit line (no analytic).

---

## Code changes (summary)

| Method | Role |
|--------|------|
| `_normalize_analytic_distribution` | Copy dict, skip `None`/blank keys, coerce keys to `str` and values to `float`. Fixes `{"": 100}`. |
| `_distribution_from_plan_accounts` | Build composite-key distribution from plan columns when JSON/helpers are empty. |
| `_read_analytic_distribution_from_record` | Unified read path (field → `_get_analytic_distribution` → plan accounts). |
| `_get_analytic_distribution_for_batch_line` | Timesheet then project; replaces old single-account helper. |
| `_prepare_labor_accrual_move_vals` | Groups by full distribution; multiple debit lines; credit unchanged. |
| `_labor_accrual_log_analytic_resolution` | Debug logs per batch line when debug parameter is on. |

**Removed / superseded:** `_get_single_analytic_account_for_labor_accrual_line` and related `UserError` on multiple accounts.

---

## Example (verified on `trgulf_Mrp`)

Demo script: `scripts/demo_labor_accrual_multi_analytic_verify.py`

- One project, two timesheets, two analytic accounts.
- Batch: `LAB ACCR DEMO MULTI ANALYTIC`
- Draft JE (move id example: **372**):

| Line | Debit | Credit | Analytic distribution |
|------|-------|--------|------------------------|
| Labor accrual expense | 200.00 | 0.00 | `{'247,248': 100.0}` (composite) |
| Labor accrual expense | 100.00 | 0.00 | `{'247': 100.0}` |
| Labor accrual offset (WIP) | 0.00 | 300.00 | *(empty)* |

UI screenshot (Playwright):  
`gpc_worker_timesheet_labor_accrual_bridge/e2e/screenshots/labor-accrual-multi-analytic/03-journal-items-multi-analytic-debit-lines.png`

---

## Automated tests

File: `tests/test_labor_accrual.py` — class `TestLaborAccrualAnalyticDistribution`

| Test | Asserts |
|------|---------|
| `test_normalize_analytic_distribution_preserves_multi_key` | Multiple single-account keys kept. |
| `test_normalize_analytic_distribution_preserves_composite_key` | `"id1,id2"` composite key kept. |
| `test_debit_line_uses_timesheet_analytic_distribution_json_when_plans_cleared` | JSON on timesheet used when plans empty. |
| `test_timesheet_two_analytic_accounts_returns_full_distribution` | Two accounts → full dist, not forced to one id. |
| `test_single_project_analytic_on_debit_line` | Debit has analytic; credit does not. |
| `test_no_analytic_entry_still_generated_no_crash` | All `None` → JE still balanced (mocked). |
| `test_two_lines_same_project_same_analytic_grouped_one_debit` | Same dist → one debit. |
| `test_same_project_different_analytic_two_debit_lines` | Same project, different dist → two debits, one credit. |
| `test_mixed_analytic_and_no_analytic_two_debit_lines_one_credit` | With/without analytic → two debit groups. |
| `test_debit_always_equals_credit_multi_project` | Rounding: total debit = total credit. |

Run:

```bash
odoo -c /etc/odoo/odoo.conf -d trgulf_Mrp -u gpc_hr_timesheet_labor_accrual \
  --test-enable --test-tags=/gpc_hr_timesheet_labor_accrual --stop-after-init --http-port=0
```

---

## Playwright E2E (UI proof)

Location: `gpc_worker_timesheet_labor_accrual_bridge/e2e/`

| Asset | Purpose |
|-------|---------|
| `scripts/demo_labor_accrual_multi_analytic_verify.py` | Creates batch + JE; writes `e2e/.last-multi-analytic-move-id.txt` |
| `tests/labor-accrual-multi-analytic-screenshot.spec.ts` | Opens batch → JE → Journal Items; captures PNGs |
| `npm run test:multi-analytic` | Runs the spec |

```bash
odoo shell -c /etc/odoo/odoo.conf -d trgulf_Mrp \
  < /opt/localaddons/gpc_hr_timesheet_labor_accrual/scripts/demo_labor_accrual_multi_analytic_verify.py

cd /opt/localaddons/gpc_worker_timesheet_labor_accrual_bridge/e2e
GCC_ODOO_WEB_URL=http://127.0.0.1:8069 npm run test:multi-analytic
```

Screenshots directory: `e2e/screenshots/labor-accrual-multi-analytic/`

### Five projects → five analytic accounts (UI)

**Scenario:** Five different timesheet lines on **five different projects**, each project with its own analytic account → after **Populate lines** and **Generate draft entry**, the JE has **five debit lines**, each with a **different** analytic distribution, and **one** credit line without analytic.

Demo script: `scripts/demo_labor_accrual_five_projects_verify.py`  
Batch name: `LAB ACCR DEMO FIVE PROJECTS`

```bash
odoo shell -c /etc/odoo/odoo.conf -d trgulf_Mrp \
  < /opt/localaddons/gpc_hr_timesheet_labor_accrual/scripts/demo_labor_accrual_five_projects_verify.py

cd /opt/localaddons/gpc_worker_timesheet_labor_accrual_bridge/e2e
GCC_ODOO_WEB_URL=http://127.0.0.1:8069 npm run test:five-projects
```

Key screenshot: `e2e/screenshots/labor-accrual-five-projects/03-journal-items-five-analytic-debit-lines.png`

---

## Debug logging

Set system parameter **`gpc_hr_timesheet_labor_accrual.debug_analytic`** = **`1`**.

Logs include, per batch line and per debit group:

- `timesheet_id`, `project_id`, resolved `analytic_distribution`, source (`timesheet` / `project` / `none`)
- Plan account ids from `_get_analytic_accounts()`
- Draft JE debit line vals before create

Unset when finished.

---

## Related fixes (same release cycle)

### Tier validation on automated post

Posting from the batch could fail when `base_tier_validation` blocked state writes on `account.move`.

- **`base_tier_validation`:** context flag `skip_tier_validation_state_on_write` skips tier state checks for automation.
- **`gpc_hr_timesheet_labor_accrual`:** `action_post_move` / reversal `_post()` use that context.

### Bridge module (`gpc_worker_timesheet_labor_accrual_bridge`)

- Populates batch lines from worker timesheets (`include_in_payroll`, etc.).
- Amount fallback via `employee.hourly_cost` when `labor_cost` is zero so populate/generate tests have non-zero amounts.

---

## Upgrade

```bash
odoo -c /etc/odoo/odoo.conf -d <DB> -u gpc_hr_timesheet_labor_accrual --stop-after-init
```

On staging (`gpc.odoo.com.se`), upgrade the same module on `trgulf_Mrp` (or target DB) before re-running demos or Playwright against that environment.

---

## Notes / pitfalls

- **Period uniqueness:** Only one active batch per company + `period_key`. Multi-analytic demo uses `period_key = MULTI-YYYYMMDD` to avoid clashing with `LAB ACCR DEMO VERIFY 2026-05`.
- **Odoo shell and `__file__`:** Demo scripts use a fixed path for the Playwright move-id file (`/opt/localaddons/.../e2e`) because `odoo shell` does not define `__file__`.
- **Timesheets without analytics:** Core Odoo often requires at least one analytic plan on `account.analytic.line`; “no analytic” debit lines are still supported when resolution returns `None` (see mixed test with mock).
- **Composite vs separate keys:** Two timesheets with accounts A and B may produce one line with key `"A,B"` (Odoo composite) and another with `{"A": 100}` — both are valid; grouping is by the **exact** distribution dict.

---

## Document history

| Date | Change |
|------|--------|
| 2026-05 | `19.0.1.0.5` — Full `analytic_distribution` resolution and debit grouping by distribution. |
| Earlier | `19.0.1.0.4` — First pass: read timesheet JSON; still single-account oriented. |
| Earlier | Empty debit analytics when batch lines had no resolved account. |

For older E2E notes that described a **single analytic account** rule, see `LABOR_ACCRUAL_ANALYTIC_E2E_RESULTS.md` — that file predates `19.0.1.0.5` and should be read together with this document; **this file is the authoritative fix description** for current behavior.
