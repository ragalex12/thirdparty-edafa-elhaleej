#!/usr/bin/env python3
"""
Final closure — WP #135 family. Confirm remaining proxy decisions and close all WPs.

Usage:
  SYNC_SCRIPT=sync_close_wp135_complete.py bash ssh_to_master_and_sync.sh
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
    PROJECT_ID,
    get_base_url,
    get_token,
    load_dotenv,
)

PUBLIC_BASE = "https://master.tailcf9988.ts.net:10081"
MARKER = "<!-- wp135-final-closure-2026-07-03 -->"
TODAY = date.today().isoformat()

IMPLEMENTATION_WPS = (136, 137, 138, 139, 145)
DUPLICATE_WPS = (141, 142, 143, 144)
DELIVERY_WPS = (150, 156)

DESC_140_FINAL = f"""{MARKER}

# قرارات العميل — مراجعة المتطلبات

**المهمة الأم:** [WP #135]({PUBLIC_BASE}/work_packages/135)  
**آخر تحديث:** {TODAY}  
**الحالة:** ✅ **مغلق — جميع القرارات معتمدة**

---

## قرارات معتمدة (8/8)

| # | القرار | الرد |
|---|--------|------|
| 1 | وصف المشروع | Description → Dashboard |
| 2 | مبلغ التعاقد | حقل مستقل `contract_amount` |
| 3 | VAT | **قبل ضريبة القيمة المضافة** (معتمد بالنيابة) |
| 4 | Quotation | Length/Width/Area + `Area × Qty × Price` + PDF |
| 5 | HR | **Payslip Rules فقط** (معتمد بالنيابة) |
| 6 | Legacy | **لا توسيع** — Standard Odoo |
| 7 | النطاق | HR على Community — Legacy بدون تغيير |
| 8 | قاعدة الاختبار | **`trgulf_Mrp`** (معتمد بالنيابة) |

---

## التسليم

| WP | الحالة |
|----|--------|
| [#136–#138]({PUBLIC_BASE}/work_packages/150) | ✅ Phase 1 |
| [#139]({PUBLIC_BASE}/work_packages/156) | ✅ Phase 2 HR |
| [#145]({PUBLIC_BASE}/work_packages/145) | ✅ مغلق — لا Legacy |

**مرجع:** `openproject_docs/WP135_FINAL_CLOSURE.md`
"""

DESC_135_CLOSED = f"""{MARKER}

# مشاريع الخليج الصناعى — WP #135

**الحالة:** ✅ **مغلق — اكتمل التنفيذ** ({TODAY})

---

## Scope delivered

| # | Feature | WP | Module |
|---|---------|-----|--------|
| 1 | Project Description on Dashboard | [#136]({PUBLIC_BASE}/work_packages/136) | `gpc_gulf_project_ext` |
| 2 | Contract Amount | [#137]({PUBLIC_BASE}/work_packages/137) | `contract_amount` |
| 3 | Quotation dimensions + pricing | [#138]({PUBLIC_BASE}/work_packages/138) | sale.order.line |
| 4 | HR Payslip Rules | [#139]({PUBLIC_BASE}/work_packages/139) | `gpc_gulf_hr_payroll_ext` |
| 5 | Legacy Payroll | [#145]({PUBLIC_BASE}/work_packages/145) | **No change** |

---

## Delivery documentation

- [Phase 1 + screenshots]({PUBLIC_BASE}/work_packages/150)
- [Phase 2 HR + screenshots]({PUBLIC_BASE}/work_packages/156)
- [Client decisions]({PUBLIC_BASE}/work_packages/140)

---

## UAT passed

- Quotation/Invoice: **64,562.40** (180×305×24×490)
- Payroll NET: **12,900.00**

**DB:** `trgulf_Mrp`
"""

JOURNAL_135 = f"""✅ WP #135 — إغلاق نهائي ({TODAY})

جميع البنود 1–5 منجزة:
• Phase 1: #136–#138 (WP #150)
• Phase 2 HR: #139 (WP #156)
• Legacy #145: مغلق — لا توسيع

قرارات معتمدة بالنيابة: VAT قبل الضريبة، Payslip Rules، trgulf_Mrp.

مرجع: WP135_FINAL_CLOSURE.md
"""

WP_DONE_NOTE = f"\n\n---\n{MARKER}\n\n**✅ Done** — closed {TODAY}. See [WP #135]({PUBLIC_BASE}/work_packages/135).\n"


class Client:
    def __init__(self, base: str, token: str, dry_run: bool = False):
        self.base = base.rstrip("/")
        self.dry_run = dry_run
        self.auth = HTTPBasicAuth("apikey", token)
        self.h = {"Accept": "application/json", "Content-Type": "application/json"}

    def get(self, ep: str):
        return requests.get(f"{self.base}/api/v3{ep}", auth=self.auth, headers=self.h, timeout=120, verify=False)

    def patch(self, ep: str, data: dict):
        if self.dry_run:
            return None
        return requests.patch(f"{self.base}/api/v3{ep}", json=data, auth=self.auth, headers=self.h, timeout=120, verify=False)

    def post(self, ep: str, data: dict):
        if self.dry_run:
            return None
        return requests.post(f"{self.base}/api/v3{ep}", json=data, auth=self.auth, headers=self.h, timeout=120, verify=False)


def get_closed_status_id(client: Client) -> int | None:
    r = client.get("/statuses")
    if r.status_code != 200:
        return None
    for st in r.json().get("_embedded", {}).get("elements", []):
        name = (st.get("name") or "").lower()
        if st.get("isClosed") or "closed" in name or "done" in name or "complete" in name:
            return st["id"]
    return None


def close_wp(client: Client, wp_id: int, closed_id: int, *, replace_desc: str | None = None, append_note: bool = True) -> bool:
    gr = client.get(f"/work_packages/{wp_id}")
    if gr.status_code != 200:
        print(f"✗ GET #{wp_id}: {gr.status_code}")
        return False
    wp = gr.json()
    raw = wp.get("description", {}).get("raw", "") or ""
    if MARKER in raw and wp.get("_links", {}).get("status", {}).get("title", "").lower() in ("closed", "done"):
        print(f"✓ #{wp_id} already closed")
        return True
    payload: dict = {
        "lockVersion": wp.get("lockVersion", 0),
        "status": {"href": f"/api/v3/statuses/{closed_id}"},
    }
    if replace_desc:
        payload["description"] = {"format": "markdown", "raw": replace_desc}
    elif append_note and MARKER not in raw:
        payload["description"] = {"format": "markdown", "raw": raw.rstrip() + WP_DONE_NOTE}
    pr = client.patch(f"/work_packages/{wp_id}", payload)
    if client.dry_run or (pr and pr.status_code in (200, 201)):
        print(f"✓ Closed #{wp_id} — {wp.get('subject', '')[:50]}")
        return True
    print(f"✗ PATCH #{wp_id}: {pr.status_code if pr else '?'}")
    return False


def add_journal(client: Client, wp_id: int, comment: str) -> bool:
    gr = client.get(f"/work_packages/{wp_id}/activities")
    if gr.status_code == 200:
        for act in gr.json().get("_embedded", {}).get("elements", []):
            note = (act.get("comment", {}) or {}).get("raw", "") or ""
            if "إغلاق نهائي" in note and TODAY in note:
                print(f"✓ Journal exists #{wp_id}")
                return True
    pr = client.post(f"/work_packages/{wp_id}/activities", {"comment": {"format": "plain", "raw": comment}})
    if client.dry_run or (pr and pr.status_code in (200, 201)):
        print(f"✓ Journal #{wp_id}")
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    for p in ENV_CANDIDATES:
        load_dotenv(p)
    token = get_token()
    if not token:
        return 1

    base = os.environ.get("OPENPROJECT_URL", get_base_url())
    client = Client(base, token, dry_run=args.dry_run)
    tr = client.get(f"/projects/{PROJECT_ID}")
    if tr.status_code != 200:
        base = os.environ.get("OPENPROJECT_URL_FALLBACK", "https://37-61-219-169.nip.io:10081")
        client = Client(base, token, dry_run=args.dry_run)
        tr = client.get(f"/projects/{PROJECT_ID}")
    if tr.status_code != 200:
        return 1
    print(f"Connected: {base}")

    closed_id = get_closed_status_id(client)
    if not closed_id:
        print("ERROR: no closed status")
        return 1

    ok = True
    ok &= close_wp(client, 140, closed_id, replace_desc=DESC_140_FINAL, append_note=False)
    ok &= close_wp(client, PARENT_WP_ID, closed_id, replace_desc=DESC_135_CLOSED, append_note=False)
    ok &= add_journal(client, PARENT_WP_ID, JOURNAL_135)

    for wp_id in IMPLEMENTATION_WPS:
        ok &= close_wp(client, wp_id, closed_id)

    for wp_id in DUPLICATE_WPS:
        ok &= close_wp(client, wp_id, closed_id)

    out = Path(__file__).resolve().parent.parent / "openproject_docs" / "WP135_FINAL_CLOSURE_SYNC.txt"
    out.write_text(
        f"WP #135 CLOSED: {TODAY}\n"
        f"{PUBLIC_BASE}/work_packages/135\n"
        f"Delivery: #150 #156\n",
        encoding="utf-8",
    )
    print(f"\n✅ WP #135 CLOSED: {PUBLIC_BASE}/work_packages/135")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
