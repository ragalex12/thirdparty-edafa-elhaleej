#!/usr/bin/env python3
"""Patch OpenProject WP descriptions that are empty or label-only."""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import requests
from requests.auth import HTTPBasicAuth

PUBLIC_BASE = "https://master.tailcf9988.ts.net:10081"
DOCS = Path(__file__).resolve().parent / "docs"
MIN_LEN = 200  # below this => needs enrichment

# Match by WP id => full markdown description
PATCH_BY_ID: dict[int, str] = {}

def _load(name: str) -> str:
    p = DOCS / name
    if p.is_file():
        return p.read_text(encoding="utf-8").strip()
    # fallback: openproject_docs on dev machine
    p2 = Path(__file__).resolve().parent.parent / "openproject_docs" / name
    if p2.is_file():
        return p2.read_text(encoding="utf-8").strip()
    return ""


def _desc_136() -> str:
    return """# إضافة وصف المشروع داخل Project Dashboard

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


def _desc_137() -> str:
    return """# إضافة حقل مبلغ التعاقد — Contract Amount

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


def _desc_138() -> str:
    return """# تخصيص Quotation — مقاسات + حساب + PDF

**المهمة الأم:** WP #135 — مشاريع الخليج الصناعى  
**النظام:** Odoo Community  
**الحالة:** 🟢 **جاهز للتنفيذ** — مواصفات العميل معتمدة (2026-07-03)

## 1. حقول جديدة على `sale.order.line`
| Field | Type | Unit |
|-------|------|------|
| Length (الطول) | Float | CM |
| Width/Height (العرض) | Float | CM |
| Area (المساحة) | Computed | m² |

`Area = (Length × Width) ÷ 10,000`

## 2. معادلة إجمالي السطر
`Line Total = Area × Quantity × Unit Price`  
مع خصم: `Area × Qty × Price × (1 - Discount ÷ 100)`  
**Fallback:** بدون مقاسات → Area = 1

## 3. الأعمدة (شاشة + PDF)
Item | Description | Length | Width/Height | Area | Unit Price | Quantity | Total

## 4. سيناريو اختبار
180×305 → 5.49 m² × 24 × 490 = **64,562.40** (Quotation, PDF, Invoice)
"""


def _desc_139() -> str:
    return """# تأثيرات الرواتب — HR (Odoo القياسي)

**المهمة الأم:** WP #135 — مشاريع الخليج الصناعى  
**النظام:** Odoo Community — مسير رواتب قياسي

## المطلوب
إضافة وتنظيم تأثيرات الراتب:
- العمل الإضافي (Overtime)
- الخصومات
- الزيادات
- البدلات
- أي تأثيرات أخرى على الراتب

## قرارات معلّقة
- [ ] Payslip Rules قياسي أم ربط بمشاريع/أنشطة محددة؟

**الحالة:** بانتظار قرار العميل (#140)
"""


def _desc_141() -> str:
    return _desc_136().replace("# إضافة", "# 1. ")


def _desc_142() -> str:
    return _desc_137().replace("# إضافة", "# 2. ")


def _desc_143() -> str:
    return _desc_138().replace("# تخصيص", "# 3. ")


def _desc_144() -> str:
    return """# 4. تأثيرات الرواتب — HR (Odoo القياسي)

**المهمة الأم:** WP #135

## المطلوب
- العمل الإضافي، الخصومات، الزيادات، البدلات
- إعداد **Payslip Rules** و/أو ربط بمشاريع/أنشطة

**الحالة:** بانتظار قرار العميل (#140)
"""


def _desc_145() -> str:
    return """# 5. تأثيرات الرواتب — Legacy Payroll

**النظام:** `legacy_mixed_system` / واجهة كلاسيك — قاعدة `trgcc`

النظام الحالي يدعم: يوميات العمل، قيود الحسابات، Non Day Works، بطاقات، حسابات المجموعات.

## قرارات معلّقة
- [ ] توسيع التأثيرات (إضافي، خصومات، بدلات)؟
- [ ] أي شاشة: كلاسيك / عادية؟
- [ ] Account Entry أم Non Day Work أم نوع جديد؟
- [ ] علاقتها بفترة الرواتب والمشاريع؟

**الحالة:** بانتظار قرار العميل (#140)
"""


def _desc_146() -> str:
    body = _load("REQUIREMENTS_REVIEW_TIME_ESTIMATE_AR.txt")
    if not body:
        body = "(محتوى التقدير غير متوفر محلياً — راجع openproject_docs/REQUIREMENTS_REVIEW_TIME_ESTIMATE_AR.txt)"
    return f"<!-- time-estimate-wp135 -->\n\n{body}"


PATCH_BY_ID = {
    136: _desc_136(),
    137: _desc_137(),
    138: _desc_138(),
    139: _desc_139(),
    141: _desc_141(),
    142: _desc_142(),
    143: _desc_143(),
    144: _desc_144(),
    145: _desc_145(),
    146: _desc_146(),
}


def needs_patch(raw: str, wp_id: int) -> bool:
    if wp_id not in PATCH_BY_ID:
        return False
    raw = raw or ""
    if len(raw.strip()) < MIN_LEN:
        return True
    if wp_id in (142, 143, 144) and len(raw) < 220:
        return True
    if wp_id == 146 and "تقدير الوقت" not in raw and "يوم عمل" not in raw:
        return True
    if raw.strip() in ("", "<!-- time-estimate-wp135 -->", "<!-- time-estimate-wp135 -->\n\n"):
        return True
    # label-only: single line or only "مهمة فرعية"
    if len(raw) < MIN_LEN and "مهمة فرعية" in raw:
        return True
    return False


def main() -> int:
    token = os.environ.get("OPENPROJECT_API_TOKEN") or os.environ.get("OPENPROJECT_API_KEY")
    base = os.environ.get("OPENPROJECT_URL", PUBLIC_BASE).rstrip("/")
    if not token:
        print("ERROR: OPENPROJECT_API_TOKEN required")
        return 1

    auth = HTTPBasicAuth("apikey", token)
    h = {"Accept": "application/json", "Content-Type": "application/json"}
    updated = skipped = 0

    for wp_id, new_desc in sorted(PATCH_BY_ID.items()):
        gr = requests.get(f"{base}/api/v3/work_packages/{wp_id}", auth=auth, headers=h, timeout=60, verify=False)
        if gr.status_code != 200:
            print(f"#{wp_id} GET failed: {gr.status_code}")
            continue
        wp = gr.json()
        raw = wp.get("description", {}).get("raw", "") or ""
        subj = wp.get("subject", "")[:55]
        if not needs_patch(raw, wp_id):
            print(f"✓ #{wp_id} OK (len={len(raw)}) — {subj}")
            skipped += 1
            continue
        pr = requests.patch(
            f"{base}/api/v3/work_packages/{wp_id}",
            json={
                "lockVersion": wp.get("lockVersion", 0),
                "description": {"format": "markdown", "raw": new_desc},
            },
            auth=auth, headers=h, timeout=60, verify=False,
        )
        if pr.status_code in (200, 201):
            print(f"✓ PATCH #{wp_id} (len {len(raw)} → {len(new_desc)}) — {subj}")
            updated += 1
        else:
            print(f"✗ PATCH #{wp_id} failed: {pr.status_code} {pr.text[:200]}")

    print(f"\nDone: {updated} updated, {skipped} already OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
