# Playwright result summary (sanitized)

Raw Playwright HTML reports are **not** published (they can embed local URLs and auth paths).

| Project | Scenarios | Passed | Failed | Errors | Skipped |
|---------|-----------|-------:|-------:|-------:|--------:|
| odoo-uat | PW-MM browser suite | 16 | 0 | 0 | 0 |
| case-study-page | Static page QA | 5 | 0 | 0 | 0 |

## Safety

- Allowed database: UAT clone only
- Production database names abort the suite before browser work
- Credentials via environment variables only (never committed)

## Notes

- Populate/post for the identifiable January proof batch was finalized with current hours-guard code on the UAT clone.
- Statement private RPC methods are not callable remotely; statement proof uses public read models + verified statement screenshots.
- Thin loading frames for wizard/XLSX were replaced with verified UAT evidence screenshots for the public gallery.
