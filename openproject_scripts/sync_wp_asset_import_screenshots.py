#!/usr/bin/env python3
"""Attach Playwright evidence to the canonical asset-import work package."""

import json
from pathlib import Path

import requests
from requests.auth import HTTPBasicAuth

from op_client import OPClient, get_base_url, get_token, load_env


WP_ID = 336
DUPLICATE_WP_ID = 344
SCREENSHOTS_DIR = (
    Path(__file__).resolve().parent.parent
    / "edafa_legacy_asset_import"
    / "e2e"
    / "screenshots"
    / "asset-import"
)
CAPTIONS = {
    "01-assets-list-769-records.png": "Assets list showing all 769 imported staging records.",
    "02-assets-list-migration-columns.png": "Assets list with legacy accumulated depreciation and carrying-value columns.",
    "03-first-asset-form.png": "First imported asset form in Draft state.",
    "04-first-asset-legacy-migration.png": "First asset Legacy Migration tab with source values.",
    "05-last-asset-legacy-migration.png": "Last imported asset, proving the complete 0001–0769 range.",
    "06-import-mapping-fields.png": "Odoo generic import screen exposing and matching the required migration fields.",
}

COMMENT = """📸 **Playwright UI evidence attached — 4/4 tests passed**

The screenshots verify:

1. The Assets list contains all **769** imported records.
2. Legacy Accumulated Depreciation and Legacy Carrying Value are visible.
3. The first imported asset (`NADI-ASSET-0001`) is Draft and preserves its source values.
4. The last imported asset (`NADI-ASSET-0769`) verifies the complete migration range.
5. Odoo’s generic import screen exposes and maps the required asset fields.

Screenshot files `01` through `06` are attached to this work package.
"""


def existing_filenames(client):
    response = client.get(f"/work_packages/{WP_ID}/attachments")
    if not response or response.status_code != 200:
        return set()
    elements = response.json().get("_embedded", {}).get("elements", [])
    return {
        element.get("fileName")
        for element in elements
        if element.get("fileName")
    }


def upload(base_url, token, path):
    metadata = json.dumps(
        {
            "fileName": path.name,
            "description": CAPTIONS[path.name],
        }
    )
    with path.open("rb") as file_handle:
        response = requests.post(
            f"{base_url}/api/v3/work_packages/{WP_ID}/attachments",
            auth=HTTPBasicAuth("apikey", token),
            headers={"Accept": "application/json"},
            files={
                "file": (path.name, file_handle, "image/png"),
                "metadata": (None, metadata),
            },
            timeout=300,
            verify=False,
        )
    if response.status_code not in (200, 201):
        raise RuntimeError(
            f"Could not attach {path.name}: HTTP {response.status_code} "
            f"{response.text[:300]}"
        )


def add_comment(client, wp_id, comment):
    response = client.post(
        f"/work_packages/{wp_id}/activities",
        {"comment": {"format": "markdown", "raw": comment}},
    )
    if not response or response.status_code not in (200, 201):
        raise RuntimeError(f"Could not comment on WP #{wp_id}")


def main():
    load_env()
    base_url = get_base_url()
    token = get_token()
    client = OPClient(base_url, token)
    if not SCREENSHOTS_DIR.is_dir():
        raise RuntimeError(f"Screenshot directory not found: {SCREENSHOTS_DIR}")

    screenshot_paths = [
        SCREENSHOTS_DIR / filename for filename in sorted(CAPTIONS)
    ]
    missing = [path for path in screenshot_paths if not path.is_file()]
    if missing:
        raise RuntimeError(f"Missing screenshots: {missing}")

    existing = existing_filenames(client)
    uploaded = []
    skipped = []
    for path in screenshot_paths:
        if path.name in existing:
            skipped.append(path.name)
            continue
        upload(base_url, token, path)
        uploaded.append(path.name)
        print(f"✓ attached {path.name}")

    add_comment(client, WP_ID, COMMENT)
    add_comment(
        client,
        DUPLICATE_WP_ID,
        f"Playwright screenshots and 4/4 test evidence were attached to canonical WP #{WP_ID}.",
    )

    output = Path(__file__).resolve().parent.parent / "openproject_docs"
    output.mkdir(parents=True, exist_ok=True)
    result_path = output / "ASSET_IMPORT_SCREENSHOTS_SYNC.txt"
    result_path.write_text(
        f"WP: https://master.tailcf9988.ts.net:10081/work_packages/{WP_ID}\n"
        f"uploaded={len(uploaded)}\n"
        f"skipped={len(skipped)}\n"
        + "\n".join(uploaded or skipped)
        + "\n",
        encoding="utf-8",
    )
    print(result_path.read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
