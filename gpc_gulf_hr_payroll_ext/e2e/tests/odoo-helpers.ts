import { expect, type Page } from "@playwright/test";

export async function odooLogin(page: Page) {
  const login = process.env.GCC_ODOO_LOGIN || process.env.ODOO_LOGIN || "";
  const password = process.env.GCC_ODOO_PASSWORD || process.env.ODOO_PASSWORD || "";
  const db = process.env.GCC_ODOO_DB || process.env.ODOO_DB || "";
  await page.goto(`/web/login${db ? `?db=${encodeURIComponent(db)}` : ""}`);
  await page.locator('input[name="login"]').first().fill(login);
  await page.locator('input[name="password"]').first().fill(password);
  await page.getByRole("button", { name: /Log in|Sign in/i }).click();
  await expect(page.locator("body.o_web_client")).toBeVisible({ timeout: 90_000 });
  await page.waitForTimeout(1500);
}

export async function openRecordForm(page: Page, model: string, recordId: number) {
  const slug = model.replace(/\./g, "-");
  for (const p of [`/odoo/${slug}/${recordId}`, `/web#id=${recordId}&model=${model}&view_type=form`]) {
    await page.goto(p, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(2500);
    if (await page.locator(".o_form_view").first().isVisible().catch(() => false)) return;
  }
  throw new Error(`Could not open ${model} ${recordId}`);
}
