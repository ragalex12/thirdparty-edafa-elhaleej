#!/usr/bin/env bash
# Run Playwright from a temp directory when the project filesystem disallows chmod on node_modules.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKDIR="$(mktemp -d -t pw-bridge-e2e-XXXXXX)"

cleanup() {
  rm -rf "${WORKDIR}"
}
trap cleanup EXIT

cp -a "${SCRIPT_DIR}/package.json" "${SCRIPT_DIR}/playwright.config.ts" "${SCRIPT_DIR}/tests" "${WORKDIR}/"
cd "${WORKDIR}"

# Avoid broken caches on some mounts (ENOENT during cacache rename).
# Use pnpm when available (avoids chmod/rename errors on network mounts),
# otherwise fall back to npm with isolated cache.
if command -v pnpm >/dev/null 2>&1; then
    pnpm install
    PW_BIN="./node_modules/.bin/playwright"
else
    NP_CACHE="${WORKDIR}/.npm-cache"
    mkdir -p "${NP_CACHE}"
    export NPM_CONFIG_CACHE="${NP_CACHE}"
    npm install --cache "${NP_CACHE}" --globalconfig /dev/null --userconfig /dev/null
    PW_BIN="npx playwright"
fi

if [ "${PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD:-0}" != "1" ]; then
    ${PW_BIN} install chromium
fi
exec ${PW_BIN} test "$@"
