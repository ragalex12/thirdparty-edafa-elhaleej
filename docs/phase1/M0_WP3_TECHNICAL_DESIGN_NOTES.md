# M0 / WP3 — Technical design notes (Phase 1 modules)

**Odoo target:** 19.0  
**Repository standards:** `/opt/localaddons/REPOSITORY_STANDARDS.md`  
**Naming:** `gpc_<area>_<feature>` (approved list below)

**Execution order (revised — backend first):** See **`docs/phase1/PHASE1_EXECUTION_PLAN.md`**.  
Implementation sequence: **M2 → M1 → M3** (Wave 1), then **M4 → M5 → M6** (Wave 2). **Full security groups matrix** is **deferred** to a **pre-UAT hardening** step (Wave 3) — it does **not** block backend work. Each module below still lists **minimum role assumptions** in §5 for design traceability.

| Design doc section | Milestone | Module technical name |
|--------------------|-----------|------------------------|
| Module B | **M2** | `gpc_account_gl_range_fix_local` |
| Module A | **M1** | `gpc_account_move_line_reference_ext` |
| Module C | **M3** | `gpc_report_analytic_project_statement` |
| Module D | **M4** | `gpc_hr_timesheet_labor_accrual` |
| Module E | **M5** | `gpc_stock_project_material_reclass` |
| Module F | **M6** | `gpc_account_invoice_approval_zatca_gate` |

This document is structured for **copy-paste into OpenProject** (one section per work package). Each module has **10 required fields**.

---

## Module A — `gpc_account_move_line_reference_ext`

| # | Field | Content |
|---|--------|---------|
| **1** | **Module technical name** | `gpc_account_move_line_reference_ext` |
| **2** | **Business purpose** | Enrich **journal item lines** with a stable, user-visible **reference / traceability** chain (e.g. link to source document number, batch, or external key) so finance and auditors can reconcile GL lines to operational documents without exporting raw SQL. |
| **3** | **Scope in Phase 1** | Add **stored or related fields** on `account.move.line` (and minimal wiring on `account.move` if needed for defaults). Optional **list/form column** for Accounting users. **No** change to posting logic or account determination in Phase 1 unless explicitly required for defaulting the new reference. |
| **4** | **Key models to extend** | `account.move.line` (primary); possibly `account.move` for computed display or `ref` sync rules. |
| **5** | **Key views / actions / security** | Inherited **tree/form** views for journal items (accounting); optional **search** filters. **Groups:** `account.group_account_readonly` / `account.group_account_invoice` as appropriate for visibility vs edit. |
| **6** | **Dependencies** | `account` (required). Optional: `analytic` if references tie to analytic documents; avoid hard dependency on `sale`/`purchase` unless cross-document linking is in scope. |
| **7** | **Main technical risks** | Performance if heavy `related`/`computed` fields on large journals; **reconciliation** widgets assuming specific line shapes; multi-company **check_company** on any new Many2one. |
| **8** | **Areas not to override deeply** | Do **not** override `account.move._post()`, `create()`/`write()` on `account.move` for posting, or core **matching/reconciliation** engines. Prefer **computed/related** fields and view extensions. |
| **9** | **Test scope** | Create posted entry → lines show expected reference; multi-company isolation; readonly user sees fields; upgrade does not drop columns (`store=True` migration). |
| **10** | **Migration / upgrade** | New stored columns require **module install/upgrade**; backfill script optional Phase 2. If `account` changes line API in future Odoo versions, retest inherited views. |

---

## Module B — `gpc_account_gl_range_fix_local`

| # | Field | Content |
|---|--------|---------|
| **1** | **Module technical name** | `gpc_account_gl_range_fix_local` |
| **2** | **Business purpose** | Provide a **local, controlled** adjustment for **General Ledger date/period range behaviour** (e.g. default fiscal range, domain constraints on reports, or company-specific cut-off rules) where standard Odoo or OCA reports misalign with **local operating practice** on this database. |
| **3** | **Scope in Phase 1** | Implement **minimal patch**: e.g. extended **domain** on a specific report wizard, **defaults** for date_from/date_to**, or a small **constraint** on allowed posting dates per journal type — **only** what is signed off in functional spec. **Explicitly local** = not pushed as generic OCA. |
| **4** | **Key models to extend** | Targeted: wizard models for GL reports (e.g. `account.report` helpers or OCA `account_financial_report` wizards if installed), or `res.company` / `account.fiscalyear` **read-only** helpers. **Avoid** touching core `account.move` date validation unless required. |
| **5** | **Key views / actions / security** | Inherit **wizard forms** for affected reports; optional **settings** on company (Accounting manager). **Groups:** accounting manager for config; readonly for report execution. |
| **6** | **Dependencies** | `account`. **Soft dependency** on `account_financial_report` / `date_range` if integration is scoped — declare in manifest only if features require them at install time. |
| **7** | **Main technical risks** | **Drift** when upgrading OCA financial reports; **double-fix** if both OCA and this module adjust the same domain; **fiscal year** edge cases (year-end). |
| **8** | **Areas not to override deeply** | Do **not** monkey-patch `fields.Date` or global **report rendering**; avoid overriding `account.move` `date` constraint globally. Prefer **wizard-level** domains and **company-specific** parameters. |
| **9** | **Test scope** | Matrix: fiscal year boundaries, period 12/13, multi-company; report output row counts vs baseline without module. |
| **10** | **Migration / upgrade** | Document **dependency versions** of OCA financial stack when upgrading; feature-flag company parameters to disable local fix quickly. |

