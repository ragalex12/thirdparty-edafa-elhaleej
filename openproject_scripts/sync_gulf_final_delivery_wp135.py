#!/usr/bin/env python3
"""
Final delivery WP #135 — developer docs, user guides, all screenshots.
Uploads bundle to OpenProject attachments + Nextcloud (on master).

Usage:
  SYNC_SCRIPT=sync_gulf_final_delivery_wp135.py bash ssh_to_master_and_sync.sh
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

import requests
from requests.auth import HTTPBasicAuth

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sync_requirements_review_wp135 import (  # noqa: E402
    ENV_CANDIDATES,
    PARENT_WP_ID,
    PROJECT_ID,
    TYPE_TASK,
    STATUS_NEW,
    PRIORITY_NORMAL,
    get_base_url,
    get_token,
    load_dotenv,
)

PUBLIC_BASE = "https://master.tailcf9988.ts.net:10081"
MARKER = "<!-- gulf-final-delivery-package-2026-07-03 -->"
TODAY = date.today().isoformat()
LOCALADDONS = Path(__file__).resolve().parent.parent
DOCS = LOCALADDONS / "openproject_docs" / "gulf_delivery"
BUNDLE = DOCS / "bundle"
NC_REMOTE = "Gulf-Industrial-Projects/WP135-Final-Delivery"

WP_SUBJECT = "Final Delivery — docs + user guide + screenshots / التسليم النهائي WP #135"

SCREENSHOT_SOURCES = [
    LOCALADDONS / "gpc_gulf_project_ext" / "e2e" / "screenshots" / "gulf-phase1",
    LOCALADDONS / "gpc_gulf_hr_payroll_ext" / "e2e" / "screenshots" / "gulf-phase2",
]

DOC_FILES = [
    DOCS / "README.md",
    DOCS / "DEVELOPER_GUIDE.md",
    DOCS / "USER_GUIDE_EN.md",
    DOCS / "USER_GUIDE_AR.md",
    LOCALADDONS / "openproject_docs" / "WP135_FINAL_CLOSURE.md",
    LOCALADDONS / "openproject_docs" / "PHASE1_IMPLEMENTATION_DELIVERY.md",
    LOCALADDONS / "openproject_docs" / "PHASE2_IMPLEMENTATION_DELIVERY.md",
    LOCALADDONS / "gpc_gulf_project_ext" / "e2e" / "screenshots" / "gulf-phase1" / "README.md",
    LOCALADDONS / "gpc_gulf_project_ext" / "e2e" / "screenshots" / "gulf-phase1" / "INDEX_AR.md",
    LOCALADDONS / "gpc_gulf_hr_payroll_ext" / "e2e" / "screenshots" / "gulf-phase2" / "README.md",
]


def build_description(nc_path: str) -> str:
    return f"""{MARKER}

# Final Delivery — WP #135 / التسليم النهائي

