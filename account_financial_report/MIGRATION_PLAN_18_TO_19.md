# Migration Plan: account_financial_report from Odoo 18 to Odoo 19

## ⚠️ IMPORTANT: Configuration Warning

**DO NOT add `custom_addons` to `config/odoo.conf` until ALL modules are migrated to 19.0.x.x.x**

This project contains mixed Odoo versions:
- ✅ `date_range`: 19.0.1.0.0 (migrated)
- ❌ `account_financial_report`: 18.0.1.4.2 (this module - pending)
- ❌ `report_xlsx`: 18.0.1.1.2 (pending)

Adding the `custom_addons` path to the config now would cause conflicts with Odoo 18 modules. See `CONFIGURATION_NOTE.md` in the project root for details.

---

## Executive Summary

This document outlines a **lazy migration plan** for migrating the `account_financial_report` module from Odoo 18.0.1.4.2 to Odoo 19. The plan focuses on minimal changes required for compatibility while maintaining functionality.

**Current Version:** 18.0.1.4.2  
**Target Version:** 19.0.0.0.0  
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
- **Models**: 6 Python models (account_move_line, account, account_group, ir_actions_report, res_config_settings, account_age_report_configuration)
- **Reports**: 6 report types (General Ledger, Trial Balance, Open Items, Aged Partner Balance, VAT Report, Journal Ledger)
- **Wizards**: 6 wizards (one per report type)
- **Views**: XML views for wizards and reports
- **Assets**: JavaScript (ESM) and CSS files
- **Templates**: QWeb templates for HTML/PDF reports

### 1.2 Current Dependencies

```python
depends = ["account", "date_range", "report_xlsx"]
```

**Action Required:**
- ✅ Verify `account` module compatibility with Odoo 19
- ✅ Verify `date_range` module compatibility with Odoo 19
- ✅ Verify `report_xlsx` module compatibility with Odoo 19

### 1.3 Key APIs Currently Used

1. **Report Rendering**: `_render_qweb_html()`, `_render_xlsx()`
2. **Model APIs**: `search_read()`, `search_fetch()`, `browse()`
3. **Field APIs**: `Command.link()`, `Command.clear()` (already Odoo 19 compatible)
4. **JavaScript**: OWL/ESM modules with `patch()` from `@web/core/utils/patch`

---

## 2. Code Differences Analysis (Odoo 18 vs 19)

### 2.1 Report Rendering API Changes

#### Current Implementation (Odoo 18)
```python
# models/ir_actions_report.py
@api.model
def _render_qweb_html(self, report_ref, docids, data=None):
    context = self._prepare_account_financial_report_context(data)
    obj = self.with_context(**context) if context else self
    return super(IrActionsReport, obj)._render_qweb_html(
        report_ref, docids, data=data
    )
```

#### Odoo 19 Changes Required

**Status**: ⚠️ **VERIFY** - The `_render_qweb_html` method signature may have changed. 

**Action Items:**
1. Check if `_render_qweb_html` still exists in Odoo 19 `ir.actions.report` model
2. Verify if `get_html()` method should be used instead
3. Check parameter changes (e.g., `docids` vs other identifier format)

**Potential Change:**
```python
# If get_html() is the new method
@api.model
def get_html(self, report_ref, res_ids=None, data=None):
    context = self._prepare_account_financial_report_context(data)
    obj = self.with_context(**context) if context else self
    return super(IrActionsReport, obj).get_html(
        report_ref, res_ids=res_ids, data=data
    )
```

**Search Strategy:**
- Search Odoo 19 codebase for `ir.actions.report` methods
- Check for deprecation warnings in Odoo 19 logs
- Review OCA module migrations from 18.0 to 19.0 branches

### 2.2 Abstract Report Model

#### Current Implementation
```python
# report/abstract_report.py
class AgedPartnerBalanceReport(models.AbstractModel):
    _name = "report.account_financial_report.abstract_report"
    
    def _get_report_values(self, docids, data):
        wizard = self.env[data["wizard_name"]].browse(data["wizard_id"])
        return {
            "limit_text": wizard._limit_text,
        }
```

#### Odoo 19 Changes Required

**Status**: ✅ **LIKELY COMPATIBLE** - `_get_report_values()` is still used in Odoo 19, but verify parameter naming.

**Action Items:**
1. Verify `docids` parameter name (might be `res_ids` or `docids` still)
2. Check if `data` parameter structure changed
3. Ensure wizard model access patterns are still valid

**Search Strategy:**
- Search for `_get_report_values` in Odoo 19 report examples
- Check abstract report base classes in Odoo 19 core

### 2.3 Model Query Methods

