# Meeting requirements traceability

Source: Hatem WhatsApp + identified meeting tasks, 11 Aug 2026, database **MM** on https://gpc.odoo.com.se.

Test DB: **`trgcc_mm_uat`** (clone of production `trgcc`). Production writes: **0**.

Excel mode: **`EXCEL_TEMPLATE_STYLE_ONLY`** — Industrial P&L calculations are out of scope.

| ID | Meeting point (transcript wording/intent) | Business scenario | Test case | Test data | Expected | Actual | Evidence |
|----|-------------------------------------------|-------------------|-----------|-----------|----------|--------|----------|
| M01 | Create new time sheets and generate journals on MM | Timesheet → Generate Journal | MM-UAT-001, auto labor extended | `MM-UAT-TS-2026-05-*`, batch 280, move `SLR/2026/05/0001` | Posted balanced JE | PASS: Dr/Cr 4970 | inventory JSON; SQL summary |
| M02 | Reports must pull from **Analytical Items** not Journal Items | AAL-primary statement | MM-UAT-020, `test_no_duplicate_when_aal_represents_aml` | May/Jun JE AAL + timesheets | JE once via AAL; timesheets listed | PASS: 154 rows, source=aal for JE | statement wizard; ANALYTICAL_VS_JOURNAL_PROOF.md |
| M03 | Why analytical items miss financial accounts | Missing GL root cause + hours guard | MM-UAT-010, MM-UAT-036 | Legacy 29–59 + Dec 2026 in-period 25–260h | Anomalies remain visible; populate excludes them | PASS | 58_anomaly_guard; SLR/2026/12/0001 = 640 |
| M04 | **Include in Payroll** must be selected before generating journals | Flag → eligibility → batch | MM-UAT-007–009, workers_timesheet + bridge tests | EXCL / OPTOUT lines | Excluded from populate | PASS: 3 false flags; May populate 16 | tests 103/103; batch 280 |
| M05 | SQL analysis of production logs for discrepancies | Read-only prod analysis | MM-UAT-030 | `trgcc` 10 timesheets, no labor modules | No prod writes | PASS: timesheets=10, labor_mods=0 | sql/01_timesheets.txt; this run |
| M06 | Journal creation must not bypass account IDs | Debit 410028 / credit 202001 / analytic on Dr only | MM-UAT-012 | May JE 396 | Accounts present; credit no analytic | PASS | SQL move 396 lines |
| M07 | Backup production before any historical payroll SQL | Backup + TEST-only remediation | MM-UAT-014 | dump `trgcc_20260811_223821.dump`; April retro on UAT | No prod SQL backfill | PASS | sql/backup_meta.txt; batch 281 |
| M08 | Mohammad desired layout: project, materials, direct labour, overhead, sales, totals | Excel visual only | MM-UAT-028 | `تقرير الصناعي.xlsx` vs statement XLSX | Style only; no P&L columns | PASS: forbidden headers absent | EXCEL_TEMPLATE_VISUAL_COMPARISON.md; test_xlsx_* |
| M09 | Follow-up meeting on construction/contracting | Scheduling | — | — | NOT_TESTABLE | NOT_TESTABLE | Meeting logistics, not software |
| M10 | Provide Sabri DB link, recording, login | Access | — | — | NOT_TESTABLE | NOT_TESTABLE | Ops/handoff, not product |
| M11 | Share unprotected recording for transcription | Recording | — | — | NOT_TESTABLE | NOT_TESTABLE | Ops |
| M12 | Historical records with/without journals | Legacy vs JE AAL | MM-UAT-010, 015 | HIST anomalies; LEGACY retro | Source TS remain no-GL; JE AAL has GL | PASS: 124 TS no-GL | SQL aal_ts_no_gl |
| M13 | Posted vs unposted journals | Draft October vs posted May/Jun/Apr | MM-UAT-013 | move 399 draft; 396–398 posted | Draft excluded from posted target | PASS | test_draft_je_excluded; move 399 |
| M14 | Correct project/account linkage | Multi-project debit slices | MM-UAT-012 | May 5 debit slices | Analytic on each debit | PASS | SQL move 396 |
| M15 | Company context / wrong company | Foreign company 23 | MM-UAT-025 | `MM-UAT-CO-FOREIGN`, EMP-11 | Guards block foreign journal/accounts/TS | PASS | auto tests + foreign inventory |
| M16 | Retroactive remediation staged | April 1–7 posted; 20–25 held | MM-UAT-014, 016 | RETRO vs HELD timesheets | Subset posted; held remain no-GL | PASS | batch 281 4 lines; HELD 5 TS |
| M17 | Report completeness + no duplication | Large statement | MM-UAT-020–024 | 154 rows Apr–Oct | Totals match rows; JE once | PASS | inventory statement_row_count |
| M18 | XLSX presentation current fields only | RTL export | MM-UAT-028 | `/tmp/mm_uat_extended_statement.xlsx` | Values = Phase-1; no P&L | PASS | 11433 bytes; tests |

**Mapped: 15 testable + 3 NOT_TESTABLE. None omitted.**
