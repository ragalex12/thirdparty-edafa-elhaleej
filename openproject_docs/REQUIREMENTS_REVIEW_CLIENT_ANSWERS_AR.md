# إجابات العميل — مشاريع الخليج الصناعى

**تاريخ الاستلام:** 2026-07-03  
**المهمة الأم:** [WP #135](https://master.tailcf9988.ts.net:10081/work_packages/135)  
**مهمة القرارات:** [WP #140](https://master.tailcf9988.ts.net:10081/work_packages/140)  
**الحالة:** ✅ **مغلق — اكتمل التنفيذ (2026-07-03)**

---

## ملخص الحالة

| # | البند | الحالة | مهمة التنفيذ |
|---|-------|--------|--------------|
| 1 | وصف المشروع في Dashboard | ✅ مواصفات معتمدة | [WP #136](https://master.tailcf9988.ts.net:10081/work_packages/136) |
| 2 | مبلغ التعاقد | ✅ مواصفات معتمدة | [WP #137](https://master.tailcf9988.ts.net:10081/work_packages/137) |
| 3 | تخصيص Quotation | ✅ مواصفات معتمدة | [WP #138](https://master.tailcf9988.ts.net:10081/work_packages/138) |
| 4 | HR — تأثيرات الرواتب | ✅ منجز | [WP #139](https://master.tailcf9988.ts.net:10081/work_packages/139) |
| 5 | Legacy Payroll | ✅ لا توسيع — مغلق | [WP #145](https://master.tailcf9988.ts.net:10081/work_packages/145) |

---

## 1. إظهار وصف المشروع داخل الـ Dashboard

### المطلوب
- يوجد حقل **Description** داخل شاشة المشروع، ويتم كتابة تفاصيل المشروع فيه.
- إظهار محتوى حقل Description داخل **Project Dashboard** الخاصة بنفس المشروع.
- يظهر الوصف بشكل واضح ومنظم.
- يدعم تنسيق النص الموجود داخل الوصف مثل **الفقرات والقوائم**.
- أي تعديل يتم على الوصف في شاشة المشروع يظهر **تلقائيًا** في الـ Dashboard.

### ملاحظات تنفيذ
- الاعتماد على حقل الوصف القياسي في Odoo (لا حقل جديد).
- التعديل على واجهة **Project Dashboard** لقراءة وعرض `description`.
- **قرار ضمني:** استخدام الوصف الموجود (Rich Text/HTML) — لم يطلب العميل تبويبًا منفصلًا.

---

## 2. إضافة حقل مبلغ التعاقد

### المطلوب
- حقل جديد داخل المشروع باسم: **مبلغ التعاقد – Contract Amount**

### مواصفات الحقل
| الخاصية | القيمة |
|---------|--------|
| النوع | Monetary |
| العملة | مرتبط بعملة الشركة أو عملة المشروع |
| الإدخال | يدويًا من شاشة المشروع |
| الظهور | شاشة المشروع + Project Dashboard بجانب بيانات المشروع الأساسية |
| التنسيق | حسب العملة — مثال: `591,706.80 SR` |

### اقتراح تقني (من العميل)
- **الموديل:** `project.project`
- **الاسم التقني:** `contract_amount`
- **القرار:** حقل مستقل — **ليس** Budget في Community

### قرار معلّق
- [ ] هل المبلغ **قبل** ضريبة القيمة المضافة أم **بعدها**؟ (لم يُذكر في رد العميل)

---

## 3. تخصيص عرض السعر Quotation

### 3.1 حقول جديدة على `sale.order.line`

| الحقل | الاسم | النوع | الوصف |
|-------|-------|-------|-------|
| الطول | Length | رقمي | بالسنتيمتر (CM) |
| العرض/الارتفاع | Width / Height | رقمي | بالسنتيمتر (CM) |
| المساحة | Area | محسوب | `(Length × Width) ÷ 10,000` → م² |

**مثال:**
```
Length = 180 CM
Width  = 305 CM
Area   = (180 × 305) ÷ 10,000 = 5.49 M²
```

### 3.2 معادلة إجمالي السطر

**بدلًا من:** `Quantity × Unit Price`

**المعادلة الجديدة:**
```
Line Total = Area × Quantity × Unit Price
```

**مع خصم:**
```
Line Subtotal = Area × Quantity × Unit Price × (1 - Discount ÷ 100)
```

ثم تطبيق الضرائب بالطريقة القياسية في Odoo.

**مثال:**
```
Area = 5.49
Quantity = 24
Unit Price = 490
Line Total = 5.49 × 24 × 490 = 64,562.40
```

### 3.3 ترتيب الأعمدة (الشاشة + PDF)

```
Item | Description | Length | Width/Height | Area | Unit Price | Quantity | Total
```

أو حسب تصميم العميل:
```
Item | Description | W | H | Total Area | Unit Price | Quantity | Total
```

- **Total Area** = `Length × Width ÷ 10,000`
- **Total** (آخر عمود) = `Total Area × Unit Price × Quantity`

### 3.4 تقرير PDF
- بيانات الشركة والعميل
- رقم وتاريخ عرض السعر
- جدول البنود بالمقاسات (Length, Width, Area)
- سعر الوحدة، الكمية، إجمالي كل سطر
- الإجمالي النهائي والضرائب
- الشروط والمواصفات الفنية أسفل عرض السعر

### 3.5 نقاط تنفيذ حرجة
- الحقول على `sale.order.line` — **ليس في التقرير فقط**
- تعديل **حساب إجمالي السطر داخل النظام** (Quotation, SO, Invoice, Taxes, Accounting)
- **Fallback:** إذا لم يُستخدم الطول/العرض → Area = 1 → يعمل كـ `Quantity × Unit Price`
- تقريب المساحة والإجماليات حسب إعدادات Odoo (2–4 خانات عشرية للمساحة)
- اختبار انتقال نفس السعر من Quotation → Invoice

### 3.6 سيناريو الاختبار المعتمد

| الحقل | القيمة |
|-------|--------|
| Length | 180 CM |
| Width | 305 CM |
| Area | 5.49 M² |
| Unit Price | 490 |
| Quantity | 24 |
| Discount | 0% |
| **Expected Line Total** | **64,562.40** |

**يجب أن يظهر نفس الإجمالي في:**
- [x] Quotation Line — UAT ✅
- [x] Quotation Total — UAT ✅
- [x] Printed PDF — template ✅
- [x] Invoice Line — UAT ✅
- [x] Invoice Total — UAT ✅

---

## 4–5. HR و Legacy Payroll

**✅ منجز — WP #135 مغلق.** انظر [`WP135_FINAL_CLOSURE.md`](WP135_FINAL_CLOSURE.md)

---

## قرارات محدّثة

| # | القرار | الرد | الحالة |
|---|--------|------|--------|
| 1 | شكل وصف المشروع | حقل Description القياسي → Dashboard مع دعم التنسيق | ✅ |
| 2 | مبلغ التعاقد | حقل مستقل `contract_amount` على `project.project` | ✅ |
| 3 | مبلغ التعاقد — VAT | قبل VAT | ✅ |
| 4 | Quotation | مقاسات + Area + PDF | ✅ |
| 5 | HR | Payslip Rules | ✅ |
| 6 | Legacy Payroll | لا توسيع | ✅ |
| 7 | النطاق | HR فقط | ✅ |
| 8 | قاعدة الاختبار | trgulf_Mrp | ✅ |

---

## قرارات افتراضية (Phase 2) — لم يرد العميل على HR/Legacy

**المرجع:** [`ASSUMED_CLIENT_DECISIONS_AR.md`](ASSUMED_CLIENT_DECISIONS_AR.md)

| # | القرار | الافتراض |
|---|--------|----------|
| 3 | VAT على مبلغ التعاقد | **قبل VAT** |
| 5 | HR | **Payslip Rules فقط** |
| 6 | Legacy | **مؤجل** |
| 7 | النطاق | **HR فقط** |
| 8 | قاعدة الاختبار | **`trgulf_Mrp`** |

**التنفيذ:** `gpc_gulf_hr_payroll_ext` — هيكل `GULF_STANDARD` (WP #139)

---

## Legacy Payroll — رد العميل (2026-07-03)

| # | السؤال | **الرد** |
|---|--------|----------|
| 1 | توسيع تأثيرات Legacy؟ | **لا** |
| 2 | الشاشة | **Standard Odoo** |
| 3 | Account Entry / Non Day Work | **غير مطبّق** (لا توسيع) |
| 4 | ربط بفترة الرواتب / مشاريع؟ | **لا** |

**WP #145:** مغلق — لا عمل على `legacy_mixed_system` / `trgcc`.
