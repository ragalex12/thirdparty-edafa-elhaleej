# Gulf / MM — Request → Implementation Matrix

Source table behind the public case-study page. Status vocabulary: `PASS` · `FIXED` · `VALIDATED` · `STYLE ONLY` · `NOT TESTABLE` · `MANUAL_PROOF_ONLY`.

| # | Meeting request | What was found | What was done | Status | Proof |
|---|-----------------|----------------|---------------|--------|-------|
| 1 | Create timesheets and Generate Journal | Labor Accrual stack not on production; clone required | Populate eligible TS → draft JE → post Salaries JE on UAT | PASS | `09_batch_population.png`, `11_posted_je.png`, PW-MM-031/035 |
| 2 | Why Analytical Items miss Financial Account | Source timesheets are analytic-only until a JE posts a related AAL | Document design; show source no-GL vs JE-backed AAL | VALIDATED | `14_source_timesheet_no_gl.png`, `15_resulting_aal_gl.png` |
| 3 | Report should use Analytical Items | AML-primary report missed timesheets without GL | AAL-primary statement with Timesheet / no GL + JE-once | FIXED | `18_statement_wizard.png`, statement row shots, statement tests |
| 4 | Review Include in Payroll | Project onchange could reset eligibility | Preserve flag; explicit opt-out project only | FIXED | `04_include_payroll.png`, `05_payroll_optout.png` |
| 5 | Prevent same issue in code | Missing guards for payroll, company, anomalous hours | Payroll, multi-company, >24h single + cumulative guards | FIXED | `06_anomaly_25h.png`, `07_anomaly_cumulative.png`, `58_anomaly_guard.png` |
| 6 | Retroactive remediation for valid old data | Valid historical periods never received labor JE | Retro batch workflow validated on clone | PASS | Manual `32`–`34`, inventory |
| 7 | Correct company / account / journal | Wrong company must not use GCC labor accounts | GCC config 410028 / 202001 / Salaries; foreign company distinct | PASS | `02_company_context.png`, `08_labor_config.png`, PW-MM-003 |
| 8 | Excel visual design | Client wanted Industrial look | Apply RTL/Arabic style to **existing** six columns only | STYLE ONLY | Excel gallery; forbidden P&L headers absent |

## Playwright scenario map

| ID | Scenario | Result | Screenshot |
|----|----------|--------|------------|
| PW-MM-001 | Login to UAT DB | PASS | `01_test_db.png`, `pw_001_test_db_login.png` |
| PW-MM-002 | GCC labor configuration | PASS | `02_company_context.png`, `08_labor_config.png` |
| PW-MM-003 | Foreign company distinct | PASS | `pw_003_foreign_company.png` |
| PW-MM-010 | 8h timesheet + Include in Payroll | PASS | `03_timesheet_8h.png`, `04_include_payroll.png` |
| PW-MM-011 | 6h timesheet create | PASS | (session create + batch lines) |
| PW-MM-013 | Payroll opt-out visible & unchecked | PASS | `05_payroll_optout.png` |
| PW-MM-020 | 24.00h boundary eligible | PASS | Batch includes 24h line |
| PW-MM-021 | 25h anomalous excluded | PASS | `06_anomaly_25h.png` |
| PW-MM-022 | Cumulative 16+16 excluded | PASS | `07_anomaly_cumulative.png` |
| PW-MM-023 | Anomalous hours not rewritten | PASS | unit_amount still 25 |
| PW-MM-030 | Labor Accrual config accounts | PASS | `08_labor_config.png` |
| PW-MM-031 | Populate excludes opt-out & anomalies | PASS | `09_batch_population.png` |
| PW-MM-032–035 | Draft/post JE, debit analytic, credit clearing | PASS | `10`–`13` |
| PW-MM-040 | Source timesheet no GL | PASS | `14_source_timesheet_no_gl.png` |
| PW-MM-041 | JE-backed AAL has GL | PASS | `15_resulting_aal_gl.png` |
| PW-MM-042/050–052 | Material vs journal vs analytic | PASS | `16`, `17`, `pw_052` |
| PW-MM-060–064 | Statement wizard / mixed rows | PASS | `18`–`21` (+ manual statement rows) |
| PW-MM-070–071 | XLSX style-only, no P&L headers | PASS | `22_xlsx_export.png`, Excel gallery |

## Coverage baseline

- Automated Odoo: **110 passed**, 2 justified skips
- Manual UAT: **35 + MM-UAT-036**
- Playwright Odoo project: **16 passed / 0 failed**
- Production writes: **0**

## Not claimed

- Industrial P&L logic from Excel
- Production deployment
- Automatic merge to main/master
