# Phase 1 — Execution plan (revised)

**Effective:** Backend-first; security matrix deferred  
**Foundation (complete):** M0 WP1 (Odoo/OCA baseline), M0 WP2 (repository standards), M0 WP3 (technical design notes)

---

## 1. Guiding principles

| Principle | Decision |
|-----------|----------|
| **Implementation order** | **Backend-first:** models, business logic, minimal views, automated tests — before UI polish and before the **full security groups matrix**. |
| **Security** | Each module still documents **minimum roles / permission assumptions** during design (see §3). **Full permission hardening** (cross-module matrix, least-privilege review) is a **single later gate** before UAT / production — **does not block** backend delivery. |
| **Dependencies** | Respect technical dependencies between modules (e.g. reports may assume GL range behaviour is stable). |

---

## 2. Revised milestone order

### Wave 1 — Backend-oriented (implement first)

| Order | Milestone | Module technical name | Focus |
|-------|-----------|------------------------|--------|
| **1** | **M2** — OCA General Ledger Range Fix | `gpc_account_gl_range_fix_local` | Local GL / fiscal range behaviour aligned with reporting and operating cut-offs |
| **2** | **M1** — Journal Line Reference Extension | `gpc_account_move_line_reference_ext` | Traceability fields on `account.move.line` |
| **3** | **M3** — Analytic Project Statement Report | `gpc_report_analytic_project_statement` | Read-only project analytic statement (PDF/XLSX) |

**Rationale:** Stabilize **reporting context** (M2) before line-level enrichment (M1) and heavy **analytic aggregation** (M3). Adjust if product owner prefers M1 before M2 — document change in OpenProject.

### Wave 2 — Operations & compliance

| Order | Milestone | Module technical name | Focus |
|-------|-----------|------------------------|--------|
| **4** | **M4** — Timesheet Labor Accrual | `gpc_hr_timesheet_labor_accrual` | HR timesheet → accrual JE; coordination with existing labor modules |
| **5** | **M5** — Stock Project Material Reclassification | `gpc_stock_project_material_reclass` | Project-tied stock / valuation flows |
| **6** | **M6** — Invoice Approval & ZATCA Gate | `gpc_account_invoice_approval_zatca_gate` | Approval workflow before ZATCA submission |

### Wave 3 — Cross-module hardening (before UAT / production)

| Order | Milestone | Description |
|-------|-----------|-------------|
| **7** | **Security & permissions hardening** | **Full security groups matrix**, record rules review, least-privilege UI, segregation-of-duties checks **across** M1–M6. **Not** the immediate next step after M0. |

---

## 3. Minimum permission assumptions (backend phase — per module)

Use **standard Odoo groups** where possible until the hardening milestone. Intended as **design notes**, not a full matrix.

| Module | Minimum roles (assumed) | Backend-phase rule |
|--------|-------------------------|---------------------|
| **M2** `gpc_account_gl_range_fix_local` | Accounting Manager / Advisor for **company settings**; Accountants run reports | Wizard defaults: any user with report access today |
| **M1** `gpc_account_move_line_reference_ext` | **Read:** `account.group_account_readonly`; **Edit new fields:** `account.group_account_invoice` or Manager (TBD in hardening) | Implement fields with sensible `groups=` on views; avoid custom groups in Wave 1 unless unavoidable |
| **M3** `gpc_report_analytic_project_statement` | Report runners: Accounting; Project users may be limited to **own** projects via existing project rules | Prefer `sudo()` only inside report data layer if needed; document in code |
| **M4** `gpc_hr_timesheet_labor_accrual` | HR Officers / Payroll config; workers **do not** need accounting write | Mirror pattern from existing labor JE modules (`sudo` + audit narration) |
| **M5** `gpc_stock_project_material_reclass` | Stock Manager + Accounting for valuation-impacting actions | Restrict wizard to stock/account groups |
| **M6** `gpc_account_invoice_approval_zatca_gate` | New **approver** group (lightweight in Wave 2); full SoD in Wave 3 | Gate logic first; **full** approval matrix later |

---

## 4. What moved out of the critical path

| Deferred item | When |
|---------------|------|
| **Full security groups matrix** | **Wave 3** — before UAT / production |
| **Cross-module permission hardening** | Same gate |
| **Production segregation-of-duties sign-off** | After matrix |

---

## 5. OpenProject alignment

**Suggested structure:**

1. Create or rename a parent **“Phase 1 — Implementation”** with children in order: **M2 → M1 → M3 → M4 → M5 → M6**.
2. Add a final child **“Phase 1 — Security & permissions hardening (pre-UAT)”** with **lowest** priority sequence number after M6 **or** a separate swimlane/milestone so it is **not** scheduled immediately after M0.
3. In each WP description, link **`docs/phase1/M0_WP3_TECHNICAL_DESIGN_NOTES.md`** and this file.
4. Set **dependencies** in OpenProject: M1 depends on M2 completion *if* team agrees GL range must land first; otherwise leave parallel where possible.

---

## 6. Document index

| Document | Purpose |
|----------|---------|
| `REPOSITORY_STANDARDS.md` | Naming, branches, manifest versions |
| `docs/phase1/M0_WP3_TECHNICAL_DESIGN_NOTES.md` | Per-module technical design (10 fields) |
| `docs/phase1/PHASE1_EXECUTION_PLAN.md` | **This file** — execution order and security deferral |

---

*Maintained for GPC Odoo 19 Phase 1.*
