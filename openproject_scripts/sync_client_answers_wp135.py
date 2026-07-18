#!/usr/bin/env python3
"""
Sync client answers (2026-07-03) to OpenProject WP #135 family.

Updates:
  - WP #140 — client decisions (partial answers recorded)
  - WP #136, #137, #138 — full implementation specs
  - WP #141, #142, #143 — English scope mirrors
  - WP #135 — parent summary append
  - Activity journal on #140

Env: OPENPROJECT_API_TOKEN, OPENPROJECT_URL (default: master Tailscale URL)

Usage:
  python3 sync_client_answers_wp135.py           # live
  python3 sync_client_answers_wp135.py --dry-run
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
CLIENT_ANSWERS_MARKER = "<!-- client-answers-2026-07-03 -->"
TODAY = date.today().isoformat()

# ─── WP descriptions ────────────────────────────────────────────────────────

DESC_140 = f"""{CLIENT_ANSWERS_MARKER}

# قرارات العميل — مراجعة المتطلبات

**المهمة الأم:** WP #135 — مشاريع الخليج الصناعى  
**آخر تحديث:** {TODAY}  
**الحالة:** تم استلام مواصفات البنود **1–3** — البنود **4–5** بانتظار رد العميل

---

## ✅ البند 1 — وصف المشروع في Dashboard

