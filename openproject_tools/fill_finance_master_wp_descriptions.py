#!/usr/bin/env python3
"""Fill descriptions (Milestone/Epic/Step format) + Activity tab (journal notes v1) for project 9."""
import psycopg2

conn = psycopg2.connect(dbname="openproject", user="postgres")
cur = conn.cursor()

cur.execute(
    """
    SELECT w.id, w.subject, w.parent_id,
           (SELECT p.subject FROM work_packages p WHERE p.id = w.parent_id) AS parent_subject
    FROM work_packages w
    WHERE w.project_id = 9
    ORDER BY w.id
    """
)
rows = cur.fetchall()

cur.execute(
    """
    SELECT j.journable_id, j.data_id
    FROM journals j
    WHERE j.journable_type = 'WorkPackage'
      AND j.version = 1
      AND j.journable_id IN (SELECT id FROM work_packages WHERE project_id = 9)
    """
)
wp_to_wpj = {r[0]: r[1] for r in cur.fetchall()}


def blk(lead: str, module: str, tail_label: str, tail: str) -> str:
    """Three-part description: lead line, Module, third block (Deliverables / Scope / …)."""
    return f"{lead}\n\nModule: {module}\n\n{tail_label}: {tail}".strip()


# Epic wp_id -> (module line, stream achievement one-liner for Epic: line)
EPIC_IDS = {
    515: (
        "gpc_account_move_line_reference_ext",
        "Task 1 — journal line references are reliable for audit, search, and handover.",
    ),
    527: (
        "OCA General Ledger / account_financial_report (deployed revision)",
        "Task 2 — OCA GL reporting respects chart account ranges without silent omissions.",
    ),
    539: (
        "gpc_analytic_project_statement",
        "Task 3 — analytic project statement, wizard, and exports match allocations.",
    ),
    551: (
        "gpc_hr_timesheet_labor_accrual",
        "Task 4 — timesheet labor posts through draft JE with clear reversal rules.",
    ),
    563: (
        "gpc_stock_project_issue",
        "Task 5 — stock moves to projects are valued at cost with correct JE traceability.",
    ),
    575: (
        "base_tier_validation, account_move_tier_validation, l10n_sa_edi",
        "Task 6 — invoice approvals and ZATCA e-invoicing path are ready for go-live.",
    ),
}

TASK_KEY_BY_EPIC = {eid: f"T{i}" for i, eid in enumerate([515, 527, 539, 551, 563, 575], start=1)}

# Step label (after "Tn – ") -> (verb phrase for Step line, deliverables text)
STEP_LINES = {
    "Business requirement": (
        "lock the business need in testable form",
        "problem statement, actors, acceptance criteria, explicit out-of-scope items, dependencies on COA/journals/analytics",
    ),
    "Analysis / investigation": (
        "turn requirements into a concrete approach before build",
        "process map, Odoo vs gap, risks, OCA revision notes, performance/security considerations",
    ),
    "Sign-off / requirement freeze": (
        "baseline scope under change control",
        "signed scope, Odoo/OCA version reference, freeze date, change-handling rules",
    ),
    "Implementation design": (
        "produce a buildable design for developers",
        "data model, module boundaries, key methods, views/security outline, migration notes",
    ),
    "Module scaffold": (
        "deliver an installable empty module",
        "__manifest__, security, empty models/views, minimal dependencies, clean `-i` on staging",
    ),
    "Implementation": (
        "deliver agreed behaviour in code",
        "scoped commits, review-ready PRs, known limitations listed",
    ),
    "Install / load verification": (
        "prove the module loads in a real database",
        "clean install or upgrade on staging, error-free logs, documented DB and Odoo build",
    ),
    "Automated tests": (
        "protect regressions with automated coverage",
        "Odoo tests where viable, CI or staged run green, known environment caveats noted",
    ),
    "Functional UAT": (
        "validate with business on staging using realistic data",
        "scenario list executed, evidence attached, sign-off name/date",
    ),
    "Testing guide / UAT notes (this stream)": (
        "give testers a repeatable script without asking devs",
        "prerequisites, steps, expected results, negative cases, pointers to evidence WPs",
    ),
    "Remaining issues / follow-ups": (
        "close the loop on defects and deferred items",
        "open defects, tech debt, external decisions, each with owner and next action",
    ),
}


