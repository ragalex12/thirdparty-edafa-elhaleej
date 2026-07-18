import { test, expect } from "@playwright/test";
import { odooLogin, openLaborAccrualBatches } from "./odoo-helpers";

test.describe("Labor Accrual Batch (bridge smoke)", () => {
  test("login and reach Labor Accrual Batches list or form", async ({ page }) => {
    const login =
      process.env.GCC_ODOO_LOGIN || process.env.ODOO_LOGIN || "";
    const password =
      process.env.GCC_ODOO_PASSWORD || process.env.ODOO_PASSWORD || "";

    test.skip(!login || !password, "Set GCC_ODOO_LOGIN and GCC_ODOO_PASSWORD (e.g. via .env)");

    await odooLogin(page);

    await openLaborAccrualBatches(page);

    const listView = page.locator(".o_list_view");
    const formView = page.locator(".o_form_view");
    const kanbanView = page.locator(".o_kanban_view");
    const hasList = await listView.isVisible().catch(() => false);
    const hasForm = await formView.isVisible().catch(() => false);
    const hasKanban = await kanbanView.isVisible().catch(() => false);

    expect(
      hasList || hasForm || hasKanban,
      "Expected list, kanban, or form after navigation",
    ).toBe(true);

    if (hasList || hasKanban) {
      const row = page.locator(".o_list_table tbody tr.o_data_row").first();
      if ((await row.count()) > 0) {
        await row.click();
        await page.waitForTimeout(2000);
      }
    }

    const populateBtn = page.getByRole("button", {
      name: /Populate lines|ملء البنود/i,
    });
    const onForm = await page.locator(".o_form_view").isVisible().catch(() => false);
    if (onForm) {
      await expect(populateBtn).toBeVisible({ timeout: 30_000 });
    } else {
      test.info().annotations.push({
        type: "note",
        description:
          "Stayed on list/kanban (no row opened or empty). Set GCC_ODOO_LABOR_ACCRUAL_ACTION_ID or create a draft batch to assert Populate lines.",
      });
    }
  });
});
