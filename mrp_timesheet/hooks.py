# -*- coding: utf-8 -*-

from odoo import api, SUPERUSER_ID


def post_init_hook(env):
    """
    Keep installs/updates resilient.

    Odoo calls this symbol by name (from __manifest__.py) via:
    getattr(odoo.addons.<module>, 'post_init_hook')(env)
    """
    # No-op by default. If later you need initialization/migration logic,
    # implement it here.
    if env is None:
        # Defensive: some custom loaders may pass None.
        return

    # Ensure hook can always run even if called with a non-superuser env.
    env = api.Environment(env.cr, SUPERUSER_ID, {})
    # Intentionally empty.

