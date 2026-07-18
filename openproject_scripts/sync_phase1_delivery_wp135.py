#!/usr/bin/env python3
"""
Create/update OpenProject delivery WP under #135 — Phase 1 implementation + screenshots.

Creates child WP with PNG attachments from Playwright run.

Usage (on machine with OpenProject API access, or via ssh_to_master_and_sync.sh):
  SYNC_SCRIPT=sync_phase1_delivery_wp135.py bash ssh_to_master_and_sync.sh

Env: OPENPROJECT_API_TOKEN, OPENPROJECT_URL
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
MARKER = "<!-- phase1-implementation-delivery-2026-07-03 -->"
TODAY = date.today().isoformat()

WP_SUBJECT = (
    "Phase 1 — تنفيذ Odoo + Playwright (WP #136–138) / Odoo delivery + screenshots"
)

SCREENSHOTS_DIR = Path(__file__).resolve().parent.parent / "gpc_gulf_project_ext" / "e2e" / "screenshots" / "gulf-phase1"

SCREENSHOT_CAPTIONS = {
    "01-login-page.png": "01 — Login page (trgulf_Mrp)",
    "02-after-login.png": "02 — After login",
    "03-project-form.png": "03 — Project form: GPC Playwright Phase1 UAT (WP #136/#137)",
    "04-project-expected-budget-contract-amount.png": "04 — Contract Amount 591,706.80 SR (WP #137)",
    "05-project-description-tab.png": "05 — Description tab with rich text (WP #136)",
    "06-project-dashboard.png": "06 — Project Dashboard navigation (WP #136)",
    "07-project-dashboard-details-panel.png": "07 — Dashboard Project Details panel (WP #136/#137)",
    "08-quotation-form-dimensions.png": "08 — Quotation S00030: 180×305→5.49×24×490=64,562.40 (WP #138)",
    "09-quotation-order-lines.png": "09 — Order lines table crop (WP #138)",
    "10-quotation-print-dialog.png": "10 — Print dialog (WP #138)",
    "10-quotation-print.pdf": "10 — Quotation PDF (if generated)",
    "11-final-quotation.png": "11 — Final quotation totals (WP #138)",
}


def build_description() -> str:
    return f"""{MARKER}

# Phase 1 — تنفيذ Odoo + Playwright (WP #136–138)

