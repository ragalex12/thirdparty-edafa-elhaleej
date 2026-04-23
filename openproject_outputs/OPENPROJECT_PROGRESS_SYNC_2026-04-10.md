# OpenProject progress sync — M1, M2, M6 (2026-04-10)

## What was requested

Align **Odoo Finance Customization Phase 1** (`odoo-fin-cust-p1`) work packages **M1**, **M2**, and **M6** with current delivery reality: comments + parent status **In progress** (not closed), conservative handling of child tasks.

## What was executed on the server

**No live API updates were applied.** The OpenProject instance was **not reachable** from this environment:

- `http://127.0.0.1:8090` — connection refused  
- `https://generated-complexity-ireland-fully.trycloudflare.com` — **502 Bad Gateway** (origin unreachable)

## Deliverable: automation script

**Path:** `/opt/localaddons/openproject_scripts/update_finance_progress_m1_m2_m6.py`

**Dry-run (safe):**
```bash
python3 /opt/localaddons/openproject_scripts/update_finance_progress_m1_m2_m6.py
```

**Apply when OpenProject is up:**
```bash
python3 /opt/localaddons/openproject_scripts/update_finance_progress_m1_m2_m6.py --apply
```

The script:

1. Resolves API base URL (localhost with `Host` header, then HTTPS tunnel).  
2. Finds parent work packages by **exact subject**:  
   - `M1 - Journal Line Reference Extension`  
   - `M2 - OCA General Ledger Range Fix`  
   - `M6 - Invoice Approval and ZATCA Gate`  
3. Sets each parent’s status to **In progress** (first matching status from `/api/v3/statuses`).  
4. **POST**s a detailed progress **comment** on each parent (`POST /api/v3/work_packages/{id}/activities`).  
5. Prints all **child** work packages under those milestones (informational; **does not** mass-close leaves).

## Intended state after `--apply`

| Parent | Status | Rationale |
|--------|--------|-----------|
| M1 | In progress | Dev complete; UAT / optional hardening pending |
| M2 | In progress | Investigation + fix in repo; full production/UAT closure not claimed |
| M6 | In progress | OCA approval path validated; **ZATCA / l10n_sa_edi** not done |

## Child tasks

**Left open intentionally** — no automatic “Closed” on leaf packages (original plan diverges from OCA tier implementation for M6; M1 leaves include items not implemented).

## Next step

1. Restore OpenProject (and tunnel if used).  
2. Run the script with **`--apply`**.  
3. Manually adjust any leaf work packages if you need finer-grained closure.
