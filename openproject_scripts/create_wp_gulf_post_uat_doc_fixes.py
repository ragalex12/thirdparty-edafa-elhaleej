#!/usr/bin/env python3
"""
Create OpenProject WP — Gulf WP #135 post-UAT fixes:
  1) Lazy UAT guide not in server repo path
  2) Invoice form missing dimension fields (#138 UI gap)

Usage:
  SYNC_SCRIPT=create_wp_gulf_post_uat_doc_fixes.py bash ssh_to_master_and_sync.sh
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from pathlib import Path

import requests
from requests.auth import HTTPBasicAuth

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sync_requirements_review_wp135 import (  # noqa: E402
    ENV_CANDIDATES,
    PARENT_WP_ID,
    PRIORITY_NORMAL,
    PROJECT_ID,
    STATUS_NEW,
    TYPE_TASK,
    get_base_url,
    get_token,
    load_dotenv,
)

PUBLIC_BASE = "https://master.tailcf9988.ts.net:10081"
TODAY = date.today().isoformat()
MARKER = "<!-- gulf-lazy-guide-repo-fix-2026-07-08 -->"
WP_SUBJECT = (
    "[Gulf] Post-UAT fixes: Lazy UAT guide in repo + invoice dimension fields (#138)"
)

DESCRIPTION = f"""# Gulf WP #135 — Post-verification fixes

