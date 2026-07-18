import * as fs from "fs";
import * as path from "path";
import { expect, test, type Page } from "@playwright/test";
import {
  closeOdooDialogs,
  openRecordForm,
  odooLogin,
  showOptionalListColumns,
} from "./odoo-helpers";

const ASSET_ACTION_ID = 749;
const FIRST_ASSET_ID = Number(process.env.LEGACY_FIRST_ASSET_ID || "770");
const LAST_ASSET_ID = Number(process.env.LEGACY_LAST_ASSET_ID || "1538");
const screenshotsDir = path.resolve(
  __dirname,
  "../../../edafa_legacy_asset_import/e2e/screenshots/asset-import"
);
const mappingFixture = path.resolve(
  __dirname,
  "../../../edafa_legacy_asset_import/e2e/fixtures/asset-import-mapping-sample.csv"
);

function collectCriticalErrors(page: Page) {
  const errors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") {
      errors.push(message.text());
    }
  });
  page.on("pageerror", (error) => errors.push(error.message));
  return errors;
}

function expectNoCriticalErrors(errors: string[]) {
  const critical = errors.filter(
    (error) =>
      /OwlError|QWebError|KeyError|Access Error|cannot be located/i.test(error) &&
      !/favicon|404|Failed to load resource/i.test(error)
  );
  expect(critical, `Critical browser errors: ${critical.join(" | ")}`).toEqual([]);
}

async function openAssetList(page: Page) {
  for (const route of [
    `/odoo/action-${ASSET_ACTION_ID}`,
    `/web#action=${ASSET_ACTION_ID}&model=account.asset.asset&view_type=list`,
  ]) {
    await page.goto(route, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(2500);
    await closeOdooDialogs(page);
    if (await page.locator(".o_list_view").isVisible().catch(() => false)) {
      return;
    }
  }
  throw new Error("Could not open the Assets list view");
}

async function openLegacyMigrationTab(page: Page) {
  const tab = page.getByRole("tab", { name: /Legacy Migration/i }).first();
  await expect(tab).toBeVisible();
  await tab.click();
  await page.waitForTimeout(500);
}

test.describe.configure({ mode: "serial" });

test.describe("Legacy asset migration — staging UI evidence", () => {
  test.beforeAll(() => {
    fs.mkdirSync(screenshotsDir, { recursive: true });
  });

  test("769 imported assets are visible with migration totals", async ({ page }) => {
    const errors = collectCriticalErrors(page);
    await odooLogin(page);
    await openAssetList(page);

    await expect(page.locator(".o_list_view")).toBeVisible();
    await expect(page.locator(".o_pager_limit").first()).toContainText("769");
    await page.screenshot({
      path: path.join(screenshotsDir, "01-assets-list-769-records.png"),
      fullPage: true,
    });

    await showOptionalListColumns(page, [
      "Legacy Accumulated Depreciation",
      "Legacy Carrying Value",
    ]);
    await expect(
      page.locator("th[data-name='legacy_accumulated_depreciation']")
    ).toBeVisible();
    await expect(page.locator("th[data-name='legacy_carrying_value']")).toBeVisible();
    await page.screenshot({
      path: path.join(screenshotsDir, "02-assets-list-migration-columns.png"),
      fullPage: true,
    });

    expectNoCriticalErrors(errors);
  });

  test("first historical asset preserves source and accounting values", async ({
    page,
  }) => {
    const errors = collectCriticalErrors(page);
    await odooLogin(page);
    await openRecordForm(page, "account.asset.asset", FIRST_ASSET_ID);

    await expect(
      page.getByText(/مكيفات هام-FIXTR-0002/).first()
    ).toBeVisible();
    await expect(page.getByText(/^Draft$|^مسودة$/i).first()).toBeVisible();
    await page.screenshot({
      path: path.join(screenshotsDir, "03-first-asset-form.png"),
      fullPage: true,
    });

    await openLegacyMigrationTab(page);
    await expect(page.locator("[name='legacy_import_key']")).toContainText(
      "NADI-ASSET-0001"
    );
    await expect(page.locator("[name='legacy_cutover_date']")).toContainText(
      /Jan 1|01\/01\/2026/
    );
    await expect(
      page.locator("[name='legacy_accumulated_depreciation']")
    ).toContainText(/3,?374/);
    await expect(page.locator("[name='legacy_carrying_value']")).toContainText(
      /0(?:\.00)?/
    );
    await page.screenshot({
      path: path.join(screenshotsDir, "04-first-asset-legacy-migration.png"),
      fullPage: true,
    });

    expectNoCriticalErrors(errors);
  });

  test("last imported asset verifies the complete migration range", async ({
    page,
  }) => {
    const errors = collectCriticalErrors(page);
    await odooLogin(page);
    await openRecordForm(page, "account.asset.asset", LAST_ASSET_ID);
    await openLegacyMigrationTab(page);

    await expect(page.locator("[name='legacy_import_key']")).toContainText(
      "NADI-ASSET-0769"
    );
    await expect(
      page.locator("[name='legacy_accumulated_depreciation']")
    ).toContainText(/90\.87/);
    await expect(page.locator("[name='legacy_carrying_value']")).toContainText(
      /10,?964\.13/
    );
    await page.screenshot({
      path: path.join(screenshotsDir, "05-last-asset-legacy-migration.png"),
      fullPage: true,
    });

    expectNoCriticalErrors(errors);
  });

  test("generic import screen exposes the migration columns", async ({ page }) => {
    const errors = collectCriticalErrors(page);
    await odooLogin(page);
    await page.goto(
      `/odoo/action-${ASSET_ACTION_ID}/import?debug=1&active_model=account.asset.asset`,
      { waitUntil: "domcontentloaded" }
    );
    await page.locator('input[type="file"]').setInputFiles(mappingFixture);
    await page.waitForTimeout(2500);

    await expect(page.getByText("Legacy Cutover Date").first()).toBeVisible();
    await expect(
      page.getByText("Legacy Accumulated Depreciation").first()
    ).toBeVisible();
    await expect(page.getByText("Force Salvage Value = 1").first()).toBeVisible();
    await page.screenshot({
      path: path.join(screenshotsDir, "06-import-mapping-fields.png"),
      fullPage: true,
    });

    expectNoCriticalErrors(errors);
  });
});
