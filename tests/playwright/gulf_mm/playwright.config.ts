import path from "path";
import { pathToFileURL } from "url";
import { defineConfig, devices } from "@playwright/test";
import dotenv from "dotenv";

dotenv.config({ path: path.resolve(__dirname, ".env") });

const ALLOWED_DB = "trgcc_mm_uat";
const db = (process.env.GULF_MM_DB || process.env.GCC_ODOO_DB || "").trim();
const baseURL = (
  process.env.GULF_MM_BASE_URL ||
  process.env.GCC_ODOO_WEB_URL ||
  "http://localhost:8069"
).replace(/\/$/, "");

if (db && (db === "trgcc" || db === "entgcc" || db !== ALLOWED_DB)) {
  throw new Error(
    `ABORT: Playwright Gulf/MM suite refuses database ${JSON.stringify(db)}. Allowed: ${ALLOWED_DB}`,
  );
}

const shots = path.resolve(
  __dirname,
  "../../../docs/client_demo/gulf_mm/assets/playwright",
);
const pageRoot = path.resolve(__dirname, "../../../docs/client_demo/gulf_mm");
const pageBaseURL = pathToFileURL(pageRoot + path.sep).href;

export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: [
    ["list"],
    ["json", { outputFile: "test-results/results.json" }],
    ["html", { open: "never", outputFolder: "playwright-report" }],
  ],
  timeout: 120_000,
  expect: { timeout: 30_000 },
  use: {
    locale: "en-US",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "off",
    actionTimeout: 30_000,
    navigationTimeout: 60_000,
  },
  projects: [
    {
      name: "setup",
      testMatch: /auth\.setup\.ts/,
      use: {
        ...devices["Desktop Chrome"],
        baseURL,
      },
    },
    {
      name: "odoo-uat",
      dependencies: ["setup"],
      use: {
        ...devices["Desktop Chrome"],
        baseURL,
        storageState: path.join(__dirname, "playwright/.auth/user.json"),
      },
      testMatch: /gulf_mm_odoo\.spec\.ts/,
    },
    {
      name: "case-study-page",
      use: {
        ...devices["Desktop Chrome"],
        baseURL: pageBaseURL,
      },
      testMatch: /gulf_mm_page\.spec\.ts/,
    },
  ],
  metadata: { shotsDir: shots, allowedDb: ALLOWED_DB, pageRoot },
});
