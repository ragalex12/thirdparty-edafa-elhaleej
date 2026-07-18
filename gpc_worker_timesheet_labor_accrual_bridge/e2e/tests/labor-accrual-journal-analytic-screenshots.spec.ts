import * as fs from "fs";
import * as path from "path";
import { test, expect } from "@playwright/test";
import { odooLogin } from "./odoo-helpers";
import {
  openJournalEntryById,
  openJournalItemsTab,
  resolveFiveProjectsMoveId,
  resolveMultiAnalyticMoveId,
  screenshotJournalFormZoomed,
} from "./odoo-journal-entry-helpers";

const outMulti = path.join(__dirname, "..", "screenshots", "labor-accrual-multi-analytic");
const outFive = path.join(__dirname, "..", "screenshots", "labor-accrual-five-projects");

test.describe.configure({ mode: "serial" });

test.describe("Journal Items — multiple analytic debit lines (direct open)", () => {
  test.beforeAll(() => {
    fs.mkdirSync(outMulti, { recursive: true });
    fs.mkdirSync(outFive, { recursive: true });
  });

  test("Capture multi-analytic and five-project JE screenshots", async ({ page }) => {
    const login = process.env.GCC_ODOO_LOGIN || process.env.ODOO_LOGIN || "";
    const password = process.env.GCC_ODOO_PASSWORD || process.env.ODOO_PASSWORD || "";
    test.skip(!login || !password, "GCC_ODOO_LOGIN / GCC_ODOO_PASSWORD required");

    const multiMoveId = resolveMultiAnalyticMoveId();
    const fiveMoveId = resolveFiveProjectsMoveId();
    test.skip(!multiMoveId && !fiveMoveId, "Set move ids or run demo scripts first");

    await odooLogin(page);
    await page.keyboard.press("Escape").catch(() => {});
    await page.waitForTimeout(500);

    if (multiMoveId) {
      await test.step(`Multi-analytic JE (move ${multiMoveId})`, async () => {
        await openJournalEntryById(page, multiMoveId);
        await openJournalItemsTab(page);

        const expenseRows = page
          .locator(".o_list_table tbody tr.o_data_row")
          .filter({ hasText: /Labor accrual expense/i });
        expect(await expenseRows.count()).toBeGreaterThanOrEqual(2);

        await screenshotJournalFormZoomed(
          page,
          path.join(outMulti, "03-journal-items-multi-analytic-debit-lines.png"),
          0.68,
        );
      });
    }

    if (fiveMoveId) {
      await test.step(`Five projects JE (move ${fiveMoveId})`, async () => {
        await openJournalEntryById(page, fiveMoveId);
        await openJournalItemsTab(page);
        await page.waitForTimeout(1500);

        const expenseRows = page
          .locator(".o_list_table tbody tr.o_data_row")
          .filter({ hasText: /Labor accrual expense/i });
        expect(await expenseRows.count()).toBeGreaterThanOrEqual(5);

        await screenshotJournalFormZoomed(
          page,
          path.join(outFive, "03-journal-items-five-analytic-debit-lines.png"),
          0.62,
        );
      });
    }
  });
});