**المهمة الأم:** [WP #135]({PUBLIC_BASE}/work_packages/135) — مشاريع الخليج الصناعى  
**تاريخ التسليم:** {TODAY}  
**الحالة:** ✅ **تم التنفيذ والاختبار** (UAT + Playwright)

---

## ما تم إنجازه

| WP | الميزة | الحالة |
|----|--------|--------|
| [#136]({PUBLIC_BASE}/work_packages/136) | وصف المشروع في Dashboard | ✅ Done |
| [#137]({PUBLIC_BASE}/work_packages/137) | مبلغ التعاقد `contract_amount` | ✅ Done |
| [#138]({PUBLIC_BASE}/work_packages/138) | Quotation — مقاسات + Area + PDF | ✅ Done |

**خارج النطاق:** [#139]({PUBLIC_BASE}/work_packages/139) / [#145]({PUBLIC_BASE}/work_packages/145) — بانتظار العميل

---

## الموديول Odoo

**`gpc_gulf_project_ext`** — Odoo 19 — DB: `trgulf_Mrp`

| WP | التنفيذ |
|----|---------|
| #136 | `get_panel_data()` + OWL patch — عرض Description في Project Dashboard |
| #137 | حقل `contract_amount` (Monetary) + مزامنة مع `project_valuebvat` |
| #138 | `length_cm`, `width_cm`, `area_sqm` + `Area × Qty × Price` + فاتورة + PDF |

**المسار:** `/opt/localaddons/gpc_gulf_project_ext/`

---

## UAT — سيناريو العميل ✅

| Length | Width | Area | Qty | Price | **Total** |
|--------|-------|------|-----|-------|-----------|
| 180 CM | 305 CM | 5.49 m² | 24 | 490 | **64,562.40** |

تم التحقق في: Quotation line/total + Invoice line/total (Odoo shell)

---

## Playwright — لقطات الشاشة

**المشروع:** GPC Playwright Phase1 UAT  
**عرض السعر:** S00030

| # | اللقطة | ماذا أثبتنا |
|---|--------|-------------|
| 01 | Login | الوصول للبيئة |
| 02 | After login | تسجيل الدخول |
| 03 | Project form | فتح المشروع |
| 04 | Expected Budget | **591,706.80 SR** — مبلغ التعاقد |
| 05 | Description tab | وصف منسّق |
| 06 | Dashboard | التنقل للـ Dashboard |
| 08 | Quotation | Length/Width/Area + **64,562.40** |
| 09 | Order lines | جدول البنود |
| 10 | Print | طباعة PDF |
| 11 | Final | الإجماليات النهائية |

📎 **المرفقات:** ملفات PNG مرفقة بهذه المهمة

---

## مراجع محلية

- `openproject_docs/PHASE1_IMPLEMENTATION_DELIVERY.md`
- `openproject_docs/REQUIREMENTS_REVIEW_CLIENT_ANSWERS_AR.md`
- `gpc_gulf_project_ext/e2e/screenshots/gulf-phase1/README.md`
- `gpc_gulf_project_ext/e2e/screenshots/gulf-phase1/INDEX_AR.md`

---

## معلّق (غير حاسم)

- VAT على `contract_amount` — تأكيد على [#140]({PUBLIC_BASE}/work_packages/140)
- HR / Legacy — بانتظار رد العميل
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
            print(f"[dry-run] POST {ep}")
            return None
        headers = {"Accept": "application/json"}
        if files:
            return requests.post(
                f"{self.base}/api/v3{ep}", auth=self.auth, headers=headers, files=files, timeout=300, verify=False,
            )
        return requests.post(
            f"{self.base}/api/v3{ep}", json=data, auth=self.auth,
            headers={**headers, "Content-Type": "application/json"}, timeout=120, verify=False,
        )

    def patch(self, ep: str, data: dict):
        if self.dry_run:
            print(f"[dry-run] PATCH {ep}")
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
        subj = wp.get("subject", "")
        raw = wp.get("description", {}).get("raw", "") or ""
        if MARKER in raw or subj.startswith("Phase 1 — تنفيذ Odoo"):
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
        print(f"[dry-run] would attach {path.name}")
        return True
    if pr and pr.status_code in (200, 201):
        print(f"  ✓ attached {path.name}")
        return True
    print(f"  ✗ attach {path.name}: {pr.status_code if pr else '?'} {pr.text[:200] if pr else ''}")
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
        fallback = os.environ.get("OPENPROJECT_URL_FALLBACK", "https://37-61-219-169.nip.io:10081")
        client = Client(fallback, token, dry_run=args.dry_run)
        base = fallback
        tr = client.get(f"/projects/{PROJECT_ID}")
    if tr.status_code != 200:
        print(f"ERROR: Cannot reach OpenProject (HTTP {tr.status_code})")
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
        if client.dry_run:
            print(f"[dry-run] would update WP #{wp_id}")
        elif pr and pr.status_code in (200, 201):
            print(f"✓ Updated WP #{wp_id}: {WP_SUBJECT[:60]}")
        else:
            print(f"✗ PATCH #{wp_id} failed")
            return 1
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
        if client.dry_run:
            print("[dry-run] would CREATE delivery WP")
            wp_id = 0
        elif pr and pr.status_code in (200, 201):
            wp_id = pr.json()["id"]
            print(f"✓ Created WP #{wp_id}: {WP_SUBJECT[:60]}")
        else:
            print(f"✗ CREATE failed: {pr.status_code if pr else '?'} {pr.text[:300] if pr else ''}")
            return 1

    if not args.skip_attachments and wp_id and SCREENSHOTS_DIR.is_dir():
        print(f"Uploading screenshots from {SCREENSHOTS_DIR} ...")
        for png in sorted(SCREENSHOTS_DIR.glob("*.png")):
            upload_attachment(client, wp_id, png)
        for pdf in sorted(SCREENSHOTS_DIR.glob("*.pdf")):
            upload_attachment(client, wp_id, pdf)

    url = f"{PUBLIC_BASE}/work_packages/{wp_id}"
    print(f"\n========== DELIVERY WP ==========")
    print(url)
    print("=================================")

    out = Path(__file__).resolve().parent.parent / "openproject_docs" / "PHASE1_DELIVERY_WP.txt"
    out.write_text(f"Delivery WP: {url}\nDate: {TODAY}\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
