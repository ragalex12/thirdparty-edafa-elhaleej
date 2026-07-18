import { expect, type Page } from "@playwright/test";

/** Convert `YYYY-MM-DD` to `MM/DD/YYYY` for Odoo date widgets with en-US locale. */
export function isoDateToUsMmDdYyyy(iso: string): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso.trim());
  if (!m) return iso;
  return `${m[2]}/${m[3]}/${m[1]}`;
}

export async function odooLogin(page: Page) {
  const login =
    process.env.GCC_ODOO_LOGIN || process.env.ODOO_LOGIN || "";
  const password =
    process.env.GCC_ODOO_PASSWORD || process.env.ODOO_PASSWORD || "";
  const db = process.env.GCC_ODOO_DB || process.env.ODOO_DB || "";

  if (!login || !password) {
    throw new Error(
      "Set GCC_ODOO_LOGIN and GCC_ODOO_PASSWORD (e.g. load /opt/.env via playwright config)",
    );
  }

  const loginPath = `/web/login${db ? `?db=${encodeURIComponent(db)}` : ""}`;
  await page.goto(loginPath);

  await page.locator('input[name="login"], input#login').first().fill(login);
  await page.locator('input[name="password"], input#password').first().fill(password);

  await page.getByRole("button", { name: /Log in|Sign in/i }).click();

  await expect(page.locator("body.o_web_client")).toBeVisible({ timeout: 90_000 });
}

/** Open Accounting app from home / app switcher (Odoo 16+). */
export async function openAccountingApp(page: Page) {
  await page.keyboard.press("Escape").catch(() => {});
  await page.waitForTimeout(300);

  const accountingOption = page.getByRole("option", { name: /^Accounting$/i }).first();
  const accountingLink = page.getByRole("link", { name: /Accounting|المحاسبة/i }).first();

  if ((await accountingOption.count()) > 0 && (await accountingOption.isVisible())) {
    await accountingOption.click();
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(1500);
    return;
  }
  if ((await accountingLink.count()) > 0 && (await accountingLink.isVisible())) {
    await accountingLink.click();
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(1500);
    return;
  }

  await page.goto("/web");
  await page.waitForTimeout(1000);
  const opt2 = page.getByRole("option", { name: /^Accounting$/i }).first();
  if ((await opt2.count()) > 0) {
    await opt2.click();
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(1500);
  }
}

/** Accounting → open **Transactions** (or equivalent) submenu bar. */
export async function openAccountingTransactionsArea(page: Page) {
  await openAccountingApp(page);
  await page.keyboard.press("Escape").catch(() => {});
  await page.waitForTimeout(400);

  const transactionsRe = /Transactions|حركات|Accounting/i;
  const transactionsNav = page
    .getByRole("link", { name: transactionsRe })
    .or(page.getByRole("button", { name: transactionsRe }))
    .first();

  if (await transactionsNav.isVisible().catch(() => false)) {
    await transactionsNav.hover().catch(() => {});
    await transactionsNav.click({ timeout: 15_000 }).catch(() => {});
    await page.waitForTimeout(600);
  }
}

/**
 * Navigate to Labor Accrual Batches list:
 * - Prefer direct action URL if GCC_ODOO_LABOR_ACCRUAL_ACTION_ID is set.
 * - Else Accounting → Transactions → Labor Accrual Batches (menu label may vary by locale).
 */
export async function openLaborAccrualBatches(page: Page) {
  const actionId = process.env.GCC_ODOO_LABOR_ACCRUAL_ACTION_ID?.trim();
  if (actionId) {
    await page.goto(`/web#action=${encodeURIComponent(actionId)}`, {
      waitUntil: "domcontentloaded",
    });
    await page.waitForTimeout(2500);
    const listOrKanban = page.locator(".o_list_view, .o_kanban_view").first();
    if (await listOrKanban.isVisible().catch(() => false)) {
      return;
    }
  }

  await openAccountingTransactionsArea(page);

  const batchMenu = page
    .getByRole("menuitem", {
      name: /Labor Accrual Batches|دفعات استحقاق العمالة/i,
    })
    .first();

  await batchMenu.waitFor({ state: "visible", timeout: 25_000 });
  await batchMenu.click({ timeout: 15_000 });
  await page.waitForTimeout(2000);
}

