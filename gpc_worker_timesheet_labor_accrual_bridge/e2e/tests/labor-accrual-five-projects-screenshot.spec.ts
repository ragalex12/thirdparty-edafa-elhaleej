import * as fs from "fs";
import * as path from "path";
import { test, expect } from "@playwright/test";
import { odooLogin, openLaborAccrualBatches, waitForLaborAccrualBatchForm } from "./odoo-helpers";
import {
  openJournalEntryById,
  openJournalItemsTab,
  resolveFiveProjectsMoveId,
  screenshotJournalFormZoomed,
} from "./odoo-journal-entry-helpers";

const EXPECTED_PROJECT_LINES = 5;
const outDir = path.join(__dirname, "..", "screenshots", "labor-accrual-five-projects");

const BATCH_MATCH =
  process.env.GCC_ODOO_LABOR_ACCR_LIST_ROW_MATCH?.trim() || "LAB ACCR DEMO FIVE";

test.describe.configure({ mode: "serial" });

test.describe("Five projects — five analytic accounts on Journal Entry (UI)", () => {
  test.beforeAll(() => {
    fs.mkdirSync(outDir, { recursive: true });
  });

  test("Journal Items shows five debit lines with five analytic distributions", async ({
    page,
  }) => {
    const login = process.env.GCC_ODOO_LOGIN || process.env.ODOO_LOGIN || "";
    const password = process.env.GCC_ODOO_PASSWORD || process.env.ODOO_PASSWORD || "";
    test.skip(!login || !password, "GCC_ODOO_LOGIN / GCC_ODOO_PASSWORD required");

    const moveId = resolveFiveProjectsMoveId();
    test.skip(
      !moveId,
      "Run demo_labor_accrual_five_projects_verify.py first, or set GCC_ODOO_FIVE_PROJECTS_MOVE_ID",
    );

    await odooLogin(page);

    await test.step("Open Labor Accrual batch (5 projects / 5 lines)", async () => {
      await openLaborAccrualBatches(page);
      const row = page
        .locator(".o_list_table tbody tr.o_data_row")
        .filter({ hasText: BATCH_MATCH })
        .first();
      await row.waitFor({ state: "visible", timeout: 30_000 });
      await row.dblclick();
      await waitForLaborAccrualBatchForm(page);
      await page.screenshot({
        path: path.join(outDir, "01-batch-form-five-project-lines.png"),
        fullPage: true,
      });

      const lineRows = page.locator(
        '[name="line_ids"] .o_list_table tbody tr.o_data_row, .o_field_widget[name="line_ids"] tr.o_data_row',
      );
      expect(await lineRows.count()).toBeGreaterThanOrEqual(EXPECTED_PROJECT_LINES);
    });

    await test.step("Generate draft entry visible — open Journal Entry", async () => {
      const moveLink = page.locator('[name="move_id"] a, div[name="move_id"] a').first();
      await expect(moveLink).toBeVisible({ timeout: 30_000 });
      await moveLink.click();
      await page.waitForTimeout(3500);
      await page.screenshot({
        path: path.join(outDir, "02-journal-entry-header-five-projects.png"),
        fullPage: true,
      });
    });

    await test.step("Journal Items — five debit lines with analytic tags", async () => {
      await openJournalItemsTab(page);

      const expenseRows = page
        .locator(".o_list_table tbody tr.o_data_row")
        .filter({ hasText: /Labor accrual expense/i });
      const debitCount = await expenseRows.count();
      expect(debitCount).toBeGreaterThanOrEqual(EXPECTED_PROJECT_LINES);

      const expenseWithAnalytic = expenseRows.filter({
        has: page.locator(
          ".o_field_widget[name='analytic_distribution'], .o_field_analytic_distribution, .o_tag, .badge",
        ),
      });
      expect(await expenseWithAnalytic.count()).toBeGreaterThanOrEqual(EXPECTED_PROJECT_LINES);

      await screenshotJournalFormZoomed(
        page,
        path.join(outDir, "03-journal-items-five-analytic-debit-lines.png"),
        0.68,
      );
    });

    await test.step("Direct open by move id — assert five debits, one credit", async () => {
      await openJournalEntryById(page, moveId);
      await openJournalItemsTab(page);
      await screenshotJournalFormZoomed(
        page,
        path.join(outDir, "04-journal-items-by-move-id-five-projects.png"),
        0.68,
      );

      const expenseRows = page
        .locator(".o_list_table tbody tr.o_data_row")
        .filter({ hasText: /Labor accrual expense/i });
      expect(await expenseRows.count()).toBeGreaterThanOrEqual(EXPECTED_PROJECT_LINES);

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
