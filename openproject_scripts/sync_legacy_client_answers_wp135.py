#!/usr/bin/env python3
"""
Sync Legacy client answers to OpenProject — close WP #145 (no expansion).

Client answers (2026-07-03):
  1. Expand Legacy effects? → NO
  2. UI → Standard Odoo
  4. Link to payroll period/projects? → NO

Usage:
  SYNC_SCRIPT=sync_legacy_client_answers_wp135.py bash ssh_to_master_and_sync.sh
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
MARKER = "<!-- legacy-client-answers-2026-07-03 -->"
TODAY = date.today().isoformat()

DESC_140_APPEND = f"""

---

{MARKER}

## Legacy Payroll — رد العميل ({TODAY})

| # | السؤال | **الرد** |
|---|--------|----------|
| 1 | توسيع تأثيرات Legacy (إضافي، خصومات، بدلات)؟ | **لا** — بدون توسيع |
| 2 | أي شاشة؟ | **Standard Odoo** (الواجهة العادية) |
| 3 | Account Entry أم Non Day Work؟ | **غير مطبّق** — لا توسيع |
| 4 | ربط بفترة الرواتب والمشاريع؟ | **لا** |

**النتيجة:** [WP #145]({PUBLIC_BASE}/work_packages/145) — **مغلق / خارج النطاق** — النظام الحالي `legacy_mixed_system` على `trgcc` بدون تعديل.

**HR (Odoo Community):** منجز — [WP #139]({PUBLIC_BASE}/work_packages/139) / [WP #156]({PUBLIC_BASE}/work_packages/156)
"""

JOURNAL_140 = f"""Legacy Payroll — رد العميل ({TODAY})

1) توسيع التأثيرات في Legacy؟ → لا
2) الشاشة → Standard Odoo
4) ربط بفترة/مشاريع؟ → لا

WP #145 مغلق — لا عمل تنفيذي على Legacy.
WP #135 — اكتمل نطاق Odoo Community (Phase 1 + Phase 2 HR).
"""

DESC_145_CLOSED = f"""{MARKER}

# Legacy Payroll — تأثيرات الرواتب

**الحالة:** ✅ **مغلق — خارج النطاق** ({TODAY})

## قرار العميل

| السؤال | الرد |
|--------|------|
| توسيع التأثيرات في Legacy؟ | **لا** |
| الشاشة | **Standard Odoo** |
| ربط بفترة الرواتب / مشاريع؟ | **لا** |

**لا يوجد عمل تنفيذي.** النظام الحالي `legacy_mixed_system` على قاعدة `trgcc` يبقى كما هو.

**HR قياسي:** تم على `trgulf_Mrp` — [WP #139]({PUBLIC_BASE}/work_packages/139)
"""

PARENT_APPEND = f"""

---

{MARKER}

## Legacy — قرار العميل ({TODAY})

**WP #145:** مغلق — **لا توسيع** Legacy. Standard Odoo، بدون ربط فترة/مشاريع.

**WP #135:** ✅ **اكتمل نطاق التنفيذ** (Community Phase 1 + HR Phase 2). Legacy بدون تغيير.
"""


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


def patch_wp(client: Client, wp_id: int, *, desc: str | None = None, append_desc: str | None = None, status_id: int | None = None) -> bool:
    gr = client.get(f"/work_packages/{wp_id}")
    if gr.status_code != 200:
        return False
    wp = gr.json()
    payload: dict = {"lockVersion": wp.get("lockVersion", 0)}
    if desc is not None:
        payload["description"] = {"format": "markdown", "raw": desc}
    elif append_desc:
        raw = wp.get("description", {}).get("raw", "") or ""
        if MARKER in raw:
            print(f"✓ #{wp_id} already updated")
            return True
        payload["description"] = {"format": "markdown", "raw": raw.rstrip() + append_desc}
    if status_id:
        payload["status"] = {"href": f"/api/v3/statuses/{status_id}"}
    pr = client.patch(f"/work_packages/{wp_id}", payload)
    if client.dry_run or (pr and pr.status_code in (200, 201)):
        print(f"✓ PATCH #{wp_id}")
        return True
    return False


def add_journal(client: Client, wp_id: int, comment: str, marker: str) -> bool:
    gr = client.get(f"/work_packages/{wp_id}/activities")
    if gr.status_code == 200:
        for act in gr.json().get("_embedded", {}).get("elements", []):
            note = (act.get("comment", {}) or {}).get("raw", "") or ""
            if marker.split("(")[0].strip() in note:
                print(f"✓ Journal exists on #{wp_id}")
                return True
    pr = client.post(f"/work_packages/{wp_id}/activities", {"comment": {"format": "plain", "raw": comment}})
    if client.dry_run or (pr and pr.status_code in (200, 201)):
        print(f"✓ Journal on #{wp_id}")
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
    ok = True
    ok &= patch_wp(client, 140, append_desc=DESC_140_APPEND)
    ok &= add_journal(client, 140, JOURNAL_140, "Legacy Payroll — رد العميل")
    ok &= patch_wp(client, 145, desc=DESC_145_CLOSED, status_id=closed_id)
    ok &= patch_wp(client, PARENT_WP_ID, append_desc=PARENT_APPEND)

    out = Path(__file__).resolve().parent.parent / "openproject_docs" / "LEGACY_CLIENT_ANSWERS_SYNC.txt"
    out.write_text(
        f"Legacy answers synced: {TODAY}\n"
        f"WP #145 closed (no expansion)\n"
        f"{PUBLIC_BASE}/work_packages/145\n",
        encoding="utf-8",
    )
    print(f"\nWP #135 complete — Legacy #145 closed: {PUBLIC_BASE}/work_packages/145")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