#### Current Usage
```python
# Already using Odoo 19 compatible methods
move_lines = self.env["account.move.line"].search_read(
    domain=domain, fields=ml_fields
)

# Using search_fetch (already Odoo 19 method)
analytic_accounts = self.env["account.analytic.account"].search_fetch(
    [("id", "in", analytic_account_ids)], ["name"]
)
```

#### Odoo 19 Changes Required

**Status**: ✅ **COMPATIBLE** - `search_read()` and `search_fetch()` are both valid in Odoo 19.

**Action Items:**
- ✅ No changes needed for query methods
- ✅ Consider performance optimization opportunities with `search_fetch()` where applicable

### 2.4 Many2many Field Updates

#### Current Implementation
```python
# models/account_move_line.py
from odoo.fields import Command

self.analytic_account_ids = [Command.clear()]
for account_id, records in batch_by_analytic_account.items():
    if account_id in existing_account_ids:
        records.analytic_account_ids = [Command.link(account_id)]
```

#### Odoo 19 Changes Required

**Status**: ✅ **ALREADY COMPATIBLE** - Using `Command` class which is Odoo 19 standard.

**Action Items:**
- ✅ No changes needed

### 2.5 JavaScript/OWL Code

#### Current Implementation
```javascript
// static/src/js/report_action.esm.js
import {ReportAction} from "@web/webclient/actions/reports/report_action";
import {patch} from "@web/core/utils/patch";

patch(ReportAction.prototype, {
    setup() {
        super.setup(...arguments);
        // ...
    },
    export() {
        // ...
    },
});
```

#### Odoo 19 Changes Required

**Status**: ⚠️ **VERIFY** - OWL 3.x or 4.x API might have changes.

**Action Items:**
1. Check if `ReportAction` class still exists at same import path
2. Verify `patch()` utility is still available
3. Check if `setup()` lifecycle method signature changed
4. Verify `action.doAction()` method compatibility

**Search Strategy:**
- Search for `ReportAction` in Odoo 19 JavaScript code
- Check OCA modules for JavaScript patches in 19.0 branches

---

## 3. Detailed Migration Steps

### Phase 1: Manifest and Metadata Updates

#### 3.1 Update `__manifest__.py`

**File**: `__manifest__.py`

**Changes:**
```python
{
    "name": "Account Financial Reports",
    "version": "19.0.1.0.0",  # Changed from 18.0.1.4.2
    "category": "Reporting",
    # ... rest remains the same
}
```

**Action Items:**
- [ ] Update version number
- [ ] Verify all dependencies are Odoo 19 compatible
- [ ] Update author strings if needed
- [ ] Verify website URLs point to 19.0 branch

---

### Phase 2: Python Code Updates

#### 3.2 Update Report Rendering (High Priority)

**File**: `models/ir_actions_report.py`

**Current Code:**
```python
@api.model
def _render_qweb_html(self, report_ref, docids, data=None):
    # ...
```

**Action Items:**
- [ ] Search Odoo 19 codebase for `ir.actions.report` methods
- [ ] Determine if `_render_qweb_html` is deprecated
- [ ] If deprecated, update to `get_html()` or equivalent
- [ ] Update method signature if parameters changed
- [ ] Test report generation (HTML/PDF)

**Testing Checklist:**
- [ ] HTML report generation works
- [ ] PDF report generation works
- [ ] Language context is preserved
- [ ] Report data is correct

#### 3.3 Verify Abstract Report Methods

**File**: `report/abstract_report.py`

**Current Code:**
```python
def _get_report_values(self, docids, data):
    # ...
```

**Action Items:**
- [ ] Verify `_get_report_values` method signature
- [ ] Check if `docids` parameter name changed to `res_ids`
- [ ] Verify data structure compatibility
- [ ] Test all 6 report types

**Testing Checklist:**
- [ ] General Ledger report works
- [ ] Trial Balance report works
- [ ] Open Items report works
- [ ] Aged Partner Balance report works
- [ ] VAT Report works
- [ ] Journal Ledger report works

#### 3.4 Update Model Query Optimization

**Files**: All report Python files

**Current Status**: Already using `search_fetch()` in some places.

**Action Items:**
- [ ] Review all `search_read()` calls
- [ ] Consider converting to `search_fetch()` for performance
- [ ] Test query performance
- [ ] Ensure field lists are optimized

**Low Priority** - Can be done in post-migration optimization phase.

#### 3.5 Verify API Decorators

**Files**: All model files

**Current Usage**: `@api.model`, `@api.depends`

**Action Items:**
- [ ] Verify all `@api.model` decorators are correct
- [ ] Verify `@api.depends` syntax (should be compatible)
- [ ] Check for any deprecated decorators
- [ ] Add `@api.readonly` where needed (if introduced in Odoo 19)

