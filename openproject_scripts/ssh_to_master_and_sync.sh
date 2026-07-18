#!/usr/bin/env bash
# SSH to master via Tailscale, copy scripts + docs, run OpenProject sync on master.
# OpenProject on master is reachable via Funnel URL (not localhost:10081).
set -euo pipefail

SOCKET=/var/run/tailscale/tailscaled.sock
KEY="${SSH_KEY:-/root/.ssh/id_master}"
REMOTE_USER="${MASTER_SSH_USER:-}"
REMOTE_HOST="${MASTER_SSH_HOST:-master}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOCALADDONS="$(cd "$SCRIPT_DIR/.." && pwd)"
REMOTE_BASE="/tmp/op_sync/opt/localaddons"

# Which Python sync script to run (basename)
SYNC_SCRIPT="${SYNC_SCRIPT:-sync_requirements_review_wp135.py}"
DRY_RUN="${DRY_RUN:-}"
EXTRA_ARGS=("$@")

if [[ -f /opt/.env ]]; then
  set -a
  # shellcheck disable=SC1091
  source <(grep -E '^OPENPROJECT_' /opt/.env | grep -v '^#')
  set +a
fi

: "${OPENPROJECT_API_TOKEN:?Set OPENPROJECT_API_TOKEN in /opt/.env}"

# On master, Funnel URL works; localhost:10081 does not (proxy is 127.0.0.1:8081).
MASTER_OP_URL="${MASTER_OPENPROJECT_URL:-https://master.tailcf9988.ts.net:10081}"

SSH_OPTS_BASE=(
  -i "$KEY"
  -o BatchMode=yes
  -o ConnectTimeout=20
  -o StrictHostKeyChecking=accept-new
  -o UserKnownHostsFile=/dev/null
  -o ProxyCommand="tailscale --socket=$SOCKET nc %h %p"
)

try_ssh() {
  local user="$1"
  ssh "${SSH_OPTS_BASE[@]}" "${user}@${REMOTE_HOST}" "hostname" 2>/dev/null
}

if [[ -z "$REMOTE_USER" ]]; then
  for u in sabry vendorah2 root ubuntu debian; do
    if try_ssh "$u"; then REMOTE_USER="$u"; break; fi
  done
fi

SSH_OPTS=("${SSH_OPTS_BASE[@]}")

echo "SSH → ${REMOTE_USER:-?}@${REMOTE_HOST} ..."
if [[ -z "$REMOTE_USER" ]] || ! try_ssh "$REMOTE_USER"; then
  echo ""
  echo "SSH denied. On MASTER run once (authorize this machine):"
  echo "  mkdir -p ~/.ssh && chmod 700 ~/.ssh"
  echo "  echo '$(cat "${KEY}.pub" 2>/dev/null || echo MISSING_PUBKEY)' >> ~/.ssh/authorized_keys"
  echo "  chmod 600 ~/.ssh/authorized_keys"
  exit 1
fi

echo "Preparing remote sync tree at ${REMOTE_BASE} ..."
ssh "${SSH_OPTS[@]}" "${REMOTE_USER}@${REMOTE_HOST}" \
  "rm -rf /tmp/op_sync && mkdir -p ${REMOTE_BASE}/openproject_scripts ${REMOTE_BASE}/openproject_docs ${REMOTE_BASE}/openproject_scripts/docs"

echo "Copying scripts and docs to master ..."
scp "${SSH_OPTS[@]}" -r \
  "$LOCALADDONS/openproject_scripts/"*.py \
  "$LOCALADDONS/openproject_scripts/docs" \
  "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_BASE}/openproject_scripts/"

scp "${SSH_OPTS[@]}" -r \
  "$LOCALADDONS/openproject_docs/" \
  "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_BASE}/"

if [[ -d "$LOCALADDONS/gpc_gulf_project_ext/e2e/screenshots/gulf-phase1" ]]; then
  echo "Copying Playwright screenshots to master ..."
  ssh "${SSH_OPTS[@]}" "${REMOTE_USER}@${REMOTE_HOST}" \
    "mkdir -p ${REMOTE_BASE}/gpc_gulf_project_ext/e2e/screenshots"
  scp "${SSH_OPTS[@]}" -r \
    "$LOCALADDONS/gpc_gulf_project_ext/e2e/screenshots/gulf-phase1" \
    "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_BASE}/gpc_gulf_project_ext/e2e/screenshots/"
fi

if [[ -d "$LOCALADDONS/openproject_docs/gulf_delivery/bundle" ]] || [[ -d "$LOCALADDONS/openproject_docs/gulf_delivery" ]]; then
  echo "Copying Gulf delivery docs/bundle to master ..."
  ssh "${SSH_OPTS[@]}" "${REMOTE_USER}@${REMOTE_HOST}" \
    "mkdir -p ${REMOTE_BASE}/openproject_docs/gulf_delivery"
  scp "${SSH_OPTS[@]}" -r \
    "$LOCALADDONS/openproject_docs/gulf_delivery/" \
    "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_BASE}/openproject_docs/"
fi

if [[ -d "$LOCALADDONS/gpc_gulf_hr_payroll_ext/e2e/screenshots/gulf-phase2" ]]; then
  echo "Copying Phase 2 HR screenshots to master ..."
  ssh "${SSH_OPTS[@]}" "${REMOTE_USER}@${REMOTE_HOST}" \
    "mkdir -p ${REMOTE_BASE}/gpc_gulf_hr_payroll_ext/e2e/screenshots"
  scp "${SSH_OPTS[@]}" -r \
    "$LOCALADDONS/gpc_gulf_hr_payroll_ext/e2e/screenshots/gulf-phase2" \
    "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_BASE}/gpc_gulf_hr_payroll_ext/e2e/screenshots/"
fi

PY_ARGS=()
if [[ "$DRY_RUN" == "1" || " ${EXTRA_ARGS[*]} " == *" --dry-run "* ]]; then
  PY_ARGS+=(--dry-run)
fi

echo "Running ${SYNC_SCRIPT} on master (OPENPROJECT_URL=${MASTER_OP_URL}) ..."
ssh "${SSH_OPTS[@]}" "${REMOTE_USER}@${REMOTE_HOST}" bash -s <<REMOTE
set -euo pipefail
export OPENPROJECT_URL='${MASTER_OP_URL}'
export OPENPROJECT_API_TOKEN='${OPENPROJECT_API_TOKEN}'
export OPENPROJECT_PROJECT_ID='${OPENPROJECT_PROJECT_ID:-19}'
export OPENPROJECT_PARENT_WP_ID='${OPENPROJECT_PARENT_WP_ID:-135}'
cd '${REMOTE_BASE}/openproject_scripts'
python3 '${SYNC_SCRIPT}' ${PY_ARGS[@]+"${PY_ARGS[@]}"} ${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"}
REMOTE

echo ""
echo "Copying result files back ..."
for f in WP135_SYNC_RESULT.txt WP135_CLIENT_ANSWERS_SYNC.txt PHASE1_DELIVERY_WP.txt PHASE2_ASSUMED_SYNC.txt PHASE2_DELIVERY_WP.txt LEGACY_CLIENT_ANSWERS_SYNC.txt WP135_FINAL_CLOSURE_SYNC.txt GULF_FINAL_DELIVERY_WP.txt; do
  scp "${SSH_OPTS[@]}" \
    "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_BASE}/openproject_docs/${f}" \
    "$LOCALADDONS/openproject_docs/${f}" 2>/dev/null && echo "  ✓ ${f}" || true
done

echo ""
echo "Done. Board: ${MASTER_OP_URL}/projects/dev-needed-internal-tasks/work_packages"
