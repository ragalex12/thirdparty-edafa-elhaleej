#!/usr/bin/env bash
# Main entry: try direct API sync from this machine; fall back to SSH on master.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SYNC_SCRIPT="${SYNC_SCRIPT:-sync_requirements_review_wp135.py}"

set +e
bash "$SCRIPT_DIR/check_openproject_connectivity.sh" >/tmp/op_connectivity.log 2>&1
CONNECT_EXIT=$?
set -e

if [[ "$CONNECT_EXIT" == "0" ]]; then
  cat /tmp/op_connectivity.log
  echo "Direct API available — running locally ..."
  export $(grep -E '^OPENPROJECT_' /opt/.env | xargs)
  exec python3 "$SCRIPT_DIR/$SYNC_SCRIPT" "$@"
fi

cat /tmp/op_connectivity.log

if [[ "$CONNECT_EXIT" == "2" ]]; then
  echo ""
  echo "Falling back to SSH sync on master ..."
  export SYNC_SCRIPT
  exec bash "$SCRIPT_DIR/ssh_to_master_and_sync.sh" "$@"
fi

exit "$CONNECT_EXIT"
