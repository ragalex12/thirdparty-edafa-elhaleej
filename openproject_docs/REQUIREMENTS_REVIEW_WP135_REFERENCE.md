# Requirements Review — WP #135 (مشاريع الخليج الصناعى)

**Project:** Dev Needed — Internal Tasks  
**Project ID:** 19  
**Identifier:** `dev-needed-internal-tasks`  
**OpenProject URL:** https://master.tailcf9988.ts.net:10081  
**Board:** https://master.tailcf9988.ts.net:10081/projects/dev-needed-internal-tasks/work_packages  
**Status:** مواصفات البنود 1–3 معتمدة — جاهز للتنفيذ (#136–#138) — البنود 4–5 بانتظار العميل  
**Last synced:** 2026-07-03 (client answers — `sync_client_answers_wp135.py`)

---

## Parent work package

| ID | Subject | Link |
|----|---------|------|
| **135** | مشاريع الخليج الصناعى | https://master.tailcf9988.ts.net:10081/work_packages/135 |

Parent of WP #135 in hierarchy: **#88** (`gulf_projects_industrial_parent`)

---

## Child work packages under #135

### قرارات العميل (primary — send client here)

| ID | Subject | Link |
|----|---------|------|
| **140** | قرارات العميل — مراجعة المتطلبات (قبل التنفيذ) | https://master.tailcf9988.ts.net:10081/work_packages/140 |

**Gate for all implementation** — client answers here first.

### تقدير الوقت

| ID | Subject | Link |
|----|---------|------|
| **146** | تقدير الوقت — مشاريع الخليج (Time estimate) | https://master.tailcf9988.ts.net:10081/work_packages/146 |

Contains full Arabic time estimate from [`REQUIREMENTS_REVIEW_TIME_ESTIMATE_AR.txt`](REQUIREMENTS_REVIEW_TIME_ESTIMATE_AR.txt).

### مهام التنفيذ — عربي (created first on master)

| ID | Subject | Link |
|----|---------|------|
| 136 | إضافة وصف المشروع داخل شاشة المشروع | https://master.tailcf9988.ts.net:10081/work_packages/136 |
| 137 | إضافة قيمة/مبلغ التعاقد (أو استخدام Budget) | https://master.tailcf9988.ts.net:10081/work_packages/137 |
| 138 | تعديل شاشة الـ Quotation وشكل عرض الإجماليات | https://master.tailcf9988.ts.net:10081/work_packages/138 |
| 139 | تأثيرات الرواتب داخل HR (Overtime، خصومات، بدلات…) | https://master.tailcf9988.ts.net:10081/work_packages/139 |

### مهام النطاق — إنجليزي (tracking / blocked until #140 confirmed)

| ID | Subject | Link |
|----|---------|------|
| 141 | 1. وصف المشروع — Odoo Community | https://master.tailcf9988.ts.net:10081/work_packages/141 |
| 142 | 2. مبلغ التعاقد — Odoo Community | https://master.tailcf9988.ts.net:10081/work_packages/142 |
| 143 | 3. Quotation — Odoo Community | https://master.tailcf9988.ts.net:10081/work_packages/143 |
| 144 | 4. تأثيرات الرواتب — HR (Odoo القياسي) | https://master.tailcf9988.ts.net:10081/work_packages/144 |
| 145 | 5. تأثيرات الرواتب — Legacy Payroll | https://master.tailcf9988.ts.net:10081/work_packages/145 |

> **Note:** #136–#139 and #141–#145 overlap by topic. Prefer Arabic tasks (#136–#139) for execution; consider closing #141–#145 as duplicates in OpenProject UI.

---

## Local documentation (this folder)

| File | Purpose |
|------|---------|
| [`REQUIREMENTS_REVIEW_MESSAGE_AR.txt`](REQUIREMENTS_REVIEW_MESSAGE_AR.txt) | Full Arabic message to client |
| [`REQUIREMENTS_REVIEW_MESSAGE_SEND_AR.txt`](REQUIREMENTS_REVIEW_MESSAGE_SEND_AR.txt) | Send-ready message + questions |
| [`REQUIREMENTS_REVIEW_MESSAGE_SHORT_AR.txt`](REQUIREMENTS_REVIEW_MESSAGE_SHORT_AR.txt) | Short WhatsApp version |
| [`REQUIREMENTS_REVIEW_DECISIONS_CHECKLIST.md`](REQUIREMENTS_REVIEW_DECISIONS_CHECKLIST.md) | Track client answers (8 decisions) |
| [`REQUIREMENTS_REVIEW_CLIENT_ANSWERS_AR.md`](REQUIREMENTS_REVIEW_CLIENT_ANSWERS_AR.md) | **Client answers (2026-07-03) — items 1–3** |
| [`REQUIREMENTS_REVIEW_OPENPROJECT_WP135_DRAFT.md`](REQUIREMENTS_REVIEW_OPENPROJECT_WP135_DRAFT.md) | WP description draft (updated 2026-07-03) |
| [`REQUIREMENTS_REVIEW_TIME_ESTIMATE_SHORT_AR.txt`](REQUIREMENTS_REVIEW_TIME_ESTIMATE_SHORT_AR.txt) | Short estimate (WhatsApp) |
| [`WP135_SYNC_RESULT.txt`](WP135_SYNC_RESULT.txt) | Machine-readable link list |
| [`WP135_CLIENT_ANSWERS_SYNC.txt`](WP135_CLIENT_ANSWERS_SYNC.txt) | Client-answers sync result |

---

## Automation scripts

| Script | Purpose |
|--------|---------|
| `/opt/localaddons/openproject_scripts/complete_wp135_packages.py` | Idempotent create/update all WPs |
| `/opt/localaddons/openproject_scripts/ssh_to_master_and_sync.sh` | SSH `sabry@master` + run sync |
| `/opt/localaddons/openproject_scripts/sync_client_answers_wp135.py` | **Sync client answers (2026-07-03) to WPs** |
| `/opt/localaddons/openproject_scripts/fix_wp135_descriptions.py` | Patch WP descriptions from local specs |

**API access from opt-cursor:** use Funnel URL `https://master.tailcf9988.ts.net:10081` (not Tailscale IP).  
**SSH from opt-cursor:** `ssh sabry@master` (key in `/home/sabry/.ssh/authorized_keys`).

**Env:** `/opt/.env` — `OPENPROJECT_*`, `TAILSCALE_AUTHKEY`

---

## Scope summary (Odoo)

1. **Odoo Community** — project description, contract amount, Quotation, standard HR
2. **Legacy Payroll** — `legacy_mixed_system` / classic UI on test DB `trgcc`

---

## After client replies on #140

1. ✅ Updated [`REQUIREMENTS_REVIEW_DECISIONS_CHECKLIST.md`](REQUIREMENTS_REVIEW_DECISIONS_CHECKLIST.md) — items 1–3 answered (2026-07-03)
2. ✅ Client answers documented in [`REQUIREMENTS_REVIEW_CLIENT_ANSWERS_AR.md`](REQUIREMENTS_REVIEW_CLIENT_ANSWERS_AR.md)
3. Run `sync_client_answers_wp135.py` on master to push to OpenProject
4. 🟢 Move #136–#138 to **In progress**
5. ⏳ Items 4–5 (HR/Legacy) — still awaiting client on #140
