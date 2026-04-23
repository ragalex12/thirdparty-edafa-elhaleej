# Migration Plan: report_xlsx from Odoo 18 to Odoo 19

## ⚠️ IMPORTANT: Configuration Warning

**DO NOT add `custom_addons` to `config/odoo.conf` until ALL modules are migrated to 19.0.x.x.x**

This project contains mixed Odoo versions:
- ✅ `date_range`: 19.0.1.0.0 (migrated)
- ❌ `account_financial_report`: 18.0.1.4.2 (pending)
- ❌ `report_xlsx`: 18.0.1.1.2 (this module - pending)

Adding the `custom_addons` path to the config now would cause conflicts with Odoo 18 modules. See `CONFIGURATION_NOTE.md` in the project root for details.

---

## Executive Summary

This document outlines a **lazy migration plan** for migrating the `report_xlsx` module from Odoo 18.0.1.1.2 to Odoo 19. The plan focuses on minimal changes required for compatibility while maintaining functionality.

**Current Version:** 18.0.1.1.2  
**Target Version:** 19.0.1.0.0  
**Migration Approach:** Lazy (minimal changes for compatibility)

### Note on Migration Tools (Priority Order)

**This plan prioritizes Elasticsearch for code review, with fallback methods if needed.** The recommended execution order is:

**1. PRIMARY: Elasticsearch Docker Image** 🔍 **CODE REVIEW TOOL**
   - Set up and run Elasticsearch Docker container with Odoo 19 codebase indexed
   - Use for semantic code search and pattern matching
   - See Section 5 for setup and usage instructions

**2. FALLBACK: Alternative Methods** (If Elasticsearch unavailable)
   - **Grep/Find Tools**: Use `grep`, `ripgrep`, or IDE search across Odoo 19 codebase
   - **GitHub Search**: Search OCA repositories for 19.0 branch examples
   - **Manual Code Review**: Open Odoo 19 source code files directly
   - **Odoo Documentation**: Refer to official Odoo 19 documentation
   - **Trial and Error**: Install module and fix errors as they appear (incremental approach)

**Note**: odoo-module-migrator is skipped because it does not support Odoo 19.0 (only supports up to 18.0).

**Execution Strategy:**
- 🔍 **Step 1**: Use Elasticsearch Docker image for code review and verification
- ✅ **Step 2**: Use alternative tools if Elasticsearch is not available

---

## 1. Pre-Migration Assessment

### 1.1 Module Structure Overview

The module consists of:
- **Models**: 1 Python model (`ir.actions.report` extension)
- **Controllers**: 1 controller (report routes for XLSX)
- **Reports**: Abstract report base classes for XLSX generation
- **Assets**: JavaScript files for frontend integration
- **Demo**: Demo report examples
- **Tests**: Test files

### 1.2 Current Dependencies

```python
depends = ["base", "web"]
```

**Action Required:**
- ✅ Verify `base` module compatibility with Odoo 19
- ✅ Verify `web` module compatibility with Odoo 19
- ⚠️ **Critical**: This module extends `ir.actions.report` - high priority for verification

### 1.3 Key APIs Currently Used

1. **Report Rendering**: `_render_xlsx()`, `_get_report()`, `_get_report_from_name()`
2. **Model APIs**: `ir.actions.report` model inheritance
3. **Controller APIs**: `@route()`, `ReportController` inheritance
4. **JavaScript**: Registry handlers for report actions
5. **Field Types**: `Selection` field extension

---

## 2. Code Differences Analysis (Odoo 18 vs 19)

### 2.1 Report Rendering API Changes

#### Current Implementation (Odoo 18)
```python
# models/ir_report.py
@api.model
def _render_xlsx(self, report_ref, docids, data):
    report_sudo = self._get_report(report_ref)
    report_model_name = f"report.{report_sudo.report_name}"
    report_model = self.env[report_model_name]
    ret = (
        report_model.with_context(active_model=report_sudo.model)
        .sudo(False)
        .create_xlsx_report(docids, data)
    )
    if ret and isinstance(ret, (tuple | list)):
        report_sudo.save_xlsx_report_attachment(docids, ret[0])
    return ret
```

