import * as fs from "fs";
import * as path from "path";
import { test, expect } from "@playwright/test";
import { odooLogin } from "./odoo-helpers";

const outDir = path.join(__dirname, "..", "screenshots", "labor-accrual-verify");

test("screenshot Journal Items for verified move (GCC_ODOO_VERIFY_MOVE_ID)", async ({ page }) => {
  fs.mkdirSync(outDir, { recursive: true });
  const moveId = (process.env.GCC_ODOO_VERIFY_MOVE_ID || "").trim();
  test.skip(!moveId, "Set GCC_ODOO_VERIFY_MOVE_ID (account.move id)");

  await odooLogin(page);
  await page.goto(`/web#id=${encodeURIComponent(moveId)}&model=account.move`, {
    waitUntil: "domcontentloaded",
  });
  await page.waitForTimeout(4000);

  const jiTab = page
    .getByRole("tab", { name: /Journal Items|بنود القيد|Journal items/i })
    .first();
  await jiTab.waitFor({ state: "visible", timeout: 60_000 }).catch(() => {});
  if (await jiTab.isVisible().catch(() => false)) {
    await jiTab.click();
    await page.waitForTimeout(2500);
  }

  await page.screenshot({
    path: path.join(outDir, "journal-items-analytic-verify.png"),
    fullPage: true,
  });

  await expect(page.locator("body.o_web_client")).toBeVisible();
});
