import { existsSync, readFileSync } from "fs";
import { resolve } from "path";

export type PlaywrightSeed = {
  project_id: number;
  project_name: string;
  sale_order_id: number;
  sale_order_name: string;
  expected_line_total: number;
  dashboard_action_id: number;
  quotations_action_id: number;
};

export function loadSeed(): PlaywrightSeed {
  const seedPath = resolve(__dirname, "..", ".playwright-seed.json");
  if (!existsSync(seedPath)) {
    throw new Error(
      `Missing ${seedPath}. Run seed_playwright_data.py via odoo shell first.`,
    );
  }
  return JSON.parse(readFileSync(seedPath, "utf-8")) as PlaywrightSeed;
}
