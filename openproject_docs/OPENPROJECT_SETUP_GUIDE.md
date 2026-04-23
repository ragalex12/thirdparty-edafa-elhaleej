# OpenProject 15 Native Install on Containerized Ubuntu — Problem & Solution Guide

## Context

You are installing OpenProject 15 natively (no Docker) on Ubuntu 24.04 running
inside a container (e.g. Cursor, Codespace, or any Docker-in-Docker environment).
The machine has NO Docker capabilities and NO LAN IP — only an internal bridge IP
(e.g. `172.17.0.x`) and loopback (`127.0.0.1`).

---

## Problem 1 — OpenProject apt package not found on Ubuntu 24.04

**Error:** `E: Unable to locate package openproject`

**Root cause:** OpenProject 15 has no Ubuntu 24.04 (Noble) repository.

**Fix:** Use the Ubuntu 22.04 (Jammy) repo — it installs fine on 24.04:

```bash
curl -sL "https://dl.packager.io/srv/opf/openproject/key" | apt-key add -
echo "deb https://dl.packager.io/srv/opf/openproject/stable/15/installer/ubuntu/22.04 ./" \
  > /etc/apt/sources.list.d/openproject.list
apt-get update && apt-get install -y openproject
```

---

## Problem 2 — `openproject configure` fails (TTY / cannot open tty-output)

**Error:** `PostgreSQL configuration canceled by user. cannot open tty-output`

**Root cause:** The interactive installer requires a TTY which is not available in
containerized/headless environments.

**Fix:** Do NOT run `openproject configure`. Configure manually:

### Step 1 — Install PostgreSQL and Memcached

```bash
apt-get install -y postgresql memcached
service postgresql start
sudo -u postgres psql -c "CREATE USER openproject WITH PASSWORD 'openproject_secret';"
sudo -u postgres psql -c "CREATE DATABASE openproject OWNER openproject;"
memcached -d -u root -l 127.0.0.1 -p 11211 -m 256
```

### Step 2 — Write the server config file directly

```bash
cat > /etc/openproject/conf.d/server << 'EOF'
OPENPROJECT_HOST__NAME="localhost:8090"
OPENPROJECT_HTTPS="false"
PORT="8090"
HOST="0.0.0.0"
RAILS_ENV="production"
RAILS_MIN_THREADS=4
RAILS_MAX_THREADS=16
OPENPROJECT_EMAIL__DELIVERY__METHOD="test"
SECRET_KEY_BASE="change_this_to_a_long_random_string"
RAILS_SERVE_STATIC_FILES="true"
EOF
```

### Step 3 — Set remaining config via openproject CLI

```bash
openproject config:set DATABASE_URL="postgres://openproject:openproject_secret@127.0.0.1:5432/openproject"
openproject config:set OPENPROJECT_CACHE__MEMCACHE__SERVER="127.0.0.1:11211"
openproject config:set OPENPROJECT_RAILS__CACHE__STORE="memcache"
openproject config:set OPENPROJECT_HTTPS="false"
openproject config:set RAILS_SERVE_STATIC_FILES="true"
```

### Step 4 — Run migrations and seed the database

```bash
openproject run rake db:migrate
openproject run rake db:seed
```

---

## Problem 3 — Puma binds to 127.0.0.1 only (not reachable externally)

**Error:** Puma starts on `127.0.0.1:8080` — unreachable from outside the container.

**Root cause:** The web script at `/opt/openproject/packaging/scripts/web` reads
the `HOST` env var (defaults to `127.0.0.1`). The `openproject run` script uses a
`BASE_PORT` / `PORT` consistency check — if `PORT` differs between `conf.d/server`
and `conf.d/other`, it always falls back to the value in `server`.

**Fix:** Set `HOST` and `PORT` consistently in ALL conf.d files:

```bash
openproject config:set HOST="0.0.0.0"
openproject config:set PORT="8090"

# Also patch the server conf file directly to match:
sed -i 's/^PORT=.*/PORT="8090"/' /etc/openproject/conf.d/server
sed -i 's/^HOST=.*/HOST="0.0.0.0"/' /etc/openproject/conf.d/server
```

> **Key rule:** `PORT` in `conf.d/server` and `conf.d/other` must be identical.
> If they differ, the script uses `BASE_PORT` (from `server`) and ignores the rest.

---

## Problem 4 — `bundle: command not found` when running rake tasks

**Error:** `sh: 1: bundle: command not found`

**Root cause:** The `bundle` binary is inside OpenProject's vendored Ruby environment,
not on the system PATH.

**Fix:** Always use the `openproject run` wrapper — never call `bundle exec` directly:

```bash
# CORRECT
openproject run rake db:migrate
openproject run rake db:seed
openproject run rails runner /tmp/script.rb

# WRONG — will always fail
bundle exec rake db:migrate
```

---

## Problem 5 — API returns 401 Unauthorized with a correct-looking token

**Root cause:** OpenProject 15 stores API tokens hashed as
`SHA256(plain_token + secret_key_base)`. The plain token shown in the UI cannot
be used directly via Basic Auth without this hashing being applied server-side.

