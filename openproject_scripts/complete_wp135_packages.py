#!/usr/bin/env python3
"""Complete WP #135 sync — run ON MASTER with OPENPROJECT_URL=http://127.0.0.1:10081"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import requests
from requests.auth import HTTPBasicAuth

# Reuse content from main sync script
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sync_requirements_review_wp135 import (  # noqa: E402
    APPEND_SECTION,
    CHILD_DESCRIPTION,
    CHILD_SUBJECT,
    CHILD_SUBJECT_AR,
    MARKER,
    PARENT_WP_ID,
    PRIORITY_NORMAL,
    PROJECT_ID,
    STATUS_NEW,
    TYPE_TASK,
    ENV_CANDIDATES,
    get_base_url,
    get_token,
    load_dotenv,
)

PUBLIC_BASE = "https://master.tailcf9988.ts.net:10081"

# Scope children — created under WP 135, blocked until client decisions
SCOPE_CHILDREN = [
    (
        "1. وصف المشروع — Odoo Community",
        "إضافة وصف كامل في شاشة المشروع.\n\n**الحالة:** بانتظار قرار العميل (شكل الوصف).\n**لا يبدأ التنفيذ قبل تأكيد المهمة الأم.**",
    ),
    (
        "2. مبلغ التعاقد — Odoo Community",
        "قيمة التعاقد — Budget أم حقل مستقل؛ قبل/بعد VAT.\n\n**الحالة:** بانتظار قرار العميل.",
    ),
    (
        "3. Quotation — Odoo Community",
        "تعديل شاشة/تقرير عرض السعر وعرض الإجمالي (Total).\n\n**الحالة:** بانتظار نموذج PDF/لقطة مرجعية من العميل.",
    ),
    (
        "4. تأثيرات الرواتب — HR (Odoo القياسي)",
        "إضافي، خصومات، زيادات، بدلات — Payslip Rules و/أو ربط بمشاريع.\n\n**الحالة:** بانتظار قرار العميل.",
    ),
    (
        "5. تأثيرات الرواتب — Legacy Payroll",
        "توسيع التأثيرات في Legacy — شاشة كلاسيك/عادية، نوع القيد.\n\n**الحالة:** بانتظار قرار العميل.",
    ),
]


class Client:
    def __init__(self, base: str, token: str):
        self.base = base.rstrip("/")
        self.auth = HTTPBasicAuth("apikey", token)
        self.h = {"Accept": "application/json", "Content-Type": "application/json"}

    def get(self, ep: str):
        return requests.get(f"{self.base}/api/v3{ep}", auth=self.auth, headers=self.h, timeout=60)

    def post(self, ep: str, data: dict):
        return requests.post(f"{self.base}/api/v3{ep}", json=data, auth=self.auth, headers=self.h, timeout=60)

    def patch(self, ep: str, data: dict):
        return requests.patch(f"{self.base}/api/v3{ep}", json=data, auth=self.auth, headers=self.h, timeout=60)


def list_children(client: Client) -> dict[str, int]:
    r = client.get(f"/work_packages/{PARENT_WP_ID}")
    r.raise_for_status()
    wp = r.json()
    out: dict[str, int] = {}
    for link in wp.get("_links", {}).get("children", []):
        href = link.get("href", "")
        if "/work_packages/" not in href:
            continue
        cid = int(href.rsplit("/", 1)[-1])
        cr = client.get(f"/work_packages/{cid}")
        if cr.status_code == 200:
            out[cr.json().get("subject", "")] = cid
    return out


def update_parent(client: Client) -> None:
    r = client.get(f"/work_packages/{PARENT_WP_ID}")
    r.raise_for_status()
    wp = r.json()
    desc = wp.get("description", {}).get("raw", "") or ""
    if MARKER in desc:
        print(f"✓ WP #{PARENT_WP_ID} already has automation section")
        return
    pr = client.patch(
        f"/work_packages/{PARENT_WP_ID}",
        {
            "lockVersion": wp.get("lockVersion", 0),
            "description": {"format": "markdown", "raw": desc.rstrip() + APPEND_SECTION},
        },
    )
    pr.raise_for_status()
    print(f"✓ Updated WP #{PARENT_WP_ID}")


def ensure_child(client: Client, subject: str, description: str, existing: dict[str, int]) -> int:
    for subj, wid in existing.items():
        if subj == subject or subj.startswith(subject[:20]):
            print(f"✓ Exists #{wid}: {subject}")
            return wid
    payload = {
        "subject": subject,
        "description": {"format": "markdown", "raw": description},
        "type": {"href": f"/api/v3/types/{TYPE_TASK}"},
        "status": {"href": f"/api/v3/statuses/{STATUS_NEW}"},
        "priority": {"href": f"/api/v3/priorities/{PRIORITY_NORMAL}"},
        "parent": {"href": f"/api/v3/work_packages/{PARENT_WP_ID}"},
    }
    pr = client.post(f"/projects/{PROJECT_ID}/work_packages", payload)
    pr.raise_for_status()
    wid = pr.json()["id"]
    print(f"✓ Created #{wid}: {subject}")
    existing[subject] = wid
    return wid


def main() -> int:
    for p in ENV_CANDIDATES:
        load_dotenv(p)
    token = get_token()
    if not token:
        print("ERROR: set OPENPROJECT_API_TOKEN")
        return 1
    base = os.environ.get("OPENPROJECT_URL", get_base_url())
    client = Client(base, token)

    tr = client.get(f"/projects/{PROJECT_ID}")
    if tr.status_code != 200:
        print(f"ERROR: cannot reach OpenProject at {base} (HTTP {tr.status_code})")
        print("Run on MASTER: export OPENPROJECT_URL=http://127.0.0.1:10081")
        return 1
    print(f"Connected: {base} — {tr.json().get('name')}")

    existing = list_children(client)
    print(f"Current children under #{PARENT_WP_ID}: {len(existing)}")
    for s, i in sorted(existing.items(), key=lambda x: x[1]):
        print(f"  #{i} {s[:60]}")

    update_parent(client)
    existing = list_children(client)

    decisions_id = ensure_child(client, CHILD_SUBJECT, CHILD_DESCRIPTION, existing)
    existing = list_children(client)

    scope_ids = []
    for subject, desc in SCOPE_CHILDREN:
        scope_ids.append(ensure_child(client, subject, desc, existing))
        existing = list_children(client)

    print("\n========== LINKS ==========")
    print(f"Parent:  {PUBLIC_BASE}/work_packages/{PARENT_WP_ID}")
    print(f"Decisions: {PUBLIC_BASE}/work_packages/{decisions_id}")
    for sid in scope_ids:
        print(f"Scope:   {PUBLIC_BASE}/work_packages/{sid}")
    print(f"Board:   {PUBLIC_BASE}/projects/dev-needed-internal-tasks/work_packages")
    print("===========================")

    out = Path(__file__).resolve().parent.parent / "openproject_docs" / "WP135_SYNC_RESULT.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"Parent: {PUBLIC_BASE}/work_packages/{PARENT_WP_ID}",
             f"Decisions: {PUBLIC_BASE}/work_packages/{decisions_id}"]
    lines += [f"Scope: {PUBLIC_BASE}/work_packages/{i}" for i in scope_ids]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