#### Odoo 19 Changes Required

**Status**: ⚠️ **HIGH PRIORITY** - Core report rendering API may have changed.

**Action Items:**
1. **CRITICAL**: Use Elasticsearch to search for `_render_xlsx` or alternative methods in Odoo 19
2. Verify `_get_report()` method signature
3. Verify `docids` parameter (may have changed to `res_ids`)
4. Check if `create_xlsx_report()` calling pattern changed
5. Verify attachment saving method compatibility

**Search Strategy:**
- Search Odoo 19 codebase for report rendering patterns
- Check `ir.actions.report` model for method changes
- Verify controller integration patterns

### 2.2 Controller Route Changes

#### Current Implementation (Odoo 18)
```python
# controllers/main.py
from odoo.addons.web.controllers.report import ReportController

class ReportController(ReportController):
    @route()
    def report_routes(self, reportname, docids=None, converter=None, **data):
        if converter == "xlsx":
            # ... XLSX handling
        return super().report_routes(reportname, docids=docids, converter=converter, **data)
```

#### Odoo 19 Changes Required

**Status**: ⚠️ **VERIFY** - Controller inheritance and route decorators may have changed.

**Action Items:**
1. Verify `ReportController` import path
2. Verify `@route()` decorator usage
3. Check parameter names (`docids` vs `res_ids`)
4. Verify controller inheritance pattern

**Search Strategy:**
- Search for `ReportController` in Odoo 19
- Verify controller inheritance patterns
- Check route decorator usage

### 2.3 Field Selection Extension

#### Current Implementation (Odoo 18)
```python
# models/ir_report.py
report_type = fields.Selection(
    selection_add=[("xlsx", "XLSX")], ondelete={"xlsx": "set default"}
)
```

#### Odoo 19 Changes Required

**Status**: ✅ **LIKELY COMPATIBLE** - Selection field extension is stable.

**Action Items:**
- ✅ Verify `selection_add` still works
- ✅ Test field value storage

### 2.4 JavaScript Registry Handlers

#### Current Implementation (Odoo 18)
```javascript
// static/src/js/report/action_manager_report.esm.js
registry
    .category("ir.actions.report handlers")
    .add("xlsx_handler", async function (action, options, env) {
        // ... handler implementation
    });
```

#### Odoo 19 Changes Required

**Status**: ⚠️ **VERIFY** - Registry API and handler signatures may have changed.

**Action Items:**
1. Verify registry category name is still `"ir.actions.report handlers"`
2. Check handler function signature (parameters)
3. Verify `download()` function import path
4. Test handler execution flow

**Search Strategy:**
- Search for registry handlers in Odoo 19 JavaScript
- Verify handler patterns match current implementation

### 2.5 Safe Eval and Context Methods

#### Current Implementation (Odoo 18)
```python
from odoo.tools.safe_eval import safe_eval, time
context = self.env["res.users"].context_get()
```

#### Odoo 19 Changes Required

**Status**: ⚠️ **VERIFY** - Utility functions may have moved or changed.

**Action Items:**
1. Verify `safe_eval` import path
2. Verify `context_get()` method still exists
3. Check alternative methods if deprecated

**Search Strategy:**
- Search for `safe_eval` usage in Odoo 19
- Search for `context_get()` method

---

## 3. Detailed Migration Steps

### Phase 1: Manifest and Metadata Updates

#### 3.1 Update `__manifest__.py`

**File**: `__manifest__.py`

**Changes:**
```python
{
    "name": "Base report xlsx",
    "version": "19.0.1.0.0",  # Changed from 18.0.1.1.2
    # ... rest remains the same
}
```

**Action Items:**
- [ ] Update version number
- [ ] Verify `base` and `web` dependencies are Odoo 19 compatible
- [ ] Verify website URLs point to 19.0 branch

---

### Phase 2: Python Code Updates

#### 3.2 Update Report Rendering Method (CRITICAL PRIORITY)

**File**: `models/ir_report.py`

**Current Code:**
```python
@api.model
def _render_xlsx(self, report_ref, docids, data):
    # ...
```