- إظهار حقل **Description** القياسي داخل **Project Dashboard**.
- دعم تنسيق النص (فقرات، قوائم).
- أي تعديل في شاشة المشروع يظهر تلقائيًا في Dashboard.
- **مهمة التنفيذ:** [WP #136]({PUBLIC_BASE}/work_packages/136)

---

## ✅ البند 2 — مبلغ التعاقد

| الخاصية | القيمة |
|---------|--------|
| الاسم | مبلغ التعاقد – Contract Amount |
| الموديل | `project.project` |
| الحقل | `contract_amount` |
| النوع | Monetary — عملة الشركة/المشروع |
| الظهور | شاشة المشروع + Project Dashboard |
| مثال | `591,706.80 SR` |

**القرار:** حقل مستقل (ليس Budget في Community).

⏳ **معلق:** قبل أم بعد VAT؟

**مهمة التنفيذ:** [WP #137]({PUBLIC_BASE}/work_packages/137)

---

## ✅ البند 3 — Quotation (مقاسات + حساب مخصص)

### حقول `sale.order.line`
| الحقل | النوع | ملاحظة |
|-------|-------|--------|
| Length | رقمي | CM |
| Width / Height | رقمي | CM |
| Area | محسوب | `(Length × Width) ÷ 10,000` → m² |

### معادلة السطر
```
Line Total = Area × Quantity × Unit Price
Line Subtotal = Area × Qty × Price × (1 - Discount ÷ 100)
```
**Fallback:** بدون مقاسات → Area = 1 → `Qty × Price`

### الأعمدة (شاشة + PDF)
`Item | Description | Length | Width/Height | Area | Unit Price | Quantity | Total`

### سيناريو اختبار
| Length | Width | Area | Qty | Price | Discount | **Total** |
|--------|-------|------|-----|-------|----------|-----------|
| 180 CM | 305 CM | 5.49 m² | 24 | 490 | 0% | **64,562.40** |

يجب تطابق الإجمالي في: Quotation Line/Total, PDF, Invoice Line/Total.

**مهمة التنفيذ:** [WP #138]({PUBLIC_BASE}/work_packages/138)

---

## ⏳ البند 4 — HR (Odoo القياسي) — بانتظار رد

- [ ] Payslip Rules أم ربط بمشاريع/أنشطة؟
- [ ] التأثيرات: إضافي، خصومات، زيادات، بدلات…

**مهمة:** [WP #139]({PUBLIC_BASE}/work_packages/139)

---

## ⏳ البند 5 — Legacy Payroll — بانتظار رد

- [ ] توسيع التأثيرات؟
- [ ] أي شاشة (كلاسيك/عادية)؟
- [ ] Account Entry / Non Day Work / نوع جديد؟

**مهمة:** [WP #145]({PUBLIC_BASE}/work_packages/145)

---

## قرارات عامة — ما زالت مفتوحة

| # | القرار | الحالة |
|---|--------|--------|
| 3 | مبلغ التعاقد — VAT | ⏳ |
| 7 | نطاق: HR / Legacy / الاثنان | ⏳ |
| 8 | قاعدة الاختبار | ⏳ |

**المرجع المحلي:** `openproject_docs/REQUIREMENTS_REVIEW_CLIENT_ANSWERS_AR.md`
"""

DESC_136 = """# إضافة وصف المشروع داخل Project Dashboard

**المهمة الأم:** WP #135 — مشاريع الخليج الصناعى  
**النظام:** Odoo Community  
**الحالة:** 🟢 **جاهز للتنفيذ** — مواصفات العميل معتمدة (2026-07-03)

## المطلوب
- إظهار محتوى حقل **Description** القياسي داخل **Project Dashboard** لنفس المشروع.
- عرض واضح ومنظم يدعم **الفقرات والقوائم** (Rich Text/HTML).
- أي تعديل على الوصف في شاشة المشروع يظهر **تلقائيًا** في Dashboard.

## التنفيذ المقترح
- تعديل واجهة Project Dashboard لقراءة `project.description`.
- لا حاجة لحقل جديد — الاعتماد على الحقل القياسي.

## معايير القبول
- [ ] الوصف يظهر في Dashboard مع التنسيق
- [ ] التعديل في شاشة المشروع ينعكس فورًا في Dashboard
"""

DESC_137 = """# إضافة حقل مبلغ التعاقد — Contract Amount

**المهمة الأم:** WP #135 — مشاريع الخليج الصناعى  
**النظام:** Odoo Community  
**الحالة:** 🟢 **جاهز للتنفيذ** — مواصفات العميل معتمدة (2026-07-03)

## المطلوب
| الخاصية | القيمة |
|---------|--------|
| Label | مبلغ التعاقد – Contract Amount |
| Model | `project.project` |
| Field | `contract_amount` |
| Type | Monetary (company/project currency) |
| Input | يدوي من شاشة المشروع |
| Display | شاشة المشروع + Project Dashboard |
| Format | `591,706.80 SR` |

## قرار العميل
- ✅ **حقل مستقل** — ليس Budget في Community
- ⏳ **VAT:** قبل/بعد — لم يُحدد بعد

## معايير القبول
- [ ] الحقل يظهر في form view المشروع
- [ ] الحقل يظهر في Project Dashboard
- [ ] التنسيق حسب عملة الشركة/المشروع
"""

DESC_138 = """# تخصيص Quotation — مقاسات + حساب + PDF

**المهمة الأم:** WP #135 — مشاريع الخليج الصناعى  
**النظام:** Odoo Community  
**الحالة:** 🟢 **جاهز للتنفيذ** — مواصفات العميل معتمدة (2026-07-03)

## 1. More fields on `sale.order.line`

| Field | Type | Unit |
|-------|------|------|
| `length` (Length / الطول) | Float | CM |
| `width` (Width/Height / العرض) | Float | CM |
| `area` (Area / المساحة) | Computed | m² |

```
Area = (Length × Width) ÷ 10,000
```

## 2 Line total formula

```
Line Total = Area × Quantity × Unit Price
With discount: Area × Qty × Price × (1 - Discount ÷ 100)
```

**Fallback:** no dimensions → Area = 1 → standard `Qty × Price`

Must propagate to: Quotation Total, SO, Taxes, Invoices, Accounting.

## 3 UI columns (form + PDF)

`Item | Description | Length | Width/Height | Area | Unit Price | Quantity | Total`

## 4 PDF report
Company/client info, quote number/date, dimension table, line totals, taxes, terms.

## 5 Test scenario (acceptance)

| Length | Width | Area | Qty | Price | Disc | Expected |
|--------|-------|------|-----|-------|------|----------|
| 180 | 305 | 5.49 | 24 | 490 | 0% | **64,562.40** |

Verify same total in: Quotation line/total, PDF, Invoice line/total.

## معايير القبول
- [ ] Fields on model (not report-only)
- [ ] System calculation updated (not display-only)
- [ ] Fallback Area=1 works
- [ ] Decimal precision 2–4 for area
- [ ] Quotation → Invoice preserves totals
"""

DESC_141 = DESC_136.replace("Project Dashboard", "Project Dashboard").replace("# إضافة", "# 1. ")
DESC_142 = DESC_137.replace("# إضافة", "# 2. ")
DESC_143 = DESC_138.replace("# تخصيص", "# 3. ")

PARENT_APPEND = f"""

{CLIENT_ANSWERS_MARKER}

---

## تحديث إجابات العميل — {TODAY}

**الحالة:** مواصفات معتمدة للبنود 1–3 — **يمكن بدء التنفيذ**

| # | البند | WP | الحالة |
|---|-------|-----|--------|
| 1 | وصف المشروع → Dashboard | [#136]({PUBLIC_BASE}/work_packages/136) | 🟢 جاهز |
| 2 | مبلغ التعاقد `contract_amount` | [#137]({PUBLIC_BASE}/work_packages/137) | 🟢 جاهز |
| 3 | Quotation — مقاسات + PDF | [#138]({PUBLIC_BASE}/work_packages/138) | 🟢 جاهز |
| 4 | HR | [#139]({PUBLIC_BASE}/work_packages/139) | ⏳ بانتظار |
| 5 | Legacy | [#145]({PUBLIC_BASE}/work_packages/145) | ⏳ بانتظار |

**المرجع:** `openproject_docs/REQUIREMENTS_REVIEW_CLIENT_ANSWERS_AR.md`
"""

JOURNAL_140 = f"""تم استلام مواصفات تفصيلية من العميل ({TODAY}) للبنود 1–3:

1. **وصف المشروع** — إظهار Description في Project Dashboard
2. **مبلغ التعاقد** — حقل `contract_amount` على project.project (Monetary)
3. **Quotation** — Length/Width/Area + معادلة Area × Qty × Price + PDF

يمكن بدء التنفيذ على WP #136, #137, #138.
البنود 4–5 (HR/Legacy) ما زالت بانتظار رد العميل.

سيناريو اختبار Quotation: 180×305 → 5.49 m² × 24 × 490 = 64,562.40

المرجع: REQUIREMENTS_REVIEW_CLIENT_ANSWERS_AR.md
"""

PATCH_MAP: dict[int, str] = {
    135: PARENT_APPEND,  # append-only
    140: DESC_140,
    136: DESC_136,
    137: DESC_137,
    138: DESC_138,
    141: DESC_141,
    142: DESC_142,
    143: DESC_143,
}


class Client:
    def __init__(self, base: str, token: str, dry_run: bool = False):
        self.base = base.rstrip("/")
        self.dry_run = dry_run
        self.auth = HTTPBasicAuth("apikey", token)
        self.h = {"Accept": "application/json", "Content-Type": "application/json"}

    def get(self, ep: str):
        return requests.get(f"{self.base}/api/v3{ep}", auth=self.auth, headers=self.h, timeout=60, verify=False)

    def patch(self, ep: str, data: dict):
        if self.dry_run:
            print(f"[dry-run] PATCH {ep}")
            return None
        return requests.patch(f"{self.base}/api/v3{ep}", json=data, auth=self.auth, headers=self.h, timeout=60, verify=False)

    def post(self, ep: str, data: dict):
        if self.dry_run:
            print(f"[dry-run] POST {ep}")
            return None
        return requests.post(f"{self.base}/api/v3{ep}", json=data, auth=self.auth, headers=self.h, timeout=60, verify=False)


def patch_description(client: Client, wp_id: int, new_desc: str, *, append: bool = False) -> bool:
    gr = client.get(f"/work_packages/{wp_id}")
    if gr.status_code != 200:
        print(f"✗ GET #{wp_id}: HTTP {gr.status_code}")
        return False
    wp = gr.json()
    raw = wp.get("description", {}).get("raw", "") or ""
    subj = wp.get("subject", "")[:60]

    if append:
        if CLIENT_ANSWERS_MARKER in raw:
            print(f"✓ #{wp_id} already has client-answers section — {subj}")
            return True
        final = raw.rstrip() + new_desc
    else:
        if CLIENT_ANSWERS_MARKER in raw and len(raw) > len(new_desc):
            print(f"✓ #{wp_id} already updated — {subj}")
            return True
        final = new_desc

    pr = client.patch(
        f"/work_packages/{wp_id}",
        {"lockVersion": wp.get("lockVersion", 0), "description": {"format": "markdown", "raw": final}},
    )
    if client.dry_run:
        print(f"[dry-run] would PATCH #{wp_id} (len {len(raw)} → {len(final)}) — {subj}")
        return True
    if pr and pr.status_code in (200, 201):
        print(f"✓ PATCH #{wp_id} (len {len(raw)} → {len(final)}) — {subj}")
        return True
    print(f"✗ PATCH #{wp_id}: {pr.status_code if pr else '?'} {pr.text[:300] if pr else ''}")
    return False


def add_journal(client: Client, wp_id: int, comment: str) -> bool:
    gr = client.get(f"/work_packages/{wp_id}/activities")
    if gr.status_code != 200:
        print(f"✗ GET activities #{wp_id}: {gr.status_code}")
        return False
    for act in gr.json().get("_embedded", {}).get("elements", []):
        note = (act.get("comment", {}) or {}).get("raw", "") or ""
        if "تم استلام مواصفات تفصيلية من العميل" in note and TODAY in note:
            print(f"✓ Journal already exists on #{wp_id}")
            return True

    pr = client.post(
        f"/work_packages/{wp_id}/activities",
        {"comment": {"format": "plain", "raw": comment}},
    )
    if client.dry_run:
        print(f"[dry-run] would POST journal on #{wp_id}")
        return True
    if pr and pr.status_code in (200, 201):
        print(f"✓ Journal added on #{wp_id}")
        return True
    print(f"✗ Journal #{wp_id}: {pr.status_code if pr else '?'} {pr.text[:300] if pr else ''}")
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
        fallback = os.environ.get("OPENPROJECT_URL_FALLBACK", "https://37-61-219-169.nip.io:10081")
        print(f"[WARN] Primary failed — trying {fallback}")
        client = Client(fallback, token, dry_run=args.dry_run)
        base = fallback
        tr = client.get(f"/projects/{PROJECT_ID}")
    if tr.status_code != 200:
        print(f"ERROR: Cannot reach OpenProject (HTTP {getattr(tr, 'status_code', 'unreachable')})")
        print("Run on master:")
        print("  export OPENPROJECT_URL=http://127.0.0.1:10081")
        print("  python3 /opt/localaddons/openproject_scripts/sync_client_answers_wp135.py")
        return 1
    print(f"Connected: {base} — {tr.json().get('name')}")

    ok = True
    ok &= patch_description(client, PARENT_WP_ID, PATCH_MAP[PARENT_WP_ID], append=True)
    for wp_id in (140, 136, 137, 138, 141, 142, 143):
        ok &= patch_description(client, wp_id, PATCH_MAP[wp_id])
    ok &= add_journal(client, 140, JOURNAL_140)

    print("\n========== LINKS ==========")
    for wp_id in (135, 140, 136, 137, 138):
        print(f"WP #{wp_id}: {PUBLIC_BASE}/work_packages/{wp_id}")
    print("===========================")

    result = Path(__file__).resolve().parent.parent / "openproject_docs" / "WP135_CLIENT_ANSWERS_SYNC.txt"
    result.parent.mkdir(parents=True, exist_ok=True)
    result.write_text(
        f"Synced: {TODAY}\n"
        + "\n".join(f"WP #{i}: {PUBLIC_BASE}/work_packages/{i}" for i in (135, 140, 136, 137, 138))
        + "\n",
        encoding="utf-8",
    )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
