#!/usr/bin/env bash
# Test OpenProject reachability from this machine and recommend sync path.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SOCKET=/var/run/tailscale/tailscaled.sock
KEY="${SSH_KEY:-/root/.ssh/id_master}"
REMOTE_HOST="${MASTER_SSH_HOST:-master}"
REMOTE_USER="${MASTER_SSH_USER:-sabry}"

if [[ -f /opt/.env ]]; then
  set -a
  # shellcheck disable=SC1091
  source <(grep -E '^(OPENPROJECT_|TAILSCALE_)' /opt/.env | grep -v '^#')
  set +a
fi

: "${OPENPROJECT_API_TOKEN:?Set OPENPROJECT_API_TOKEN in /opt/.env}"
BASE="${OPENPROJECT_URL:-https://master.tailcf9988.ts.net:10081}"
PROJECT_ID="${OPENPROJECT_PROJECT_ID:-19}"
FALLBACK_IP="${MASTER_TAILSCALE_IP:-100.76.217.35}"

echo "=== OpenProject connectivity check ==="
echo "URL: $BASE"
echo "Project: $PROJECT_ID"
echo ""

# Tailscale
if tailscale --socket="$SOCKET" status >/dev/null 2>&1; then
  echo "[OK] Tailscale running"
  tailscale --socket="$SOCKET" status | grep -E 'master|opt-cursor' || true
else
  echo "[WARN] Tailscale not running — run: bash $SCRIPT_DIR/tailscale_auth_and_sync.sh"
fi
echo ""

test_curl() {
  local url="$1"
  local code
  code=$(curl -skS -m 20 -o /dev/null -w "%{http_code}" \
    -u "apikey:${OPENPROJECT_API_TOKEN}" \
    "${url}/api/v3/projects/${PROJECT_ID}" \
    -H "Accept: application/json" 2>/dev/null || true)
  echo "${code:-000}"
}

DIRECT_CODE=$(test_curl "$BASE")
echo "Direct API ($BASE): HTTP $DIRECT_CODE"

TS_CODE=$(test_curl "https://${FALLBACK_IP}:10081")
echo "Tailscale IP (https://${FALLBACK_IP}:10081): HTTP $TS_CODE"

SSH_OK=0
MASTER_CODE="000"
if ssh -i "$KEY" -o BatchMode=yes -o ConnectTimeout=15 -o StrictHostKeyChecking=accept-new \
  -o UserKnownHostsFile=/dev/null \
  -o ProxyCommand="tailscale --socket=$SOCKET nc %h %p" \
  "${REMOTE_USER}@${REMOTE_HOST}" "hostname" >/dev/null 2>&1; then
  SSH_OK=1
  echo "[OK] SSH to ${REMOTE_USER}@${REMOTE_HOST}"
  MASTER_CODE=$(ssh -i "$KEY" -o BatchMode=yes -o ConnectTimeout=20 -o StrictHostKeyChecking=accept-new \
    -o UserKnownHostsFile=/dev/null \
    -o ProxyCommand="tailscale --socket=$SOCKET nc %h %p" \
    "${REMOTE_USER}@${REMOTE_HOST}" \
    "curl -skS -m 15 -o /dev/null -w '%{http_code}' -u 'apikey:${OPENPROJECT_API_TOKEN}' '${BASE}/api/v3/projects/${PROJECT_ID}' -H 'Accept: application/json' 2>/dev/null || echo 000")
  echo "API via master (SSH hop): HTTP $MASTER_CODE"
else
  echo "[FAIL] SSH to ${REMOTE_USER}@${REMOTE_HOST}"
fi

echo ""
echo "=== Recommendation ==="
if [[ "$DIRECT_CODE" == "200" ]] || [[ "$TS_CODE" == "200" ]]; then
  echo "PRIMARY: Run sync locally"
  echo "  bash $SCRIPT_DIR/run_sync_wp135.sh"
  echo "  # or: bash $SCRIPT_DIR/sync_openproject.sh"
  exit 0
fi

if [[ "$SSH_OK" == "1" && "$MASTER_CODE" == "200" ]]; then
  echo "FALLBACK: Direct API blocked from this machine; use SSH sync"
  echo "  bash $SCRIPT_DIR/ssh_to_master_and_sync.sh"
  echo "  # or: bash $SCRIPT_DIR/sync_openproject.sh"
  if [[ "$DIRECT_CODE" == "000" ]]; then
    echo ""
    echo "To enable direct API (optional), on MASTER run as root:"
    echo "  bash $SCRIPT_DIR/apply_master_firewall.sh"
  fi
  exit 2
fi

echo "BLOCKED: Fix Tailscale/SSH or OpenProject on master first."
echo "  On master: curl -sk -u apikey:TOKEN ${BASE}/api/v3/projects/${PROJECT_ID}"
exit 1