**Action Items:**
- [ ] **USE ELASTICSEARCH FIRST** - Search Odoo 19 for report rendering patterns
- [ ] Verify `_render_xlsx` method exists or is replaced
- [ ] Verify parameter names (`docids` vs `res_ids`)
- [ ] Verify `_get_report()` method compatibility
- [ ] Test report generation with actual XLSX reports
- [ ] Verify attachment saving functionality

**Testing Checklist:**
- [ ] XLSX report generation works
- [ ] Report attachments are saved correctly
- [ ] Multiple record reports work
- [ ] Single record reports work

#### 3.3 Update Controller Routes (High Priority)

**File**: `controllers/main.py`

**Current Code:**
```python
from odoo.addons.web.controllers.report import ReportController

class ReportController(ReportController):
    @route()
    def report_routes(self, reportname, docids=None, converter=None, **data):
        # ...
```

**Action Items:**
- [ ] Use Elasticsearch to verify `ReportController` import path
- [ ] Verify `@route()` decorator usage
- [ ] Check parameter names in controller methods
- [ ] Verify `super()` call pattern
- [ ] Test report download functionality

**Testing Checklist:**
- [ ] XLSX report download works
- [ ] Report routes handle XLSX converter correctly
- [ ] File naming works correctly
- [ ] Error handling works

#### 3.4 Verify Utility Functions

**File**: `models/ir_report.py`

**Current Imports:**
```python
from odoo.tools.safe_eval import safe_eval, time
context = self.env["res.users"].context_get()
```

**Action Items:**
- [ ] Use Elasticsearch to verify `safe_eval` import path
- [ ] Verify `context_get()` method exists
- [ ] Check for alternative methods if deprecated
- [ ] Test context retrieval

#### 3.5 Verify Report Base Classes

**File**: `report/report_abstract_xlsx.py`

**Action Items:**
- [ ] Verify abstract report base class structure
- [ ] Test `create_xlsx_report()` method signature
- [ ] Verify XLSX generation logic
- [ ] Test with demo reports

---

### Phase 3: JavaScript Assets

#### 3.6 Update JavaScript Registry Handler (High Priority)

**File**: `static/src/js/report/action_manager_report.esm.js`

**Current Code:**
```javascript
registry
    .category("ir.actions.report handlers")
    .add("xlsx_handler", async function (action, options, env) {
        // ...
    });
```

**Action Items:**
- [ ] Use Elasticsearch to find registry handler patterns in Odoo 19
- [ ] Verify registry category name
- [ ] Verify handler function signature
- [ ] Check `download()` import path
- [ ] Verify `env.services` access patterns
- [ ] Test frontend report download

**Testing Checklist:**
- [ ] XLSX export button works in UI
- [ ] Report download triggers correctly
- [ ] UI blocking/unblocking works
- [ ] Error handling works in frontend

---

### Phase 4: Tests

#### 3.7 Update Test Files

**Files**: `tests/test_report.py`

**Action Items:**
- [ ] Verify test base classes
- [ ] Update deprecated test methods
- [ ] Verify `_render()` method calls
- [ ] Run all tests
- [ ] Fix any failing tests

---

## 4. Verification Checklist

### 4.1 Functional Testing

- [ ] **XLSX Report Generation**
  - [ ] Abstract report base class works
  - [ ] `create_xlsx_report()` method works
  - [ ] XLSX file is generated correctly
  - [ ] File content is correct

- [ ] **Report Controller**
  - [ ] XLSX report routes work
  - [ ] Report download works
  - [ ] File naming works correctly
  - [ ] Multiple records handled correctly

- [ ] **Report Actions**
  - [ ] XLSX option appears in report type selection
  - [ ] Report action configuration works
  - [ ] Attachment saving works (if configured)

- [ ] **Frontend Integration**
  - [ ] XLSX export button appears
  - [ ] Download works from UI
  - [ ] UI feedback (blocking/unblocking) works
  - [ ] Error messages display correctly

### 4.2 Integration Testing

- [ ] **Dependencies**
  - [ ] `base` module integration works
  - [ ] `web` module integration works

- [ ] **Module Integration**
  - [ ] Modules using `report_xlsx` (like `account_financial_report`) work correctly
  - [ ] XLSX reports from dependent modules generate correctly

