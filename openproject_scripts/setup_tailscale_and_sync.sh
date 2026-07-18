#!/usr/bin/env bash
# Start Tailscale (if needed) and sync OpenProject WP #135.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if grep -qE '^TAILSCALE_AUTHKEY=tskey-' /opt/.env 2>/dev/null; then
  exec "$SCRIPT_DIR/tailscale_auth_and_sync.sh"
fi

SOCKET=/var/run/tailscale/tailscaled.sock
STATE=/var/lib/tailscale/tailscaled.state

mkdir -p /var/lib/tailscale /var/run/tailscale

if ! pgrep -x tailscaled >/dev/null 2>&1; then
  echo "Starting tailscaled ..."
  tailscaled --state="$STATE" --socket="$SOCKET" --tun=userspace-networking &
  sleep 3
fi

if ! tailscale --socket="$SOCKET" status --json 2>/dev/null | grep -q '"BackendState":"Running"'; then
  echo ""
  echo "Tailscale not logged in."
  echo ""
  echo "Option A — auth key (recommended): add to /opt/.env:"
  echo "  TAILSCALE_AUTHKEY=tskey-auth-..."
  echo "Then run: bash $SCRIPT_DIR/tailscale_auth_and_sync.sh"
  echo ""
  echo "Option B — browser login:"
  echo "  tailscale --socket=$SOCKET up --accept-routes --hostname=opt-cursor-openproject"
  exit 1
fi

echo "Tailscale connected:"
tailscale --socket="$SOCKET" status | head -5

echo ""
echo "Testing OpenProject ..."
export $(grep -E '^OPENPROJECT_' /opt/.env | xargs)
CODE=$(curl -sS -m 30 -o /dev/null -w "%{http_code}" \
  -u "apikey:${OPENPROJECT_API_TOKEN}" \
  "${OPENPROJECT_URL}/api/v3/projects/19" \
  -H "Accept: application/json" || echo "000")
echo "OpenProject HTTP: $CODE"

if [[ "$CODE" != "200" ]]; then
  echo "[ERROR] Cannot reach OpenProject (expected 200, got $CODE)"
  exit 1
fi

echo ""
exec bash "$SCRIPT_DIR/one_shot_sync_wp135.sh"
