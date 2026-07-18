#!/usr/bin/env python3
"""
Template: sync local markdown docs to OpenProject work packages.

Copy this file, set OPENPROJECT_* in /opt/.env, and customize TASKS below.

Usage:
  export OPENPROJECT_PROJECT_ID=19
  export OPENPROJECT_PARENT_WP_ID=135   # optional
  python3 sync_project_template.py --dry-run
  python3 sync_project_template.py
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from op_client import (  # noqa: E402
    OPClient,
    get_base_url,
    get_parent_wp_id,
    get_project_id,
    get_token,
    load_env,
)

DOCS_ROOT = Path(__file__).resolve().parent.parent / "openproject_docs"
MARKER = "<!-- project-sync-template -->"

# Customize per project: subject => relative doc path under openproject_docs/
TASKS: dict[str, str] = {
    "Example task — replace me": "README.md",
}

TYPE_TASK = int(os.environ.get("OPENPROJECT_DEFAULT_TYPE_ID", "1"))
STATUS_NEW = int(os.environ.get("OPENPROJECT_DEFAULT_STATUS_ID", "1"))
PRIORITY_NORMAL = int(os.environ.get("OPENPROJECT_DEFAULT_PRIORITY_ID", "8"))


def load_doc(rel: str) -> str:
    path = DOCS_ROOT / rel
    if not path.is_file():
        return f"(missing local doc: {rel})"
    body = path.read_text(encoding="utf-8").strip()
    return f"{body}\n\n{MARKER}"


def find_wp_by_subject(client: OPClient, project_id: int, subject: str) -> int | None:
    r = client.get(f"/projects/{project_id}/work_packages")
    if not r or r.status_code != 200:
        return None
    for el in r.json().get("_embedded", {}).get("elements", []):
        if el.get("subject") == subject:
            return el.get("id")
    return None


def upsert_wp(client: OPClient, project_id: int, subject: str, description: str) -> int | None:
    parent_id = get_parent_wp_id()
    wp_id = find_wp_by_subject(client, project_id, subject)
    payload = {
        "subject": subject,
        "description": {"format": "markdown", "raw": description},
        "type": {"href": f"/api/v3/types/{TYPE_TASK}"},
        "status": {"href": f"/api/v3/statuses/{STATUS_NEW}"},
        "priority": {"href": f"/api/v3/priorities/{PRIORITY_NORMAL}"},
    }
    if parent_id:
        payload["parent"] = {"href": f"/api/v3/work_packages/{parent_id}"}

    if wp_id:
        r = client.get(f"/work_packages/{wp_id}")
        if not r or r.status_code != 200:
            return None
        lock = r.json().get("lockVersion", 0)
        raw = r.json().get("description", {}).get("raw", "")
        if MARKER in raw:
            print(f"  skip (already synced): #{wp_id} {subject}")
            return wp_id
        payload["lockVersion"] = lock
        pr = client.patch(f"/work_packages/{wp_id}", payload)
        if client.dry_run:
            print(f"  [dry-run] PATCH #{wp_id} {subject}")
            return wp_id
        if pr and pr.status_code == 200:
            print(f"  ✓ updated #{wp_id} {subject}")
            return wp_id
        print(f"  [ERROR] PATCH #{wp_id}: {pr.status_code if pr else 'no response'}")
        return None

    pr = client.post(f"/projects/{project_id}/work_packages", payload)
    if client.dry_run:
        print(f"  [dry-run] CREATE {subject}")
        return None
    if pr and pr.status_code in (200, 201):
        new_id = pr.json().get("id")
        print(f"  ✓ created #{new_id} {subject}")
        return new_id
    print(f"  [ERROR] CREATE {subject}: {pr.status_code if pr else 'no response'}")
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    load_env()
    token = get_token()
    if not token:
        print("[ERROR] Set OPENPROJECT_API_TOKEN in /opt/.env")
        return 1

    project_id = get_project_id()
    base = get_base_url()
    client = OPClient(base, token, dry_run=args.dry_run)
    print(f"OpenProject: {base}")
    print(f"Project: {project_id} | Docs: {DOCS_ROOT}")
    if not client.connect(project_id):
        return 1

    for subject, doc_rel in TASKS.items():
        if subject.startswith("Example"):
            print(f"[SKIP] Template placeholder: {subject!r} — edit TASKS in this script")
            continue
        upsert_wp(client, project_id, subject, load_doc(doc_rel))

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