- [ ] **Report Types**
  - [ ] Single record reports work
  - [ ] Multiple record reports work
  - [ ] Wizard-based reports work
  - [ ] Context-aware reports work

### 4.3 Error Handling Testing

- [ ] **Report Generation Errors**
  - [ ] Invalid report names handled gracefully
  - [ ] Missing data handled correctly
  - [ ] Permission errors handled correctly

- [ ] **Controller Errors**
  - [ ] Invalid routes return proper errors
  - [ ] Missing reports handled correctly
  - [ ] File generation errors logged properly

---

## 5. Migration Tools Strategy: Automated First, Then Code Review

### 5.0 Automated Migration: odoo-module-migrator (FIRST STEP) ⭐

**Priority**: ⭐ **USE FIRST** - Automated tool handles common code changes automatically

#### 5.0.1 Installation

The library is already installed in the project virtual environment:
```bash
cd /home/sabry3/sabry_backup/odoo_base/base_odoo_19/projects/accounting_financial_report_19
source venv/bin/activate  # If not already activated
python3 venv/bin/odoo-module-migrate --help  # Verify installation
```

**Installation Location**: Project virtual environment at `venv/`  
**Reference**: [OCA odoo-module-migrator GitHub](https://github.com/OCA/odoo-module-migrator)

#### 5.0.2 Usage for This Module

**⚠️ LIMITATION**: The tool currently **DOES NOT support Odoo 19.0** as a target version. It only supports up to 18.0.

**Strategy**: Since we're migrating from 18.0 → 19.0, we can:
1. Run the tool with target 18.0 to clean up and standardize the code
2. This will handle common patterns (file renames, imports, XML updates)
3. Then use Elasticsearch and manual review for 19.0-specific changes

**Alternative Approach**: You can skip the automated tool and go directly to Elasticsearch code review if you prefer, since the tool won't handle 19.0-specific changes anyway.

**Run the automated migration:**

```bash
cd /home/sabry3/sabry_backup/odoo_base/base_odoo_19/projects/accounting_financial_report_19

# Activate virtual environment
source venv/bin/activate

# Run migration tool
python3 venv/bin/odoo-module-migrate \
    --directory ./custom_addons \
    --modules report_xlsx \
    --init-version-name 18.0 \
    --target-version-name 18.0 \
    --log-level INFO \
    --no-commit  # Review changes before committing
```

#### 5.0.3 Understanding Log Output

**INFO Log** - Automatically changed (no action needed)  
**WARNING Log** - Should review (may need manual changes)  
**ERROR Log** - Must fix manually (will cause failures)

#### 5.0.4 Post-Migration Review

After running odoo-module-migrator:
1. Review changes: Check git diff for all modifications
2. Review WARNINGS: Address items that need manual attention
3. Review ERRORS: Fix all errors before proceeding
4. Manual updates for 19.0: Update version numbers, review 19.0-specific changes using Elasticsearch

#### 5.0.5 What the Tool Handles Automatically

- File renames, encoding header removal, import updates
- XML tag updates, dependency replacements
- Migration folder cleanup, common code pattern updates

---

### 5.1 Code Review Strategy: Elasticsearch Docker Image (SECOND STEP)

#### 5.1.1 Setup: Elasticsearch Docker Image

Follow the same setup instructions as in `account_financial_report/MIGRATION_PLAN_18_TO_19.md` Section 5.1.

### 5.2 Using Elasticsearch for Code Review

#### 5.2.1 Report Rendering API Search (CRITICAL)

**Elasticsearch Query:**
```bash
curl -X GET "localhost:9200/odoo19_code/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "should": [
        { "match": { "content": "_render_xlsx" }},
        { "match": { "content": "_render" }},
        { "match": { "content": "get_html" }}
      ]
    }
  },
  "filter": {
    "wildcard": { "file_path": "*ir_actions_report*" }
  },
  "highlight": {
    "fields": { "content": {} }
  }
}
'
```

**Expected Results:**
- Find: Report rendering methods in Odoo 19 `ir.actions.report`
- Verify: Which methods are available (`_render_xlsx`, `_render`, etc.)
- Verify: Parameter names (`docids` vs `res_ids`)
- Files: `addons/base/models/ir_actions_report.py` and related files

#### 5.2.2 Controller Base Class Search

**Elasticsearch Query:**
```bash
curl -X GET "localhost:9200/odoo19_code/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        { "match": { "content": "ReportController" }},
        { "match": { "content": "class" }}
      ]
    }
  },
  "filter": {
    "wildcard": { "file_path": "*controllers/report*" }
  }
}
'
```

**Expected Results:**
- Find: `ReportController` class definition
- Verify: Import path in Odoo 19
- Verify: Method signatures
- Files: Controller files in `addons/web/controllers/report/`

#### 5.2.3 Route Decorator Patterns Search

**Elasticsearch Query:**
```bash
curl -X GET "localhost:9200/odoo19_code/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        { "match": { "content": "@route" }},
        { "match": { "content": "report_routes" }}
      ]
    }
  },
  "filter": {
    "term": { "file_type": "python" }
  }
}
'
```

**Expected Results:**
- Find: Route decorator usage patterns
- Verify: Route method signatures
- Files: Controller files with report routes

#### 5.2.4 JavaScript Registry Handler Search

**Elasticsearch Query:**
```bash
curl -X GET "localhost:9200/odoo19_code/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        { "match": { "content": "ir.actions.report handlers" }},
        { "match": { "content": "registry.category" }}
      ]
    }
  },
  "filter": {
    "term": { "file_type": "javascript" }
  }
}
'
```

**Expected Results:**
- Find: Registry handler patterns in Odoo 19
- Verify: Registry category names
- Verify: Handler function signatures
- Files: JavaScript files with report handlers

#### 5.2.5 Safe Eval and Context Methods Search

**Elasticsearch Query:**
```bash
curl -X GET "localhost:9200/odoo19_code/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "should": [
        { "match": { "content": "safe_eval" }},
        { "match": { "content": "context_get" }}
      ]
    }
  },
  "filter": {
    "term": { "file_type": "python" }
  }
}
'
```

**Expected Results:**
- Find: `safe_eval` import paths and usage
- Find: `context_get()` method usage
- Verify: Alternative methods if deprecated

### 5.3 Fallback Methods

If Elasticsearch unavailable, use these methods:

#### 5.3.1 Method 1: Direct File Inspection with Grep

```bash
cd /path/to/odoo19

# Search for report rendering methods
grep -r "_render_xlsx\|_render\|get_html" addons/base/models/ir_actions_report.py

# Search for ReportController
grep -r "class ReportController" addons/web/controllers/report/

# Search for route patterns
grep -r "@route.*report_routes" addons/web/controllers/report/

# Search for registry handlers
grep -r "ir.actions.report handlers" addons/web/static/src/

# Search for safe_eval
grep -r "from.*safe_eval\|import.*safe_eval" addons/*/models/*.py | head -10
```

#### 5.3.2 Method 2: IDE/Editor Search
- Search for: `_render_xlsx`, `ReportController`, `ir.actions.report handlers`

#### 5.3.3 Method 3: GitHub Search
- Search OCA reporting-engine repository 19.0 branch
- Compare with current implementation

#### 5.3.4 Method 4: Incremental Testing
- Install module in Odoo 19
- Fix errors as they appear

---

## 6. Risk Assessment

### 6.1 High Risk Areas

1. **Report Rendering API** ⚠️ **CRITICAL RISK**
   - **Reason**: Core `ir.actions.report` API changes are common between major versions
   - **Impact**: XLSX reports will not work if API changed
   - **Mitigation**: Use Elasticsearch FIRST to verify API before making changes

2. **Controller Integration** ⚠️ **HIGH RISK**
   - **Reason**: Controller inheritance and routes may have changed
   - **Impact**: Report download may fail
   - **Mitigation**: Verify controller patterns early in migration

3. **JavaScript Registry** ⚠️ **MEDIUM-HIGH RISK**
   - **Reason**: Frontend framework updates may change registry APIs
   - **Impact**: Frontend export button may not work
   - **Mitigation**: Verify registry patterns before updating JavaScript

### 6.2 Medium Risk Areas

4. **Utility Functions** ⚠️ **LOW-MEDIUM RISK**
   - **Reason**: Import paths and methods may have moved
   - **Impact**: Code may fail at runtime
   - **Mitigation**: Easy to fix if found early

### 6.3 Low Risk Areas

5. **Field Extensions** ✅ **LOW RISK**
   - **Reason**: Selection field extension is stable
   - **Impact**: Minimal

---

## 7. Migration Execution Order

### Step 1: Setup and Preparation (1-2 hours)
1. Set up Odoo 19 development environment
2. Create new branch: `19.0` (source control provides backup)
3. **Set up Elasticsearch Docker image** (PRIMARY STEP - see Section 5.1)
4. Review Odoo 19 release notes

### Step 2: Manifest Update (15 minutes)
1. Update `__manifest__.py` version to `19.0.1.0.0`
2. Verify dependencies

### Step 3: Code Review Using Elasticsearch (2-3 hours) 🔍 PRIMARY STEP (CRITICAL)
1. **CRITICAL**: Search Report Rendering API (Section 5.2.1)
2. Search Controller Base Class (Section 5.2.2)
3. Search Route Patterns (Section 5.2.3)
4. Search JavaScript Registry Handlers (Section 5.2.4)
5. Search Utility Functions (Section 5.2.5)

### Step 4: Core API Updates Based on Code Review (3-4 hours)
**Based on Elasticsearch findings (from Step 3):**
1. Update `_render_xlsx()` method if needed (CRITICAL)
2. Update controller routes if needed
3. Update utility function imports if needed
4. Test report generation

### Step 5: JavaScript Updates (1-2 hours)
1. Update JavaScript registry handler if needed
2. Update import paths
3. Test frontend functionality

### Step 6: Testing (3-5 hours)
1. Run all tests
2. Manual testing of XLSX report generation
3. Test with dependent modules (e.g., account_financial_report)
4. Fix issues found

### Step 7: Documentation (30 minutes)
1. Update README if needed
2. Update changelog

**Total Estimated Time**: 9-15 hours (critical module, requires careful testing, no backup/automated tool overhead)

---

## 8. Quick Reference: Common Odoo 18 → 19 Changes

| Area | Odoo 18 | Odoo 19 | Status | Elasticsearch Query |
|------|---------|---------|--------|---------------------|
| Report Rendering | `_render_xlsx(docids, data)` | Verify: parameters? | ⚠️ CRITICAL | Section 5.2.1 |
| Controller | `ReportController` | Verify: import path | ⚠️ VERIFY | Section 5.2.2 |
| Route Decorator | `@route()` | Same | ✅ Compatible | Not needed |
| JS Registry | `registry.category().add()` | Verify: signature | ⚠️ VERIFY | Section 5.2.4 |
| Field Extension | `selection_add` | Same | ✅ Compatible | Not needed |
| Safe Eval | `from odoo.tools.safe_eval` | Verify: import | ⚠️ VERIFY | Section 5.2.5 |

**Legend:**
- ✅ **Compatible**: No changes needed
- ⚠️ **Verify**: Needs investigation using Elasticsearch (PRIMARY) or fallback methods
- ⚠️ **CRITICAL**: Must verify before proceeding - high impact

---

## 9. Special Considerations

### 9.1 Dependency on Other Modules

This module is used by other modules (e.g., `account_financial_report`). When migrating:

1. **Coordinate**: Ensure `report_xlsx` is migrated BEFORE modules that depend on it
2. **Test Integration**: After migration, test with dependent modules
3. **Backward Compatibility**: If possible, maintain backward compatibility during transition

### 9.2 XLSX Generation Libraries

Verify that Python XLSX generation libraries are compatible:
- `xlsxwriter` - Should be compatible, but verify version requirements
- Any other XLSX libraries used in abstract report classes

---

## End of Migration Plan

**Document Version**: 1.0  
**Created**: 2024  
**Last Updated**: 2024  
**Status**: Draft - Ready for Execution

**Note**: This is a CRITICAL infrastructure module. Test thoroughly with dependent modules after migration.