**Fix:** Generate and store a known token via Rails runner so you control the plain value:

```bash
cat > /tmp/create_token.rb << 'EOF'
require 'digest'
plain  = "mynewtoken123456789012345678901234567890"
hashed = Digest::SHA256.hexdigest(plain + Rails.application.secret_key_base)
user   = User.find_by(login: 'admin')
Token::Api.where(user: user).delete_all
t       = Token::Api.new(user: user)
t.value = hashed
t.save!
puts "Done. Use plain token: #{plain}"
EOF

openproject run rails runner /tmp/create_token.rb
```

Then authenticate with:

```bash
curl -u "apikey:mynewtoken123456789012345678901234567890" http://localhost:8090/api/v3
```

---

## Problem 6 — "Invalid host_name configuration" error in browser or API

**Error:** HTTP 400 `Invalid host_name configuration`

**Root cause:** OpenProject validates that the `Host` header of every incoming
request matches `OPENPROJECT_HOST__NAME` exactly.

**Fix:** Set the hostname to match whatever the browser/client sends as the `Host`
header. Update BOTH conf files and restart Puma:

```bash
openproject config:set OPENPROJECT_HOST__NAME="your-domain-or-ip:port"
sed -i 's/^OPENPROJECT_HOST__NAME=.*/OPENPROJECT_HOST__NAME="your-domain-or-ip:port"/' \
  /etc/openproject/conf.d/server

# Restart Puma
pkill -9 -u openproject 2>/dev/null || true
pkill -9 -f "rails\|puma" 2>/dev/null || true
openproject run web &
```

---

## Problem 7 — UI loads but is completely unstyled (no CSS or JavaScript)

**Symptom:** OpenProject renders as plain HTML — "Top Menu", "Content", sign-in
form with no styles. Looks like an accessibility/text-only page.

**Root cause:** Rails in production mode does NOT serve static files by default.
It expects Nginx or Apache to serve `/public/assets/`. Without a reverse proxy,
all asset requests (`/assets/frontend/main.*.js`, `styles.*.css`) return 404.

**Fix:** Enable Rails static file serving, then restart:

```bash
openproject config:set RAILS_SERVE_STATIC_FILES="true"
echo 'RAILS_SERVE_STATIC_FILES="true"' >> /etc/openproject/conf.d/server

# Restart Puma
pkill -9 -u openproject 2>/dev/null || true
pkill -9 -f "rails\|puma" 2>/dev/null || true
openproject run web &
```

**Verify assets are being served:**

```bash
curl -sI http://127.0.0.1:8090/assets/frontend/main.*.js | head -1
# Should return: HTTP/1.1 200 OK
```

---

## Problem 8 — Machine IP is unreachable from the user's browser

**Symptom:** Firefox shows "can't connect to server at 172.17.x.x:8090".

**Root cause:** The container only has an internal Docker bridge IP (`172.17.x.x`)
which is not routable from the user's physical machine on their LAN.

**Fix:** Use a Cloudflare Quick Tunnel — free, no account, no config needed:

```bash
# Install cloudflared
curl -L "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb" \
  -o /tmp/cloudflared.deb
dpkg -i /tmp/cloudflared.deb

# Start tunnel
nohup cloudflared tunnel --url http://127.0.0.1:8090 --no-autoupdate \
  > /var/log/cloudflared.log 2>&1 &

# Get the public URL (wait ~15 seconds)
sleep 15 && grep "trycloudflare.com" /var/log/cloudflared.log
```

Then update OpenProject's hostname to the generated `*.trycloudflare.com` URL
(see Problem 6) and restart Puma.

> **Note:** The tunnel URL changes every restart. For a stable URL, use a named
> Cloudflare tunnel with a free Cloudflare account.

---

## Problem 9 — API error "Parent cannot be a milestone" when creating tasks

**Error:** HTTP 422 `Parent cannot be a milestone`

**Root cause:** OpenProject does not allow Milestone work package types to have
child tasks.

**Fix:** When creating work packages via the API, use `"Task"` for leaf items and
`"Phase"` or `"Feature"` for parent containers. Never assign `"Milestone"` as the
type of a work package that will have children.

---

## Quick Start Order (full summary)

| Step | Command |
|------|---------|
| 1 | Add Jammy apt repo → `apt-get install openproject` |
| 2 | Install postgresql + memcached manually |
| 3 | Write `conf.d/server` with `HOST=0.0.0.0`, `PORT=8090`, `RAILS_SERVE_STATIC_FILES=true` |
| 4 | `openproject config:set` for DB URL, cache, hostname |
| 5 | `openproject run rake db:migrate && db:seed` |
| 6 | `openproject run web &` |
| 7 | Generate API token via `openproject run rails runner` |
| 8 | `cloudflared tunnel --url http://127.0.0.1:8090` for external access |
| 9 | Update `OPENPROJECT_HOST__NAME` to tunnel URL → restart Puma |
