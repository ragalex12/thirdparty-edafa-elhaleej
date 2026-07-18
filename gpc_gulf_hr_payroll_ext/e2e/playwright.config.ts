import { existsSync } from "fs";
import { resolve } from "path";
import { config as loadEnv } from "dotenv";
import { defineConfig, devices } from "@playwright/test";

const dotenvPath = resolve(__dirname, "../../../.env");
if (existsSync(dotenvPath)) loadEnv({ path: dotenvPath });
else if (existsSync("/opt/.env")) loadEnv({ path: "/opt/.env" });

const baseURL = (
  process.env.GPC_GULF_ODOO_URL ||
  process.env.GCC_ODOO_WEB_URL ||
  "http://127.0.0.1:8069"
).replace(/\/$/, "");

export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  workers: 1,
  timeout: 180_000,
  use: {
    baseURL,
    locale: "en-US",
    navigationTimeout: 90_000,
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
