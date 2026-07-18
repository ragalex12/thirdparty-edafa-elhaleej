#!/usr/bin/env python3
"""
Sync Phase 2 assumed client decisions + WP status updates to OpenProject.

Updates WP #140, #137, #139, #145, #135 with assumed decisions and completion status.

Usage:
  SYNC_SCRIPT=sync_phase2_assumed_decisions_wp135.py bash ssh_to_master_and_sync.sh
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
MARKER = "<!-- assumed-decisions-phase2-2026-07-03 -->"
TODAY = date.today().isoformat()

DESC_140_APPEND = f"""

---

{MARKER}

## قرارات افتراضية — Phase 2 ({TODAY})

**انتظرنا رد العميل على البنود 4–5 — لم يصل.**

اعتمدنا **أبسط قرارات معقولة** لإكمال التنفيذ. يمكن للعميل تعديل أي قرار هنا.

| # | السؤال | القرار المعتمد |
|---|--------|----------------|
| 3 | VAT على مبلغ التعاقد | **قبل ضريبة القيمة المضافة** |
| 5 | HR | **Payslip Rules القياسي فقط** (بدون ربط مشاريع) |
| 6 | Legacy Payroll | **مؤجل** — بدون تغيير حتى يرد العميل |
| 7 | النطاق | **HR فقط** (Odoo Community) |
| 8 | قاعدة الاختبار | **`trgulf_Mrp`** |

