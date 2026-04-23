# Copyright 2026
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from collections import defaultdict

from odoo import Command, _, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class StockPicking(models.Model):
    _inherit = "stock.picking"

    gpc_issue_project_id = fields.Many2one(
        comodel_name="project.project",
        string="GPC issue — project",
        copy=False,
        check_company=True,
        index=True,
        domain="[('company_id', '=?', company_id)]",
        help="Project receiving the material issue for management reporting. "
        "Used at picking level in Phase 1 together with the analytic account.",
    )
    gpc_issue_analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="GPC issue — analytic account",
        copy=False,
        check_company=True,
        index=True,
        domain="['&', ('active', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="Primary analytic account for the project issue journal entry (Phase 1). "
        "Typically aligned with the selected project; can be set explicitly when needed.",
    )
    gpc_issue_move_id = fields.Many2one(
        comodel_name="account.move",
        string="GPC issue — journal entry",
        copy=False,
        readonly=True,
        check_company=True,
        index="btree_not_null",
        help="Draft or posted account.move created by the GPC project issue wizard. "
        "At most one entry per picking; the wizard will link it here.",
    )
    gpc_issue_move_state = fields.Selection(
        related="gpc_issue_move_id.state",
        string="GPC issue — entry state",
        readonly=True,
    )

    def action_post_gpc_project_issue_entry(self):
        """Post the linked Task 5 journal entry when it is still draft (standard Odoo posting)."""
        self.ensure_one()
        move = self.gpc_issue_move_id
        if not move:
            raise UserError(
                _("No GPC project issue journal entry is linked to this transfer. Create one from the wizard first.")
            )
        if move.state != "draft":
            raise UserError(
                _(
                    "The GPC project issue journal entry is not in draft state (current: %(state)s).",
                    state=move.state,
                )
            )
        if move.company_id != self.company_id:
            raise UserError(_("The journal entry belongs to a different company than this transfer."))
        move.action_post()
        return True

    def _gpc_project_issue_check_eligibility(self):
        """Phase 1 rules before opening the wizard or confirming (no valuation/JE here)."""
        for picking in self:
            if picking.state != "done":
                raise UserError(
                    _("Only transfers in Done state can use GPC project issue. (Current state: %s)")
                    % (picking.state,)
                )
            if not picking.picking_type_id.gpc_project_issue_enabled:
                raise UserError(
                    _("This operation type is not enabled for GPC project issue. "
                      "Enable it on the operation type or use a different operation type.")
                )
            if not picking.gpc_issue_project_id:
                raise UserError(_("Select a project on the transfer before using GPC project issue."))
            if not picking.gpc_issue_analytic_account_id:
                raise UserError(
                    _("Select an analytic account on the transfer before using GPC project issue.")
                )
            if picking.gpc_issue_move_id:
                raise UserError(
                    _("A GPC project issue journal entry is already linked to this transfer. "
                      "Remove or reverse it in accounting before creating another.")
                )

    def _gpc_project_issue_get_included_moves(self):
        """Moves on this picking that count toward Task 5 cost basis (Phase 1).

        Rules (conservative, done picking only):
        - ``state == 'done'``
        - storable product (inventory-tracked)
        - valued *outgoing* move per stock_account (``is_out``): leaves a valued internal location
        - not excluded for valuation (e.g. consignment owner mismatch)
        - not dropship / dropship-return flows (different accounting treatment)
        """
        self.ensure_one()
        if self.state != "done":
            return self.env["stock.move"]
        moves = self.move_ids.filtered(
            lambda m: m.state == "done"
            and m.product_id.is_storable
            and m.is_out
            and not m._should_exclude_for_valuation()
        )
        moves = moves.filtered(
            lambda m: not m._is_dropshipped() and not m._is_dropshipped_returned()
        )
        return moves

    def _gpc_project_issue_prepare_accounting_basis(self):
        """Compute valued cost basis and a single stock valuation account for later JE creation.

        Does not create any ``account.move``. Raises ``UserError`` if there are no eligible moves,
        total valued amount is not positive, or included moves use different stock valuation accounts.

        :returns: dict with keys ``included_moves`` (stock.move recordset), ``total_value`` (float),
            ``stock_valuation_account_id`` (account.account), ``currency_id`` (res.currency)
        """
        self.ensure_one()
        if self.state != "done":
            raise UserError(
                _("GPC project issue accounting basis can only be computed for a transfer in Done state.")
            )
        moves = self._gpc_project_issue_get_included_moves()
        if not moves:
            raise UserError(
                _(
                    "No eligible stock moves found for GPC project issue on this transfer. "
                    "There must be at least one done, storable, valued outgoing move (inventory leaving valued stock). "
                    "Dropship moves are excluded."
                )
            )
        currency = self.company_id.currency_id
        rounding = currency.rounding
        total_value = sum(moves.mapped("value"))
        if float_compare(total_value, 0.0, precision_rounding=rounding) <= 0:
            raise UserError(
                _(
                    "The total valued amount for this transfer is not positive (zero or negative). "
                    "GPC project issue requires a positive inventory value on the included moves."
                )
            )
        by_account = defaultdict(list)
        for move in moves:
            acc = move._gpc_project_issue_get_stock_valuation_account()
            by_account[acc].append(move.product_id.display_name)
        if len(by_account) > 1:
            detail_lines = []
            for acc, prod_names in sorted(by_account.items(), key=lambda item: item[0].id):
                unique_names = ", ".join(sorted(set(prod_names)))
                detail_lines.append(_("%(account)s → %(products)s", account=acc.display_name, products=unique_names))
            raise UserError(
                _(
                    "GPC project issue (Phase 1) requires all included moves to use the same stock valuation account. "
                    "This transfer mixes different inventory accounts:\n%(details)s\n"
                    "Split the transfer or align product categories / valuation accounts, then try again.",
                    details="\n".join(detail_lines),
                )
            )
        valuation_account = next(iter(by_account))
        return {
            "included_moves": moves,
            "total_value": total_value,
            "stock_valuation_account_id": valuation_account,
            "currency_id": currency,
        }

    def _gpc_project_issue_validate_accounting_config(self, basis):
        """Ensure company journals/accounts required for draft JE creation are set."""
        self.ensure_one()
        company = self.company_id
        journal = company.gpc_project_issue_journal_id or company.account_stock_journal_id
        if not journal:
            raise UserError(
                _(
                    "Configure a GPC project issue journal or a stock journal on company “%(company)s” "
                    "before creating the journal entry.",
                    company=company.display_name,
                )
            )
        if journal.company_id != company:
            raise UserError(
                _("The GPC project issue journal must belong to the same company as the transfer.")
            )
        debit_account = company.gpc_project_issue_debit_account_id
        if not debit_account:
            raise UserError(
                _(
                    "Configure the GPC project issue debit account on company “%(company)s” "
                    "before creating the journal entry.",
                    company=company.display_name,
                )
            )
        if (
            debit_account.company_ids
            and company.id not in debit_account.company_ids.ids
        ):
            raise UserError(
                _(
                    "The GPC project issue debit account must be available for company “%(company)s”.",
                    company=company.display_name,
                )
            )
        credit_acc = basis["stock_valuation_account_id"]
        if credit_acc.id == debit_account.id:
            raise UserError(
                _(
                    "The configured debit account is the same as the stock valuation account for this transfer. "
                    "Use a distinct project/WIP/expense debit account in company settings."
                )
            )
        return {"journal_id": journal, "debit_account_id": debit_account}

    def _gpc_project_issue_create_draft_journal_entry(self):
        """Create one draft account.move for Task 5 and link it to this picking (both ways). Does not post."""
        self.ensure_one()
        self._gpc_project_issue_check_eligibility()
        basis = self._gpc_project_issue_prepare_accounting_basis()
        cfg = self._gpc_project_issue_validate_accounting_config(basis)
        company = self.company_id
        currency = basis["currency_id"]
        total_value = basis["total_value"]
        valuation_account = basis["stock_valuation_account_id"]
        debit_account = cfg["debit_account_id"]
        journal = cfg["journal_id"]
        move_date = self.date_done.date() if self.date_done else fields.Date.context_today(self)
        products_summary = ", ".join(
            sorted({m.product_id.display_name for m in basis["included_moves"]})
        )
        ref = _("GPC project issue — %(picking)s", picking=self.name or "")
        narration_parts = [
            _("Task 5 — project material issue at inventory cost (Phase 1)."),
            _("Transfer: %(name)s", name=self.name or ""),
            _("Project: %(project)s", project=self.gpc_issue_project_id.display_name),
            _("Analytic account: %(analytic)s", analytic=self.gpc_issue_analytic_account_id.display_name),
            _("Products: %(products)s", products=products_summary),
            _("Valued amount: %(amount)s %(currency)s", amount=total_value, currency=currency.name),
            _("Included moves: %(count)s", count=len(basis["included_moves"])),
        ]
        narration = "\n".join(narration_parts)
        analytic = self.gpc_issue_analytic_account_id
        debit_line = {
            "account_id": debit_account.id,
            "name": _("Project issue debit — %(picking)s", picking=self.name or ""),
            "debit": total_value,
            "credit": 0.0,
        }
        if analytic:
            debit_line["analytic_distribution"] = {str(analytic.id): 100.0}
        credit_line = {
            "account_id": valuation_account.id,
            "name": _("Inventory credit — %(picking)s", picking=self.name or ""),
            "debit": 0.0,
            "credit": total_value,
        }
        move_vals = {
            "move_type": "entry",
            "journal_id": journal.id,
            "date": move_date,
            "ref": ref,
            "narration": narration,
            "company_id": company.id,
            "currency_id": currency.id,
            "gpc_issue_picking_id": self.id,
            "line_ids": [
                Command.create(debit_line),
                Command.create(credit_line),
            ],
        }
        Move = self.env["account.move"].sudo().with_company(company)
        move = Move.create(move_vals)
        self.gpc_issue_move_id = move
        return move

    def action_open_gpc_project_issue_wizard(self):
        """Open the wizard after server-side eligibility checks."""
        self.ensure_one()
        self._gpc_project_issue_check_eligibility()
        self._gpc_project_issue_prepare_accounting_basis()
        return {
            "type": "ir.actions.act_window",
            "name": _("GPC project issue"),
            "res_model": "gpc.project.issue.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                **self.env.context,
                "default_picking_id": self.id,
            },
        }
