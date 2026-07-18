#!/usr/bin/env bash
# Tailscale headless login + OpenProject WP #135 sync.
set -euo pipefail

SOCKET=/var/run/tailscale/tailscaled.sock
STATE=/var/lib/tailscale/tailscaled.state
ENV_FILE=/opt/.env

mkdir -p /var/lib/tailscale /var/run/tailscale

# Load env
if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source <(grep -E '^(OPENPROJECT_|TAILSCALE_)' "$ENV_FILE" | grep -v '^#')
  set +a
fi

: "${TAILSCALE_AUTHKEY:?Add TAILSCALE_AUTHKEY=tskey-auth-... to /opt/.env}"

if ! pgrep -x tailscaled >/dev/null 2>&1; then
  echo "Starting tailscaled ..."
  tailscaled --state="$STATE" --socket="$SOCKET" --tun=userspace-networking &
  sleep 3
fi

echo "Logging in to Tailscale (hostname: opt-cursor-openproject) ..."
tailscale --socket="$SOCKET" up \
  --auth-key="$TAILSCALE_AUTHKEY" \
  --accept-routes \
  --hostname=opt-cursor-openproject \
  --reset

echo ""
tailscale --socket="$SOCKET" status | head -8

echo ""
echo "Testing OpenProject ..."
: "${OPENPROJECT_API_TOKEN:?Set OPENPROJECT_API_TOKEN in /opt/.env}"
BASE="${OPENPROJECT_URL:-https://master.tailcf9988.ts.net:10081}"
CODE=$(curl -sS -m 30 -o /dev/null -w "%{http_code}" \
  -u "apikey:${OPENPROJECT_API_TOKEN}" \
  "${BASE}/api/v3/projects/19" \
  -H "Accept: application/json" || echo "000")
echo "OpenProject HTTP: $CODE"

if [[ "$CODE" != "200" ]]; then
  echo "[ERROR] OpenProject not reachable (got $CODE). Check tailscale status and OPENPROJECT_URL."
  exit 1
fi

echo ""
exec python3 /opt/localaddons/openproject_scripts/sync_requirements_review_wp135.py
