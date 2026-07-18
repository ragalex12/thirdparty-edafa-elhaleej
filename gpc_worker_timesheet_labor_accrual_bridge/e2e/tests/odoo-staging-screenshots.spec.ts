import * as fs from "fs";
import * as path from "path";
import { test, expect } from "@playwright/test";
import { openLaborAccrualBatches } from "./odoo-helpers";

const screenshotsDir = path.join(__dirname, "..", "screenshots");

test.describe.configure({ mode: "serial" });

test.describe("Odoo staging screenshots", () => {
  test.beforeAll(() => {
    fs.mkdirSync(screenshotsDir, { recursive: true });
  });

  test("login flow and Labor Accrual Batches (PNG)", async ({ page }) => {
    const login =
      process.env.GCC_ODOO_LOGIN || process.env.ODOO_LOGIN || "";
    const password =
      process.env.GCC_ODOO_PASSWORD || process.env.ODOO_PASSWORD || "";
    const db = process.env.GCC_ODOO_DB || process.env.ODOO_DB || "";

    test.skip(!login || !password, "GCC_ODOO_LOGIN / GCC_ODOO_PASSWORD required");

    const loginPath = `/web/login${db ? `?db=${encodeURIComponent(db)}` : ""}`;
    await page.goto(loginPath);
    await page.waitForLoadState("domcontentloaded");
    await page.screenshot({
      path: path.join(screenshotsDir, "01-login-page.png"),
      fullPage: true,
    });

    await page.locator('input[name="login"], input#login').first().fill(login);
    await page.locator('input[name="password"], input#password').first().fill(password);
    await page.screenshot({
      path: path.join(screenshotsDir, "02-login-filled.png"),
      fullPage: true,
    });

    await page.getByRole("button", { name: /Log in|Sign in/i }).click();
    await expect(page.locator("body.o_web_client")).toBeVisible({ timeout: 90_000 });
    await page.waitForTimeout(1500);
    await page.screenshot({
      path: path.join(screenshotsDir, "03-after-login.png"),
      fullPage: true,
    });

    await openLaborAccrualBatches(page);
    await page.screenshot({
      path: path.join(screenshotsDir, "04-labor-accrual-batches.png"),
      fullPage: true,
    });
  });
});
