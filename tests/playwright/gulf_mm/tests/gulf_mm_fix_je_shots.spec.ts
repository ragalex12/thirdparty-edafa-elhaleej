import fs from "fs";
import path from "path";
import { test } from "@playwright/test";
import { SHOTS_DIR, odooLogin, openForm, sanitizeUi } from "./helpers";

const HTML = `/home/sabry/evidence/gulf_mm_uat_20260811/gulf_mm_statement_rows.html`;

test("capture draft JE move 399", async ({ page }) => {
  await odooLogin(page);
  await openForm(page, "account.move", 399, 262);
  await page.addStyleTag({
    content: `.o-mail-Chatter, .o_FormRenderer_chatter, .o-mail-Form-chatter { display:none !important; }`,
  });
  await sanitizeUi(page);
  await page.locator(".o_form_view").first().waitFor();
  await page.locator(".o_form_view").first().screenshot({
    path: path.join(SHOTS_DIR, "10_draft_je.png"),
  });
});

test("capture debit and credit row crops", async ({ page }) => {
  await odooLogin(page);
  await openForm(page, "account.move", 453, 262);
  await page.addStyleTag({
    content: `.o-mail-Chatter, .o_FormRenderer_chatter, .o-mail-Form-chatter { display:none !important; }`,
  });
  await sanitizeUi(page);
  const debit = page.locator(".o_data_row").filter({ hasText: /410028|Basic Salary/i }).first();
  const credit = page.locator(".o_data_row").filter({ hasText: /202001|ACCRUED/i }).first();
  await debit.waitFor();
  await credit.waitFor();
  await debit.screenshot({ path: path.join(SHOTS_DIR, "12_debit_analytic.png") });
  await credit.screenshot({ path: path.join(SHOTS_DIR, "13_credit_no_analytic.png") });
  await page.locator(".o_form_view").first().screenshot({
    path: path.join(SHOTS_DIR, "11_posted_je.png"),
  });
});

test("render distinct statement row proofs from HTML", async ({ page }) => {
  const html = fs.readFileSync(HTML, "utf8");
  const onlyTs = html
    .replace(/<tr class="je">[\s\S]*?<\/tr>/g, "")
    .replace(
      "<h1>",
      "<h1>Timesheet / no GL rows — ",
    );
  const onlyJe = html
    .replace(/<tr class="timesheet-nogl">[\s\S]*?<\/tr>/g, "")
    .replace(
      "<h1>",
      "<h1>GL-backed labor JE rows — ",
    );
  await page.setContent(onlyTs, { waitUntil: "domcontentloaded" });
  await page.screenshot({
    path: path.join(SHOTS_DIR, "19_statement_timesheet_no_gl.png"),
    fullPage: true,
  });
  await page.setContent(onlyJe, { waitUntil: "domcontentloaded" });
  await page.screenshot({
    path: path.join(SHOTS_DIR, "20_statement_gl_backed.png"),
    fullPage: true,
  });
  await page.setContent(html, { waitUntil: "domcontentloaded" });
  await page.screenshot({
    path: path.join(SHOTS_DIR, "21_statement_mixed.png"),
    fullPage: true,
  });
});
