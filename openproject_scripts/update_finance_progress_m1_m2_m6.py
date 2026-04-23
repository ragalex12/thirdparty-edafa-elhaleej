#!/usr/bin/env python3
"""
Update OpenProject work packages for Odoo Finance Phase 1 — M1, M2, M6 progress (April 2026).

Usage:
  python3 update_finance_progress_m1_m2_m6.py          # dry-run: list changes only
  python3 update_finance_progress_m1_m2_m6.py --apply  # apply status + comments

Requires OpenProject reachable (localhost:8090 with Host header, or HTTPS tunnel).
API token must have work package edit rights.
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

import requests
from requests.auth import HTTPBasicAuth

API_TOKEN = "f1336582f568d3dc0c27a938d711c10c5f3cb81366aed6ad27b663dc2a7034b3"
AUTH = HTTPBasicAuth("apikey", API_TOKEN)

# Both finance trackers: "cust-p1" is the original plan; "p1-delivery" is Active Delivery (often what users open in UI).
# M2 parent may exist only on cust-p1 — delivery project sometimes omits that milestone row.
PROJECT_IDENTIFIERS = ["odoo-fin-cust-p1", "odoo-fin-p1-delivery"]

# Try in order until one responds OK to GET /api/v3/projects/{id}
URL_CONFIGS = [
    {
        "name": "localhost+Host",
        "base": "http://127.0.0.1:8090",
        "headers": {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Host": "generated-complexity-ireland-fully.trycloudflare.com",
        },
    },
    {
        "name": "https_tunnel",
        "base": "https://generated-complexity-ireland-fully.trycloudflare.com",
        "headers": {
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    },
]

PARENT_SUBJECTS = {
    "M1": "M1 - Journal Line Reference Extension",
    "M2": "M2 - OCA General Ledger Range Fix",
    "M6": "M6 - Invoice Approval and ZATCA Gate",
}

TARGET_STATUS = "in progress"  # matched case-insensitively against /statuses

COMMENTS = {
    "M1": """**Progress (automated update — April 2026)**

**Done:** Analysis, design, scaffold (`gpc_account_move_line_reference_ext`). Model fields (`line_reference`, `line_reference_number`, `line_tax_number`), partner VAT onchange, form/tree views for manual entries (`move_type=entry`), automated tests. Module installed on staging; implementation ready for functional/UAT per `docs/TESTING_GUIDE_FINISHED.md`.

**Note:** Journal Items search/filter XML for these fields is present in module but **commented out** (Odoo 19 search validation) — not available in UI until re-enabled.

**Remaining:** Formal UAT sign-off; optional hardening (security/post-lock) if still in scope vs original spec.""",
    "M2": """**Progress (automated update — April 2026)**

**Done:** Investigation, root cause analysis, evidence (SQL/ORM). **account_financial_report** wizards (General Ledger, Open Items, Aged Partner Balance) updated for Odoo 19: account From/To uses **string** account `code` bounds (no `int()` TypeError). Focused tests referenced in workspace handoff.

**Not claimed as full production closure:** Broader regression across all reports/companies, or upstream OCA merge — track separately if needed.

**Remaining:** UAT on staging (`trgulf_Mrp`); optional Trial Balance parity check; data-quality follow-ups if any.""",
    "M6": """**Progress (automated update — April 2026)**

**Done:** Approval path analysis; OCA approach. **`base_tier_validation`** (19.0) and **`account_move_tier_validation`** ported, installed, load-verified. Customer invoice smoke test on **`trgulf_Mrp`**: request validation → approve → post. Standard Saudi ZATCA path analyzed: **`l10n_sa_edi`** (not installed yet).

**Not done:** End-to-end ZATCA (`l10n_sa_edi` install, journal onboarding, submission). Custom gate module not started.

