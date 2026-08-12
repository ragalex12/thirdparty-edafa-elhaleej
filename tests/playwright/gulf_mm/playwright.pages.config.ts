import { defineConfig, devices } from "@playwright/test";

const baseURL = (
  process.env.GULF_MM_PAGES_URL ||
  "https://sabryyoussef.github.io/edafa_elhaleej/client_demo/gulf_mm/"
).replace(/\/?$/, "/");

export default defineConfig({
  testDir: "./tests",
  workers: 1,
  reporter: [["list"]],
  use: {
    ...devices["Desktop Chrome"],
    baseURL,
  },
  projects: [
    {
      name: "case-study-page",
      testMatch: /gulf_mm_page\.spec\.ts/,
    },
  ],
});
