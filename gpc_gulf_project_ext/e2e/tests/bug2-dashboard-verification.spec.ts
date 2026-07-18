import * as fs from "fs";
import * as path from "path";
import { test, expect, type Page } from "@playwright/test";
import {
  closeOdooDialogs,
  openProjectDashboard,
  odooLogin,
} from "./odoo-helpers";

const screenshotsDir = path.join(
  __dirname,
  "..",
  "screenshots",
  "bug2-verification"
);

const PROJECT_FULL = 133;
const PROJECT_NO_DESC = 139;
const PROJECT_NO_CONTRACT = 140;

const PROJECT_USER = {
  login: "gulf_uat_project_user@test.local",
  password: "GulfUatProjectUser2026!",
};

function collectConsoleErrors(page: Page) {
  const errors: string[] = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") {
      errors.push(msg.text());
    }
  });
  page.on("pageerror", (err) => {
    errors.push(err.message);
  });
  return errors;
}

function assertNoCriticalErrors(errors: string[]) {
  const critical = errors.filter(
    (e) =>
      /OwlError|QWebError|KeyError|Access Error|cannot be located/i.test(e) &&
      !/favicon|404|Failed to load resource/i.test(e)
  );
  expect(critical, `Console errors: ${critical.join(" | ")}`).toHaveLength(0);
}

async function loginAs(page: Page, login: string, password: string) {
  const db = process.env.GCC_ODOO_DB || process.env.ODOO_DB || "trgulf_Mrp";
  await page.goto(`/web/login?db=${encodeURIComponent(db)}`);
  await page.locator('input[name="login"]').fill(login);
  await page.locator('input[name="password"]').fill(password);
  await page.getByRole("button", { name: /Log in|Sign in/i }).click();
  await expect(page.locator("body.o_web_client")).toBeVisible({ timeout: 90_000 });
  await page.waitForTimeout(1500);
  await closeOdooDialogs(page);
}

test.describe.configure({ mode: "serial" });

test.describe("Bug #2 — Project Dashboard OWL verification", () => {
  test.beforeAll(() => {
    fs.mkdirSync(screenshotsDir, { recursive: true });
  });

  test("manager: full project — Project Details + HTML + currency", async ({
    page,
  }) => {
    const errors = collectConsoleErrors(page);
    const login = process.env.GCC_ODOO_LOGIN || "";
    const password = process.env.GCC_ODOO_PASSWORD || "";
    test.skip(!login || !password, "GCC_ODOO_LOGIN required");

    await loginAs(page, login, password);
    await openProjectDashboard(page, PROJECT_FULL);
    await page.waitForTimeout(2000);

    await page.screenshot({
      path: path.join(screenshotsDir, "01-dashboard-full-project-manager.png"),
      fullPage: true,
    });

    await expect(page.getByText("Project Details").first()).toBeVisible({
      timeout: 30_000,
    });
    await expect(
      page.getByText(/Contract Amount|مبلغ التعاقد/i).first()
    ).toBeVisible();
    await expect(page.getByText(/591,?70[67](?:\.80)?\s*SR?/i).first()).toBeVisible();

    const desc = page.locator(".o_gpc_project_description").first();
    await expect(desc).toBeVisible();
    await expect(desc.locator("li")).toHaveCount(2, { timeout: 10_000 });

    await page
      .locator(".o_rightpanel")
      .first()
      .screenshot({
        path: path.join(
          screenshotsDir,
          "02-project-details-panel-full.png"
        ),
      });

    assertNoCriticalErrors(errors);
  });

  test("manager: project without description", async ({ page }) => {
    const errors = collectConsoleErrors(page);
    const login = process.env.GCC_ODOO_LOGIN || "";
    const password = process.env.GCC_ODOO_PASSWORD || "";
    test.skip(!login || !password, "GCC_ODOO_LOGIN required");

    await loginAs(page, login, password);
    await openProjectDashboard(page, PROJECT_NO_DESC);
    await page.waitForTimeout(2000);

    await page.screenshot({
      path: path.join(screenshotsDir, "03-dashboard-no-description.png"),
      fullPage: true,
    });

    await expect(page.getByText(/Contract Amount|مبلغ التعاقد/i).first()).toBeVisible();
    await expect(page.getByText(/100,?000\s*SR?/i).first()).toBeVisible();
    await expect(page.locator(".o_gpc_project_description")).toHaveCount(0);
    assertNoCriticalErrors(errors);
  });

  test("manager: project without contract amount", async ({ page }) => {
    const errors = collectConsoleErrors(page);
    const login = process.env.GCC_ODOO_LOGIN || "";
    const password = process.env.GCC_ODOO_PASSWORD || "";
    test.skip(!login || !password, "GCC_ODOO_LOGIN required");

    await loginAs(page, login, password);
    await openProjectDashboard(page, PROJECT_NO_CONTRACT);
    await page.waitForTimeout(2000);

    await page.screenshot({
      path: path.join(screenshotsDir, "04-dashboard-no-contract.png"),
      fullPage: true,
    });

    const desc = page.locator(".o_gpc_project_description").first();
    await expect(desc).toBeVisible();
    await expect(desc).toContainText(/description/i);
    await expect(page.getByText(/Contract Amount|مبلغ التعاقد/i)).toHaveCount(0);
    assertNoCriticalErrors(errors);
  });

  test("project user: no contract amount, no access error", async ({ page }) => {
    const errors = collectConsoleErrors(page);
    await loginAs(page, PROJECT_USER.login, PROJECT_USER.password);
    await openProjectDashboard(page, PROJECT_FULL);
    await page.waitForTimeout(2000);

    await page.screenshot({
      path: path.join(screenshotsDir, "05-dashboard-project-user.png"),
      fullPage: true,
    });

    await expect(page.getByText("Project Details").first()).toBeVisible({
      timeout: 30_000,
    });
    const desc = page.locator(".o_gpc_project_description").first();
    await expect(desc).toBeVisible();
    await expect(page.getByText(/Contract Amount|مبلغ التعاقد/i)).toHaveCount(0);
    assertNoCriticalErrors(errors);
  });
});
