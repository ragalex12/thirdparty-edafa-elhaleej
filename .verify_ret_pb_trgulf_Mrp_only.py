# Functional verification: retention_performance_bond on database trgulf_Mrp ONLY
# Usage: odoo shell -d trgulf_Mrp -c /etc/odoo/odoo.conf < this_file

from odoo import fields

EXPECTED_DB = "trgulf_Mrp"
if env.cr.dbname != EXPECTED_DB:
    raise SystemExit(
        f"FAIL: Wrong database (got {env.cr.dbname!r}, expected {EXPECTED_DB!r})"
    )

mod = env["ir.module.module"].search([("name", "=", "retention_performance_bond")], limit=1)
mod_state = mod.state if mod else "not_found"
print("=== MODULE STATUS ===")
print(f"database: {env.cr.dbname}")
print(f"retention_performance_bond state: {mod_state}")
if mod_state != "installed":
    raise SystemExit(f"FAIL: module not installed (state={mod_state!r})")

views = env["ir.ui.view"].search(
    [
        (
            "key",
            "=",
            "retention_performance_bond.report_invoice_document_retention_performance_bond",
        )
    ]
)
assert len(views) == 1, f"Expected 1 invoice report inherit view, got {len(views)}"
raw_arch = views.arch_db or ""
if isinstance(raw_arch, dict):
    raw_arch = raw_arch.get(env.lang) or raw_arch.get("en_US") or next(iter(raw_arch.values()))
arch = str(raw_arch or "").replace("\n", " ")
pb_pat = "performance_bond_percent or 0.0) * 100"
ret_pat = "retention_percent or 0.0) * 100"
pb_ok = pb_pat in arch
ret_ok = ret_pat in arch
print("=== RUNTIME ir.ui.view ARCH CHECK ===")
print(f"view id={views.id}, write_date={views.write_date}")
print(f"contains {pb_pat!r}: {pb_ok}")
print(f"contains {ret_pat!r}: {ret_ok}")
if not (pb_ok and ret_ok):
    raise SystemExit("FAIL: Report template missing expected * 100 expressions")

company = env.company
partner = env["res.partner"].search(
    [
        ("customer_rank", ">", 0),
        ("parent_id", "=", False),
        "|",
        ("company_id", "=", company.id),
        ("company_id", "=", False),
    ],
    limit=1,
)
if not partner:
    partner = env["res.partner"].create(
        {
            "name": "TEST_RETENTION_VER_SHELL_TRGULF_MRP",
            "customer_rank": 1,
            "company_id": company.id,
        }
    )

journal = env["account.journal"].search(
    [("type", "=", "sale"), ("company_id", "=", company.id)], limit=1
)
if not journal:
    raise SystemExit("FAIL: No sale journal")

income_account = env["account.account"].search(
    [
        ("company_ids", "in", [company.id]),
        ("account_type", "in", ("income", "income_other")),
    ],
    limit=1,
)
if not income_account:
    raise SystemExit("FAIL: No income account")

ref_tag = "TEST_RET_PB_TRGULF_MRP"
existing = env["account.move"].search(
    [("ref", "=", ref_tag), ("move_type", "=", "out_invoice")], limit=1
)
if existing:
    existing.unlink()

move = env["account.move"].create(
    {
        "move_type": "out_invoice",
        "partner_id": partner.id,
        "journal_id": journal.id,
        "company_id": company.id,
        "invoice_date": fields.Date.context_today(env["account.move"]),
        "ref": ref_tag,
        "invoice_line_ids": [
            (
                0,
                0,
                {
                    "name": "[VERIFY trgulf_Mrp] retention_performance_bond test line",
                    "quantity": 1,
                    "price_unit": 1000.0,
                    "account_id": income_account.id,
                },
            )
        ],
    }
)

# Widget semantics: 10% -> 0.10, 5% -> 0.05
move.write({"performance_bond_percent": 0.10, "retention_percent": 0.05})
move.invalidate_recordset()

print("=== INVOICE STORED/COMPUTED FIELDS ===")
print(f"id={move.id}, ref={move.ref}, state={move.state}")
print(f"amount_untaxed={move.amount_untaxed}")
print(f"performance_bond_percent={move.performance_bond_percent}")
print(f"performance_bond_amount={move.performance_bond_amount}")
print(f"retention_percent={move.retention_percent}")
print(f"retention_amount={move.retention_amount}")

amt_pb = round(move.performance_bond_amount or 0, 2)
amt_ret = round(move.retention_amount or 0, 2)
untaxed = round(move.amount_untaxed or 0, 2)

report = env.ref("account.account_invoices_without_payment", raise_if_not_found=False)
if not report:
    report = env.ref("account.account_invoices")

html, _rt = env["ir.actions.report"]._render_qweb_html(report, move.ids)
if isinstance(html, (list, tuple)):
    html = html[0]
if isinstance(html, bytes):
    html = html.decode("utf-8", errors="replace")

inv_summary = html.find("Invoice Summary")
block = html[inv_summary : inv_summary + 12000] if inv_summary >= 0 else html

print("=== RENDERED REPORT SNIPPET (Performance Bond + Retention block) ===")
pb_idx = block.find("Performance Bond and Retention")
print(block[pb_idx : pb_idx + 2200] if pb_idx >= 0 else block[:3500])

strict = (
    untaxed == 1000.0
    and amt_pb == 100.0
    and amt_ret == 50.0
    and "<span>10.00</span>%" in block
    and "<span>5.00</span>%" in block
    and "Performance Bond Amount" in block
    and "Retention Amount" in block
    and "oe_currency_value\">100.00</span>" in block.replace(" ", "")
    and "oe_currency_value\">50.00</span>" in block.replace(" ", "")
)

print(f"FINAL_RESULT_trgulf_Mrp: {'PASS' if strict else 'FAIL'}")