---

## Module C — `gpc_report_analytic_project_statement`

| # | Field | Content |
|---|--------|---------|
| **1** | **Module technical name** | `gpc_report_analytic_project_statement` |
| **2** | **Business purpose** | Deliver a **project-oriented analytic statement** (PDF/XLSX): for a selected **project** (and date range), show **move lines / balances** with analytic distribution, suitable for **management review** and **customer or internal reporting**. |
| **3** | **Scope in Phase 1** | **One report** (wizard → PDF and/or XLSX using `report_xlsx` if available): filters = project, date range, company; output = **tabular statement** with opening, movement, closing **per analytic account** or per account as per spec. **No** full BI replacement. |
| **4** | **Key models to extend** | Read-heavy use of `account.move.line`, `account.analytic.line`, `project.project`; **transient** wizard model `gpc.project.statement.wizard` (or similar); **abstract** report model for data assembly. |
| **5** | **Key views / actions / security** | Wizard form + menu under **Accounting → Reporting** or **Project → Reporting**. **Groups:** project user for own projects; accounting for all companies. **Record rules:** respect project multi-company and analytic visibility. |
| **6** | **Dependencies** | `account`, `analytic`, `project`. Optional: `report_xlsx` for Excel export (recommended if already in repo). |
| **7** | **Main technical risks** | **Performance** on large analytic tables; **incorrect analytic_distribution** parsing (JSON in 17+); **currency** conversion if multi-currency projects. |
| **8** | **Areas not to override deeply** | Do **not** alter `account.move` posting or `analytic.line` create; **read-only** reporting module. No overrides of `mail.thread` on projects unless needed for distribution. |
| **9** | **Test scope** | Known project with fixed dataset → golden-file comparison of totals; empty project; multi-company forbidden access. |
| **10** | **Migration / upgrade** | If Odoo changes `analytic_distribution` format, adjust SQL/Python aggregation; version-gate in manifest. |

---

## Module D — `gpc_hr_timesheet_labor_accrual`

| # | Field | Content |
|---|--------|---------|
| **1** | **Module technical name** | `gpc_hr_timesheet_labor_accrual` |
| **2** | **Business purpose** | Automate **HR timesheet → payroll accrual** journal entries (or accrual **lines**) for **non-MO** or **HR-centric** labor: align with **labor clearing / WIP** logic where required, without duplicating `mrp_timesheet` MO workflows. |
| **3** | **Scope in Phase 1** | Define **when** accrual runs (on validate? on period close?), **accounts** (company or project level), and **per-line or batch** `account.move`. Integrate with **`hr_timesheet`** lines; **optional** bridge to `hr_payroll_community` **read-only** hooks. **Explicit boundary** with existing `mrp_timesheet` (no double posting for same line). |
| **4** | **Key models to extend** | `account.analytic.line` (timesheet), `res.company` (accrual accounts), possibly `hr.employee`; transient wizard for **manual accrual run** if needed. |
| **5** | **Key views / actions / security** | Company settings tab (Accounting manager); timesheet optional fields (HR officer). **Sudo** pattern for move creation with audit in `narration` (align with `REPOSITORY_STANDARDS` / internal security policy). |
| **6** | **Dependencies** | `hr_timesheet`, `account`. Soft: `hr_payroll_community`, `mrp_timesheet` — use **detection** (`module_installed`) to avoid duplicate JE rules. |
| **7** | **Main technical risks** | **Double posting** vs `mrp_timesheet` or payroll; **access rights** for workers creating moves; **period locking** vs draft timesheets. |
| **8** | **Areas not to override deeply** | Do **not** replace `hr_timesheet` validation pipeline entirely; avoid overriding `account.move` global `create` without `skip_*` guards; **no** deep override of payroll salary rules in Phase 1. |
| **9** | **Test scope** | Single employee, single period: accrual amount = expected; toggle modules on/off; reversal on correction. |
| **10** | **Migration / upgrade** | Data migration for historical timesheets optional Phase 2; version pin against `mrp_timesheet` to document interaction. |