**Next:** Environment/test setup decision; controlled **`l10n_sa_edi`** pilot when ready. Milestone stays **open** until ZATCA path and UAT agreed.""",
}


def pick_base_url() -> tuple[str, dict[str, str]] | tuple[None, None]:
    for cfg in URL_CONFIGS:
        base = cfg["base"]
        h = cfg["headers"]
        try:
            r = requests.get(
                f"{base}/api/v3/projects/{PROJECT_IDENTIFIERS[0]}",
                auth=AUTH,
                headers=h,
                timeout=20,
            )
            if r.ok:
                return base, h
        except requests.RequestException:
            continue
    return None, None


def api_get(base: str, headers: dict, path: str) -> dict[str, Any]:
    r = requests.get(f"{base}/api/v3{path}", auth=AUTH, headers=headers, timeout=60)
    r.raise_for_status()
    return r.json()


def api_patch(base: str, headers: dict, path: str, body: dict) -> dict[str, Any]:
    r = requests.patch(
        f"{base}/api/v3{path}",
        auth=AUTH,
        headers=headers,
        json=body,
        timeout=60,
    )
    if not r.ok:
        raise RuntimeError(f"PATCH {path} -> {r.status_code}: {r.text[:800]}")
    return r.json()


def fetch_all_work_packages(base: str, headers: dict, project_identifier: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    offset = 0
    page = 100
    while True:
        data = api_get(
            base,
            headers,
            f"/projects/{project_identifier}/work_packages?offset={offset}&pageSize={page}",
        )
        els = data.get("_embedded", {}).get("elements", [])
        out.extend(els)
        if len(els) < page:
            break
        offset += page
    return out


def resolve_status_href(base: str, headers: dict, name_substring: str) -> str:
    data = api_get(base, headers, "/statuses")
    want = name_substring.strip().lower()
    for s in data.get("_embedded", {}).get("elements", []):
        if s.get("name", "").lower() == want:
            return s["_links"]["self"]["href"]
    for s in data.get("_embedded", {}).get("elements", []):
        if want in s.get("name", "").lower():
            return s["_links"]["self"]["href"]
    raise RuntimeError(f"No status matching {name_substring!r}")


def add_comment(base: str, headers: dict, wp_id: int, raw: str, apply: bool) -> None:
    """POST activity with comment (OpenProject API v3)."""
    if not apply:
        print(f"    [dry-run] would add comment ({len(raw)} chars) to WP {wp_id}")
        return
    url = f"{base}/api/v3/work_packages/{wp_id}/activities"
    body = {"comment": {"raw": raw}}
    r = requests.post(url, auth=AUTH, headers=headers, json=body, timeout=60)
    if not r.ok:
        raise RuntimeError(f"Comment POST failed {r.status_code}: {r.text[:600]}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Apply changes (default is dry-run)")
    args = ap.parse_args()
    apply = args.apply

    base, headers = pick_base_url()
    if not base:
        print(
            "ERROR: OpenProject API unreachable (tried localhost:8090 + HTTPS tunnel). "
            "Start OpenProject/cloudflared and re-run:\n"
            "  python3 /opt/localaddons/openproject_scripts/update_finance_progress_m1_m2_m6.py --apply",
            file=sys.stderr,
        )
        return 2

    print(f"Using endpoint: {base} (config OK)")
    status_href = resolve_status_href(base, headers, TARGET_STATUS)
    print(f"Target status: {TARGET_STATUS!r} -> {status_href}")

    updated: list[str] = []

    for project_identifier in PROJECT_IDENTIFIERS:
        print(f"\n========== Project: {project_identifier} ==========")
        try:
            api_get(base, headers, f"/projects/{project_identifier}")
        except Exception as e:
            print(f"SKIP: cannot read project: {e}")
            continue

        wps = fetch_all_work_packages(base, headers, project_identifier)
        by_subject = {wp.get("subject", ""): wp for wp in wps}

        for key, subject in PARENT_SUBJECTS.items():
            wp = by_subject.get(subject)
            if not wp:
                print(f"WARNING: [{project_identifier}] work package not found: {subject!r}")
                continue
            wid = wp["id"]
            lock = wp.get("lockVersion")
            cur = wp.get("_links", {}).get("status", {}).get("title", "?")
            print(f"\n{key} WP#{wid} ({subject[:50]}...): current status = {cur}")

            if apply:
                body = {
                    "lockVersion": lock,
                    "_links": {"status": {"href": status_href}},
                }
                api_patch(base, headers, f"/work_packages/{wid}", body)
                print(f"  -> status set to in progress")
            else:
                print(f"  [dry-run] would PATCH status -> in progress (lockVersion={lock})")

            try:
                add_comment(base, headers, wid, COMMENTS[key], apply)
            except Exception as e:
                print(f"  COMMENT FAILED: {e}")
            updated.append(f"{project_identifier} {key} (WP {wid})")

        print(
            f"\n--- Child WPs under M1/M2/M6 in {project_identifier} (informational; not auto-closed) ---"
        )
        parents = {by_subject[s]["id"] for s in PARENT_SUBJECTS.values() if s in by_subject}
        id_to_wp = {w["id"]: w for w in wps}
        for wp in sorted(wps, key=lambda x: x.get("id", 0)):
            par = wp.get("_links", {}).get("parent", {})
            phref = par.get("href") if isinstance(par, dict) else None
            if not phref:
                continue
            try:
                pid = int(phref.rstrip("/").split("/")[-1])
            except (ValueError, IndexError):
                continue
            chain = [wp["id"]]
            p = pid
            for _ in range(15):
                if p not in id_to_wp:
                    break
                chain.append(p)
                p2 = id_to_wp[p].get("_links", {}).get("parent", {})
                href2 = p2.get("href") if isinstance(p2, dict) else None
                if not href2:
                    break
                p = int(href2.rstrip("/").split("/")[-1])
            if any(x in parents for x in chain):
                st = wp.get("_links", {}).get("status", {}).get("title", "?")
                sub = (wp.get("subject") or "")[:75]
                print(f"  WP{wp['id']:5d} [{st:12s}] {sub}")

    print("\nDone.")
    if "odoo-fin-p1-delivery" in PROJECT_IDENTIFIERS:
        print(
            "(Note: Active Delivery project may not include an M2 parent WP; M2 progress is on odoo-fin-cust-p1 only.)"
        )
    print("Updated parents:" if apply else "Dry-run — no API writes. Updated would be:")
    for u in updated:
        print(f"  - {u}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
