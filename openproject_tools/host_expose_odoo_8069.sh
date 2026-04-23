#!/usr/bin/env bash
# Run on the DOCKER HOST (e.g. 208.109.229.216), as root, where docker.sock exists.
# NOT inside a dev container — there is no Docker API there.
#
# Purpose: find the Odoo container and ensure host port 8069 is published to container 8069.
set -euo pipefail

echo "=== Docker containers (look for 8069) ==="
docker ps -a --format 'table {{.ID}}\t{{.Names}}\t{{.Ports}}\t{{.Image}}' || {
  echo "ERROR: Cannot talk to Docker. Run this script on the machine that runs Docker (your VPS), not inside a container."
  exit 1
}

echo ""
echo "=== Containers publishing 8069 ==="
docker ps --filter publish=8069 --format '{{.ID}} {{.Names}} {{.Ports}}' || true

if docker ps --filter publish=8069 --format '{{.ID}}' | grep -q .; then
  echo "OK: Something is already publishing host :8069"
  exit 0
fi

echo ""
echo "No container publishes 8069 yet. Typical fix:"
echo "  1) Recreate the container with:  -p 8069:8069  (and often -p 8072:8072 for longpolling)"
echo "  2) Or with docker compose, under services.odoo.ports: - \"8069:8069\""
echo ""
echo "Example (replace CONTAINER_NAME):"
echo "  docker commit CONTAINER_NAME odoo-snapshot   # optional backup"
echo "  docker stop CONTAINER_NAME"
echo "  docker inspect CONTAINER_NAME   # note image, env, mounts, then run again with -p 8069:8069"
echo ""
echo "=== Host firewall (if ufw exists) ==="
if command -v ufw >/dev/null 2>&1; then
  ufw allow 8069/tcp || true
  ufw allow 8072/tcp || true
  ufw status || true
else
  echo "ufw not installed. Open TCP 8069 in your cloud provider firewall / security group for 208.109.229.216"
fi

exit 0
