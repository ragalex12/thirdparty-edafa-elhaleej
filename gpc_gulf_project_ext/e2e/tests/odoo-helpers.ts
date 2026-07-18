import { expect, type Page } from "@playwright/test";

export async function odooLogin(page: Page) {
  const login =
    process.env.GCC_ODOO_LOGIN || process.env.ODOO_LOGIN || "";
  const password =
    process.env.GCC_ODOO_PASSWORD || process.env.ODOO_PASSWORD || "";
  const db = process.env.GCC_ODOO_DB || process.env.ODOO_DB || "";

  if (!login || !password) {
    throw new Error("Set GCC_ODOO_LOGIN and GCC_ODOO_PASSWORD in /opt/.env");
  }

  const loginPath = `/web/login${db ? `?db=${encodeURIComponent(db)}` : ""}`;
  await page.goto(loginPath);
  await page.locator('input[name="login"], input#login').first().fill(login);
  await page.locator('input[name="password"], input#password').first().fill(password);
  await page.getByRole("button", { name: /Log in|Sign in/i }).click();
  await expect(page.locator("body.o_web_client")).toBeVisible({ timeout: 90_000 });
  await page.waitForTimeout(1500);
}

export async function closeOdooDialogs(page: Page) {
  const closeBtn = page.getByRole("button", { name: /^Close$|إغلاق/i }).first();
  if (await closeBtn.isVisible().catch(() => false)) {
    await closeBtn.click().catch(() => {});
    await page.waitForTimeout(400);
  }
}

export async function openRecordForm(page: Page, model: string, recordId: number) {
  const paths = [
    `/odoo/${model.replace(".", "-")}/${recordId}`,
    `/odoo/m-${model.replace(".", "-")}/${recordId}`,
    `/web#id=${recordId}&model=${model}&view_type=form`,
  ];
  for (const p of paths) {
    await page.goto(p, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(2500);
    await closeOdooDialogs(page);
    if (await page.locator(".o_form_view").first().isVisible().catch(() => false)) {
      return;
    }
  }
  throw new Error(`Could not open form ${model} id=${recordId}`);
}

export async function openProjectForm(page: Page, projectId: number) {
  await openRecordForm(page, "project.project", projectId);
  await page.waitForTimeout(1000);
}

async function isProjectDashboard(page: Page) {
  return (
    (await page.getByText("Project Details").first().isVisible().catch(() => false)) ||
    (await page.getByText(/Milestones|No updates found/i).first().isVisible().catch(() => false)) ||
    (await page.locator(".o_rightpanel").first().isVisible().catch(() => false))
  );
}

export async function openProjectDashboard(page: Page, projectId: number) {
  const dashboardPaths = [
    `/odoo/project-dashboard/${projectId}`,
    `/odoo/project-dashboard?active_id=${projectId}`,
    `/web#action=488&active_id=${projectId}&model=project.update&view_type=kanban`,
  ];
  for (const p of dashboardPaths) {
    await page.goto(p, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(2500);
    await closeOdooDialogs(page);
    if (await isProjectDashboard(page)) {
      return;
    }
  }

  await openProjectForm(page, projectId);
  await closeOdooDialogs(page);

  const dashboardBtn = page
    .locator('button[name="project_update_all_action"], a[name="project_update_all_action"]')
    .first();
  if (await dashboardBtn.isVisible().catch(() => false)) {
    await dashboardBtn.click();
    await page.waitForTimeout(3500);
    await closeOdooDialogs(page);
    if (await isProjectDashboard(page)) {
      return;
    }
  }

  const dashboardStatusBtn = page
    .getByRole("button", { name: /Dashboard/i })
    .first();
  if (await dashboardStatusBtn.isVisible().catch(() => false)) {
    await dashboardStatusBtn.click();
    await page.waitForTimeout(3500);
    await closeOdooDialogs(page);
  }
}

export async function openQuotationForm(page: Page, orderId: number) {
  await openRecordForm(page, "sale.order", orderId);
  await page.waitForTimeout(1000);
}

export async function showOptionalListColumns(page: Page, labels: string[]) {
  for (const label of labels) {
    const toggle = page.getByRole("button", { name: /Optional columns|Show optional/i }).first();
    if (await toggle.isVisible().catch(() => false)) {
      await toggle.click().catch(() => {});
      await page.waitForTimeout(400);
    }
    const item = page.getByRole("menuitemcheckbox", { name: new RegExp(label, "i") }).first();
    if (await item.isVisible().catch(() => false)) {
      const checked = await item.getAttribute("aria-checked");
      if (checked !== "true") {
        await item.click().catch(() => {});
      }
    }
  }
  await page.keyboard.press("Escape").catch(() => {});
  await page.waitForTimeout(500);
}
