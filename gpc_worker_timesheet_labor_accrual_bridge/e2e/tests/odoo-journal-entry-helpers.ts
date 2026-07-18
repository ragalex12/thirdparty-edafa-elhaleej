import * as fs from "fs";
import * as path from "path";
import { expect, type Page } from "@playwright/test";

/** Open a draft/posted account.move form by database id. */
export async function openJournalEntryById(page: Page, moveId: string) {
  await page.goto(`/web#id=${encodeURIComponent(moveId)}&model=account.move`, {
    waitUntil: "domcontentloaded",
  });
  await page.waitForTimeout(3000);
  await expect(page.locator("body.o_web_client")).toBeVisible({ timeout: 90_000 });
}

/** Activate Journal Items tab on account.move form. */
export async function openJournalItemsTab(page: Page) {
  const jiTab = page
    .getByRole("tab", { name: /Journal Items|بنود القيد|Journal items/i })
    .first();
  await jiTab.waitFor({ state: "visible", timeout: 60_000 });
  await jiTab.click();
  await page.waitForTimeout(2000);
}

/**
 * Debit rows in the journal items list (Odoo 17+ list view).
 * Returns locators for rows where Debit column has a positive amount.
 */
export function journalItemDebitRows(page: Page) {
  return page.locator(
    ".o_list_table tbody tr.o_data_row, .o_field_widget[name='line_ids'] tbody tr.o_data_row",
  );
}

/** Read move id from env or file written by demo_labor_accrual_multi_analytic_verify.py */
export function resolveMultiAnalyticMoveId(): string {
  const fromEnv =
    process.env.GCC_ODOO_MULTI_ANALYTIC_MOVE_ID?.trim() ||
    process.env.GCC_ODOO_VERIFY_MOVE_ID?.trim() ||
    "";
  if (fromEnv) return fromEnv;

  const idFile = path.join(__dirname, "..", ".last-multi-analytic-move-id.txt");
  if (fs.existsSync(idFile)) {
    return fs.readFileSync(idFile, "utf8").trim();
  }
  return "";
}

/**
 * Zoom out and expand embedded list views so multi-row Journal Items fit one screenshot.
 */
export async function prepareZoomedFormScreenshot(page: Page, zoom = 0.72) {
  await page.setViewportSize({ width: 1920, height: 1200 });
  await page.evaluate((scale) => {
    const html = document.documentElement;
    html.style.zoom = String(scale);
    document.querySelectorAll<HTMLElement>(
      ".o_list_renderer, .o_field_x2many_list, .o_list_view, .table-responsive, .o_content",
    ).forEach((el) => {
      el.style.maxHeight = "none";
      el.style.overflow = "visible";
      el.style.height = "auto";
    });
  }, zoom);
  await page.waitForTimeout(400);
}

/** Full-page screenshot after prepareZoomedFormScreenshot (all list rows visible). */
export async function screenshotJournalFormZoomed(page: Page, filePath: string, zoom = 0.72) {
  await prepareZoomedFormScreenshot(page, zoom);
  const lastExpense = page
    .locator(".o_list_table tbody tr.o_data_row")
    .filter({ hasText: /Labor accrual expense/i })
    .last();
  if (await lastExpense.isVisible().catch(() => false)) {
    await lastExpense.scrollIntoViewIfNeeded();
    await page.waitForTimeout(300);
  }
  await page.screenshot({ path: filePath, fullPage: true });
}

/** Read move id from env or file written by demo_labor_accrual_five_projects_verify.py */
export function resolveFiveProjectsMoveId(): string {
  const fromEnv = process.env.GCC_ODOO_FIVE_PROJECTS_MOVE_ID?.trim() || "";
  if (fromEnv) return fromEnv;

  const idFile = path.join(__dirname, "..", ".last-five-projects-move-id.txt");
  if (fs.existsSync(idFile)) {
    return fs.readFileSync(idFile, "utf8").trim();
  }
  return "";
}
