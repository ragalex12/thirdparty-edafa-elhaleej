#!/usr/bin/env python3
"""
Create/update OpenProject Phase 2 delivery WP under #135 — HR payroll + screenshots.

Usage:
  SYNC_SCRIPT=sync_phase2_delivery_wp135.py bash ssh_to_master_and_sync.sh
"""
from __future__ import annotations

import argparse
import json
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
    TYPE_TASK,
    STATUS_NEW,
    PRIORITY_NORMAL,
    get_base_url,
    get_token,
    load_dotenv,
)

PUBLIC_BASE = "https://master.tailcf9988.ts.net:10081"
MARKER = "<!-- phase2-implementation-delivery-2026-07-03 -->"
TODAY = date.today().isoformat()

WP_SUBJECT = "Phase 2 — HR Payslip Rules + assumed decisions (WP #139) / delivery + screenshots"

SCREENSHOTS_DIR = (
    Path(__file__).resolve().parent.parent
    / "gpc_gulf_hr_payroll_ext"
    / "e2e"
    / "screenshots"
    / "gulf-phase2"
)

SCREENSHOT_CAPTIONS = {
    "01-after-login.png": "01 — After login (payroll UAT)",
    "02-payroll-structure-gulf-standard.png": "02 — GULF_STANDARD payroll structure (WP #139)",
    "03-employee-uat.png": "03 — UAT employee with Gulf contract",
    "04-payslips-list.png": "04 — Employee payslips list",
    "05-payslip-form.png": "05 — Payslip computed lines",
    "06-payslip-net-12900.png": "06 — NET 12,900.00 UAT",
}


def build_description() -> str:
    return f"""{MARKER}

# Phase 2 — HR Payslip Rules + قرارات افتراضية (WP #139)

**المهمة الأم:** [WP #135]({PUBLIC_BASE}/work_packages/135)  
**تاريخ التسليم:** {TODAY}  
**الحالة:** ✅ **HR Done** — Legacy ⏸️ مؤجل

---

## انتظرنا رد العميل — لم يصل

أرسلنا أسئلة HR/Legacy على [WP #140]({PUBLIC_BASE}/work_packages/140).  
**لم يرد العميل** — اعتمدنا أبسط قرارات (انظر WP #140).

| # | القرار | الافتراض |
|---|--------|----------|
| 3 | VAT | قبل الضريبة |
| 5 | HR | Payslip Rules فقط |
| 6 | Legacy | **مؤجل** |
| 7 | النطاق | HR فقط |
| 8 | DB | trgulf_Mrp |

---

## ما تم إنجازه

| WP | الميزة | الحالة |
|----|--------|--------|
| [#139]({PUBLIC_BASE}/work_packages/139) | HR Payslip Rules | ✅ Done |
| [#145]({PUBLIC_BASE}/work_packages/145) | Legacy Payroll | ⏸️ Deferred |

**Phase 1:** [WP #150]({PUBLIC_BASE}/work_packages/150)

---

## الموديول

**`gpc_gulf_hr_payroll_ext`** — Odoo 19 — `trgulf_Mrp`

| Rule | الوصف |
|------|--------|
| GULF_TRAVEL | بدل انتقال من العقد |
| GULF_OTHER_ALW | بدلات أخرى |
| GULF_OT | إضافي (إدخال OT_AMT) |
| GULF_BONUS | زيادة/مكافأة |
| GULF_DED | خصم (DED_OTHER) |

**هيكل:** `GULF_STANDARD`

---

## UAT ✅

```
Wage 10,000 + Travel 500 + Other 200 + OT 1,500 + Bonus 1,000 - Ded 300 = NET 12,900
```

---

## لقطات الشاشة

📎 مرفقة — `gpc_gulf_hr_payroll_ext/e2e/screenshots/gulf-phase2/`

---

## مراجع

- `openproject_docs/ASSUMED_CLIENT_DECISIONS_AR.md`
- `openproject_docs/PHASE2_IMPLEMENTATION_DELIVERY.md`
"""


