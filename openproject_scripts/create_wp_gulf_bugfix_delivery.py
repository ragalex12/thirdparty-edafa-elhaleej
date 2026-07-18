#!/usr/bin/env python3
"""
Create/close OpenProject delivery WP — Gulf production bug fixes (2 bugs).

Usage:
  SYNC_SCRIPT=create_wp_gulf_bugfix_delivery.py bash ssh_to_master_and_sync.sh
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
MARKER = "<!-- gulf-bugfix-delivery-2026-07-08 -->"
WP_SUBJECT = "[Gulf] Delivery — Quotation PDF + Project Dashboard fixes (2 bugs)"

DESCRIPTION = f"""# Gulf Production Bug Fixes — Delivery

**Parent:** [WP #{PARENT_WP_ID}]({PUBLIC_BASE}/work_packages/{PARENT_WP_ID})  
**Date:** {TODAY}  
**Environment:** https://gpc.odoo.com.se · DB `trgulf_Mrp`  
**Status:** ✅ **Delivered & verified**

{MARKER}

---

## Summary

| # | Bug | Module | Commit | Status |
|---|-----|--------|--------|--------|
| 1 | Quotation PDF `KeyError: 'o'` | `retention_performance_bond` | `332884b` | ✅ Fixed |
| 2 | Dashboard `OwlError` (Project Details) | `gpc_gulf_project_ext` | `81d94dc` | ✅ Fixed |

---

## Bug 1 — Quotation / Sales Order PDF

**Symptom:** Printing Quotation raised `QWebError: KeyError: 'o'` on `o.contract_ref`.

**Root cause:** `retention_performance_bond/views/report_saleorder.xml` used `o.` but Odoo 19 `sale.report_saleorder_document` exposes the record as **`doc`**.

**Fix:** Replace all `o.` → `doc.` in sale order report template only (invoice report unchanged).

**Verification:**
- Quotation PDF **S00030** ✅ (68,246 bytes)
- Sales Order PDF ✅ (68,068 bytes)
- Unit tests `gpc_gulf_project_ext` **7/7** ✅

---

## Bug 2 — Project Dashboard OWL

**Symptom:** Dashboard button raised `OwlError: Element cannot be located` on XPath `//ProjectRightSidePanelSection[@name='milestones']`.

**Root cause:** OWL prop is `name="'milestones'"` — `@name='milestones'` does not match on Odoo 19.

**Fix:** XPath → `(//ProjectRightSidePanelSection)[1]` with `position="after"` in `gpc_gulf_project_ext/static/.../project_right_side_panel.xml`.

**Verification (Playwright browser — 4/4 passed):**
- Project Details section visible ✅
- Description HTML (lists/paragraphs) ✅
- Contract Amount currency format (**591,707 SR**) ✅
- Project without description ✅
- Project without contract amount ✅
- Project user (non-manager): description only, no access error ✅

**Screenshots:** `gpc_gulf_project_ext/e2e/screenshots/bug2-verification/`

---

## Git commits

```
332884b fix(retention_performance_bond): use doc in sale order PDF report
81d94dc fix(gpc_gulf_project_ext): stabilize Project Details dashboard XPath
```

**Checkpoint tag:** `checkpoint/pre-gulf-bugfix-2026-07-08`

---

## Upgrade commands (executed)

```bash
sudo -u odoo odoo -c /etc/odoo/odoo.conf -d trgulf_Mrp -u retention_performance_bond --stop-after-init
sudo -u odoo odoo -c /etc/odoo/odoo.conf -d trgulf_Mrp -u gpc_gulf_project_ext --stop-after-init
```

---

## Notify

**@Moustafa** — please verify on https://gpc.odoo.com.se (hard refresh on Dashboard).

---

## Acceptance

- [x] Quotation PDF works
- [x] Sales Order PDF works
- [x] Dashboard opens without OwlError
- [x] Project Details shows Description + Contract Amount
- [x] No new Odoo log errors from these fixes
"""

JOURNAL = f"""✅ Delivered ({TODAY}) — 2 Gulf production bugs fixed and verified.

Bug 1: retention_performance_bond — sale PDF `o` → `doc` (commit 332884b)
Bug 2: gpc_gulf_project_ext — dashboard XPath fix (commit 81d94dc)

@Moustafa — ready for client verification on gpc.odoo.com.se / trgulf_Mrp.
"""

PARENT_APPEND = f"""

---

{MARKER}

## Production bugfix delivery ({TODAY})

- **Delivery WP:** see child with subject *Quotation PDF + Project Dashboard fixes*
- **Bug 1:** Quotation PDF KeyError `o` → fixed in `retention_performance_bond` (`332884b`)
- **Bug 2:** Dashboard OwlError → fixed in `gpc_gulf_project_ext` (`81d94dc`)
- **Verified:** S00030 PDF + Playwright Dashboard 4/4 — **@Moustafa** to confirm on live site
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

    def patch(self, ep: str, data: dict):
        if self.dry_run:
            print(f"[dry-run] PATCH {ep}")
            return None
        return requests.patch(
            f"{self.base}/api/v3{ep}",
            json=data,
            auth=self.auth,
            headers=self.h,
            timeout=120,
            verify=False,
        )


def get_closed_status_id(client: Client) -> int | None:
    r = client.get("/statuses")
    if r.status_code != 200:
        return None
    for st in r.json().get("_embedded", {}).get("elements", []):
        name = (st.get("name") or "").lower()
        if st.get("isClosed") or name in ("closed", "done", "complete", "resolved"):
            return st["id"]
    return None


def find_wp(client: Client) -> int | None:
    r = client.get(
        f"/work_packages?filters=[{{\"parent\":{{\"operator\":\"=\",\"values\":[\"{PARENT_WP_ID}\"]}}}}]"
    )
    if r.status_code != 200:
        return None
    for wp in r.json().get("_embedded", {}).get("elements", []):
        raw = (wp.get("description") or {}).get("raw") or ""
        subj = wp.get("subject") or ""
        if MARKER in raw or "Quotation PDF + Project Dashboard" in subj:
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

    closed_id = get_closed_status_id(client)
    wp_id = find_wp(client)

    if wp_id:
        gr = client.get(f"/work_packages/{wp_id}")
        wp = gr.json()
        payload = {
            "lockVersion": wp.get("lockVersion", 0),
            "description": {"format": "markdown", "raw": DESCRIPTION},
        }
        if closed_id:
            payload["status"] = {"href": f"/api/v3/statuses/{closed_id}"}
        pr = client.patch(f"/work_packages/{wp_id}", payload)
        if args.dry_run or (pr and pr.status_code in (200, 201)):
            print(f"✓ Updated & closed WP #{wp_id}")
        else:
            print(f"✗ PATCH failed: {pr.status_code if pr else '?'}")
            return 1
    else:
        payload = {
            "subject": WP_SUBJECT,
            "description": {"format": "markdown", "raw": DESCRIPTION},
            "type": {"href": f"/api/v3/types/{TYPE_TASK}"},
            "status": {"href": f"/api/v3/statuses/{closed_id or STATUS_NEW}"},
            "priority": {"href": f"/api/v3/priorities/{PRIORITY_NORMAL}"},
            "parent": {"href": f"/api/v3/work_packages/{PARENT_WP_ID}"},
        }
        pr = client.post(f"/projects/{PROJECT_ID}/work_packages", payload)
        if args.dry_run:
            wp_id = 0
        elif pr and pr.status_code in (200, 201):
            wp_id = pr.json()["id"]
            print(f"✓ Created WP #{wp_id}")
        else:
            print(f"✗ CREATE failed: {pr.text[:300] if pr else ''}")
            return 1

    if wp_id:
        client.post(
            f"/work_packages/{wp_id}/activities",
            {"comment": {"format": "plain", "raw": JOURNAL}},
        )

    parent = client.get(f"/work_packages/{PARENT_WP_ID}")
    if parent.status_code == 200:
        pwp = parent.json()
        praw = (pwp.get("description") or {}).get("raw") or ""
        if MARKER not in praw:
            client.patch(
                f"/work_packages/{PARENT_WP_ID}",
                {
                    "lockVersion": pwp.get("lockVersion", 0),
                    "description": {
                        "format": "markdown",
                        "raw": praw.rstrip() + PARENT_APPEND,
                    },
                },
            )
            print(f"✓ Updated parent #{PARENT_WP_ID}")

    url = f"{PUBLIC_BASE}/work_packages/{wp_id}"
    out = Path(__file__).resolve().parent.parent / "openproject_docs"
    out.mkdir(parents=True, exist_ok=True)
    (out / "GULF_BUGFIX_DELIVERY_WP.txt").write_text(f"{url}\n{TODAY}\n", encoding="utf-8")

    wa = f"""السلام عليكم مصطفى 👋

✅ *تم إصلاح واختبار مشكلتين على Gulf Odoo*

*البيئة:* gpc.odoo.com.se — trgulf_Mrp

*1) طباعة Quotation PDF*
• كان يظهر: KeyError: 'o'
• تم الإصلاح في retention_performance_bond
• تم اختبار S00030 ✅

*2) Project Dashboard*
• كان يظهر: OwlError
• تم الإصلاح في gpc_gulf_project_ext
• Project Details + Description + Contract Amount ✅
• اختبار Playwright 4/4 ✅

*OpenProject:*
{url}

يرجى التحقق على الموقع (Hard Refresh على Dashboard).

تحياتي ✨
"""
    (out / "WHATSAPP_GULF_BUGFIX_DELIVERY_MOSTAFA_AR.txt").write_text(wa, encoding="utf-8")
    print(f"\nWhatsApp draft: {out / 'WHATSAPP_GULF_BUGFIX_DELIVERY_MOSTAFA_AR.txt'}")
    print(f"Delivery WP: {url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
