import { existsSync } from "fs";
import { resolve } from "path";
import { config as loadEnv } from "dotenv";
import { defineConfig, devices } from "@playwright/test";

const dotenvPath =
  process.env.DOTENV_CONFIG_PATH || resolve(__dirname, "../../../.env");
if (existsSync(dotenvPath)) {
  loadEnv({ path: dotenvPath });
} else if (existsSync("/opt/.env")) {
  loadEnv({ path: "/opt/.env" });
}

/** Prefer local Odoo when staging URL is unreachable from CI runner. */
const baseURL = (
  process.env.GPC_GULF_ODOO_URL ||
  process.env.GCC_ODOO_WEB_URL ||
  process.env.GCC_ODOO_BASE_URL ||
  process.env.ODOO_URL ||
  "http://127.0.0.1:8069"
).replace(/\/$/, "");

export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: [["list"], ["html", { open: "never" }]],
  timeout: 180_000,
  expect: { timeout: 45_000 },
  use: {
    baseURL,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "off",
    actionTimeout: 45_000,
    navigationTimeout: 90_000,
    locale: "en-US",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
