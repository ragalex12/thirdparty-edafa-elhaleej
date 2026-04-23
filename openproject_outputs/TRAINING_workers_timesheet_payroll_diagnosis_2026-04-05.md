# Training-Only Diagnosis Report: account.analytic.line RPC_ERROR

Date: 2026-04-05
Scope: Training environment only (database: trgulf_Mrp)
Production touched: No
New database created: No

## 1) Error Summary

Observed server error:
- Model: account.analytic.line
- Method: _onchange_project_id
- Failing file: /opt/localaddons/workers_timesheet/models/account_analytic_line.py
- Failing line pattern: self.include_in_payroll = self.project_id.use_for_payroll
- Exception: AttributeError: 'project.project' object has no attribute 'use_for_payroll'

## 2) Findings Log (Evidence)

1. workers_timesheet onchange directly accesses project_id.use_for_payroll without field guard.
2. use_for_payroll is defined in workers_project_sheets:
   - /opt/localaddons/workers_project_sheets/models/project_project.py
3. workers_timesheet manifest dependencies do NOT include workers_project_sheets:
   - /opt/localaddons/workers_timesheet/__manifest__.py
4. workers_project_sheets depends on workers_timesheet (reverse direction):
   - /opt/localaddons/workers_project_sheets/__manifest__.py
5. Training DB module states (queried from trgulf_Mrp):
   - workers_timesheet=installed
   - workers_project_sheets=uninstalled
   - workers_reports=uninstalled
6. Runtime version check:
   - Odoo Server 19.0-20251019
   - Patch compatibility with Odoo 19 confirmed.

## 3) Root Cause

Primary root cause: environment/module-load mismatch in training.

The field use_for_payroll is provided by workers_project_sheets, but workers_timesheet code assumes it always exists. In training, workers_timesheet is installed while workers_project_sheets is not, so the field is absent and onchange crashes.

This is a design/dependency coupling issue, not a core Odoo bug.

## 4) Dependency/Architecture Assessment

Missing declaration in workers_timesheet cannot be solved by simply adding workers_project_sheets to depends, because workers_project_sheets already depends on workers_timesheet (circular dependency risk).

Therefore:
- Fast safe fix: defensive guard in workers_timesheet onchange.
- Correct long-term fix: move shared payroll-project field(s) to a small base integration module and let both workers_timesheet and workers_project_sheets depend on that base module.

## 5) Backup Log

Backup created before edit:
- /opt/localaddons/workers_timesheet/models/backups/account_analytic_line.py.20260405_171350.bak

## 6) Change Log (Applied in Training Code)

Edited file:
- /opt/localaddons/workers_timesheet/models/account_analytic_line.py

Change applied in _onchange_project_id:
- Replaced direct field access with safe field-existence guard.
- Behavior when field missing: include_in_payroll = False

Applied defensive pattern:

```python
@api.onchange('project_id')
def _onchange_project_id(self):
    for rec in self:
        if rec.project_id and 'use_for_payroll' in rec.project_id._fields:
            rec.include_in_payroll = rec.project_id.use_for_payroll
        else:
            rec.include_in_payroll = False
```

## 7) Validation Log (Training Only)

1. Python syntax check:
- File compiles; no editor/lint errors after patch.

2. Odoo training upgrade command executed:
- /usr/bin/odoo -c /etc/odoo/odoo.conf -d trgulf_Mrp -u workers_timesheet --stop-after-init
- Result: completed successfully (exit code 0).

3. Onchange runtime check in training shell:
- Script executed against trgulf_Mrp.
- Output: ONCHANGE_OK include_in_payroll=False project_id=True
- Result: no AttributeError; crash stabilized.

## 8) Recommended Next Steps

Fastest temporary stabilization (already done):
- Keep defensive onchange guard in workers_timesheet.

Safest operational next step in training:
- Continue UAT in trgulf_Mrp and monitor logs for account.analytic.line onchange calls.

Architecturally correct fix:
- Create/refactor a shared base payroll-project integration module containing use_for_payroll.
- Make both workers_timesheet and workers_project_sheets depend on that shared module.
- Remove implicit cross-module assumptions from onchange logic.

## 9) Commands Used (Training Scope)

- Module states query (training DB only):
  psql ... -d trgulf_Mrp -Atc "select name||'='||state from ir_module_module where name in (...)"
- Training module upgrade:
  /usr/bin/odoo -c /etc/odoo/odoo.conf -d trgulf_Mrp -u workers_timesheet --stop-after-init
- Training onchange verification:
  /usr/bin/odoo shell -c /etc/odoo/odoo.conf -d trgulf_Mrp < /tmp/training_onchange_check.py

All actions were limited to training environment and existing training database.
