# Repository & module standards — Odoo 19 (M0 / WP2)

**Status:** Active from M0 WP2 onward  
**Odoo target:** 19.0.x (see server `odoo --version`)  
**Primary addons path:** `/opt/localaddons` (configured in `/etc/odoo/odoo.conf`)

This document defines **where new Phase 1 modules live**, **how they are named**, **git layout**, **branches**, and **manifest versions** for a **single delivery stream** with **multiple related modules**.

---

## 1. Current layout (as-is)

| Observation | Detail |
|-------------|--------|
| **Structure** | Single directory `/opt/localaddons` on `addons_path` — **flat** list of installable addon folders (each with `__manifest__.py`). |
| **VCS** | Git repository at `/opt/localaddons` (`.git` present) — **monorepo** style. |
| **Mixed content** | Third-party / OCA copies (`date_range`, `report_xlsx`, …), partner/vendor modules (`itech_*`, `ohrms_*`, `base_accounting_kit`), and **first-party** modules (`mrp_timesheet`, `workers_*`, `company_*`, …) coexist **without** a single name prefix. |
| **Non-Odoo assets** | Scripts and docs (`openproject_*`, `archived_scripts`, `.env`) live **beside** addons — they are **not** loaded by Odoo but clutter the repo root. |
| **Risk** | No namespace separation makes it unclear which directories are **owned** by this project vs vendored OCA vs legacy vendor drops. |

---

## 2. Recommended standard (going forward)

### 2.1 Where Phase 1 modules should live

**Default (recommended — no server config change):**

- New first-party modules for **Phase 1** are added as **new sibling directories** directly under `/opt/localaddons/`, using the **technical naming convention** in §2.2.

**Optional grouping (if you want a physical “stream” folder):**

1. Create `/opt/localaddons/gpc_phase1/` (or `elkhaleej_phase1/`).
2. Place each new addon as a **direct child**: `/opt/localaddons/gpc_phase1/<module_technical_name>/`.
3. **Append** that path to Odoo `addons_path` in `/etc/odoo/odoo.conf`, e.g.  
   `addons_path = ... ,/opt/localaddons,/opt/localaddons/gpc_phase1`
4. Restart Odoo.

**Rule:** Odoo only discovers addons that are **top-level** under an entry in `addons_path`. Nested `gpc_phase1/subfolder/module` without its own manifest at the right depth will **not** load.

**For this project:** use the **default** (flat under `/opt/localaddons`) unless you explicitly need a separate path for CI or permissions — keeps operations simple.

---

### 2.2 Module technical naming convention

| Rule | Specification |
|------|-----------------|
| **Pattern** | `<project_prefix>_<area>_<feature>` |
| **Project prefix** | **`gpc_`** — reserved for first-party code delivered under this stream (aligns with `gpc.odoo.com.se`). If the business standardizes another prefix (e.g. `elkhaleej_`), replace consistently in **new** modules only. |
| **Area** | Short domain: `account`, `mrp`, `stock`, `hr`, `project`, `report`, `integration`, … |
| **Feature** | `snake_case`, no abbreviations unless documented in module README. |
| **Folder name** | **Must equal** the technical name (Python package / `import` name). |
| **Examples** | `gpc_mrp_labor_clearing`, `gpc_account_analytic_bridge`, `gpc_stock_valuation_notify` |

**`__manifest__.py` → `'name'`:** User-facing English (or bilingual) title, e.g. *“GPC – MRP Labor Clearing”*.

**Do not** reuse generic names (`timesheet`, `custom1`) without prefix — they collide with OCA and other vendors.

---

### 2.3 Repository structure (monorepo)

Keep **one Git repo** at `/opt/localaddons` for this environment, with **logical** separation:

```
/opt/localaddons/
  REPOSITORY_STANDARDS.md     ← this file (source of truth)
  CHANGELOG.md
  .gitignore
  # First-party Phase 1+ (gpc_* recommended)
  gpc_*/
  mrp_timesheet/            # legacy first-party; keep until renamed with migration
  workers_*/
  # Third-party / OCA vendored (prefer git submodule or documented commit SHA)
  date_range/
  report_xlsx/
  ...
  # Tooling only (not Odoo addons — do not add __manifest__ here)
  tools/                      # recommended: move openproject_* + scripts here in a later cleanup
  archived_scripts/
```

