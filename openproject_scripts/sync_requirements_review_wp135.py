#!/usr/bin/env python3
"""
Sync requirements review to OpenProject WP #135 + child decision task.

Target (from handoff 2026-07-02):
  OPENPROJECT_URL=https://master.tailcf9988.ts.net:10081
  Project: dev-needed-internal-tasks (id 19)
  Parent WP: 135

Env (first match wins):
  OPENPROJECT_API_TOKEN or OPENPROJECT_API_KEY
  Optional file: /opt/odoo-log-report-2026-06-28/docs/.openproject.env
  Or: /opt/localaddons/openproject_tools/.openproject.env

Usage:
  export OPENPROJECT_API_TOKEN='...'
  python3 sync_requirements_review_wp135.py           # live
  python3 sync_requirements_review_wp135.py --dry-run
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import requests
from requests.auth import HTTPBasicAuth

DEFAULT_URL = "https://master.tailcf9988.ts.net:10081"
PROJECT_ID = 19
PARENT_WP_ID = 135
TYPE_TASK = 1
STATUS_NEW = 1
PRIORITY_NORMAL = 8

MARKER = "<!-- requirements-review-automation -->"

ENV_CANDIDATES = [
    Path("/opt/.env"),
    Path("/opt/odoo-log-report-2026-06-28/docs/.openproject.env"),
    Path("/opt/localaddons/openproject_tools/.openproject.env"),
]

CHILD_SUBJECT_AR = "قرارات العميل — مراجعة المتطلبات (قبل التنفيذ)"
CHILD_SUBJECT = f"{CHILD_SUBJECT_AR} / Client decisions — before implementation"

CHILD_DESCRIPTION = """# قرارات العميل — مراجعة المتطلبات (قبل التنفيذ)

**المهمة الأم:** WP #135 — مشاريع الخليج الصناعى  
**الحالة:** بانتظار مراجعة المستلم وتأكيد القرارات  
**⚠️ لا يبدأ التنفيذ في Odoo قبل إكمال الأسئلة أدناه**

---

## أولاً: Odoo Community

### 1) وصف المشروع
- [ ] **السؤال:** ما الشكل المطلوب؟ نص حر / HTML / تبويب منفصل؟
- [ ] **السؤال:** هل يظهر مع المصروفات والإيرادات وTimesheets في نفس صفحة المشروع؟

### 2) مبلغ التعاقد
- [ ] **السؤال:** هل نعتمد على Budget في Community أم حقل مستقل لمبلغ التعاقد؟
- [ ] **السؤال:** هل المبلغ **قبل** ضريبة القيمة المضافة أم **بعدها**؟

### 3) عرض السعر Quotation
- [ ] **السؤال:** يرجى إرفاق نموذج PDF أو لقطة شاشة للشكل المطلوب.
- [ ] **السؤال:** هل المطلوب تعديل الشاشة أم التقرير المطبوع أم الاثنين؟
- [ ] **السؤال:** كيف يجب أن يظهر الإجمالي (Total) بالشكل النهائي؟

### 4) تأثيرات الرواتب — HR (Odoo القياسي)
- [ ] **السؤال:** هل المقصود مسير رواتب Odoo القياسي (Payslip Rules)؟
- [ ] **السؤال:** أم ربط التأثيرات بمشاريع/أنشطة محددة؟
- [ ] **السؤال:** ما التأثيرات المطلوبة بالتحديد؟ (إضافي، خصومات، زيادات، بدلات، أخرى)

---

## ثانياً: Legacy Payroll (نظام الرواتب التراثي)

### 5) تأثيرات الراتب في Legacy
النظام الحالي يدعم: يوميات العمل، قيود الحسابات، Non Day Works، بطاقات، حسابات المجموعات.

- [ ] **السؤال:** هل المطلوب توسيع التأثيرات (إضافي، خصومات، بدلات…) داخل Legacy؟
- [ ] **السؤال:** أي شاشة بالضبط؟ كلاسيك / عادية؟
- [ ] **السؤال:** هل تُسجّل كـ Account Entry أم Non Day Work أم نوع جديد؟
- [ ] **السؤال:** ما علاقتها بفترة الرواتب والمشاريع؟

---

## قرارات عامة (قبل التنفيذ)

| # | القرار | الرد |
|---|--------|------|
| 1 | شكل وصف المشروع | |
| 2 | مبلغ التعاقد — Budget أم حقل مستقل | |
| 3 | مبلغ التعاقد — قبل/بعد VAT | |
| 4 | نموذج مرجعي لـ Quotation | |
| 5 | HR — Payslip Rules أم ربط بمشاريع | |
| 6 | Legacy — نطاق التوسيع ونوع القيد | |
| 7 | النطاق: HR فقط / Legacy فقط / الاثنان مع ربط | |
| 8 | قاعدة الاختبار: `trgulf_Mrp` / `trgcc` / أخرى | |

