import { test, expect } from "@playwright/test";
import fs from "fs";
import path from "path";
import * as XLSX from "xlsx";

function shotsDir(): string {
  const dir = path.join(process.cwd(), "test-results", "screenshots");
  fs.mkdirSync(dir, { recursive: true });
  return dir;
}

function shot(name: string): string {
  return path.join(shotsDir(), name);
}

/** Debit = col E (index 4), Credit = col F (index 5) — matches Phase 1 XLSX columns. */
function assertXlsxDebitCreditNotAllZeros(xlsxPath: string): void {
  expect(fs.existsSync(xlsxPath), `Expected XLSX at ${xlsxPath}`).toBe(true);
  const buf = fs.readFileSync(xlsxPath);
  const wb = XLSX.read(buf, { type: "buffer" });
  const ws = wb.Sheets[wb.SheetNames[0]];
  expect(ws, "first worksheet missing").toBeTruthy();
  const rows = XLSX.utils.sheet_to_json<(string | number | undefined)[]>(ws, {
    header: 1,
    defval: "",
    raw: true,
  }) as unknown[][];
  expect(rows.length, "expect header row + at least one data row").toBeGreaterThan(1);

  let anyNonZero = false;
  let dataRows = 0;
  for (let i = 1; i < rows.length; i++) {
    const row = rows[i] as unknown[];
    if (!row || row.length < 6) {
      continue;
    }
    dataRows += 1;
    const debit = Number(row[4]);
    const credit = Number(row[5]);
    const d = Number.isFinite(debit) ? debit : 0;
    const c = Number.isFinite(credit) ? credit : 0;
    if (Math.abs(d) > 1e-9 || Math.abs(c) > 1e-9) {
      anyNonZero = true;
    }
  }

  expect(dataRows, "no data rows under header").toBeGreaterThan(0);
  expect(
    anyNonZero,
    "Export must contain at least one non-zero Debit or Credit (got all zeros — deploy addon code + Apps → Upgrade)",
  ).toBe(true);
}

async function odooLogin(page: import("@playwright/test").Page) {
  const login =
    process.env.GCC_ODOO_LOGIN ||
    process.env.ODOO_LOGIN ||
    "";
  const password =
    process.env.GCC_ODOO_PASSWORD ||
    process.env.ODOO_PASSWORD ||
    "";
  const db =
    process.env.GCC_ODOO_DB ||
    process.env.ODOO_DB ||
    "";

  test.skip(!login || !password, "Set GCC_ODOO_LOGIN and GCC_ODOO_PASSWORD (e.g. via /opt/.env)");

  const loginPath = `/web/login${db ? `?db=${encodeURIComponent(db)}` : ""}`;
  await page.goto(loginPath);

  await page.locator('input[name="login"], input#login').first().fill(login);
  await page.locator('input[name="password"], input#password').first().fill(password);

  await page.getByRole("button", { name: /Log in|Sign in/i }).click();

  await expect(page.locator("body.o_web_client")).toBeVisible({ timeout: 90_000 });
}

/** Odoo home / app grid: open the Accounting app (required before finance menus exist). */
async function openAccountingApp(page: import("@playwright/test").Page) {
  await page.keyboard.press("Escape").catch(() => {});
  await page.waitForTimeout(300);

  const accountingOption = page.getByRole("option", { name: /^Accounting$/i }).first();
  const accountingLink = page.getByRole("link", { name: /Accounting|المحاسبة/i }).first();

  if ((await accountingOption.count()) > 0 && (await accountingOption.isVisible())) {
    await accountingOption.click();
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(1500);
    return;
  }
  if ((await accountingLink.count()) > 0 && (await accountingLink.isVisible())) {
    await accountingLink.click();
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(1500);
    return;
  }

  await page.goto("/web");
  await page.waitForTimeout(1000);
  const opt2 = page.getByRole("option", { name: /^Accounting$/i }).first();
  if ((await opt2.count()) > 0) {
    await opt2.click();
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(1500);
  }
}

async function openAnalyticProjectStatementWizard(page: import("@playwright/test").Page) {
  const stmtRe =
    /Analytic Project Statement|كشف حساب المشاريع التحليلية|المشاريع التحليلية/i;
  const reportingRe = /Reporting|التقارير/i;

  const actionId =
    process.env.GCC_ODOO_STATEMENT_ACTION_ID ||
    process.env.GCC_ODOO_WIZARD_ACTION_ID ||
    "";

  if (actionId) {
    await page.goto(`/web#action=${encodeURIComponent(actionId)}`, {
      waitUntil: "domcontentloaded",
    });
    await page.waitForTimeout(2500);
    const heading = page.getByRole("heading", { name: stmtRe }).first();
    if (await heading.isVisible().catch(() => false)) {
      return;
    }
  }

  await openAccountingApp(page);
  await page.keyboard.press("Escape").catch(() => {});
  await page.waitForTimeout(400);

  const reportingNav = page
    .getByRole("link", { name: reportingRe })
    .or(page.getByRole("button", { name: reportingRe }))
    .first();
  await reportingNav.waitFor({ state: "visible", timeout: 15_000 });
  await reportingNav.hover().catch(() => {});
  await reportingNav.click({ timeout: 10_000 });
  await page.waitForTimeout(500);

  // Menu is under Reporting → Management (next to *Analytic Report*).
  const management = page.getByRole("menuitem", { name: /Management|الإدارة/i }).first();
  if (await management.isVisible().catch(() => false)) {
    await management.hover();
    await page.waitForTimeout(400);
  }

  const stmtItem = page.getByRole("menuitem", { name: stmtRe }).first();
  await stmtItem.scrollIntoViewIfNeeded().catch(() => {});
  await stmtItem.waitFor({ state: "visible", timeout: 20_000 });
  await stmtItem.click({ timeout: 10_000 });
}

test.describe("Analytic Project Statement", () => {
  test("login, open wizard, screenshots", async ({ page }) => {
    await odooLogin(page);
    await page.screenshot({ path: shot("01-after-login.png"), fullPage: true });

    await openAnalyticProjectStatementWizard(page);
    await page.waitForTimeout(2000);

    await expect(
      page.getByRole("heading", {
        name: /Analytic Project Statement|كشف حساب المشاريع التحليلية/i,
      }),
    ).toBeVisible({ timeout: 60_000 });

    await page.screenshot({ path: shot("02-wizard-visible.png"), fullPage: true });

    const dialog = page.getByRole("dialog");
    const exportBtn = dialog.getByRole("button", {
      name: /Export XLSX|تصدير|XLSX/i,
    });
    await expect(exportBtn).toBeVisible({ timeout: 15_000 });
    await exportBtn.scrollIntoViewIfNeeded();

    await page.screenshot({ path: shot("03-before-export-xlsx.png"), fullPage: true });

    const downloadPromise = page.waitForEvent("download", { timeout: 60_000 });
    await exportBtn.click();
    const download = await downloadPromise;
    expect(download, "browser should download XLSX").toBeTruthy();

    const savePath = path.join(shotsDir(), "export-analytic-project-statement.xlsx");
    await download!.saveAs(savePath);

    assertXlsxDebitCreditNotAllZeros(savePath);

    await page.screenshot({ path: shot("04-after-export-click.png"), fullPage: true });
  });
});