/**
 * Accounting → Transactions → **Labor Accrual (from period)** (wizard).
 * XML name: `Labor Accrual (from period)` — matches Arabic / informal "period" wording.
 */
export async function openLaborAccrualFromPeriodWizard(page: Page) {
  await openAccountingTransactionsArea(page);

  const fromPeriodMenu = page
    .getByRole("menuitem", { name: /Labor Accrual \(from period\)/i })
    .or(
      page.getByRole("menuitem", {
        name: /Labor Accrual.*from period|Labor Accrual.*Period|استحقاق.*فترة|من فترة|دفعات.*فترة/i,
      }),
    )
    .first();

  await fromPeriodMenu.waitFor({ state: "visible", timeout: 25_000 });
  await fromPeriodMenu.click({ timeout: 15_000 });
  await page.waitForTimeout(800);

  await page
    .locator('button[name="action_create_batch_and_populate_lines"]')
    .waitFor({ state: "visible", timeout: 30_000 });
}

/** Fill period on the transient wizard and click **Create batch and populate lines**. */
export async function submitLaborAccrualPeriodWizard(
  page: Page,
  periodStartIso: string,
  periodEndIso: string,
) {
  const dialog = page
    .getByRole("dialog")
    .filter({ has: page.locator('button[name="action_create_batch_and_populate_lines"]') })
    .last();

  await dialog.waitFor({ state: "visible", timeout: 20_000 });

  const startBox = dialog.getByRole("textbox", { name: /Period start/i }).first();
  const endBox = dialog.getByRole("textbox", { name: /Period end/i }).first();

  await startBox.waitFor({ state: "visible", timeout: 15_000 });
  await startBox.click();
  await startBox.fill(periodStartIso);
  await page.keyboard.press("Escape");
  await page.waitForTimeout(400);

  await endBox.fill(periodEndIso, { force: true });
  await page.keyboard.press("Escape");
  await page.waitForTimeout(300);

  await dialog.locator('button[name="action_create_batch_and_populate_lines"]').click();
}

/** Wait until labor accrual batch **form** is shown (header buttons use model methods). */
export async function waitForLaborAccrualBatchForm(page: Page) {
  await page
    .locator('button[name="action_populate_lines"]')
    .first()
    .waitFor({ state: "visible", timeout: 45_000 });
}

/** Open first row on the Labor Accrual Batches list (double-click for form). */
export async function openFirstLaborAccrualBatchFromList(page: Page) {
  const row = page.locator(".o_list_table tbody tr.o_data_row").first();
  await row.waitFor({ state: "visible", timeout: 20_000 });
  await row.dblclick();
  await waitForLaborAccrualBatchForm(page);
}

/**
 * Prefer a list row whose text matches `rowMatch` or env `GCC_ODOO_LABOR_ACCR_LIST_ROW_MATCH` (substring);
 * default `2025-09` to align with common period keys. If no match, first row.
 */
export async function openLaborAccrualBatchFromListPreferMatch(page: Page, rowMatch?: string) {
  const needle = (
    rowMatch ??
    process.env.GCC_ODOO_LABOR_ACCR_LIST_ROW_MATCH ??
    "2025-09"
  ).trim();
  const rows = page.locator(".o_list_table tbody tr.o_data_row");
  await rows.first().waitFor({ state: "visible", timeout: 25_000 });

  if (needle) {
    const matched = rows.filter({ hasText: needle }).first();
    if ((await matched.count()) > 0) {
      await matched.dblclick();
      await waitForLaborAccrualBatchForm(page);
      return;
    }
  }

  await openFirstLaborAccrualBatchFromList(page);
}

/** Close blocking Odoo **Invalid Operation** / RPC error dialog if shown. */
export async function closeOdooBlockingDialog(page: Page) {
  const dlg = page.getByRole("dialog").filter({ hasText: /Invalid Operation|عملية غير صالحة|User Error|خطأ/i });
  if (await dlg.isVisible().catch(() => false)) {
    await dlg.getByRole("button", { name: /^Close$|إغلاق|Close/i }).first().click({ timeout: 5000 }).catch(() => {});
    await page.waitForTimeout(400);
  }
}