---

## Module E — `gpc_stock_project_material_reclass`

| # | Field | Content |
|---|--------|---------|
| **1** | **Module technical name** | `gpc_stock_project_material_reclass` |
| **2** | **Business purpose** | Support **material reclassification** tied to **projects** (e.g. move stock value or quantity from one analytic/project bucket to another, or from generic stock to project WIP) with **traceable stock moves** and accounting alignment. |
| **3** | **Scope in Phase 1** | **One** guided flow: wizard or action from **project** or **picking** creating **internal moves** or **inventory adjustments** with **analytic/project** dimensions per spec. **No** full MRP refactor. |
| **4** | **Key models to extend** | `stock.move`, `stock.picking` (optional), `project.project`; transient wizard; possibly `stock.valuation.layer` **read** for reconciliation messages. |
| **5** | **Key views / actions / security** | Server action or menu under **Inventory** / **Project**. **Groups:** stock manager / accounting for valuation impact. |
| **6** | **Dependencies** | `stock`, `stock_account`, `project`. Analytic if project costing uses `analytic_distribution` on moves. |
| **7** | **Main technical risks** | **Valuation layers** mismatch; **anglo-saxon** vs continental; **multi-company** stock; **locked** periods. |
| **8** | **Areas not to override deeply** | Do **not** override `stock.move._action_done()` globally; prefer **wizard-created moves** with standard methods. Avoid custom valuation layer creation unless approved. |
| **9** | **Test scope** | Standard product category with valuation; project A → B reclass; accounting entry tie-out. |
| **10** | **Migration / upgrade** | Odoo stock valuation API changes between minors — retest `_action_done` and layer reads. |

---

## Module F — `gpc_account_invoice_approval_zatca_gate`

| # | Field | Content |
|---|--------|---------|
| **1** | **Module technical name** | `gpc_account_invoice_approval_zatca_gate` |
| **2** | **Business purpose** | Enforce an **internal approval step** on **customer invoices / credit notes** before they are allowed to proceed to **ZATCA e-invoicing** submission (or before the technical ZATCA integration marks them as “ready”). Reduces rejected submissions and ensures **segregation of duties**. |
| **3** | **Scope in Phase 1** | Add **state or boolean** gate: e.g. `gpc_zatca_ready` / approval flag; **constraint** blocking ZATCA send (or blocking “confirm to ZATCA” action) until **approved by group**. Integrate with existing **Saudi/ZATCA** module if present via **inherited** methods or **constraint** on the send button visibility. |
| **4** | **Key models to extend** | `account.move` (`move_type` in `out_invoice`, `out_refund`); possibly `account.payment` if out of scope for Phase 1 — **exclude** unless spec says otherwise. |
| **5** | **Key views / actions / security** | Invoice form: approval button, chatter messages, **statusbar** optional. **Groups:** `gpc.group_invoice_zatca_approver` (new). Hide/postpone ZATCA server actions until approved. |
| **6** | **Dependencies** | `account`. **Soft dependency:** enterprise or community ZATCA module — use `_check_module` / manifest optional `auto_install` = False; code paths if `l10n_sa` / ZATCA addon installed. |
| **7** | **Main technical risks** | **Double blocking** if ZATCA module also validates; **refund** flows; **portal** invoice upload; **EDI** timing. |
| **8** | **Areas not to override deeply** | Do **not** patch `account.move._post()` globally for all move types; scope to **customer invoices** only. Avoid overriding **cryptographic signing** in ZATCA libraries — only **workflow** before call. |
| **9** | **Test scope** | Draft → approve → ZATCA action allowed; without approval, action blocked; multi-company approvers. |
| **10** | **Migration / upgrade** | When ZATCA addon upgrades, re-verify **xpath** on button views and external method names; feature flag to disable gate in emergency. |

---

## Cross-cutting checklist (all Phase 1 modules)

| Item | Standard |
|------|----------|
| **Manifest version** | `19.0.x.y` per `REPOSITORY_STANDARDS.md` |
| **License** | Align with repo policy (e.g. LGPL-3 / OEEL as applicable) |
| **i18n** | `i18n/` for EN + AR if UI exposed to KSA users |
| **Security (Wave 1–2)** | Minimum access: `ir.model.access.csv` for new models; use **standard Odoo groups** on views (`groups="..."`) per §5 in each module. **Custom groups + full matrix:** **Wave 3** (pre-UAT) per `PHASE1_EXECUTION_PLAN.md`. |

---

## OpenProject usage

- Attach this file to the **M0 / WP3** work package, **or** split each **Module A–F** section into a child work package description field.

**End of M0 / WP3 technical design notes.**
