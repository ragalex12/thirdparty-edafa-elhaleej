#!/usr/bin/env python3
"""Close the asset-import issue and its duplicate with staging evidence."""

from pathlib import Path

from op_client import OPClient, get_base_url, get_token, load_env


WORK_PACKAGES = (336, 344)
CANONICAL_WP = 336
COMMENT = """✅ Asset Excel migration completed on staging (`trgulf_Mrp`).

- Source workbook: `AssetRevenue Recognition (account.asset.asset).xlsx`
- Validated and imported: **769 / 769** assets
- All assets remain **Draft**; no depreciation lines or journal entries were generated
- Acquisition dates parsed from the historical dates embedded in Asset Name
- Workbook date `2026-01-01` preserved as Legacy Cutover Date
- Workbook “Salvage Value” preserved as Legacy Accumulated Depreciation
- Nominal salvage value set to `1` according to the source flag
- Created/matched 5 asset models and 20 analytic accounts in staging company 1
- Totals: Gross `7,642,335.44`; accumulated depreciation `5,903,764.76`; legacy carrying value `1,737,801.68`
- Import mapping fields verified through Odoo `base_import.import.get_fields_tree`
- Module: `edafa_legacy_asset_import` v19.0.1.0.0
- Automated tests: 3/3 passed
- Idempotency rehearsal: 0 creates / 769 updates, rolled back

No Production database was changed.
"""


def main():
    load_env()
    client = OPClient(get_base_url(), get_token())

    statuses = client.get("/statuses")
    if not statuses or statuses.status_code != 200:
        raise RuntimeError("Could not load OpenProject statuses")
    elements = statuses.json().get("_embedded", {}).get("elements", [])
    closed = next((status for status in elements if status.get("name") == "Closed"), None)
    if not closed:
        raise RuntimeError("Closed status not found")

    results = []
    for wp_id in WORK_PACKAGES:
        response = client.get(f"/work_packages/{wp_id}")
        if not response or response.status_code != 200:
            raise RuntimeError(f"Could not load WP #{wp_id}")
        work_package = response.json()
        note = COMMENT
        if wp_id != CANONICAL_WP:
            note = f"Duplicate of WP #{CANONICAL_WP}.\n\n{COMMENT}"
        activity = client.post(
            f"/work_packages/{wp_id}/activities",
            {"comment": {"format": "markdown", "raw": note}},
        )
        if not activity or activity.status_code not in (200, 201):
            raise RuntimeError(f"Could not add evidence to WP #{wp_id}")
        update = client.patch(
            f"/work_packages/{wp_id}",
            {
                "lockVersion": work_package["lockVersion"],
                "_links": {"status": {"href": closed["_links"]["self"]["href"]}},
            },
        )
        if not update or update.status_code != 200:
            raise RuntimeError(f"Could not close WP #{wp_id}")
        results.append(f"#{wp_id}: {update.json()['_links']['status']['title']}")

    output = Path(__file__).resolve().parent.parent / "openproject_docs"
    output.mkdir(parents=True, exist_ok=True)
    result_path = output / "ASSET_IMPORT_WP_CLOSURE.txt"
    result_path.write_text(
        "\n".join(results)
        + "\n"
        + "\n".join(
            f"https://master.tailcf9988.ts.net:10081/work_packages/{wp_id}"
            for wp_id in WORK_PACKAGES
        )
        + "\n",
        encoding="utf-8",
    )
    print(result_path.read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