**Parent:** [WP #{PARENT_WP_ID}]({PUBLIC_BASE}/work_packages/{PARENT_WP_ID})  
**Date:** {TODAY}  
**Source:** Verification audit + client Lazy UAT guide handoff  
**DB:** `trgulf_Mrp` · **Modules:** `gpc_gulf_project_ext`, `gpc_gulf_hr_payroll_ext`

{MARKER}

---

## Problem summary

After WP #135 delivery verification, two gaps block smooth **client self-testing** and **UI parity**:

| # | Issue | Severity | WP |
|---|-------|----------|-----|
| 1 | **Lazy UAT guide** exists only on infra host path, not in Odoo server repo | High (docs) | #135 / UAT |
| 2 | **Invoice form** missing Length/Width/Area columns; totals are correct but fields invisible | Medium (UI) | #138 |

---

## Bug 1 — Lazy UAT guide location

### Symptom

Client-facing guide written at:

`/home/sabry/infra/openproject/docs/gulf-wp135/GULF_LAZY_USER_TESTING_GUIDE.md`

**Not present** under server addons docs:

`/opt/localaddons/openproject_docs/gulf-wp135/`

Developers and client testers on the Gulf server cannot find the guide in the standard repo path used for Phase 1/2 delivery docs.

### Code / repo analysis

| Path | Status before fix |
|------|-------------------|
| `openproject_docs/PHASE1_IMPLEMENTATION_DELIVERY.md` | ✅ in `/opt/localaddons/openproject_docs/` |
| `openproject_docs/gulf_delivery/DEVELOPER_GUIDE.md` | ✅ in repo |
| `openproject_docs/gulf-wp135/GULF_LAZY_USER_TESTING_GUIDE.md` | ❌ missing on server |

No Odoo module change required — **documentation sync only**.

### Fix plan (Bug 1)

1. Create directory `/opt/localaddons/openproject_docs/gulf-wp135/` on Gulf server.
2. Copy `GULF_LAZY_USER_TESTING_GUIDE.md` from infra path into repo.
3. Add one-line pointer in `openproject_docs/gulf_delivery/DEVELOPER_GUIDE.md` or `WP135_FINAL_CLOSURE.md` → link to lazy guide.
4. (Optional) Attach guide to OpenProject WP #163 or parent #135 as reference file.

### Acceptance (Bug 1)

- [ ] File exists: `/opt/localaddons/openproject_docs/gulf-wp135/GULF_LAZY_USER_TESTING_GUIDE.md`
- [ ] Arabic guide lists all 7 use cases with numbers: 591,706.80 / 64,562.40 / 12,900.00
- [ ] Client can open guide from repo without SSH to infra host

---

## Bug 2 — Invoice line dimension fields not on form (#138)

### Symptom

Lazy UAT Use Case 4 notes: after Confirm SO → Create Invoice, **Untaxed Amount = 64,562.40** ✅ but **Length / Width / Area** do not appear on invoice form.

### Code analysis

**Fields exist and accounting works:**

| File | What it does |
|------|----------------|
| `gpc_gulf_project_ext/models/sale_order_line.py` | `length_cm`, `width_cm`, `area_sqm`; `_gpc_effective_quantity()` |
| `gpc_gulf_project_ext/models/account_move_line.py` | Same fields; `_gpc_effective_quantity()` for invoice tax base |
| `gpc_gulf_project_ext/models/account_move.py` | `_prepare_product_base_line_for_taxes_computation()` uses effective qty |
| `gpc_gulf_project_ext/views/sale_order_views.xml` | SO form/list shows dimensions ✅ |

**Missing:**

- No `views/account_move_views.xml` inheriting `account.view_move_form` to show `length_cm`, `width_cm`, `area_sqm` on `invoice_line_ids`.

**Verification (trgulf_Mrp):** `ir.ui.view` search for `length_cm` on `account.move` → **empty**.

Totals verified correct via `uat_scenario.py` and audit — **UI-only gap**.

### Fix plan (Bug 2)

1. **Create** `gpc_gulf_project_ext/views/account_move_views.xml`:
   - Inherit `account.view_move_form`
   - Add optional columns on `invoice_line_ids` list: `length_cm`, `width_cm`, `area_sqm` (readonly)
   - Add same fields on invoice line form sub-view (before `price_unit`)
2. **Register** in `__manifest__.py` `data` list.
3. **Upgrade** module on `trgulf_Mrp`: `-u gpc_gulf_project_ext --stop-after-init`
4. **Test:** Open invoice from S00030 → columns visible; subtotal still **64,562.40**
5. **Update** Lazy UAT guide Use Case 4 — remove "UI gap" note once fixed.

### Acceptance (Bug 2)

- [ ] Invoice form shows Length (CM), Width (CM), Area (M²) on product lines
- [ ] Values copied from SO (180 / 305 / 5.49 on UAT line)
- [ ] Untaxed total unchanged: **64,562.40**
- [ ] Existing unit test `test_invoice_preserves_dimension_totals` still passes

---

## Out of scope (do not fix in this WP)

| Item | Reason |
|------|--------|
| WP #145 Legacy payroll | Closed — no expansion |
| `date_range` / `odoo_test_helper` test loader crash | Third-party; unrelated env issue |
| HR module unit tests | Nice-to-have; UAT scripts already pass |

---

## Test checklist after both fixes

| Step | Expected |
|------|----------|
| Open lazy guide from repo path | File readable |
| UC3 S00030 | 64,562.40 |
| UC4 Invoice | 64,562.40 + dimensions visible on form |
| UC6 Payroll UAT | NET 12,900.00 |

---

## References

- Lazy guide: `openproject_docs/gulf-wp135/GULF_LAZY_USER_TESTING_GUIDE.md`
- Verification audit: `openproject_docs/gulf-wp135/` (if synced) or audit session 2026-07-08
- Module: `/opt/localaddons/gpc_gulf_project_ext/`
"""


class Client:
    def __init__(self, base: str, token: str, dry_run: bool = False):
        self.base = base.rstrip("/")
        self.dry_run = dry_run
        self.auth = HTTPBasicAuth("apikey", token)
        self.h = {"Accept": "application/json", "Content-Type": "application/json"}

    def get(self, ep: str):
        return requests.get(
            f"{self.base}/api/v3{ep}",
            auth=self.auth,
            headers=self.h,
            timeout=120,
            verify=False,
        )

    def post(self, ep: str, data: dict):
        if self.dry_run:
            print(f"[dry-run] POST {ep}")
            return None
        return requests.post(
            f"{self.base}/api/v3{ep}",
            json=data,
            auth=self.auth,
            headers=self.h,
            timeout=120,
            verify=False,
        )


def find_existing(client: Client) -> int | None:
    r = client.get(f"/work_packages?filters=[{{\"parent\":{{\"operator\":\"=\",\"values\":[\"{PARENT_WP_ID}\"]}}}}]")
    if r.status_code != 200:
        return None
    for wp in r.json().get("_embedded", {}).get("elements", []):
        subj = wp.get("subject") or ""
        if MARKER in (wp.get("description") or {}).get("raw", "") or "Lazy UAT guide" in subj:
            return wp["id"]
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    for p in ENV_CANDIDATES:
        load_dotenv(p)
    token = get_token()
    if not token:
        print("ERROR: OPENPROJECT_API_TOKEN required")
        return 1

    base = os.environ.get("OPENPROJECT_URL", get_base_url())
    client = Client(base, token, dry_run=args.dry_run)
    tr = client.get(f"/projects/{PROJECT_ID}")
    if tr.status_code != 200:
        base = os.environ.get(
            "OPENPROJECT_URL_FALLBACK", "https://37-61-219-169.nip.io:10081"
        )
        client = Client(base, token, dry_run=args.dry_run)
        tr = client.get(f"/projects/{PROJECT_ID}")
    if tr.status_code != 200:
        print("ERROR: OpenProject unreachable")
        return 1
    print(f"Connected: {base}")

    existing = find_existing(client)
    if existing:
        print(f"✓ WP already exists: #{existing} — {PUBLIC_BASE}/work_packages/{existing}")
        return 0

    payload = {
        "subject": WP_SUBJECT,
        "description": {"format": "markdown", "raw": DESCRIPTION},
        "type": {"href": f"/api/v3/types/{TYPE_TASK}"},
        "status": {"href": f"/api/v3/statuses/{STATUS_NEW}"},
        "priority": {"href": f"/api/v3/priorities/{PRIORITY_NORMAL}"},
        "parent": {"href": f"/api/v3/work_packages/{PARENT_WP_ID}"},
    }
    pr = client.post(f"/projects/{PROJECT_ID}/work_packages", payload)
    if args.dry_run:
        print("[dry-run] would create WP")
        return 0
    if pr and pr.status_code in (200, 201):
        wp_id = pr.json()["id"]
        url = f"{PUBLIC_BASE}/work_packages/{wp_id}"
        out = Path(__file__).resolve().parent.parent / "openproject_docs" / "GULF_POST_UAT_FIXES_WP.txt"
        out.write_text(f"Created: {url}\nDate: {TODAY}\n", encoding="utf-8")
        print(f"✓ Created WP #{wp_id}")
        print(url)
        return 0
    print(f"✗ CREATE failed: {pr.status_code if pr else '?'} {pr.text[:400] if pr else ''}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