class Client:
    def __init__(self, base: str, token: str, dry_run: bool = False):
        self.base = base.rstrip("/")
        self.dry_run = dry_run
        self.auth = HTTPBasicAuth("apikey", token)
        self.h = {"Accept": "application/json"}

    def get(self, ep: str):
        return requests.get(f"{self.base}/api/v3{ep}", auth=self.auth, headers=self.h, timeout=120, verify=False)

    def post(self, ep: str, data: dict | None = None, files=None):
        if self.dry_run:
            return None
        headers = {"Accept": "application/json"}
        if files:
            return requests.post(f"{self.base}/api/v3{ep}", auth=self.auth, headers=headers, files=files, timeout=300, verify=False)
        return requests.post(
            f"{self.base}/api/v3{ep}", json=data, auth=self.auth,
            headers={**headers, "Content-Type": "application/json"}, timeout=120, verify=False,
        )

    def patch(self, ep: str, data: dict):
        if self.dry_run:
            return None
        return requests.patch(
            f"{self.base}/api/v3{ep}", json=data, auth=self.auth,
            headers={**self.h, "Content-Type": "application/json"}, timeout=120, verify=False,
        )


def find_existing_wp(client: Client) -> int | None:
    r = client.get(f"/work_packages/{PARENT_WP_ID}")
    if r.status_code != 200:
        return None
    for link in r.json().get("_links", {}).get("children", []):
        href = link.get("href", "")
        if "/work_packages/" not in href:
            continue
        cid = int(href.rsplit("/", 1)[-1])
        cr = client.get(f"/work_packages/{cid}")
        if cr.status_code != 200:
            continue
        wp = cr.json()
        raw = wp.get("description", {}).get("raw", "") or ""
        subj = wp.get("subject", "")
        if MARKER in raw or subj.startswith("Phase 2 — HR Payslip"):
            return cid
    return None


def upload_attachment(client: Client, wp_id: int, path: Path) -> bool:
    if not path.is_file():
        return False
    caption = SCREENSHOT_CAPTIONS.get(path.name, path.name)
    metadata = json.dumps({"fileName": path.name, "description": caption})
    with path.open("rb") as fh:
        pr = client.post(
            f"/work_packages/{wp_id}/attachments",
            files={"file": (path.name, fh, "application/octet-stream"), "metadata": (None, metadata)},
        )
    if client.dry_run:
        return True
    if pr and pr.status_code in (200, 201):
        print(f"  ✓ attached {path.name}")
        return True
    print(f"  ✗ attach {path.name}: {pr.status_code if pr else '?'}")
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-attachments", action="store_true")
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
        base = os.environ.get("OPENPROJECT_URL_FALLBACK", "https://37-61-219-169.nip.io:10081")
        client = Client(base, token, dry_run=args.dry_run)
        tr = client.get(f"/projects/{PROJECT_ID}")
    if tr.status_code != 200:
        print("ERROR: Cannot reach OpenProject")
        return 1
    print(f"Connected: {base}")

    desc = build_description()
    wp_id = find_existing_wp(client)

    if wp_id:
        gr = client.get(f"/work_packages/{wp_id}")
        wp = gr.json()
        pr = client.patch(
            f"/work_packages/{wp_id}",
            {"lockVersion": wp.get("lockVersion", 0), "description": {"format": "markdown", "raw": desc}},
        )
        if not args.dry_run and pr and pr.status_code not in (200, 201):
            print(f"✗ PATCH #{wp_id} failed")
            return 1
        print(f"✓ Updated WP #{wp_id}")
    else:
        payload = {
            "subject": WP_SUBJECT,
            "description": {"format": "markdown", "raw": desc},
            "type": {"href": f"/api/v3/types/{TYPE_TASK}"},
            "status": {"href": f"/api/v3/statuses/{STATUS_NEW}"},
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
            print(f"✗ CREATE failed: {pr.status_code if pr else '?'} {pr.text[:300] if pr else ''}")
            return 1

    if not args.skip_attachments and wp_id and SCREENSHOTS_DIR.is_dir():
        print(f"Uploading from {SCREENSHOTS_DIR} ...")
        for png in sorted(SCREENSHOTS_DIR.glob("*.png")):
            upload_attachment(client, wp_id, png)

    url = f"{PUBLIC_BASE}/work_packages/{wp_id}"
    print(f"\n========== PHASE 2 DELIVERY WP ==========")
    print(url)
    print("=========================================")

    out = Path(__file__).resolve().parent.parent / "openproject_docs" / "PHASE2_DELIVERY_WP.txt"
    out.write_text(f"Phase 2 Delivery WP: {url}\nDate: {TODAY}\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
