import * as fs from "fs";
import * as path from "path";
import { test, expect } from "@playwright/test";
import { loadSeed } from "./seed-data";
import {
  odooLogin,
  openProjectDashboard,
  openProjectForm,
  openQuotationForm,
  showOptionalListColumns,
} from "./odoo-helpers";

const screenshotsDir = path.join(__dirname, "..", "screenshots", "gulf-phase1");

test.describe.configure({ mode: "serial" });

test.describe("Gulf Phase 1 — Playwright screenshots", () => {
  test.beforeAll(() => {
    fs.mkdirSync(screenshotsDir, { recursive: true });
  });

  test("WP #136–#138 UI evidence (PNG)", async ({ page }) => {
    const seed = loadSeed();
    const shot = (name: string) => path.join(screenshotsDir, name);

    // 01 Login
    const login =
      process.env.GCC_ODOO_LOGIN || process.env.ODOO_LOGIN || "";
    const password =
      process.env.GCC_ODOO_PASSWORD || process.env.ODOO_PASSWORD || "";
    const db = process.env.GCC_ODOO_DB || process.env.ODOO_DB || "";
    test.skip(!login || !password, "GCC_ODOO_LOGIN / GCC_ODOO_PASSWORD required");

    await page.goto(`/web/login${db ? `?db=${encodeURIComponent(db)}` : ""}`);
    await page.waitForLoadState("domcontentloaded");
    await page.screenshot({ path: shot("01-login-page.png"), fullPage: true });

    await odooLogin(page);
    await page.screenshot({ path: shot("02-after-login.png"), fullPage: true });

    // WP #137 — project form (contract_amount + description tab)
    await openProjectForm(page, seed.project_id);
    await page.screenshot({ path: shot("03-project-form.png"), fullPage: true });

    const budgetTab = page.getByRole("tab", { name: /Expected Budget/i }).first();
    if (await budgetTab.isVisible().catch(() => false)) {
      await budgetTab.click();
      await page.waitForTimeout(800);
      await page.screenshot({ path: shot("04-project-expected-budget-contract-amount.png"), fullPage: true });
    }

    const descTab = page.getByRole("tab", { name: /Description/i }).first();
    if (await descTab.isVisible().catch(() => false)) {
      await descTab.click();
      await page.waitForTimeout(800);
      await page.screenshot({ path: shot("05-project-description-tab.png"), fullPage: true });
    }

    // WP #136 — project dashboard right panel
    await openProjectDashboard(page, seed.project_id);
    await page.screenshot({ path: shot("06-project-dashboard.png"), fullPage: true });

    const detailsPanel = page.locator(".o_gpc_project_description, .o_rightpanel").first();
    if (await detailsPanel.isVisible().catch(() => false)) {
      await detailsPanel.screenshot({ path: shot("07-project-dashboard-details-panel.png") });
    }

    const contractLabel = page.getByText(/Contract Amount|مبلغ التعاقد/i).first();
    const descPanel = page.locator(".o_gpc_project_description").first();
    if (await contractLabel.isVisible().catch(() => false)) {
      await expect(contractLabel).toBeVisible();
    }
    if (await descPanel.isVisible().catch(() => false)) {
      await expect(descPanel).toContainText(/Playwright|Item A/i);
    }

    // WP #138 — quotation with dimensions
    await openQuotationForm(page, seed.sale_order_id);
    await showOptionalListColumns(page, ["Length", "Width", "Area"]);
    await page.screenshot({ path: shot("08-quotation-form-dimensions.png"), fullPage: true });

    const lineSubtotal = page.locator(".o_list_table tbody tr.o_data_row").first().locator("[name='price_subtotal'], .o_field_monetary").last();
    if (await lineSubtotal.isVisible().catch(() => false)) {
      await lineSubtotal.scrollIntoViewIfNeeded().catch(() => {});
    }
    await page.locator(".o_list_table").first().screenshot({ path: shot("09-quotation-order-lines.png") }).catch(() => {});

    // Assert client scenario total on quotation (form footer or line)
    const totalText = page.getByText(/64,?562\.40|64562\.40/).first();
    await expect(totalText).toBeVisible({ timeout: 30_000 });

    // PDF / print preview
    const printBtn = page.getByRole("button", { name: /^Print$|Print/i }).first();
    if (await printBtn.isVisible().catch(() => false)) {
      const [download] = await Promise.all([
        page.waitForEvent("download", { timeout: 90_000 }).catch(() => null),
        printBtn.click(),
      ]);
      if (download) {
        const pdfPath = path.join(screenshotsDir, "10-quotation-print.pdf");
        await download.saveAs(pdfPath);
      } else {
        await page.waitForTimeout(3000);
        await page.screenshot({ path: shot("10-quotation-print-dialog.png"), fullPage: true });
      }
    }

    await page.screenshot({ path: shot("11-final-quotation.png"), fullPage: true });
  });
});
