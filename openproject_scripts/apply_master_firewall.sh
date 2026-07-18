#!/usr/bin/env bash
# Run ON THE MASTER SERVER (as root) to allow OpenProject port 10081 from Tailscale peers.
# Usage on master: sudo bash apply_master_firewall.sh
set -euo pipefail

PORT=10081

echo "=== OpenProject firewall — allow Tailscale port $PORT ==="
echo "Host: $(hostname)"
ss -tlnp | grep "$PORT" || { echo "[WARN] Nothing listening on $PORT"; }

if command -v ufw >/dev/null 2>&1; then
  ufw allow in on tailscale0 to any port "$PORT" proto tcp
  ufw reload || true
  echo "[OK] ufw rule added for tailscale0:$PORT"
fi

if command -v iptables >/dev/null 2>&1; then
  if ! iptables -C INPUT -i tailscale0 -p tcp --dport "$PORT" -j ACCEPT 2>/dev/null; then
    iptables -I INPUT -i tailscale0 -p tcp --dport "$PORT" -j ACCEPT
    echo "[OK] iptables rule added for tailscale0:$PORT"
  else
    echo "[OK] iptables rule already present"
  fi
fi

echo ""
echo "Test from another Tailscale node:"
echo "  curl -sk -u 'apikey:TOKEN' 'https://100.76.217.35:${PORT}/api/v3/projects/19' -H 'Accept: application/json'"
