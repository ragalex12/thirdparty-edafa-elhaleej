#!/usr/bin/env bash
# Run on machine with OpenProject network access (Tailscale).
set -euo pipefail
cd /opt
export $(grep -E '^OPENPROJECT_' .env | xargs)
python3 /opt/localaddons/openproject_scripts/sync_requirements_review_wp135.py "$@"
