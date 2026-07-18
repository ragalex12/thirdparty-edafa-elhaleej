#!/usr/bin/env python3
"""
Update OpenProject WP #205 — Fix Projects Analysis PDF report KeyError: data.

Records resolution, closes the work package, and posts an activity comment.

Usage:
  SYNC_SCRIPT=sync_wp205_projects_analysis_fix.py bash ssh_to_master_and_sync.sh
  # or locally when API is reachable:
  python3 sync_wp205_projects_analysis_fix.py
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from pathlib import Path

import requests
from requests.auth import HTTPBasicAuth

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sync_requirements_review_wp135 import (  # noqa: E402
    ENV_CANDIDATES,
    get_base_url,
    get_token,
    load_dotenv,
)

PUBLIC_BASE = "https://master.tailcf9988.ts.net:10081"
WP_ID = 205
PARENT_WP_ID = 88
MARKER = "<!-- wp205-resolution-2026-07-04 -->"
TODAY = date.today().isoformat()

RESOLUTION = f"""

---

{MARKER}

## Resolution ({TODAY})

**Status:** Fixed and deployed.

### Root cause

Template `legacy_mixed_system.report_legacy_projects_analysis` used `data.get('date_from')` / `data.get('date_to')`.

In Odoo 18, wizard `data` keys are merged into the **top-level** QWeb render context (there is no variable named `data`). Evaluating `data.get(...)` raised:

`KeyError: 'data'`

Source: Chatwoot #49 / GPC traceback on `gpc.odoo.com.se` (2026-07-04).

### Fix (minimal)

File: `legacy_mixed_system/reports/legacy_report_projects_templates.xml`

Replaced:

```xml
<p t-if="data.get('date_from')">
    <strong>Period:</strong>
    <span t-esc="data.get('date_from')"/> —
    <span t-esc="data.get('date_to')"/>
</p>
```

with:

```xml
<p t-if="date_from">
    <strong>Period:</strong>
    <span t-esc="date_from"/> —
    <span t-esc="date_to"/>
</p>
```

No Python / wizard / report-action changes.

### Deploy

- Upgraded `legacy_mixed_system` on **trgcc** and **trgulf_Mrp**
- Template `legacy_report_projects_templates.xml` loaded successfully

### Verification

Smoke test on `trgcc` via wizard → `_render_qweb_html`:

- Report title **Projects Analysis** present
- Period line renders (`2025-01-01` — `2025-12-31`)
- No `KeyError: 'data'`

Unit tests (`--test-tags=/legacy_mixed_system` on `trgcc`): daywork suite ran; `TestLegacyPhases` setUpClass failed due to **pre-existing** demo data (current payroll period already set) — unrelated to this fix.

### How to retest in UI

1. Legacy → Reports → Projects Analysis
2. Set date range and print PDF
3. Confirm period header and line table render without RPC error