**OCA / third-party:**

- Prefer **git submodule** pointing to official OCA branch `19.0`, **or** a vendor fork with tag — record the **commit SHA** in `CHANGELOG.md` when upgrading.
- Avoid unlabeled copies that drift from upstream.

**Non-Odoo files:** Prefer `tools/`, `docs/project/`, or `archived_scripts/` so the root lists **mostly** installable addons.

---

### 2.4 Git branch naming convention

| Branch type | Pattern | Example |
|-------------|---------|---------|
| **Main integration line (Odoo 19)** | `19.0` | `19.0` — production-aligned code for this server |
| **Feature / WP** | `19.0/feature/<short-id>-<slug>` | `19.0/feature/m0-wp2-repo-standards` |
| **Hotfix** | `19.0/hotfix/<ticket>-<slug>` | `19.0/hotfix/142-labor-je-rounding` |
| **Release tag (optional)** | `v<manifest-series>+<build>` or date | `v19.0.1.0+20260409` |

**Rules:**

- **Never** commit directly to `19.0` without review if team > 1.
- Merge features **into** `19.0` after upgrade test on a staging DB.

---

### 2.5 Manifest versioning convention (`version` in `__manifest__.py`)

Align with **Odoo series** + **module lifecycle**:

| Field | Format | Meaning |
|-------|--------|---------|
| **Series** | `19.0` | Must match server Odoo major.minor. |
| **Release** | `19.0.<major>.<minor>` | **Major:** breaking DB/API change for this module. **Minor:** additive features, fixes. |

**Recommended for Phase 1:**

```text
19.0.<phase>.<patch>
```

Examples:

- `19.0.1.0` — first stable drop of Phase 1 module A  
- `19.0.1.1` — bugfix / translation / small UI change, same DB schema  
- `19.0.2.0` — new fields or behavior requiring upgrade script  

**Bump `version`** on **every** change that is deployed (triggers upgrade awareness).

**Do not** use unrelated schemes (e.g. `1.0` alone) — they break Odoo upgrade ordering and team communication.

---

## 3. Conflicts with the current `/opt/localaddons` layout

| Conflict | Impact | Mitigation |
|----------|--------|------------|
| **Flat mix of vendors** | Hard to see “our” code | New work uses **`gpc_` prefix**; document OCA SHAs in CHANGELOG. |
| **`openproject_*` next to addons** | Noise; risk of accidental packaging | Move to `tools/openproject_*` in a scheduled cleanup (no Odoo change). |
| **Duplicate UI stacks** | `ica_web_responsive` vs `web_responsive` (OCA) | Install **one** responsive stack; remove unused from DB and repo when safe. |
| **`dbfilter_from_header` @ 18.0** | Wrong series for Odoo 19 | Upgrade to 19.0 branch or remove from `addons_path`. |
| **Legacy names** (`itech_*`, `workers_*`) | Inconsistent with `gpc_` | **Do not mass-rename** without migration scripts; new modules follow `gpc_`. |

---

## 4. Summary — use this for the project going forward

| Topic | Decision |
|-------|----------|
| **Location** | New Phase 1 modules: **`/opt/localaddons/<technical_name>/`** (flat). Optional: separate `addons_path` subdir if needed. |
| **Technical name** | **`gpc_<area>_<feature>`** (snake_case, folder = module name). |
| **Repository** | **Single monorepo** at `/opt/localaddons`; OCA as submodule or pinned copy; tooling under `tools/` over time. |
| **Branches** | **`19.0`** mainline; features **`19.0/feature/...`**; hotfixes **`19.0/hotfix/...`**. |
| **Manifest version** | **`19.0.<major>.<minor>`** (e.g. `19.0.1.0`), bump on each deployable change. |

**Owner:** Update `CHANGELOG.md` when adding modules or bumping OCA pins.

---

## 5. Applied in this workspace

- This file is the **canonical** reference for M0 WP2.  
- No existing module directories were renamed (avoids breaking installs).  
- New Phase 1 deliverables **must** follow §2 unless an exception is recorded in `CHANGELOG.md`.
