#!/usr/bin/env bash
# Run THIS SCRIPT ON THE MASTER SERVER (where OpenProject listens on :10081).
# From master, localhost API works even if Tailscale ingress is blocked.
set -euo pipefail

# On master, OpenProject is behind Tailscale Funnel (not 127.0.0.1:10081).
export OPENPROJECT_URL="${OPENPROJECT_URL:-https://master.tailcf9988.ts.net:10081}"
export $(grep -E '^OPENPROJECT_' /opt/.env 2>/dev/null | xargs) || true

: "${OPENPROJECT_API_TOKEN:?Set OPENPROJECT_API_TOKEN}"

echo "OpenProject: $OPENPROJECT_URL"
python3 /opt/localaddons/openproject_scripts/sync_requirements_review_wp135.py
