import fs from "fs";
import path from "path";
import { expect, type Page } from "@playwright/test";

export const ALLOWED_DB = "trgcc_mm_uat";
export const FORBIDDEN_DBS = new Set(["trgcc", "entgcc"]);

export const SHOTS_DIR = path.resolve(
  __dirname,
  "../../../../docs/client_demo/gulf_mm/assets/playwright",
);

export function gulfEnv() {
  const baseURL = (
    process.env.GULF_MM_BASE_URL ||
    process.env.GCC_ODOO_WEB_URL ||
    ""
  ).replace(/\/$/, "");
  const db = (process.env.GULF_MM_DB || process.env.GCC_ODOO_DB || "").trim();
  const user = (process.env.GULF_MM_USER || process.env.GCC_ODOO_LOGIN || "").trim();
  const password = (
    process.env.GULF_MM_PASSWORD ||
    process.env.GCC_ODOO_PASSWORD ||
    ""
  ).trim();
  return { baseURL, db, user, password };
}

/** Hard abort before any browser work if env points at production. */
export function assertTestDatabase(): void {
  const { db, baseURL } = gulfEnv();
  if (!db) {
    throw new Error("ABORT: GULF_MM_DB is required and must be trgcc_mm_uat");
  }
  if (FORBIDDEN_DBS.has(db) || db !== ALLOWED_DB) {
    throw new Error(
      `ABORT: refusing database ${JSON.stringify(db)}. This suite runs only on ${ALLOWED_DB}.`,
    );
  }
  const lowered = baseURL.toLowerCase();
  if (lowered.includes("db=trgcc") && !lowered.includes("trgcc_mm_uat")) {
    throw new Error("ABORT: base URL looks like production trgcc");
  }
}

export async function assertTestDatabaseSession(page: Page): Promise<string> {
  const resp = await page.request.post("/web/session/get_session_info", {
    data: { jsonrpc: "2.0", method: "call", id: Date.now(), params: {} },
    headers: { "Content-Type": "application/json" },
  });
  const body = await resp.json();
  const db = body?.result?.db;
  if (db !== ALLOWED_DB) {
    throw new Error(
      `ABORT: session database is ${JSON.stringify(db)}, expected ${ALLOWED_DB}`,
    );
  }
  return db;
}

export async function odooLogin(page: Page): Promise<void> {
  assertTestDatabase();
  const { db, user, password } = gulfEnv();
  if (!user || !password) {
    throw new Error("ABORT: GULF_MM_USER / GULF_MM_PASSWORD required (not committed)");
  }
  try {
    await page.goto("/web", { waitUntil: "domcontentloaded" });
    if (await page.locator("body.o_web_client").isVisible().catch(() => false)) {
      const sessionDb = await assertTestDatabaseSession(page);
      if (sessionDb === ALLOWED_DB) {
        return;
      }
    }
  } catch {
    /* fall through to explicit login */
  }
  await page.goto(`/web/login?db=${encodeURIComponent(db)}`);
  await page
    .locator('input[placeholder="Enter your email"], input[name="login"]:not([readonly])')
    .first()
    .fill(user);
  await page.locator('input[type="password"]').first().fill(password);
  await page.getByRole("button", { name: /Log in|Sign in/i }).click();
  await expect(page.locator("body.o_web_client")).toBeVisible({
    timeout: 90_000,
  });
  await assertTestDatabaseSession(page);
}

export async function sanitizeUi(page: Page): Promise<void> {
  await page.addStyleTag({
    content: `
      .o_user_menu, .o_MessagingMenu, .o_mail_systray_item,
      .o_notification_manager, .o_debug_manager, .o_activity_menu,
      .o-mail-Chatter, .o_FormRenderer_chatter, .o-mail-Form-chatter {
        visibility: hidden !important;
      }
    `,
  }).catch(() => undefined);
}

export async function shot(page: Page, filename: string): Promise<string> {
  fs.mkdirSync(SHOTS_DIR, { recursive: true });
  await sanitizeUi(page);
  const dest = path.join(SHOTS_DIR, filename);
  const content = page.locator(".o_form_view, .o_list_view, .o_content, body").first();
  if (await content.count().catch(() => 0)) {
    await page.screenshot({ path: dest, fullPage: false });
  } else {
    await page.screenshot({ path: dest, fullPage: false });
  }
  return dest;
}

export async function formText(page: Page): Promise<string> {
  await page.locator(".o_form_view").first().waitFor({ timeout: 30_000 });
  return page.locator(".o_form_view").first().evaluate((el) => {
    const typed = Array.from(el.querySelectorAll("input, textarea, select"))
      .map((n) => (n as HTMLInputElement).value || "")
      .join(" ");
    return `${(el as HTMLElement).innerText}\n${typed}`;
  });
}

export async function clickNotebookTab(page: Page, name: RegExp | string): Promise<void> {
  const tab = page
    .locator(".o_notebook_headers a, .nav-link, [role='tab']")
    .filter({ hasText: name })
    .first();
  await tab.waitFor({ timeout: 15_000 });
  await tab.click();
  await page.waitForTimeout(600);
}

export async function rpc(
  page: Page,
  model: string,
  method: string,
  args: unknown[] = [],
  kwargs: Record<string, unknown> = {},
): Promise<unknown> {
  const resp = await page.request.post(`/web/dataset/call_kw/${model}/${method}`, {
    data: {
      jsonrpc: "2.0",
      method: "call",
      id: Date.now(),
      params: { model, method, args, kwargs },
    },
    headers: { "Content-Type": "application/json" },
  });
  const body = await resp.json();
  if (body.error) {
    const msg =
      body.error.data?.message || body.error.message || JSON.stringify(body.error);
    throw new Error(`${model}.${method}: ${msg}`);
  }
  return body.result;
}

export async function openForm(
  page: Page,
  model: string,
  id: number,
  action?: number,
): Promise<void> {
  const hash = action
    ? `/web#action=${action}&id=${id}&model=${model}&view_type=form`
    : `/web#id=${id}&model=${model}&view_type=form`;
  await page.goto(hash, { waitUntil: "domcontentloaded" });
  await page.locator(".o_form_view, .o_list_view, .o_kanban_view").first().waitFor({
    timeout: 30_000,
  });
  await page.waitForTimeout(800);
}

export async function openAction(page: Page, actionId: number): Promise<void> {
  await page.goto(`/web#action=${actionId}`, { waitUntil: "domcontentloaded" });
  await page
    .locator(".o_form_view, .o_list_view, .o_kanban_view, .o_dialog, .o_technical_modal")
    .first()
    .waitFor({ timeout: 45_000 })
    .catch(() => undefined);
  await page.waitForTimeout(1500);
}