---

### Phase 3: XML Views and Templates

#### 3.6 Verify QWeb Template Syntax

**Files**: `report/templates/*.xml`

**Action Items:**
- [ ] Verify QWeb 4.x syntax compatibility
- [ ] Check for deprecated QWeb directives
- [ ] Test template rendering
- [ ] Verify `t-esc`, `t-raw`, `t-set` directives
- [ ] Check `t-call` template inclusion

**Search Strategy:**
- Check Odoo 19 QWeb documentation
- Search for breaking changes in QWeb templates

#### 3.7 Verify View Definitions

**Files**: `view/*.xml`, `wizard/*_wizard_view.xml`

**Action Items:**
- [ ] Verify view architecture compatibility
- [ ] Check for deprecated view attributes
- [ ] Verify field widget compatibility
- [ ] Test all wizard forms
- [ ] Verify menu items structure

---

### Phase 4: JavaScript Assets

#### 3.8 Update JavaScript Code

**File**: `static/src/js/report_action.esm.js`

**Current Code:**
```javascript
import {ReportAction} from "@web/webclient/actions/reports/report_action";
import {patch} from "@web/core/utils/patch";
```

**Action Items:**
- [ ] Verify import paths are correct
- [ ] Check if `ReportAction` class moved or renamed
- [ ] Verify `patch()` utility compatibility
- [ ] Test report export functionality
- [ ] Verify XLSX export button works

**Search Strategy:**
- Search for `ReportAction` in Odoo 19 codebase
- Check JavaScript console for errors
- Review OCA module JavaScript patches in 19.0

#### 3.9 Verify Assets Manifest

**File**: `__manifest__.py` (assets section)

**Current:**
```python
"assets": {
    "web.assets_backend": [
        "account_financial_report/static/src/js/*",
        "account_financial_report/static/src/xml/**/*",
    ],
}
```

**Action Items:**
- [ ] Verify asset bundle names are correct
- [ ] Test JavaScript loading
- [ ] Verify CSS loading (if applicable)
- [ ] Check for console errors

---

### Phase 5: Security and Access Rights

#### 3.10 Verify Security Files

**Files**: `security/ir.model.access.csv`, `security/security.xml`

**Action Items:**
- [ ] Verify access rights structure
- [ ] Test record rules
- [ ] Verify user permissions
- [ ] Check for deprecated security features

---

### Phase 6: Tests

#### 3.11 Update Test Files

**Files**: `tests/*.py`

**Action Items:**
- [ ] Verify test base classes
- [ ] Update deprecated test methods
- [ ] Verify test fixtures
- [ ] Run all tests
- [ ] Fix any failing tests

**Test Files to Update:**
- `test_age_report_configuration.py`
- `test_aged_partner_balance.py`
- `test_general_ledger.py`
- `test_journal_ledger.py`
- `test_open_items.py`
- `test_trial_balance.py`
- `test_vat_report.py`

---

## 4. Verification Checklist

### 4.1 Functional Testing

- [ ] **General Ledger Report**
  - [ ] HTML view renders correctly
  - [ ] PDF export works
  - [ ] XLSX export works
  - [ ] Filters work correctly
  - [ ] Data accuracy verified

- [ ] **Trial Balance Report**
  - [ ] HTML view renders correctly
  - [ ] PDF export works
  - [ ] XLSX export works
  - [ ] Filters work correctly
  - [ ] Data accuracy verified

- [ ] **Open Items Report**
  - [ ] HTML view renders correctly
  - [ ] PDF export works
  - [ ] XLSX export works
  - [ ] Filters work correctly
  - [ ] Data accuracy verified

- [ ] **Aged Partner Balance Report**
  - [ ] HTML view renders correctly
  - [ ] PDF export works
  - [ ] XLSX export works
  - [ ] Filters work correctly
  - [ ] Data accuracy verified
  - [ ] Configuration intervals work

- [ ] **VAT Report**
  - [ ] HTML view renders correctly
  - [ ] PDF export works
  - [ ] XLSX export works
  - [ ] Filters work correctly
  - [ ] Data accuracy verified

- [ ] **Journal Ledger Report**
  - [ ] HTML view renders correctly
  - [ ] PDF export works
  - [ ] XLSX export works
  - [ ] Filters work correctly
  - [ ] Data accuracy verified

### 4.2 Integration Testing

- [ ] **Dependencies**
  - [ ] `account` module integration works
  - [ ] `date_range` module integration works
  - [ ] `report_xlsx` module integration works

- [ ] **Multi-company**
  - [ ] Reports work with multiple companies
  - [ ] Company filtering works correctly

