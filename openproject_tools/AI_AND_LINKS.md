# OpenProject URLs — for assistants and humans

**Do not guess** `localhost` or port `8090` for “the link to OpenProject” unless the user explicitly asked for local-only access.

1. Read **`/opt/localaddons/openproject_tools/openproject_public_url.env`** for:
   - `OPENPROJECT_PUBLIC_BASE_URL` — public HTTPS URL (Cloudflare tunnel)
   - `OPENPROJECT_DEFAULT_PROJECT` — default project identifier slug

2. Full project URL pattern:
   ```text
   ${OPENPROJECT_PUBLIC_BASE_URL}/projects/${OPENPROJECT_DEFAULT_PROJECT}
   ```

3. Work packages board:
   ```text
   ${OPENPROJECT_PUBLIC_BASE_URL}/projects/${OPENPROJECT_DEFAULT_PROJECT}/work_packages
   ```

4. Same information is summarized in **`/opt/localaddons/WORKSPACE_GUIDE.md`** (OpenProject Access section).

If the tunnel hostname changes (common with ephemeral `cloudflared tunnel --url`), update **`openproject_public_url.env`** once; all scripts and docs should refer to that file.
