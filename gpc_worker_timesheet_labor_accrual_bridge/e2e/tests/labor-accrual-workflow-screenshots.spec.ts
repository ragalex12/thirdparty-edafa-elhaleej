import * as fs from "fs";
import * as path from "path";
import { test, expect } from "@playwright/test";
import {
  closeOdooBlockingDialog,
  odooLogin,
  openLaborAccrualBatches,
  openLaborAccrualBatchFromListPreferMatch,
  openLaborAccrualFromPeriodWizard,
  submitLaborAccrualPeriodWizard,
  waitForLaborAccrualBatchForm,
} from "./odoo-helpers";

const outDir = path.join(__dirname, "..", "screenshots", "labor-accrual-flow");

test.describe.configure({ mode: "serial" });

test.describe("Labor accrual — UI flow screenshots (Accounting → period → JE)", () => {
  test.beforeAll(() => {
    fs.mkdirSync(outDir, { recursive: true });
  });

  test("step-by-step like manual: wizard or existing batch, populate, draft JE, open move", async ({
    page,
  }) => {
    const login = process.env.GCC_ODOO_LOGIN || process.env.ODOO_LOGIN || "";
    const password = process.env.GCC_ODOO_PASSWORD || process.env.ODOO_PASSWORD || "";
    test.skip(!login || !password, "GCC_ODOO_LOGIN / GCC_ODOO_PASSWORD required");

    const startIso =
      process.env.GCC_ODOO_LABOR_ACCR_PERIOD_START?.trim() || "2025-09-01";
    const endIso = process.env.GCC_ODOO_LABOR_ACCR_PERIOD_END?.trim() || "2025-09-30";

    await odooLogin(page);
    await page.waitForTimeout(800);

    await test.step("Accounting → Labor Accrual (from period) — wizard", async () => {
      await openLaborAccrualFromPeriodWizard(page);
      await page.screenshot({
        path: path.join(outDir, "01-wizard-period-dialog.png"),
        fullPage: true,
      });
    });

    await test.step("Fill dates + Create batch and populate lines", async () => {
      await submitLaborAccrualPeriodWizard(page, startIso, endIso);
      await page.waitForTimeout(4000);

      const wizardBtn = page.locator('button[name="action_create_batch_and_populate_lines"]');
      const stillWizard = await wizardBtn.isVisible().catch(() => false);
      const danger = page.locator(".o_notification--danger, .alert-danger").first();
      const hasBlock = await danger.isVisible().catch(() => false);

      if (stillWizard || hasBlock) {
        if (hasBlock) {
          await page.screenshot({
            path: path.join(outDir, "02-wizard-error-notification.png"),
            fullPage: true,
          });
        } else {
          await page.screenshot({
            path: path.join(outDir, "02-wizard-still-open-after-submit.png"),
            fullPage: true,
          });
        }
        await page
          .locator('.o_dialog button[special="cancel"], .modal-footer .btn-secondary')
          .first()
          .click({ timeout: 5000 })
          .catch(() => {});
        await page.getByRole("button", { name: /Cancel|إلغاء/i }).click({ timeout: 3000 }).catch(() => {});
        await page.keyboard.press("Escape").catch(() => {});
        await page.waitForTimeout(600);
        await openLaborAccrualBatches(page);
        await page.waitForTimeout(1500);
        await page.screenshot({
          path: path.join(outDir, "03-fallback-batches-list.png"),
          fullPage: true,
        });
        await openLaborAccrualBatchFromListPreferMatch(page);
      } else {
        await waitForLaborAccrualBatchForm(page);
      }
    });

    await test.step("Labor Accrual Batch form (after wizard or opened list row)", async () => {
      await closeOdooBlockingDialog(page);
      await page.screenshot({
        path: path.join(outDir, "04-batch-form.png"),
        fullPage: true,
      });
    });

    await test.step("Populate lines — wait until Lines grid has rows", async () => {
      await closeOdooBlockingDialog(page);
      await page.getByRole("tab", { name: /^Lines$/i }).first().click({ timeout: 5000 }).catch(() => {});

      const populate = page.locator('button[name="action_populate_lines"]').first();
      await expect(populate).toBeVisible({ timeout: 20_000 });
      await populate.click();

      const firstLineRow = page
        .locator('[name="line_ids"] .o_list_table tbody tr.o_data_row, .o_field_widget[name="line_ids"] tr.o_data_row')
        .first();
      await expect(firstLineRow).toBeVisible({ timeout: 120_000 });

      await page.screenshot({
        path: path.join(outDir, "05-after-populate-lines.png"),
        fullPage: true,
      });
    });

    await test.step("Generate draft entry", async () => {
      await closeOdooBlockingDialog(page);
      const gen = page.locator('button[name="action_generate_draft_move"]').first();
      await expect(gen).toBeVisible({ timeout: 20_000 });
      await gen.click();
      await page.waitForTimeout(5000);
      await closeOdooBlockingDialog(page);
      await page.screenshot({
        path: path.join(outDir, "06-after-generate-draft-journal-link.png"),
        fullPage: true,
      });
    });

    await test.step("Open Journal Entry from move_id hyperlink", async () => {
      const moveLink = page
        .locator('[name="move_id"] a, div[name="move_id"] a, .o_field_widget[name="move_id"] a')
        .first();
      await expect(moveLink).toBeVisible({ timeout: 90_000 });
      await moveLink.click();
      await page.waitForTimeout(3500);
      await page.screenshot({
        path: path.join(outDir, "07-journal-entry-form.png"),
        fullPage: true,
      });
    });

    await test.step("Journal Items tab (analytic column visibility)", async () => {
      const jiTab = page
        .getByRole("tab", { name: /Journal Items|بنود القيد|Journal items/i })
        .first();
      if (await jiTab.isVisible().catch(() => false)) {
        await jiTab.click();
        await page.waitForTimeout(2000);
      }
      await page.screenshot({
        path: path.join(outDir, "08-journal-items-lines.png"),
        fullPage: true,
      });
    });
  });
});