def step_description(tkey: str, module_en: str, step_label: str) -> str:
    meta = STEP_LINES.get(step_label)
    if not meta:
        return blk(
            f"Work package: {tkey} — {step_label}",
            module_en,
            "Notes",
            "Align execution with the epic; add links and meeting notes here.",
        )
    phrase, deliver = meta
    return blk(
        f"Step: {step_label} — {phrase}",
        module_en,
        "Deliverables",
        deliver,
    )


def activity_from_description(desc: str) -> str:
    """Short activity note: mirror description + guidance (journal notes support markdown)."""
    return (
        desc
        + "\n\n---\n\n"
        + "Use **Activity** for day-to-day progress, blockers, and sign-off. "
        "Keep the **description** as the stable scope and outcome statement."
    )


def build_description(wp_id, subject, parent_id, parent_subject):
    # --- Documents ---
    if subject.startswith("DOC – Project overview"):
        return blk(
            "Document: Project overview — single entry point for Tasks 1–6 in this stream",
            "gpc_account_move_line_reference_ext; gpc_analytic_project_statement; gpc_hr_timesheet_labor_accrual; gpc_stock_project_issue; tier validation + l10n_sa_edi (see milestones)",
            "This document covers",
            "business background, module list, conservative status, risks, navigation to milestones T1–T6",
        )
    if subject.startswith("DOC – Master testing"):
        return blk(
            "Document: Master testing guide — global strategy for all streams in this project",
            "n/a (process across modules)",
            "This document covers",
            "roles, environments, recommended order of streams, evidence expectations for UAT",
        )

    # --- Milestones (type 2 in seed) ---
    if "Milestone 0:" in subject:
        return blk(
            "Milestone: Foundation — master data and environments are ready before module-specific UAT",
            "Odoo core + company chart, stock/labor/project accounts, journals, analytic dimensions",
            "Deliverables",
            "COA sanity, default journals, analytic plans, staging DB naming, Odoo 19 build baseline, backup/refresh notes",
        )
    if "Milestone 1:" in subject:
        return blk(
            "Milestone: Task 1 — journal lines carry reliable reference fields for audit and search",
            "gpc_account_move_line_reference_ext",
            "Deliverables",
            "analysis, design, scaffold, fields + onchange, list/form/search, automated tests, install note",
        )
    if "Milestone 2:" in subject:
        return blk(
            "Milestone: Task 2 — OCA General Ledger respects account ranges on the deployed OCA revision",
            "OCA account_financial_report (or deployed fork) — verify same revision as production",
            "Deliverables",
            "revision verification, range behaviour documented, tests or scripted checks, documented workaround if any",
        )
    if "Milestone 3:" in subject:
        return blk(
            "Milestone: Task 3 — analytic project statement with wizard and exports matches real allocations",
            "gpc_analytic_project_statement",
            "Deliverables",
            "requirements sign-off, report + wizard, XLSX, allocation-slice rows, tie-out to analytic entries",
        )
    if "Milestone 4:" in subject:
        return blk(
            "Milestone: Task 4 — timesheet labor accrues through draft/post journals on schedule",
            "gpc_hr_timesheet_labor_accrual",
            "Deliverables",
            "batch design, non-MO scenarios, draft JE → post, reverse/regenerate discipline, UAT evidence",
        )
    if "Milestone 5:" in subject:
        return blk(
            "Milestone: Task 5 — issue stock to project at product cost with full accounting traceability",
            "gpc_stock_project_issue",
            "Deliverables",
            "project/analytic on picking, valuation at cost, single stock valuation account, draft JE + post, tests and install note",
        )
    if "Milestone 6:" in subject:
        return blk(
            "Milestone: Task 6 — invoice approval tiers and Saudi e-invoicing (ZATCA) path are operational",
            "base_tier_validation, account_move_tier_validation, l10n_sa_edi",
            "Deliverables",
            "tier rules on invoices, ZATCA flow validated on staging, compliance sign-off inputs for go-live",
        )
    if "Milestone 7:" in subject:
        return blk(
            "Milestone: Close-out — consolidated UAT, training/handover, and rolling risk closure",
            "cross-stream (all six task tracks)",
            "Deliverables",
            "per-stream acceptance or deferrals, training index, rolling risk register with owners",
        )

    # --- M0 / M7 standalone tasks ---
    if subject.startswith("M0 – COA"):
        return blk(
            "Work package: Chart and dimension prerequisites for downstream modules",
            "Company chart of accounts, stock/WIP/clearing, default journals, analytic plans",
            "Deliverables",
            "checklist completed with accounting lead; blockers recorded in Activity",
        )
    if subject.startswith("M0 – Staging"):
        return blk(
            "Work package: Staging databases and Odoo 19 revision baseline",
            "PostgreSQL + Odoo 19 build recorded per environment",
            "Deliverables",
            "DB names, addons_path, `odoo-bin --version`, backup/refresh procedure",
        )
    if subject.startswith("M0 – Change control"):
        return blk(
            "Work package: Change control and release notes template",
            "n/a (process)",
            "Deliverables",
            "template for each deploy: scope, migrations, test evidence link, rollback notes",
        )
    if subject.startswith("M7 – Consolidated"):
        return blk(
            "Work package: Consolidated sign-off across all six streams",
            "n/a (governance)",
            "Deliverables",
            "acceptance criteria ticked or deferrals documented with owners",
        )
    if subject.startswith("M7 – Training"):
        return blk(
            "Work package: Training and handover pack",
            "READMEs and test evidence locations in repo",
            "Deliverables",
            "index of docs, who was trained, when, and where evidence lives",
        )
    if subject.startswith("M7 – Open risks"):
        return blk(
            "Work package: Rolling open risks register",
            "n/a (governance)",
            "Deliverables",
            "ZATCA, OCA drift, chart changes, integrations — reviewed with dates",
        )

    # --- Epics ---
    if wp_id in EPIC_IDS:
        mod, achievement = EPIC_IDS[wp_id]
        return blk(
            f"Epic: {achievement}",
            mod,
            "Deliverables",
            "end-to-end delivery for this stream; execute and evidence through the child work packages below",
        )

    # --- Children under epics ---
    if parent_id in EPIC_IDS:
        tkey = TASK_KEY_BY_EPIC[parent_id]
        mod = EPIC_IDS[parent_id][0]
        prefix = f"{tkey} – "
        if subject.startswith(prefix):
            step = subject[len(prefix) :]
            return step_description(tkey, mod, step)

    return blk(
        f"Work package: {subject}",
        "see parent epic or milestone",
        "Notes",
        "Expand scope and acceptance criteria with your team.",
    )


updates = []
for wp_id, subject, parent_id, parent_subject in rows:
    text = build_description(wp_id, subject, parent_id, parent_subject)
    updates.append((text, wp_id))

cur.executemany("UPDATE work_packages SET description = %s WHERE id = %s", updates)

for text, wp_id in updates:
    wpj_id = wp_to_wpj.get(wp_id)
    if wpj_id:
        cur.execute(
            "UPDATE work_package_journals SET description = %s WHERE id = %s",
            (text, wpj_id),
        )

# Activity tab = journals.notes on version 1 (empty notes show as blank Activity)
for text, wp_id in updates:
    notes = activity_from_description(text)
    cur.execute(
        """
        UPDATE journals
        SET notes = %s, updated_at = NOW()
        WHERE journable_type = 'WorkPackage'
          AND journable_id = %s
          AND version = 1
        """,
        (notes, wp_id),
    )

conn.commit()
print("Updated", len(updates), "work packages, work_package_journals, and journal notes (Activity)")
cur.close()
conn.close()