- [ ] **Multi-currency**
  - [ ] Foreign currency reports work
  - [ ] Currency conversion is accurate

- [ ] **Language/Translation**
  - [ ] Reports render in different languages
  - [ ] Translations are correct
  - [ ] Date formats are locale-aware

### 4.3 Performance Testing

- [ ] **Large Datasets**
  - [ ] Reports work with large account.move.line datasets
  - [ ] Performance is acceptable
  - [ ] No timeout errors

- [ ] **Query Optimization**
  - [ ] Database queries are optimized
  - [ ] No N+1 query problems
  - [ ] Indexes are used correctly

### 4.4 User Interface Testing

- [ ] **Wizards**
  - [ ] All wizard forms open correctly
  - [ ] Field defaults work
  - [ ] Onchange methods work
  - [ ] Validation works

- [ ] **Menus**
  - [ ] All menu items appear
  - [ ] Menu structure is correct
  - [ ] Access rights are respected

---

## 5. Code Review Strategy: Elasticsearch First, Then Fallbacks

This section provides a **prioritized approach** to code review: use Elasticsearch Docker image first for comprehensive semantic search, then fall back to alternative tools if needed.

---

### 5.1 Setup: Elasticsearch Docker Image (PRIMARY METHOD)

#### 5.1.1 Prerequisites
- Docker installed and running
- Access to Odoo 19 source code (cloned locally or mounted volume)
- Elasticsearch Docker image (e.g., `elasticsearch:8.x` or specialized Odoo code search image)

#### 5.1.2 Setup Elasticsearch Container

**Option A: Using Standard Elasticsearch Image**
```bash
# Pull Elasticsearch image
docker pull docker.elastic.co/elasticsearch/elasticsearch:8.11.0

# Run Elasticsearch container
docker run -d \
  --name odoo19-elasticsearch \
  -p 9200:9200 \
  -p 9300:9300 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" \
  docker.elastic.co/elasticsearch/elasticsearch:8.11.0

# Verify it's running
curl http://localhost:9200
```

**Option B: Using Pre-configured Odoo Code Search Image** (if available)
```bash
# If you have a custom image with Odoo code indexing tools
docker run -d \
  --name odoo19-code-search \
  -p 9200:9200 \
  -v /path/to/odoo19:/odoo19:ro \
  <odoo-code-search-image>
```

#### 5.1.3 Index Odoo 19 Codebase

**Method 1: Using Elasticsearch API with code indexing tool**
```bash
# Example: Index Odoo 19 source code
# (Adjust based on your indexing tool)
python index_odoo_code.py \
  --odoo-path /path/to/odoo19 \
  --elasticsearch-url http://localhost:9200 \
  --index-name odoo19_code
```

**Method 2: Using Elasticsearch bulk API**
```bash
# Create index with mapping
curl -X PUT "localhost:9200/odoo19_code?pretty" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "properties": {
      "content": { "type": "text" },
      "file_path": { "type": "keyword" },
      "file_type": { "type": "keyword" },
      "module": { "type": "keyword" }
    }
  }
}
'

# Bulk index files (use indexing script)
python bulk_index_odoo19.py --es-url http://localhost:9200
```

#### 5.1.4 Verify Indexing
```bash
# Check index exists
curl -X GET "localhost:9200/odoo19_code/_count?pretty"

# Search test query
curl -X GET "localhost:9200/odoo19_code/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {
      "content": "ir.actions.report"
    }
  }
}
'
```

---

### 5.2 Using Elasticsearch for Code Review

#### 5.2.1 Report Rendering API Search

**Elasticsearch Query:**
```bash
curl -X GET "localhost:9200/odoo19_code/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "should": [
        { "match": { "content": "_render_qweb_html" }},
        { "match": { "content": "get_html" }},
        { "match": { "content": "ir.actions.report" }}
      ]
    }
  },
  "filter": {
    "term": { "file_path": "ir_actions_report.py" }
  },
  "highlight": {
    "fields": { "content": {} }
  }
}
'
```

**Expected Results:**
- Files: `addons/base/models/ir_actions_report.py`
- Find: Current report rendering methods in Odoo 19
- Verify: Whether `_render_qweb_html` exists or is replaced with `get_html`

#### 5.2.2 Abstract Report Models Search

**Elasticsearch Query:**
```bash
curl -X GET "localhost:9200/odoo19_code/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        { "match": { "content": "_get_report_values" }},
        { "bool": {
          "should": [
            { "match": { "content": "res_ids" }},
            { "match": { "content": "docids" }}
          ]
        }}
      ]
    }
  },
  "filter": {
    "wildcard": { "file_path": "*report*.py" }
  }
}
'
```

