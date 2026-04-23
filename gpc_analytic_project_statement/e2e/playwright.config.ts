import path from "path";
import { defineConfig, devices } from "@playwright/test";
import dotenv from "dotenv";

dotenv.config({
  path: path.resolve(process.cwd(), "../../../.env"),
});
// Optional: ir.actions.act_window id for analytic.project.statement.wizard (per database).
// Resolve with: ir.model.data xml_id gpc_analytic_project_statement.action_analytic_project_statement_wizard
if (!process.env.GCC_ODOO_STATEMENT_ACTION_ID) {
  process.env.GCC_ODOO_STATEMENT_ACTION_ID = "1053";
}

const baseURL =
  process.env.GCC_ODOO_WEB_URL ||
  process.env.GCC_ODOO_BASE_URL ||
  "https://gpc.odoo.com.se/odoo";

export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: [["list"], ["html", { open: "never" }]],
  timeout: 120_000,
  expect: { timeout: 30_000 },
  use: {
    baseURL: baseURL.replace(/\/$/, ""),
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "off",
    actionTimeout: 30_000,
    navigationTimeout: 60_000,
    locale: "en-US",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
