#!/usr/bin/env python3
"""Create time-estimate work package under WP #135 (idempotent)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import requests
from requests.auth import HTTPBasicAuth

PROJECT_ID = 19
PARENT_WP_ID = 135
TYPE_TASK = 1
STATUS_NEW = 1
PRIORITY_NORMAL = 8
PUBLIC_BASE = "https://master.tailcf9988.ts.net:10081"

SUBJECT = "تقدير الوقت — مشاريع الخليج (Time estimate)"
MARKER = "<!-- time-estimate-wp135 -->"

DESC_FILE = Path(__file__).resolve().parent / "docs" / "REQUIREMENTS_REVIEW_TIME_ESTIMATE_AR.txt"
# fallback paths
DESC_FALLBACKS = [
    Path(__file__).resolve().parent.parent / "openproject_docs" / "REQUIREMENTS_REVIEW_TIME_ESTIMATE_AR.txt",
]


def _read_desc_file() -> str:
    for p in [DESC_FILE, *DESC_FALLBACKS]:
        if p.is_file():
            return p.read_text(encoding="utf-8").strip()
    return ""


def body() -> str:
    raw = _read_desc_file()
    return f"{MARKER}\n\n{raw}" if raw else MARKER


def patch_wp(base: str, auth, h, wid: int, new_desc: str) -> bool:
    gr = requests.get(f"{base}/api/v3/work_packages/{wid}", auth=auth, headers=h, timeout=60, verify=False)
    gr.raise_for_status()
    wp = gr.json()
    pr = requests.patch(
        f"{base}/api/v3/work_packages/{wid}",
        json={"lockVersion": wp.get("lockVersion", 0), "description": {"format": "markdown", "raw": new_desc}},
        auth=auth, headers=h, timeout=60, verify=False,
    )
    pr.raise_for_status()
    return True


def load_env():
    for p in (Path("/opt/.env"),):
        if not p.is_file():
            continue
        try:
            for line in p.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    os.environ.setdefault(k.strip(), v.strip().strip("'\""))
        except OSError:
            pass


def main() -> int:
    load_env()
    token = os.environ.get("OPENPROJECT_API_TOKEN") or os.environ.get("OPENPROJECT_API_KEY")
    base = os.environ.get("OPENPROJECT_URL", PUBLIC_BASE).rstrip("/")
    if not token:
        print("ERROR: OPENPROJECT_API_TOKEN required")
        return 1

    auth = HTTPBasicAuth("apikey", token)
    h = {"Accept": "application/json", "Content-Type": "application/json"}

    # find existing
    r = requests.get(
        f"{base}/api/v3/projects/{PROJECT_ID}/work_packages?pageSize=50",
        auth=auth, headers=h, timeout=60, verify=False,
    )
    r.raise_for_status()
    for wp in r.json().get("_embedded", {}).get("elements", []):
        if wp.get("subject") == SUBJECT or "تقدير الوقت" in wp.get("subject", ""):
            wid = wp["id"]
            desc = body()
            raw = wp.get("description", {}).get("raw", "") or ""
            if len(raw) < 200 and desc and desc != MARKER:
                patch_wp(base, auth, h, wid, desc)
                print(f"✓ Updated description WP #{wid}")
            else:
                print(f"✓ Already exists: #{wid} — {SUBJECT}")
            print(f"Link: {PUBLIC_BASE}/work_packages/{wid}")
            return 0

    desc = body()
    if not _read_desc_file():
        print("WARN: description file missing — WP may be empty")
    payload = {
        "subject": SUBJECT,
        "description": {"format": "markdown", "raw": desc},
        "type": {"href": f"/api/v3/types/{TYPE_TASK}"},
        "status": {"href": f"/api/v3/statuses/{STATUS_NEW}"},
        "priority": {"href": f"/api/v3/priorities/{PRIORITY_NORMAL}"},
        "parent": {"href": f"/api/v3/work_packages/{PARENT_WP_ID}"},
    }
    pr = requests.post(
        f"{base}/api/v3/projects/{PROJECT_ID}/work_packages",
        json=payload, auth=auth, headers=h, timeout=60, verify=False,
    )
    pr.raise_for_status()
    wid = pr.json()["id"]
    print(f"✓ Created WP #{wid}: {SUBJECT}")
    print(f"Link: {PUBLIC_BASE}/work_packages/{wid}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
