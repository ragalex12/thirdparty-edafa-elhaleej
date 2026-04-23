# Expose Odoo (8069) from Docker — agent notes

## What was verified (inside your dev container)

- Odoo listens on **`0.0.0.0:8069`** inside the container (reachable *inside* that network namespace).
- **`docker`** CLI cannot run here: no **`/var/run/docker.sock`** — port publishing must be done on the **Docker host**.

## Why `http://208.109.229.216:8069` fails from Firefox

The public IP is the **host**. Traffic must:

1. Pass the **cloud firewall** (allow **TCP 8069** to that instance).
2. Be **published** by Docker: **`host:8069` → `container:8069`** (`-p 8069:8069`).

`ufw` inside the container does not fix (1) or (2).

## What you do on the VPS (`ssh` to `208.109.229.216`)

1. Copy this repo’s script to the host (or paste contents), then:

   ```bash
   sudo bash /path/to/host_expose_odoo_8069.sh
   ```

2. If nothing publishes 8069, **recreate** the Odoo container with **`-p 8069:8069`** (see script output).

3. In the **hosting control panel**, add an inbound rule: **TCP 8069** from your IP (or `0.0.0.0/0` for a quick test).

4. From your PC:

   ```bash
   curl -v --connect-timeout 10 http://208.109.229.216:8069/
   ```

## Cursor / dev environments

If this workspace is **only** a remote dev container, your provider may map ports differently — use **Ports** / **Forwarded Ports** in the IDE and open **`http://127.0.0.1:8069`** locally when forwarded.
