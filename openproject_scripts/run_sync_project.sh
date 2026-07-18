#!/usr/bin/env bash
# Run a custom sync script (default: sync_project_template.py) with env from /opt/.env.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SYNC_SCRIPT="${SYNC_SCRIPT:-sync_project_template.py}"

cd /opt
export $(grep -E '^OPENPROJECT_' .env | xargs)

set +e
bash "$SCRIPT_DIR/check_openproject_connectivity.sh" >/tmp/op_connectivity.log 2>&1
CONNECT_EXIT=$?
set -e

if [[ "$CONNECT_EXIT" == "0" ]]; then
  cat /tmp/op_connectivity.log
  exec python3 "$SCRIPT_DIR/$SYNC_SCRIPT" "$@"
fi

cat /tmp/op_connectivity.log

if [[ "$CONNECT_EXIT" == "2" ]]; then
  export SYNC_SCRIPT
  exec bash "$SCRIPT_DIR/ssh_to_master_and_sync.sh" "$@"
fi

exit "$CONNECT_EXIT"
