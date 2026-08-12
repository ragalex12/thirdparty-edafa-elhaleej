# Gulf / MM — Client UAT case study

Public-facing requirement-to-proof page for Gulf / MM timesheet, labor accrual, and analytic reporting UAT.

## Purpose

Explain what the meeting requested, what was found, what was implemented, and show browser + manual proof — without credentials, private URLs, or production changes.

## Open locally

```bash
# From repository root
python3 -m http.server 8765 -d docs
# then open http://127.0.0.1:8765/client_demo/gulf_mm/
```

Or open `docs/client_demo/gulf_mm/index.html` directly in a browser.

## How screenshots were generated

- Browser UAT: Playwright suite in `tests/playwright/gulf_mm/` against the isolated test database only.
- Safety: `assertTestDatabase()` aborts unless the database is the approved UAT clone.
- Manual / Excel comparison shots: copied from the local evidence pack (sanitized).
- Blank loading frames were replaced with verified UAT evidence where the wizard hash needed a longer settle time.

## Playwright commands

```bash
cd tests/playwright/gulf_mm
cp .env.example .env   # fill locally; never commit .env
npm install
npx playwright install chromium
npm run test:odoo      # Odoo browser UAT
npm run test:page      # static case-study page QA
```

Environment variables (names only — see `.env.example`):

- `GULF_MM_BASE_URL`
- `GULF_MM_DB` (must be the UAT clone)
- `GULF_MM_USER`
- `GULF_MM_PASSWORD`

## Production dependency

**None.** This page and the Playwright suite must never target production. Production writes during UAT: **0**. Deployment requires separate explicit approval.

## Update procedure

1. Re-run Playwright on the UAT clone.
2. Refresh `assets/playwright/` screenshots.
3. Update counts in `index.html` and `REQUEST_IMPLEMENTATION_MATRIX.md`.
4. Re-run page QA (`npm run test:page`).
5. Secret-scan new assets before commit.
6. Push the proof branch; do not merge to production automatically.

## Related docs

- `REQUEST_IMPLEMENTATION_MATRIX.md`
- Repository `docs/FINAL_GULF_MM_UAT_REPORT.md`
- Repository `docs/MEETING_REQUIREMENTS_TRACEABILITY.md`
