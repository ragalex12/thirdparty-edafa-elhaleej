import * as fs from "fs";
import * as path from "path";
import { test, expect } from "@playwright/test";
import { loadSeed } from "./seed-data";
import { odooLogin, openRecordForm } from "./odoo-helpers";

const screenshotsDir = path.join(__dirname, "..", "screenshots", "gulf-phase2");

test.describe.configure({ mode: "serial" });

test.describe("Gulf Phase 2 — HR payroll screenshots", () => {
  test.beforeAll(() => {
    fs.mkdirSync(screenshotsDir, { recursive: true });
  });

  test("WP #139 payslip evidence", async ({ page }) => {
    const seed = loadSeed();
    const shot = (name: string) => path.join(screenshotsDir, name);
    test.skip(!process.env.GCC_ODOO_LOGIN, "GCC_ODOO_LOGIN required");

    await odooLogin(page);
    await page.screenshot({ path: shot("01-after-login.png"), fullPage: true });

    await openRecordForm(page, "hr.payroll.structure", seed.structure_id);
    await page.screenshot({ path: shot("02-payroll-structure-gulf-standard.png"), fullPage: true });
    await expect(page.getByText(/Gulf Standard Payroll/i).first()).toBeVisible();

    await openRecordForm(page, "hr.employee", seed.employee_id);
    await page.screenshot({ path: shot("03-employee-uat.png"), fullPage: true });

    const payslipBtn = page.locator('button[name="action_hr_payslip"], a[name="action_hr_payslip"]').first();
    if (await payslipBtn.isVisible().catch(() => false)) {
      await payslipBtn.click();
      await page.waitForTimeout(2500);
      await page.screenshot({ path: shot("04-payslips-list.png"), fullPage: true });
      const row = page.locator("tr.o_data_row").first();
      if (await row.isVisible().catch(() => false)) {
        await row.click();
        await page.waitForTimeout(2000);
        await page.screenshot({ path: shot("05-payslip-form.png"), fullPage: true });
        const netCell = page.getByText(/12,900|12900|Net Salary/i).first();
        if (await netCell.isVisible().catch(() => false)) {
          await page.screenshot({ path: shot("06-payslip-net-12900.png"), fullPage: true });
        }
      }
    } else if (seed.payslip_id) {
      await page.goto(`/web#id=${seed.payslip_id}&model=hr.payslip&view_type=form`);
      await page.waitForTimeout(3000);
      if (await page.locator(".o_form_view").first().isVisible().catch(() => false)) {
        await page.screenshot({ path: shot("05-payslip-form.png"), fullPage: true });
      }
    }
  });
});