**Parent:** [WP #{PARENT_WP_ID}]({PUBLIC_BASE}/work_packages/{PARENT_WP_ID})
"""

JOURNAL = f"""Resolved ({TODAY}).

Cause: QWeb template used data.get('date_from') but Odoo merges wizard data at top level (no 'data' variable) → KeyError: 'data'.

Fix: use top-level date_from / date_to in legacy_report_projects_templates.xml.

Deployed: -u legacy_mixed_system on trgcc and trgulf_Mrp. Smoke-tested report HTML render OK.
"""


class Client:
    def __init__(self, base: str, token: str, dry_run: bool = False):
        self.base = base.rstrip("/")
        self.dry_run = dry_run
        self.auth = HTTPBasicAuth("apikey", token)
        self.h = {"Accept": "application/json", "Content-Type": "application/json"}

    def get(self, ep: str):
        return requests.get(
            f"{self.base}/api/v3{ep}",
            auth=self.auth,
            headers=self.h,
            timeout=120,
            verify=False,
        )

    def patch(self, ep: str, data: dict):
        if self.dry_run:
            print(f"[dry-run] PATCH {ep} keys={list(data.keys())}")
            return None
        return requests.patch(
            f"{self.base}/api/v3{ep}",
            json=data,
            auth=self.auth,
            headers=self.h,
            timeout=120,
            verify=False,
        )

    def post(self, ep: str, data: dict):
        if self.dry_run:
            print(f"[dry-run] POST {ep}")
            return None
        return requests.post(
            f"{self.base}/api/v3{ep}",
            json=data,
            auth=self.auth,
            headers=self.h,
            timeout=120,
            verify=False,
        )


def get_closed_status_id(client: Client) -> int | None:
    r = client.get("/statuses")
    if r.status_code != 200:
        return None
    for st in r.json().get("_embedded", {}).get("elements", []):
        name = (st.get("name") or "").lower()
        if st.get("isClosed") or name in ("closed", "done", "complete", "resolved"):
            return st["id"]
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    for p in ENV_CANDIDATES:
        load_dotenv(p)
    token = get_token()
    if not token:
        print("ERROR: OPENPROJECT_API_TOKEN required")
        return 1

    base = os.environ.get("OPENPROJECT_URL", get_base_url())
    client = Client(base, token, dry_run=args.dry_run)
    gr = client.get(f"/work_packages/{WP_ID}")
    if gr.status_code != 200:
        base = os.environ.get(
            "OPENPROJECT_URL_FALLBACK", "https://37-61-219-169.nip.io:10081"
        )
        client = Client(base, token, dry_run=args.dry_run)
        gr = client.get(f"/work_packages/{WP_ID}")
    if gr.status_code != 200:
        print(f"ERROR: cannot load WP #{WP_ID}: {gr.status_code} {gr.text[:300]}")
        return 1
    print(f"Connected: {base}")

    wp = gr.json()
    subject = wp.get("subject")
    print(f"WP #{WP_ID}: {subject}")
    print(f"Status: {wp.get('_links', {}).get('status', {}).get('title')}")

    raw = (wp.get("description") or {}).get("raw") or ""
    if MARKER in raw:
        print(f"✓ #{WP_ID} description already has resolution marker")
        new_desc = raw
    else:
        new_desc = raw.rstrip() + RESOLUTION

    closed_id = get_closed_status_id(client)
    payload: dict = {
        "lockVersion": wp.get("lockVersion", 0),
        "description": {"format": "markdown", "raw": new_desc},
    }
    if closed_id:
        payload["status"] = {"href": f"/api/v3/statuses/{closed_id}"}

    pr = client.patch(f"/work_packages/{WP_ID}", payload)
    if args.dry_run or (pr and pr.status_code in (200, 201)):
        print(f"✓ PATCH #{WP_ID} (closed_id={closed_id})")
    else:
        print(
            f"✗ PATCH #{WP_ID}: {pr.status_code if pr else '?'} "
            f"{pr.text[:400] if pr is not None else ''}"
        )
        return 1

    # Activity comment (idempotent by marker text)
    ar = client.get(f"/work_packages/{WP_ID}/activities")
    if ar.status_code == 200:
        for act in ar.json().get("_embedded", {}).get("elements", []):
            note = (act.get("comment") or {}).get("raw") or ""
            if "KeyError: 'data'" in note and "Resolved" in note:
                print(f"✓ Journal already on #{WP_ID}")
                break
        else:
            jr = client.post(
                f"/work_packages/{WP_ID}/activities",
                {"comment": {"format": "plain", "raw": JOURNAL}},
            )
            if args.dry_run or (jr and jr.status_code in (200, 201)):
                print(f"✓ Journal on #{WP_ID}")
            else:
                print(
                    f"✗ Journal #{WP_ID}: {jr.status_code if jr else '?'} "
                    f"{jr.text[:300] if jr is not None else ''}"
                )
                return 1

    # Parent note
    parent = client.get(f"/work_packages/{PARENT_WP_ID}")
    if parent.status_code == 200:
        pwp = parent.json()
        praw = (pwp.get("description") or {}).get("raw") or ""
        parent_marker = "<!-- wp205-child-resolved-2026-07-04 -->"
        if parent_marker not in praw:
            append = f"""

---

{parent_marker}

## Child update ({TODAY})

- [WP #{WP_ID}]({PUBLIC_BASE}/work_packages/{WP_ID}) — **Fix Projects Analysis PDF KeyError: data** — **Closed** (template uses top-level `date_from`/`date_to`; upgraded on `trgcc` + `trgulf_Mrp`).
"""
            ppr = client.patch(
                f"/work_packages/{PARENT_WP_ID}",
                {
                    "lockVersion": pwp.get("lockVersion", 0),
                    "description": {
                        "format": "markdown",
                        "raw": praw.rstrip() + append,
                    },
                },
            )
            if args.dry_run or (ppr and ppr.status_code in (200, 201)):
                print(f"✓ PATCH parent #{PARENT_WP_ID}")
            else:
                print(
                    f"✗ PATCH parent #{PARENT_WP_ID}: "
                    f"{ppr.status_code if ppr else '?'}"
                )
        else:
            print(f"✓ Parent #{PARENT_WP_ID} already notes WP #{WP_ID}")

    url = f"{PUBLIC_BASE}/work_packages/{WP_ID}"
    out = (
        Path(__file__).resolve().parent.parent
        / "openproject_docs"
        / "WP205_PROJECTS_ANALYSIS_FIX.txt"
    )
    out.write_text(
        f"WP #{WP_ID} resolved: {TODAY}\n{url}\n",
        encoding="utf-8",
    )
    print(f"\nDone: {url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