---

## ملاحظة للمستلم

تم إرسال ملخص الاجتماع للمراجعة. يرجى الرد على الأسئلة أعلاه أو تعديل أي نقطة قبل بدء التنفيذ.

**المرجع المحلي:** `openproject_docs/REQUIREMENTS_REVIEW_MESSAGE_AR.txt`
"""

APPEND_SECTION = f"""
{MARKER}

---

## حالة التنفيذ — 2026-07-02

**الحالة:** بانتظار قرارات العميل — **لا يبدأ التنفيذ**

**الأنظمة المشمولة:**
1. **Odoo Community** — وصف المشروع، مبلغ التعاقد، Quotation، HR قياسي
2. **Legacy Payroll** — `legacy_mixed_system` / واجهة كلاسيك على قاعدة `trgcc`

**مهمة القرارات (فرعية):** {CHILD_SUBJECT_AR}

**ملخص المتطلبات:**
- وصف كامل للمشروع في شاشة المشروع
- مبلغ التعاقد (Budget أو حقل مستقل — قبل/بعد VAT)
- تعديل Quotation وعرض الإجمالي
- تأثيرات الرواتب في HR و/أو Legacy

**المراجع المحلية:**
- `openproject_docs/REQUIREMENTS_REVIEW_MESSAGE_AR.txt`
- `openproject_docs/REQUIREMENTS_REVIEW_DECISIONS_CHECKLIST.md`
"""


def load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip("'\"")
        os.environ.setdefault(key, val)


def get_token() -> str:
    for key in ("OPENPROJECT_API_TOKEN", "OPENPROJECT_API_KEY"):
        if os.environ.get(key):
            return os.environ[key]
    return ""


def get_base_url() -> str:
    return os.environ.get("OPENPROJECT_URL", DEFAULT_URL).rstrip("/")


class OPClient:
    def __init__(self, base_url: str, token: str, dry_run: bool = False):
        self.base = base_url
        self.dry_run = dry_run
        self.auth = HTTPBasicAuth("apikey", token)
        self.headers = {"Accept": "application/json", "Content-Type": "application/json"}

    def _url(self, endpoint: str) -> str:
        return f"{self.base}/api/v3{endpoint}"

    def get(self, endpoint: str):
        try:
            return requests.get(self._url(endpoint), auth=self.auth, headers=self.headers, timeout=60)
        except requests.RequestException as e:
            print(f"[NET ERROR] GET {endpoint}: {e}")
            return None

    def post(self, endpoint: str, data: dict):
        if self.dry_run:
            print(f"[dry-run] POST {endpoint}")
            return None
        return requests.post(self._url(endpoint), json=data, auth=self.auth, headers=self.headers, timeout=60)

    def patch(self, endpoint: str, data: dict):
        if self.dry_run:
            print(f"[dry-run] PATCH {endpoint}")
            return None
        return requests.patch(self._url(endpoint), json=data, auth=self.auth, headers=self.headers, timeout=60)


def find_child_wp(client: OPClient) -> int | None:
    r = client.get(f"/work_packages/{PARENT_WP_ID}")
    if not r or r.status_code != 200:
        return None
    for link in r.json().get("_links", {}).get("children", []):
        href = link.get("href", "")
        if "/work_packages/" in href:
            wp_id = int(href.rsplit("/", 1)[-1])
            cr = client.get(f"/work_packages/{wp_id}")
            if cr.status_code == 200 and cr.json().get("subject") == CHILD_SUBJECT:
                return wp_id
    # fallback: search project WPs by subject
    sr = client.get(f"/projects/{PROJECT_ID}/work_packages?filters=[{{\"subject\":{{\"operator\":\"~\",\"values\":[\"قرارات العميل\"]}}}}]")
    if sr.status_code == 200:
        for wp in sr.json().get("_embedded", {}).get("elements", []):
            if wp.get("subject") == CHILD_SUBJECT:
                return wp.get("id")
    return None


def update_parent_wp(client: OPClient) -> bool:
    r = client.get(f"/work_packages/{PARENT_WP_ID}")
    if r.status_code != 200:
        print(f"[ERROR] GET WP {PARENT_WP_ID}: {r.status_code} {r.text[:300]}")
        return False
    wp = r.json()
    current = wp.get("description", {}).get("raw", "") or ""
    lock = wp.get("lockVersion", 0)
    if MARKER in current:
        print(f"✓ WP {PARENT_WP_ID} already has automation section — skip PATCH")
        return True
    new_desc = current.rstrip() + APPEND_SECTION
    payload = {
        "lockVersion": lock,
        "description": {"format": "markdown", "raw": new_desc},
    }
    pr = client.patch(f"/work_packages/{PARENT_WP_ID}", payload)
    if client.dry_run:
        print(f"[dry-run] would PATCH WP {PARENT_WP_ID} (lockVersion={lock})")
        return True
    if pr and pr.status_code in (200, 201):
        print(f"✓ WP {PARENT_WP_ID} description updated")
        return True
    print(f"[ERROR] PATCH WP {PARENT_WP_ID}: {pr.status_code if pr else 'no response'} {pr.text[:400] if pr else ''}")
    return False


def create_child_wp(client: OPClient) -> int | None:
    existing = find_child_wp(client)
    if existing:
        print(f"✓ Child WP already exists: id={existing} — {CHILD_SUBJECT}")
        return existing
    payload = {
        "subject": CHILD_SUBJECT,
        "description": {"format": "markdown", "raw": CHILD_DESCRIPTION},
        "type": {"href": f"/api/v3/types/{TYPE_TASK}"},
        "status": {"href": f"/api/v3/statuses/{STATUS_NEW}"},
        "priority": {"href": f"/api/v3/priorities/{PRIORITY_NORMAL}"},
        "parent": {"href": f"/api/v3/work_packages/{PARENT_WP_ID}"},
    }
    pr = client.post(f"/projects/{PROJECT_ID}/work_packages", payload)
    if client.dry_run:
        print(f"[dry-run] would CREATE child under WP {PARENT_WP_ID}")
        return None
    if pr and pr.status_code in (200, 201):
        wp_id = pr.json().get("id")
        print(f"✓ Created child WP id={wp_id}: {CHILD_SUBJECT}")
        return wp_id
    print(f"[ERROR] POST child WP: {pr.status_code if pr else 'no response'} {pr.text[:400] if pr else ''}")
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    for p in ENV_CANDIDATES:
        load_dotenv(p)

    token = get_token()
    base = get_base_url()
    if not token:
        print("[ERROR] Set OPENPROJECT_API_TOKEN or OPENPROJECT_API_KEY (or .openproject.env)")
        return 1

    client = OPClient(base, token, dry_run=args.dry_run)
    print(f"OpenProject: {base}")
    print(f"Project: {PROJECT_ID} | Parent WP: {PARENT_WP_ID}")

    # connectivity — try primary URL, then optional fallback
    fallback = os.environ.get("OPENPROJECT_URL_FALLBACK", "https://37-61-219-169.nip.io:10081").rstrip("/")
    tr = client.get(f"/projects/{PROJECT_ID}")
    if not tr or tr.status_code != 200:
        if base != fallback:
            print(f"[WARN] Primary URL failed — trying fallback: {fallback}")
            client = OPClient(fallback, token, dry_run=args.dry_run)
            base = fallback
            tr = client.get(f"/projects/{PROJECT_ID}")
    if not tr or tr.status_code != 200:
        code = tr.status_code if tr else "unreachable"
        print(f"[ERROR] Cannot reach project {PROJECT_ID}: HTTP {code}")
        if tr:
            print(tr.text[:300])
        print("\nRun this script on a machine with Tailscale access to OpenProject.")
        print("  python3 /opt/localaddons/openproject_scripts/sync_requirements_review_wp135.py")
        return 1
    print(f"✓ Connected — project: {tr.json().get('name')}")

    ok_parent = update_parent_wp(client)
    child_id = create_child_wp(client)
    if not ok_parent:
        return 1
    if not args.dry_run and child_id is None and find_child_wp(client) is None:
        return 1

    print("\nDone.")
    parent_url = f"{base}/work_packages/{PARENT_WP_ID}"
    print(f"\n========== LINKS ==========")
    print(f"Parent (updated):  {parent_url}")
    if child_id:
        print(f"Child (questions): {base}/work_packages/{child_id}")
    alt = os.environ.get("OPENPROJECT_URL_FALLBACK", "https://37-61-219-169.nip.io:10081").rstrip("/")
    print(f"Alt parent:        {alt}/work_packages/{PARENT_WP_ID}")
    if child_id:
        print(f"Alt child:         {alt}/work_packages/{child_id}")
    print(f"Project board:     {base}/projects/dev-needed-internal-tasks/work_packages")
    print(f"===========================")

    result_path = Path(__file__).resolve().parent.parent / "openproject_docs" / "WP135_SYNC_RESULT.txt"
    result_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"Parent: {parent_url}",
        f"Child:  {base}/work_packages/{child_id}" if child_id else "Child:  (not created)",
    ]
    result_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