**Phase 2:** [WP #139]({PUBLIC_BASE}/work_packages/139) — موديول `gpc_gulf_hr_payroll_ext`  
**Legacy:** [WP #145]({PUBLIC_BASE}/work_packages/145) — **مؤجل**

**مرجع محلي:** `openproject_docs/ASSUMED_CLIENT_DECISIONS_AR.md`
"""

JOURNAL_140 = f"""Phase 2 — قرارات افتراضية ({TODAY})

انتظرنا رد العميل على HR/Legacy — لم يصل.

القرارات المعتمدة:
• VAT: قبل ضريبة القيمة المضافة
• HR: Payslip Rules فقط → WP #139
• Legacy: مؤجل → WP #145
• النطاق: HR فقط على trgulf_Mrp

يمكن للعميل تعديل أي قرار على WP #140.
"""

DESC_137_VAT = f"""{MARKER}

# إضافة قيمة/مبلغ التعاقد — Contract Amount

**الحالة:** ✅ **Done** (Phase 1 + VAT assumption)

| الخاصية | القيمة |
|---------|--------|
| الحقل | `contract_amount` على `project.project` |
| النوع | Monetary |
| المزامنة | ثنائية الاتجاه مع `project_valuebvat` |

**VAT (افتراض — {TODAY}):** المبلغ **قبل** ضريبة القيمة المضافة.  
لم يرد العميل — متوافق مع التنفيذ الحالي.

**التسليم:** [WP #150]({PUBLIC_BASE}/work_packages/150)
"""

DESC_139_DONE = f"""{MARKER}

# HR — تأثيرات الرواتب (Payslip Rules)

**الحالة:** ✅ **Done** (Phase 2 — {TODAY})

**قرار افتراضي:** Payslip Rules القياسي فقط — بدون ربط مشاريع/timesheet.

## الموديول

**`gpc_gulf_hr_payroll_ext`** — DB: `trgulf_Mrp`

| المكون | الوصف |
|--------|--------|
| هيكل | `GULF_STANDARD` |
| بدلات | Travel + Other من العقد |
| إدخالات | OT (إضافي), BONUS (زيادة), DED_OTHER (خصم) |

## UAT

```
Wage 10,000 + Travel 500 + Other 200 + OT 1,500 + Bonus 1,000 - Ded 300 = NET 12,900
```

**Legacy (#145):** مؤجل — بانتظار العميل.
"""

DESC_145_DEFERRED = f"""{MARKER}

# Legacy Payroll — تأثيرات الرواتب

**الحالة:** ⏸️ **مؤجل (Deferred)** — {TODAY}

**السبب:** لم يرد العميل على:
- توسيع التأثيرات؟
- أي شاشة (كلاسيك/عادية)؟
- Account Entry أم Non Day Work؟

**النظام الحالي:** `legacy_mixed_system` على `trgcc` — **بدون تغيير**.

عند رد العميل على [WP #140]({PUBLIC_BASE}/work_packages/140) يمكن فتح هذه المهمة مجدداً.
"""

PARENT_APPEND = f"""

---

{MARKER}

## Phase 2 — HR + قرارات افتراضية ({TODAY})

| WP | البند | الحالة |
|----|-------|--------|
| #136–#138 | Phase 1 | ✅ Done — [WP #150]({PUBLIC_BASE}/work_packages/150) |
| #137 | VAT قبل الضريبة | ✅ افتراض |
| #139 | HR Payslip Rules | ✅ Done |
| #145 | Legacy Payroll | ⏸️ مؤجل |

**Phase 2 delivery:** see child WP (Phase 2 delivery task)
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
            print(f"[dry-run] PATCH {ep}")
            return None
        return requests.patch(f"{self.base}/api/v3{ep}", json=data, auth=self.auth, headers=self.h, timeout=120, verify=False)

    def post(self, ep: str, data: dict):
        if self.dry_run:
            print(f"[dry-run] POST {ep}")
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


def get_on_hold_status_id(client: Client) -> int | None:
    r = client.get("/statuses")
    if r.status_code != 200:
        return None
    for st in r.json().get("_embedded", {}).get("elements", []):
        name = (st.get("name") or "").lower()
        if "hold" in name or "blocked" in name or "rejected" in name:
            return st["id"]
    return None


def patch_wp(client: Client, wp_id: int, *, desc: str | None = None, append_desc: str | None = None, status_id: int | None = None) -> bool:
    gr = client.get(f"/work_packages/{wp_id}")
    if gr.status_code != 200:
        print(f"✗ GET #{wp_id}: {gr.status_code}")
        return False
    wp = gr.json()
    payload: dict = {"lockVersion": wp.get("lockVersion", 0)}
    if desc is not None:
        payload["description"] = {"format": "markdown", "raw": desc}
    elif append_desc:
        raw = wp.get("description", {}).get("raw", "") or ""
        if MARKER in raw:
            print(f"✓ #{wp_id} already has phase2 marker")
            return True
        payload["description"] = {"format": "markdown", "raw": raw.rstrip() + append_desc}
    if status_id:
        payload["status"] = {"href": f"/api/v3/statuses/{status_id}"}
    pr = client.patch(f"/work_packages/{wp_id}", payload)
    if client.dry_run:
        print(f"[dry-run] PATCH #{wp_id}")
        return True
    if pr and pr.status_code in (200, 201):
        print(f"✓ PATCH #{wp_id}")
        return True
    print(f"✗ PATCH #{wp_id}: {pr.status_code if pr else '?'} {pr.text[:200] if pr else ''}")
    return False


def add_journal(client: Client, wp_id: int, comment: str, marker: str) -> bool:
    gr = client.get(f"/work_packages/{wp_id}/activities")
    if gr.status_code == 200:
        for act in gr.json().get("_embedded", {}).get("elements", []):
            note = (act.get("comment", {}) or {}).get("raw", "") or ""
            if marker in note:
                print(f"✓ Journal exists on #{wp_id}")
                return True
    pr = client.post(f"/work_packages/{wp_id}/activities", {"comment": {"format": "plain", "raw": comment}})
    if client.dry_run:
        return True
    if pr and pr.status_code in (200, 201):
        print(f"✓ Journal on #{wp_id}")
        return True
    print(f"✗ Journal #{wp_id}: {pr.status_code if pr else '?'}")
    return False


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
        base = os.environ.get("OPENPROJECT_URL_FALLBACK", "https://37-61-219-169.nip.io:10081")
        client = Client(base, token, dry_run=args.dry_run)
        tr = client.get(f"/projects/{PROJECT_ID}")
    if tr.status_code != 200:
        print("ERROR: Cannot reach OpenProject")
        return 1
    print(f"Connected: {base}")

    closed_id = get_closed_status_id(client)
    hold_id = get_on_hold_status_id(client)

    ok = True
    ok &= patch_wp(client, 140, append_desc=DESC_140_APPEND)
    ok &= add_journal(client, 140, JOURNAL_140, "Phase 2 — قرارات افتراضية")
    ok &= patch_wp(client, 137, desc=DESC_137_VAT, status_id=closed_id)
    ok &= patch_wp(client, 139, desc=DESC_139_DONE, status_id=closed_id)
    ok &= patch_wp(client, 145, desc=DESC_145_DEFERRED, status_id=hold_id)
    ok &= patch_wp(client, PARENT_WP_ID, append_desc=PARENT_APPEND)

    out = Path(__file__).resolve().parent.parent / "openproject_docs" / "PHASE2_ASSUMED_SYNC.txt"
    out.write_text(f"Phase 2 assumed sync: {TODAY}\nWP #140: {PUBLIC_BASE}/work_packages/140\n", encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