**Parent:** [WP #135]({PUBLIC_BASE}/work_packages/135)  
**Date:** {TODAY}  
**Status:** ✅ Complete

---

## Package contents (attachments)

| File | Type |
|------|------|
| DEVELOPER_GUIDE.md | Developer documentation |
| USER_GUIDE_EN.md | User guide (English) |
| USER_GUIDE_AR.md | User guide (Arabic) |
| WP135_FINAL_CLOSURE.md | Closure summary |
| Phase 1 + Phase 2 delivery notes | Implementation reports |
| `phase1-*.png` | Project + Quotation screenshots |
| `phase2-*.png` | HR Payroll screenshots |

---

## Modules

- `gpc_gulf_project_ext` — WP #136–#138
- `gpc_gulf_hr_payroll_ext` — WP #139

**DB:** `trgulf_Mrp` · **Legacy:** no change (#145 closed)

---

## UAT

| Test | Result |
|------|--------|
| Quotation/Invoice | **64,562.40** |
| Payroll NET | **12,900.00** |

---

## Nextcloud

Files uploaded to: **`{nc_path}`** (master Nextcloud)

---

## Related WPs

- [Phase 1 #150]({PUBLIC_BASE}/work_packages/150)
- [Phase 2 #156]({PUBLIC_BASE}/work_packages/156)
- [Decisions #140]({PUBLIC_BASE}/work_packages/140)
"""


def build_bundle() -> Path:
    if BUNDLE.exists():
        shutil.rmtree(BUNDLE)
    (BUNDLE / "screenshots" / "phase1").mkdir(parents=True)
    (BUNDLE / "screenshots" / "phase2").mkdir(parents=True)
    (BUNDLE / "docs").mkdir(parents=True)

    for doc in DOC_FILES:
        if doc.is_file():
            shutil.copy2(doc, BUNDLE / "docs" / doc.name)

    for src in SCREENSHOT_SOURCES:
        if not src.is_dir():
            continue
        dest = BUNDLE / "screenshots" / ("phase1" if "phase1" in src.name else "phase2")
        for png in sorted(src.glob("*.png")):
            shutil.copy2(png, dest / png.name)

    manifest = {
        "date": TODAY,
        "wp_parent": 135,
        "docs": [f.name for f in (BUNDLE / "docs").iterdir()],
        "screenshots_phase1": [f.name for f in (BUNDLE / "screenshots" / "phase1").glob("*.png")],
        "screenshots_phase2": [f.name for f in (BUNDLE / "screenshots" / "phase2").glob("*.png")],
    }
    (BUNDLE / "MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Bundle: {BUNDLE} ({len(list(BUNDLE.rglob('*')))} files)")
    return BUNDLE


class Client:
    def __init__(self, base: str, token: str, dry_run: bool = False):
        self.base = base.rstrip("/")
        self.dry_run = dry_run
        self.auth = HTTPBasicAuth("apikey", token)
        self.h = {"Accept": "application/json"}

    def get(self, ep: str):
        return requests.get(f"{self.base}/api/v3{ep}", auth=self.auth, headers=self.h, timeout=120, verify=False)

    def post(self, ep: str, data: dict | None = None, files=None):
        if self.dry_run:
            return None
        headers = {"Accept": "application/json"}
        if files:
            return requests.post(f"{self.base}/api/v3{ep}", auth=self.auth, headers=headers, files=files, timeout=300, verify=False)
        return requests.post(
            f"{self.base}/api/v3{ep}", json=data, auth=self.auth,
            headers={**headers, "Content-Type": "application/json"}, timeout=120, verify=False,
        )

    def patch(self, ep: str, data: dict):
        if self.dry_run:
            return None
        return requests.patch(
            f"{self.base}/api/v3{ep}", json=data, auth=self.auth,
            headers={**self.h, "Content-Type": "application/json"}, timeout=120, verify=False,
        )


def find_wp(client: Client) -> int | None:
    r = client.get(f"/work_packages/{PARENT_WP_ID}")
    if r.status_code != 200:
        return None
    for link in r.json().get("_links", {}).get("children", []):
        href = link.get("href", "")
        if "/work_packages/" not in href:
            continue
        cid = int(href.rsplit("/", 1)[-1])
        cr = client.get(f"/work_packages/{cid}")
        if cr.status_code != 200:
            continue
        wp = cr.json()
        raw = wp.get("description", {}).get("raw", "") or ""
        if MARKER in raw or wp.get("subject", "").startswith("Final Delivery"):
            return cid
    return None


def attach_file(client: Client, wp_id: int, path: Path, desc: str) -> bool:
    if not path.is_file():
        return False
    metadata = json.dumps({"fileName": path.name, "description": desc})
    with path.open("rb") as fh:
        pr = client.post(
            f"/work_packages/{wp_id}/attachments",
            files={"file": (path.name, fh, "application/octet-stream"), "metadata": (None, metadata)},
        )
    if client.dry_run:
        print(f"  [dry-run] attach {path.name}")
        return True
    if pr and pr.status_code in (200, 201):
        print(f"  ✓ OP attach {path.name}")
        return True
    print(f"  ✗ OP attach {path.name}: {pr.status_code if pr else '?'}")
    return False


def _nc_password() -> str | None:
    pw = os.environ.get("NEXTCLOUD_PASSWORD")
    if pw:
        return pw
    try:
        out = subprocess.check_output(
            ["docker", "inspect", "nextcloud", "--format", "{{range .Config.Env}}{{println .}}{{end}}"],
            text=True,
            timeout=15,
        )
        for line in out.splitlines():
            if line.startswith("NEXTCLOUD_ADMIN_PASSWORD="):
                return line.split("=", 1)[1]
    except Exception:
        pass
    return None


def _nc_mkcol(dav_base: str, auth: tuple[str, str], rel_path: str) -> None:
    url = f"{dav_base.rstrip('/')}/{rel_path.strip('/')}"
    try:
        requests.request("MKCOL", url, auth=auth, timeout=30)
    except Exception:
        pass


def upload_nextcloud(bundle: Path) -> str:
    nc_base = os.environ.get("NEXTCLOUD_URL", "http://127.0.0.1:8082")
    user = os.environ.get("NEXTCLOUD_USER", "admin")
    password = _nc_password()
    if not password:
        print("  ⚠ Nextcloud: no password — skip upload")
        return NC_REMOTE

    dav = f"{nc_base.rstrip('/')}/remote.php/dav/files/{user}"
    auth = (user, password)
    _nc_mkcol(dav, auth, NC_REMOTE)

    uploaded = 0
    for fpath in sorted(bundle.rglob("*")):
        if not fpath.is_file():
            continue
        rel = fpath.relative_to(bundle).as_posix()
        if rel.count("/"):
            dir_parts = rel.split("/")[:-1]
            for i in range(len(dir_parts)):
                _nc_mkcol(dav, auth, f"{NC_REMOTE}/{'/'.join(dir_parts[: i + 1])}")
        remote = f"{dav}/{NC_REMOTE}/{rel}"
        try:
            with fpath.open("rb") as fh:
                r = requests.put(remote, data=fh, auth=auth, timeout=120)
            if r.status_code in (200, 201, 204):
                uploaded += 1
                print(f"  ✓ NC {rel}")
            else:
                print(f"  ✗ NC {rel}: {r.status_code}")
        except Exception as e:
            print(f"  ✗ NC {rel}: {e}")

    print(f"Nextcloud: {uploaded} files → {NC_REMOTE}")
    return NC_REMOTE


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-nextcloud", action="store_true")
    parser.add_argument("--skip-attachments", action="store_true")
    args = parser.parse_args()

    for p in ENV_CANDIDATES:
        load_dotenv(p)
    token = get_token()
    if not token:
        print("ERROR: OPENPROJECT_API_TOKEN required")
        return 1

    bundle = build_bundle()
    nc_path = NC_REMOTE if args.skip_nextcloud else upload_nextcloud(bundle)

    base = os.environ.get("OPENPROJECT_URL", get_base_url())
    client = Client(base, token, dry_run=args.dry_run)
    tr = client.get(f"/projects/{PROJECT_ID}")
    if tr.status_code != 200:
        base = os.environ.get("OPENPROJECT_URL_FALLBACK", "https://37-61-219-169.nip.io:10081")
        client = Client(base, token, dry_run=args.dry_run)
        tr = client.get(f"/projects/{PROJECT_ID}")
    if tr.status_code != 200:
        print("ERROR: OpenProject unreachable")
        return 1
    print(f"Connected: {base}")

    desc = build_description(nc_path)
    wp_id = find_wp(client)

    if wp_id:
        gr = client.get(f"/work_packages/{wp_id}")
        wp = gr.json()
        pr = client.patch(
            f"/work_packages/{wp_id}",
            {"lockVersion": wp.get("lockVersion", 0), "description": {"format": "markdown", "raw": desc}},
        )
        if not args.dry_run and pr and pr.status_code not in (200, 201):
            return 1
        print(f"✓ Updated WP #{wp_id}")
    else:
        payload = {
            "subject": WP_SUBJECT,
            "description": {"format": "markdown", "raw": desc},
            "type": {"href": f"/api/v3/types/{TYPE_TASK}"},
            "status": {"href": f"/api/v3/statuses/{STATUS_NEW}"},
            "priority": {"href": f"/api/v3/priorities/{PRIORITY_NORMAL}"},
            "parent": {"href": f"/api/v3/work_packages/{PARENT_WP_ID}"},
        }
        pr = client.post(f"/projects/{PROJECT_ID}/work_packages", payload)
        if args.dry_run:
            wp_id = 0
        elif pr and pr.status_code in (200, 201):
            wp_id = pr.json()["id"]
            print(f"✓ Created WP #{wp_id}")
        else:
            print(f"✗ CREATE failed: {pr.text[:300] if pr else ''}")
            return 1

    if not args.skip_attachments and wp_id:
        print("OpenProject attachments...")
        for fpath in sorted((bundle / "docs").glob("*")):
            attach_file(client, wp_id, fpath, f"Doc: {fpath.name}")
        for phase in ("phase1", "phase2"):
            for png in sorted((bundle / "screenshots" / phase).glob("*.png")):
                attach_file(client, wp_id, png, f"Screenshot {phase}: {png.name}")
        attach_file(client, wp_id, bundle / "MANIFEST.json", "Bundle manifest")

    url = f"{PUBLIC_BASE}/work_packages/{wp_id}"
    out = LOCALADDONS / "openproject_docs" / "GULF_FINAL_DELIVERY_WP.txt"
    out.write_text(
        f"Final Delivery WP: {url}\nNextcloud: {NC_REMOTE}\nDate: {TODAY}\n",
        encoding="utf-8",
    )
    print(f"\n========== FINAL DELIVERY ==========")
    print(url)
    print(f"Nextcloud: {NC_REMOTE}")
    print("====================================")
    return 0


if __name__ == "__main__":
    sys.exit(main())
