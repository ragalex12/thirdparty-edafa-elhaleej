import * as fs from "fs";
import * as path from "path";
import { test, expect } from "@playwright/test";
import { odooLogin, openLaborAccrualBatches, waitForLaborAccrualBatchForm } from "./odoo-helpers";
import {
  journalItemDebitRows,
  openJournalEntryById,
  openJournalItemsTab,
  resolveMultiAnalyticMoveId,
} from "./odoo-journal-entry-helpers";

const outDir = path.join(__dirname, "..", "screenshots", "labor-accrual-multi-analytic");

const BATCH_MATCH = process.env.GCC_ODOO_LABOR_ACCR_LIST_ROW_MATCH?.trim() || "LAB ACCR DEMO MULTI";

test.describe.configure({ mode: "serial" });

test.describe("Same project — multiple analytics on Journal Entry (UI)", () => {
  test.beforeAll(() => {
    fs.mkdirSync(outDir, { recursive: true });
  });

  test("Journal Items shows debit lines with Analytic Distribution (multi-analytic demo)", async ({
    page,
  }) => {
    const login = process.env.GCC_ODOO_LOGIN || process.env.ODOO_LOGIN || "";
    const password = process.env.GCC_ODOO_PASSWORD || process.env.ODOO_PASSWORD || "";
    test.skip(!login || !password, "GCC_ODOO_LOGIN / GCC_ODOO_PASSWORD required");

    const moveId = resolveMultiAnalyticMoveId();
    test.skip(
      !moveId,
      "Run demo_labor_accrual_multi_analytic_verify.py first, or set GCC_ODOO_MULTI_ANALYTIC_MOVE_ID",
    );

    await odooLogin(page);

    await test.step("Open Labor Accrual batch (same project, 2 lines)", async () => {
      await openLaborAccrualBatches(page);
      const row = page
        .locator(".o_list_table tbody tr.o_data_row")
        .filter({ hasText: BATCH_MATCH })
        .first();
      await row.waitFor({ state: "visible", timeout: 30_000 });
      await row.dblclick();
      await waitForLaborAccrualBatchForm(page);
      await page.screenshot({
        path: path.join(outDir, "01-batch-form-two-lines-same-project.png"),
        fullPage: true,
      });

      const lineRows = page.locator(
        '[name="line_ids"] .o_list_table tbody tr.o_data_row, .o_field_widget[name="line_ids"] tr.o_data_row',
      );
      const lineCount = await lineRows.count();
      expect(lineCount).toBeGreaterThanOrEqual(2);
    });

    await test.step("Open Journal Entry from move_id link", async () => {
      const moveLink = page
        .locator('[name="move_id"] a, div[name="move_id"] a')
        .first();
      await expect(moveLink).toBeVisible({ timeout: 30_000 });
      await moveLink.click();
      await page.waitForTimeout(3500);
      await page.screenshot({
        path: path.join(outDir, "02-journal-entry-header.png"),
        fullPage: true,
      });
    });

    await test.step("Journal Items — debit lines with Analytic Distribution column", async () => {
      await openJournalItemsTab(page);

      const debitRows = journalItemDebitRows(page);
      const debitCount = await debitRows.count();
      expect(debitCount).toBeGreaterThanOrEqual(2);

      const withAnalyticWidget = page.locator(
        ".o_list_table tbody tr.o_data_row .o_field_widget[name='analytic_distribution'], " +
          ".o_list_table tbody tr.o_data_row .o_field_analytic_distribution, " +
          ".o_list_table tbody tr.o_data_row .badge, " +
          ".o_list_table tbody tr.o_data_row .o_tag",
      );
      const analyticCellCount = await withAnalyticWidget.count();
      expect(analyticCellCount).toBeGreaterThan(0);

      await page.screenshot({
        path: path.join(outDir, "03-journal-items-multi-analytic-debit-lines.png"),
        fullPage: true,
      });
    });

    await test.step("Direct open by move id (regression)", async () => {
      await openJournalEntryById(page, moveId);
      await openJournalItemsTab(page);
      await page.screenshot({
        path: path.join(outDir, "04-journal-items-by-move-id.png"),
        fullPage: true,
      });

      const debitRows = journalItemDebitRows(page);
      expect(await debitRows.count()).toBeGreaterThanOrEqual(2);

      const offsetRow = page
        .locator(".o_list_table tbody tr.o_data_row")
        .filter({ hasText: /Labor accrual offset/i })
        .first();
      if (await offsetRow.isVisible().catch(() => false)) {
        const creditAnalytic = offsetRow.locator(
          ".o_field_widget[name='analytic_distribution'], .o_field_analytic_distribution, .o_tag, .badge",
        );
        const creditText = (await creditAnalytic.textContent().catch(() => "")) || "";
        expect(creditText.trim()).toBe("");
      }
    });
  });
});
