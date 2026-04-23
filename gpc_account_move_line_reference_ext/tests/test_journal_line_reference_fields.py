# -*- coding: utf-8 -*-
"""
Phase 1 automated tests for gpc_account_move_line_reference_ext.

Tests cover:
  - Fields exist on account.move.line
  - line_tax_number defaults from partner.vat when blank
  - line_tax_number is not overwritten when already set
  - Removing partner does not clear line_tax_number
  - line_reference and line_reference_number remain manual-only
"""
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestJournalLineReferenceFields(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Journal: Miscellaneous (type=general)
        cls.journal = cls.env["account.journal"].search(
            [("type", "=", "general"), ("company_id", "=", cls.env.company.id)],
            limit=1,
        )
        if not cls.journal:
            cls.journal = cls.env["account.journal"].create(
                {"name": "Test Misc Journal", "code": "TMISC", "type": "general"}
            )

        # Expense account for debit / credit lines
        cls.account = cls.env["account.account"].search(
            [
                ("account_type", "in", ["expense", "liability_current", "asset_current"]),
                ("company_id", "=", cls.env.company.id),
                ("deprecated", "=", False),
            ],
            limit=1,
        )

        # Partner with VAT
        cls.partner_vat = cls.env["res.partner"].create(
            {"name": "Test Partner VAT", "vat": "SA300012345600003"}
        )

        # Partner without VAT
        cls.partner_no_vat = cls.env["res.partner"].create(
            {"name": "Test Partner No VAT", "vat": False}
        )

    def _make_draft_entry(self):
        """Create a minimal posted=False manual journal entry with one balanced line pair."""
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": self.journal.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Test debit line",
                            "account_id": self.account.id,
                            "debit": 100.0,
                            "credit": 0.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Test credit line",
                            "account_id": self.account.id,
                            "debit": 0.0,
                            "credit": 100.0,
                        },
                    ),
                ],
            }
        )
        return move

    # ── Field existence ────────────────────────────────────────────────────────

    def test_fields_exist_on_account_move_line(self):
        """account.move.line must have all three Phase 1 fields."""
        aml = self.env["account.move.line"]
        self.assertIn("line_reference", aml._fields)
        self.assertIn("line_reference_number", aml._fields)
        self.assertIn("line_tax_number", aml._fields)

    def test_fields_are_char_and_stored(self):
        """All three fields must be Char and stored."""
        fields_map = self.env["account.move.line"]._fields
        for fname in ("line_reference", "line_reference_number", "line_tax_number"):
            f = fields_map[fname]
            self.assertEqual(f.type, "char", f"{fname} must be Char")
            self.assertTrue(f.store, f"{fname} must be stored")

    # ── Onchange: default line_tax_number from partner.vat ────────────────────

    def test_onchange_sets_tax_number_from_partner_vat(self):
        """When line_tax_number is blank and partner has VAT, onchange fills it."""
        move = self._make_draft_entry()
        line = move.line_ids[0]

        # Simulate: set partner (blank tax number), trigger onchange logic directly
        line.partner_id = self.partner_vat
        line.line_tax_number = False  # ensure blank before calling onchange
        line._onchange_partner_id_line_tax_number()

        self.assertEqual(
            line.line_tax_number,
            self.partner_vat.vat,
            "line_tax_number should default from partner.vat when blank",
        )

    def test_onchange_no_effect_when_partner_has_no_vat(self):
        """When partner has no VAT, onchange must not set line_tax_number."""
        move = self._make_draft_entry()
        line = move.line_ids[0]
        line.partner_id = self.partner_no_vat
        line.line_tax_number = False
        line._onchange_partner_id_line_tax_number()

        self.assertFalse(
            line.line_tax_number,
            "line_tax_number must stay blank when partner has no VAT",
        )

    # ── Onchange: do not overwrite existing value ──────────────────────────────

    def test_onchange_does_not_overwrite_existing_tax_number(self):
        """If line_tax_number already has a value, changing partner must not overwrite it."""
        move = self._make_draft_entry()
        line = move.line_ids[0]
        line.line_tax_number = "MANUALLY-ENTERED-TAX"
        line.partner_id = self.partner_vat
        line._onchange_partner_id_line_tax_number()

        self.assertEqual(
            line.line_tax_number,
            "MANUALLY-ENTERED-TAX",
            "Existing line_tax_number must not be overwritten by partner onchange",
        )

    # ── Onchange: removing partner does not clear the field ───────────────────

    def test_removing_partner_does_not_clear_tax_number(self):
        """Removing partner_id must not auto-clear line_tax_number."""
        move = self._make_draft_entry()
        line = move.line_ids[0]
        line.line_tax_number = "SA300012345600003"
        line.partner_id = False
        line._onchange_partner_id_line_tax_number()

        self.assertEqual(
            line.line_tax_number,
            "SA300012345600003",
            "line_tax_number must be preserved when partner is removed",
        )

    # ── Reference fields remain manual-only ───────────────────────────────────

    def test_line_reference_not_auto_populated(self):
        """line_reference must stay blank after partner onchange."""
        move = self._make_draft_entry()
        line = move.line_ids[0]
        line.partner_id = self.partner_vat
        line._onchange_partner_id_line_tax_number()

        self.assertFalse(
            line.line_reference,
            "line_reference must not be auto-populated by partner onchange",
        )

    def test_line_reference_number_not_auto_populated(self):
        """line_reference_number must stay blank after partner onchange."""
        move = self._make_draft_entry()
        line = move.line_ids[0]
        line.partner_id = self.partner_vat
        line._onchange_partner_id_line_tax_number()

        self.assertFalse(
            line.line_reference_number,
            "line_reference_number must not be auto-populated by partner onchange",
        )

    # ── Manual write and read ─────────────────────────────────────────────────

    def test_fields_accept_manual_values(self):
        """All three fields must accept and persist manually entered values."""
        move = self._make_draft_entry()
        line = move.line_ids[0]
        line.write(
            {
                "line_reference": "REF-001",
                "line_reference_number": "REFNUM-999",
                "line_tax_number": "SA123456789",
            }
        )
        self.assertEqual(line.line_reference, "REF-001")
        self.assertEqual(line.line_reference_number, "REFNUM-999")
        self.assertEqual(line.line_tax_number, "SA123456789")

