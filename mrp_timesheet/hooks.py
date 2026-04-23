# -*- coding: utf-8 -*-
"""
Task 70 – post_init_hook / post_migrate hook

Runs after module install or upgrade to backfill labor cost JEs for
existing timesheet lines that are linked to Manufacturing Orders but
have no labor_move_id yet.

Only processes lines that:
  - Have unit_amount > 0
  - Are linked to an MO (mrp_production_id set)
  - Have no existing labor_move_id
  - Have a resolvable labor rate (employee.hourly_cost > 0)
"""

import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Backfill labor cost JEs for existing MO-linked timesheet lines."""
    _backfill_labor_je(env)


def post_migrate_hook(env):
    """Same backfill — called after each upgrade."""
    _backfill_labor_je(env)


def _backfill_labor_je(env):
    _logger.info('mrp_timesheet: Starting labor JE backfill for existing timesheet lines...')

    lines = env['account.analytic.line'].search([
        ('mrp_production_id', '!=', False),
        ('unit_amount', '>', 0),
        ('labor_move_id', '=', False),
    ])

    if not lines:
        _logger.info('mrp_timesheet: No existing lines to backfill.')
        return

    _logger.info('mrp_timesheet: Found %d lines to process.', len(lines))
    posted = 0
    skipped = 0

    for line in lines:
        try:
            move = line._generate_labor_cost_move()
            if move:
                posted += 1
            else:
                skipped += 1
        except Exception as e:
            _logger.warning(
                'mrp_timesheet: Skipping line %d (%s) — %s',
                line.id, line.name or '', str(e)
            )
            skipped += 1

    _logger.info(
        'mrp_timesheet: Backfill complete — %d JEs posted, %d skipped '
        '(no accounts/rate configured).',
        posted, skipped,
    )