**Expected Results:**
- Files: All report Python files in Odoo 19
- Find: Method signatures using `_get_report_values`
- Verify: Parameter names (`docids` vs `res_ids`)

#### 5.2.3 JavaScript Report Actions Search

**Elasticsearch Query:**
```bash
curl -X GET "localhost:9200/odoo19_code/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        { "match": { "content": "ReportAction" }},
        { "match": { "content": "@web/webclient/actions/reports" }}
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
- Files: JavaScript files in `addons/web/static/src/webclient/actions/reports/`
- Find: ReportAction class definition and export paths
- Verify: Import paths and class structure

#### 5.2.4 Command Class Usage Search

**Elasticsearch Query:**
```bash
curl -X GET "localhost:9200/odoo19_code/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        { "match": { "content": "Command.link" }},
        { "match": { "content": "Command.clear" }}
      ]
    }
  },
  "filter": {
    "term": { "file_type": "python" }
  },
  "size": 10
}
'
```

**Expected Results:**
- Examples of `Command` class usage in Odoo 19
- Verify: Patterns match your current implementation

#### 5.2.5 Model Query Methods Search

**Elasticsearch Query:**
```bash
curl -X GET "localhost:9200/odoo19_code/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        { "match": { "content": "search_fetch" }},
        { "match": { "content": "account.move.line" }}
      ]
    }
  },
  "filter": {
    "wildcard": { "file_path": "*account*.py" }
  }
}
'
```

**Expected Results:**
- Files: Account-related models in Odoo 19
- Find: Usage patterns of `search_fetch` with account.move.line
- Verify: Your usage matches Odoo 19 patterns

---

### 5.3 Using Elasticsearch with Python/API Client (Optional)

**Python Example:**
```python
from elasticsearch import Elasticsearch

# Connect to Elasticsearch
es = Elasticsearch(['http://localhost:9200'])

# Search for report rendering methods
response = es.search(
    index='odoo19_code',
    body={
        "query": {
            "match": {
                "content": "_render_qweb_html OR get_html"
            }
        },
        "filter": {
            "term": {"file_path": "ir_actions_report.py"}
        }
    }
)

# Process results
for hit in response['hits']['hits']:
    print(f"File: {hit['_source']['file_path']}")
    print(f"Content: {hit['_source']['content'][:200]}...")
```

---

### 5.4 Fallback Methods (If Elasticsearch Unavailable)

If Elasticsearch Docker image is not available or not working, use these methods in order:

#### 5.4.1 Method 1: Direct File Inspection with Grep

```bash
# Navigate to Odoo 19 source directory
cd /path/to/odoo19

# Search for report rendering methods
grep -r "_render_qweb_html\|get_html" addons/base/models/ir_actions_report.py

