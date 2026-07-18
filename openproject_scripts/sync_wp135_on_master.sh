#!/usr/bin/env bash
# RUN ON MASTER SERVER ONLY (hostname: master, NOT the Docker container 80d3d66c9b45)
# Verify: hostname && curl -s -o /dev/null -w "local OP: %{http_code}\n" http://127.0.0.1:10081/

set -euo pipefail

OPENPROJECT_URL="${OPENPROJECT_URL:-http://127.0.0.1:10081}"
OPENPROJECT_API_TOKEN="${OPENPROJECT_API_TOKEN:?export OPENPROJECT_API_TOKEN first}"
PROJECT_ID=19
PARENT_ID=135
AUTH="apikey:${OPENPROJECT_API_TOKEN}"

echo "=== $(hostname) — OpenProject sync WP #135 ==="
curl -sf -u "$AUTH" "${OPENPROJECT_URL}/api/v3/projects/${PROJECT_ID}" -H "Accept: application/json" >/dev/null \
  || { echo "ERROR: OpenProject not on localhost:10081 on THIS machine."; exit 1; }

# Get WP 135
WP=$(curl -sf -u "$AUTH" "${OPENPROJECT_URL}/api/v3/work_packages/${PARENT_ID}" -H "Accept: application/json")
LOCK=$(echo "$WP" | python3 -c "import sys,json; print(json.load(sys.stdin)['lockVersion'])")
DESC=$(echo "$WP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('description',{}).get('raw',''))")

MARKER='<!-- requirements-review-automation -->'
if ! echo "$DESC" | grep -qF "$MARKER"; then
  APPEND='

<!-- requirements-review-automation -->

---

## حالة التنفيذ — 2026-07-02

**الحالة:** بانتظار قرارات العميل — **لا يبدأ التنفيذ**

**مهمة القرارات (فرعية):** قرارات العميل — مراجعة المتطلبات (قبل التنفيذ)
'
  NEW_DESC="${DESC}${APPEND}"
  python3 -c "
import json,sys
print(json.dumps({'lockVersion': int('$LOCK'), 'description': {'format': 'markdown', 'raw': sys.stdin.read()}}, ensure_ascii=False))
" <<<"$NEW_DESC" | curl -sf -u "$AUTH" -X PATCH \
    "${OPENPROJECT_URL}/api/v3/work_packages/${PARENT_ID}" \
    -H "Content-Type: application/json" -d @- >/dev/null
  echo "✓ Updated WP #${PARENT_ID}"
else
  echo "✓ WP #${PARENT_ID} already updated"
fi

CHILD_SUBJECT='قرارات العميل — مراجعة المتطلبات (قبل التنفيذ)'
EXISTING=$(curl -sf -u "$AUTH" "${OPENPROJECT_URL}/api/v3/projects/${PROJECT_ID}/work_packages?pageSize=50" -H "Accept: application/json")
CHILD_ID=$(echo "$EXISTING" | python3 -c "
import sys,json
subj='$CHILD_SUBJECT'
for wp in json.load(sys.stdin).get('_embedded',{}).get('elements',[]):
    if wp.get('subject','').startswith('قرارات العميل'):
        print(wp['id']); break
")

if [[ -z "$CHILD_ID" ]]; then
  CHILD_BODY=$(cat <<'EOF'
# قرارات العميل — مراجعة المتطلبات (قبل التنفيذ)

**الحالة:** بانتظار مراجعة المستلم — لا يبدأ التنفيذ قبل الإجابة

## أسئلة للتأكيد
- [ ] شكل وصف المشروع: نص حر / HTML / تبويب منفصل؟
- [ ] مبلغ التعاقد: Budget أم حقل مستقل؟ قبل أم بعد VAT؟
- [ ] Quotation: نموذج PDF أو لقطة شاشة؟ شاشة أم تقرير؟
- [ ] HR: Payslip Rules أم ربط بمشاريع؟
- [ ] Legacy: توسيع التأثيرات؟ أي شاشة؟ Account Entry أم Non Day Work؟
- [ ] النطاق: HR فقط / Legacy فقط / الاثنان؟
- [ ] قاعدة الاختبار: trgulf_Mrp / trgcc / أخرى؟
EOF
)
  POST=$(python3 -c "
import json
body='''$CHILD_BODY'''
print(json.dumps({
  'subject': '$CHILD_SUBJECT',
  'description': {'format': 'markdown', 'raw': '''$CHILD_BODY'''},
  'type': {'href': '/api/v3/types/1'},
  'status': {'href': '/api/v3/statuses/1'},
  'priority': {'href': '/api/v3/priorities/8'},
  'parent': {'href': '/api/v3/work_packages/$PARENT_ID'},
}, ensure_ascii=False))
")
  CHILD_ID=$(curl -sf -u "$AUTH" -X POST \
    "${OPENPROJECT_URL}/api/v3/projects/${PROJECT_ID}/work_packages" \
    -H "Content-Type: application/json" -d "$POST" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
  echo "✓ Created child WP #${CHILD_ID}"
else
  echo "✓ Child WP already exists: #${CHILD_ID}"
fi

PUBLIC="https://master.tailcf9988.ts.net:10081"
echo ""
echo "========== LINKS =========="
echo "Parent: ${PUBLIC}/work_packages/${PARENT_ID}"
echo "Child:  ${PUBLIC}/work_packages/${CHILD_ID}"
echo "==========================="