# Search for abstract report methods
find . -name "*report*.py" -exec grep -l "_get_report_values" {} \;
grep -r "_get_report_values" addons/*/report/*.py | head -20

# Search for JavaScript ReportAction
grep -r "ReportAction" addons/web/static/src/webclient/actions/reports/

# Search for Command usage
grep -r "Command\.link\|Command\.clear" addons/*/models/*.py | head -10

# Search for search_fetch usage
grep -r "search_fetch.*account\.move\.line" addons/account/models/
```

#### 5.4.2 Method 2: IDE/Editor Search

- Open Odoo 19 project in your IDE (VSCode, PyCharm, etc.)
- Use "Find in Files" feature:
  - **Windows/Linux**: `Ctrl+Shift+F`
  - **Mac**: `Cmd+Shift+F`
- Search across the entire Odoo 19 codebase
- Use regex patterns for complex searches:
  - Pattern: `_render_qweb_html|get_html`
  - Pattern: `_get_report_values.*\(.*(res_ids|docids)`

#### 5.4.3 Method 3: GitHub Search

1. Go to https://github.com/odoo/odoo
2. Switch to branch `19.0`
3. Use GitHub's search feature:
   - Search: `_render_qweb_html language:Python path:*/ir_actions_report.py`
   - Search: `ReportAction language:JavaScript path:*/actions/reports/*`
   - Search: `_get_report_values language:Python`

#### 5.4.4 Method 4: Incremental Testing (Lazy Migration)

This is the most pragmatic approach for lazy migration:

1. Make changes based on plan assumptions
2. Install/update module in Odoo 19
3. Monitor logs for errors: `tail -f /var/log/odoo/odoo.log`
4. Fix errors as they appear:
   ```bash
   # Common error patterns to watch for:
   # - AttributeError: method not found
   # - TypeError: wrong parameter signature
   # - ImportError: module path changed
   ```
5. Iterate until all reports work

#### 5.4.5 Method 5: Compare with OCA Modules

```bash
# Clone OCA repository
git clone https://github.com/OCA/account-financial-reporting.git
cd account-financial-reporting

# Check if 19.0 branch exists
git branch -a | grep 19.0

# If exists, checkout and compare
git checkout 19.0
git diff 18.0..19.0 --name-only

# Compare specific files
git diff 18.0..19.0 models/ir_actions_report.py
git diff 18.0..19.0 report/abstract_report.py
```

---

### 5.5 Search Query Quick Reference

| Purpose | Elasticsearch Query | Grep Command | GitHub Search |
|---------|-------------------|--------------|---------------|
| Report Rendering | `_render_qweb_html OR get_html` | `grep -r "_render_qweb_html\|get_html"` | `_render_qweb_html language:Python` |
| Abstract Reports | `_get_report_values res_ids OR docids` | `grep -r "_get_report_values"` | `_get_report_values language:Python` |
| JS Report Actions | `ReportAction @web/webclient` | `grep -r "ReportAction" addons/web/static/` | `ReportAction language:JavaScript` |
| Command Class | `Command.link Command.clear` | `grep -r "Command\.link\|Command\.clear"` | `Command.link language:Python` |
| Search Methods | `search_fetch account.move.line` | `grep -r "search_fetch.*account\.move\.line"` | `search_fetch language:Python` |

---

## 6. Risk Assessment

### 6.1 High Risk Areas

1. **Report Rendering API** ⚠️ **HIGH RISK**
   - **Reason**: Core API changes are common between major versions
   - **Impact**: All reports may fail if not updated correctly
   - **Mitigation**: Test thoroughly, have rollback plan

2. **JavaScript/OWL Compatibility** ⚠️ **MEDIUM RISK**
   - **Reason**: Frontend framework updates can break patches
   - **Impact**: Export buttons may not work
   - **Mitigation**: Verify import paths and class names

### 6.2 Medium Risk Areas

3. **QWeb Template Syntax** ⚠️ **MEDIUM RISK**
   - **Reason**: Template engine may have syntax changes
   - **Impact**: Report rendering errors
   - **Mitigation**: Review Odoo 19 QWeb documentation

4. **Model Field Access** ⚠️ **LOW RISK**
   - **Reason**: Field access patterns usually stable
   - **Impact**: Potential data access issues
   - **Mitigation**: Test with various data scenarios

### 6.3 Low Risk Areas

5. **Security Files** ✅ **LOW RISK**
   - **Reason**: Security structure is stable
   - **Impact**: Access control issues
   - **Mitigation**: Verify access rights after migration

6. **Query Methods** ✅ **LOW RISK**
   - **Reason**: Already using Odoo 19 compatible methods
   - **Impact**: Minimal
   - **Mitigation**: None needed

---

## 7. Migration Execution Order

### Step 1: Setup and Preparation (1-2 hours)
1. Set up Odoo 19 development environment
2. Create new branch: `19.0` (source control provides backup)
3. **Set up Elasticsearch Docker image** (PRIMARY STEP - see Section 5.1)
   - Pull Elasticsearch Docker image
   - Run Elasticsearch container (see Section 5.1.2)
   - Index Odoo 19 codebase (see Section 5.1.3)
   - Verify indexing works (see Section 5.1.4)
4. **If Elasticsearch unavailable**: Set up fallback tools (grep, IDE search, GitHub access)
5. Review Odoo 19 release notes

### Step 2: Manifest Update (15 minutes)
1. Update `__manifest__.py` version to `19.0.1.0.0`
2. Verify dependencies are Odoo 19 compatible

### Step 3: Code Review Using Elasticsearch (2-3 hours) 🔍 PRIMARY STEP
**Use Elasticsearch Docker to review Odoo 19 code patterns before making changes:**

1. **Search Report Rendering API** (Section 5.2.1)
   - Query Elasticsearch for `_render_qweb_html` and `get_html`
   - Verify which method is used in Odoo 19
   - Note any parameter changes

2. **Search Abstract Report Methods** (Section 5.2.2)
   - Query for `_get_report_values` signatures
   - Verify parameter names (`docids` vs `res_ids`)

3. **Search JavaScript Report Actions** (Section 5.2.3)
   - Find `ReportAction` class location
   - Verify import paths

4. **Verify Command Class Usage** (Section 5.2.4)
   - Confirm usage patterns match current code

5. **Review Model Query Patterns** (Section 5.2.5)
   - Verify `search_fetch` usage matches Odoo 19 patterns

**If Elasticsearch unavailable**, use fallback methods (Section 5.4):
- Use grep/IDE search to find the same patterns
- Compare with OCA 19.0 branch if available

### Step 4: Core API Updates Based on Code Review (2-4 hours)
Based on Elasticsearch code review findings (from Step 3):
1. Update `ir_actions_report.py` if needed (use findings from Step 3)
2. Update abstract report methods if signature changed
3. Test report rendering
4. Fix any immediate errors

### Step 5: Model Verification (1-2 hours)
1. Verify all model code against Odoo 19 patterns (use Elasticsearch if needed)
2. Test model methods
3. Fix any compatibility issues

### Step 6: JavaScript Updates (1-2 hours)
Based on Elasticsearch findings from Step 3:
1. Update JavaScript imports if paths changed
2. Test frontend functionality
3. Fix any console errors

### Step 7: Testing (4-8 hours)
1. Run all tests
2. Manual testing of all reports
3. Fix issues found
4. Performance testing

### Step 8: Documentation (1 hour)
1. Update README if needed
2. Update changelog
3. Document any breaking changes

**Total Estimated Time**: 10-20 hours (Elasticsearch setup and code review, no backup/automated tool overhead)

### Step 4: Model Verification (1-2 hours)
1. Verify all model code
2. Test model methods
3. Fix any compatibility issues

### Step 5: JavaScript Updates (1-2 hours)
1. Update JavaScript imports if needed
2. Test frontend functionality
3. Fix any console errors

### Step 6: Testing (4-8 hours)
1. Run all tests
2. Manual testing of all reports
3. Fix issues found
4. Performance testing

### Step 7: Documentation (1 hour)
1. Update README if needed
2. Update changelog
3. Document any breaking changes

**Total Estimated Time**: 10-20 hours (depending on issues found)

---

## 8. Post-Migration Tasks

### 8.1 Optimization Opportunities

1. **Query Optimization**
   - Convert more `search_read()` to `search_fetch()` for better performance
   - Review and optimize field lists
   - Add database indexes if needed

2. **Code Modernization**
   - Use new Odoo 19 features where beneficial
   - Remove deprecated code patterns
   - Improve error handling

### 8.2 Documentation Updates

1. Update module README
2. Update changelog
3. Create migration notes for users
4. Update developer documentation

### 8.3 Continuous Monitoring

1. Monitor error logs
2. Collect user feedback
3. Track performance metrics
4. Plan future improvements

---

## 9. Rollback Plan

If migration fails or critical issues are found:

1. **Immediate Rollback**
   - Revert to Odoo 18 version
   - Restore from backup if needed
   - Document issues found

2. **Partial Rollback**
   - Keep working reports
   - Disable problematic reports temporarily
   - Fix issues incrementally

3. **Rollback Checklist**
   - [ ] Backup current state
   - [ ] Revert code changes
   - [ ] Restore database if needed
   - [ ] Verify system functionality
   - [ ] Document rollback reason

---

## 10. Resources and References

### 10.1 Odoo 19 Documentation
- [Odoo 19 Release Notes](https://www.odoo.com/documentation/19.0/)
- [Odoo 19 Developer Documentation](https://www.odoo.com/documentation/19.0/developer/)
- [Migration Guide](https://www.odoo.com/documentation/19.0/developer/misc.html#migration)

### 10.2 OCA Resources
- [OCA account-financial-reporting Repository](https://github.com/OCA/account-financial-reporting)
- [OCA 19.0 Branch](https://github.com/OCA/account-financial-reporting/tree/19.0)
- [OCA Migration Guidelines](https://github.com/OCA/maintainer-tools/wiki/Migration-to-version-19.0)

### 10.3 Code Search Tools

**PRIMARY:**
- **Elasticsearch Docker Image** - See Section 5.1 for setup instructions
  - Fastest and most comprehensive code search
  - Semantic search capabilities
  - Best for large codebase analysis

**FALLBACK:**
- GitHub search for Odoo 19.0 branch
- GitHub search for OCA modules (19.0 branches)
- Odoo Community Forum
- Local grep/IDE search tools

**Note**: odoo-module-migrator is not used because it does not support Odoo 19.0 (only supports up to 18.0).

---

## 11. Notes and Considerations

### 11.1 Lazy Migration Strategy

This plan focuses on **minimal changes** for compatibility:
- ✅ Keep existing code patterns where possible
- ✅ Only change what's necessary for Odoo 19 compatibility
- ✅ Avoid refactoring unless required
- ✅ Maintain backward compatibility patterns where possible

### 11.2 Testing Priority

Focus testing on:
1. **Critical Path**: Report generation (all formats)
2. **User-Facing**: Wizards and UI
3. **Data Integrity**: Report accuracy
4. **Performance**: Large datasets

### 11.3 Version Numbering

Following Odoo versioning:
- **19.0.1.0.0**: First version for Odoo 19
- Increment last digit for bug fixes
- Increment middle digits for feature additions

---

## 12. Appendix: File-by-File Checklist

### Models
- [ ] `models/account.py` - Verify field definitions
- [ ] `models/account_group.py` - Verify computed fields
- [ ] `models/account_move_line.py` - Verify Command usage
- [ ] `models/account_age_report_configuration.py` - Verify model structure
- [ ] `models/ir_actions_report.py` - **HIGH PRIORITY** - Update report rendering
- [ ] `models/res_config_settings.py` - Verify settings integration

### Reports
- [ ] `report/abstract_report.py` - Verify abstract methods
- [ ] `report/abstract_report_xlsx.py` - Verify XLSX generation
- [ ] `report/general_ledger.py` - Test report
- [ ] `report/general_ledger_xlsx.py` - Test XLSX export
- [ ] `report/trial_balance.py` - Test report
- [ ] `report/trial_balance_xlsx.py` - Test XLSX export
- [ ] `report/open_items.py` - Test report
- [ ] `report/open_items_xlsx.py` - Test XLSX export
- [ ] `report/aged_partner_balance.py` - Test report
- [ ] `report/aged_partner_balance_xlsx.py` - Test XLSX export
- [ ] `report/vat_report.py` - Test report
- [ ] `report/vat_report_xlsx.py` - Test XLSX export
- [ ] `report/journal_ledger.py` - Test report
- [ ] `report/journal_ledger_xlsx.py` - Test XLSX export

### Wizards
- [ ] `wizard/abstract_wizard.py` - Verify base wizard
- [ ] `wizard/general_ledger_wizard.py` - Test wizard
- [ ] `wizard/trial_balance_wizard.py` - Test wizard
- [ ] `wizard/open_items_wizard.py` - Test wizard
- [ ] `wizard/aged_partner_balance_wizard.py` - Test wizard
- [ ] `wizard/vat_report_wizard.py` - Test wizard
- [ ] `wizard/journal_ledger_wizard.py` - Test wizard

### Views
- [ ] All `view/*.xml` files - Verify structure
- [ ] All `wizard/*_wizard_view.xml` files - Test forms
- [ ] `reports.xml` - Verify report definitions
- [ ] `menuitems.xml` - Verify menu structure

### Assets
- [ ] `static/src/js/report_action.esm.js` - **HIGH PRIORITY** - Update if needed
- [ ] `static/src/js/report.esm.js` - Verify functionality
- [ ] `static/src/css/*.css` - Verify styling

### Templates
- [ ] `report/templates/*.xml` - Verify QWeb syntax

### Tests
- [ ] `tests/test_*.py` - Update and run all tests

### Configuration
- [ ] `__manifest__.py` - Update version
- [ ] `__init__.py` - Verify imports
- [ ] `security/*.csv` - Verify access rights
- [ ] `security/*.xml` - Verify security rules

---

## End of Migration Plan

**Document Version**: 1.0  
**Created**: 2024  
**Last Updated**: 2024  
**Status**: Draft - Ready for Execution

---

## Quick Reference: Common Odoo 18 → 19 Changes

**⚠️ IMPORTANT**: Use **Elasticsearch Docker image** (Section 5.1) to verify all items marked "VERIFY" before making changes. This provides the most accurate and comprehensive code review.

| Area | Odoo 18 | Odoo 19 | Status | Elasticsearch Query (Section 5.2) |
|------|---------|---------|--------|-----------------------------------|
| Report Rendering | `_render_qweb_html()` | Verify: `get_html()`? | ⚠️ VERIFY | Section 5.2.1 |
| Model Queries | `search_read()`, `search_fetch()` | Same | ✅ Compatible | Section 5.2.5 |
| Many2many Updates | `Command.link()`, `Command.clear()` | Same | ✅ Compatible | Section 5.2.4 |
| JavaScript | OWL 2.x/3.x | OWL 4.x? | ⚠️ VERIFY | Section 5.2.3 |
| QWeb Templates | QWeb 3.x | QWeb 4.x? | ⚠️ VERIFY | Use fallback methods (Section 5.4) |
| API Decorators | `@api.model`, `@api.depends` | Same | ✅ Compatible | Not needed |

**Legend:**
- ✅ **Compatible**: No changes needed
- ⚠️ **Verify**: Needs investigation using Elasticsearch (PRIMARY) or fallback methods
- ❌ **Incompatible**: Requires changes (none identified yet)

**Verification Workflow:**
1. **First**: Use Elasticsearch Docker (Section 5.1-5.2) to search Odoo 19 codebase
2. **If unavailable**: Use fallback methods (Section 5.4): grep, IDE search, GitHub
3. **Make changes** based on findings
4. **Test** thoroughly before proceeding

