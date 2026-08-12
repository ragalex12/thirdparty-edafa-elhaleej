import fs from "fs";
import path from "path";
import { test, expect } from "@playwright/test";

const ROOT = path.resolve(__dirname, "../../../../docs/client_demo/gulf_mm");
const PAGE_SHOTS = path.join(ROOT, "assets/page_qa");
const FORBIDDEN = [
  /UatMm20260811/i,
  /password\s*[:=]/i,
  /Authorization:/i,
  /AWS_SECRET/i,
  /AKIA[0-9A-Z]{16}/,
  /100\.80\.138\.80/,
  /127\.0\.0\.1:\d{4,5}/,
  /session_id/i,
  /Zoom/i,
  /Bearer\s+[A-Za-z0-9\-._~+/]+=*/,
];

test.beforeAll(() => {
  fs.mkdirSync(PAGE_SHOTS, { recursive: true });
});

test("homepage loads with key sections", async ({ page }) => {
  await page.goto("index.html");
  await expect(page.locator("h1")).toContainText(/Gulf \/ MM/i);
  await expect(page.getByText("UAT PASSED")).toBeVisible();
  await expect(page.locator("#matrix")).toBeVisible();
  await expect(page.locator("#safety")).toBeVisible();
  await expect(page.getByText(/Production changes during UAT: 0/i)).toBeVisible();
  await expect(page.getByText(/READY FOR PRODUCTION DEPLOYMENT APPROVAL/i)).toBeVisible();
  await expect(page.getByText(/\bNOT DEPLOYED\b/)).toBeVisible();
  const body = await page.locator("body").innerText();
  expect(body).not.toMatch(/(?<!NOT )\bDEPLOYED\b/);
  await page.screenshot({ path: path.join(PAGE_SHOTS, "homepage_desktop.png"), fullPage: true });
  await page.locator("#matrix").scrollIntoViewIfNeeded();
  await page.screenshot({ path: path.join(PAGE_SHOTS, "request_solution_matrix.png"), fullPage: false });
  await page.locator("#status").scrollIntoViewIfNeeded();
  await page.screenshot({ path: path.join(PAGE_SHOTS, "status_block.png"), fullPage: false });
});

test("all gallery assets load and lightbox works", async ({ page }) => {
  await page.goto("index.html");
  const imgs = page.locator("img[src]");
  const count = await imgs.count();
  expect(count).toBeGreaterThan(10);
  for (let i = 0; i < count; i++) {
    const src = await imgs.nth(i).getAttribute("src");
    expect(src).toBeTruthy();
    const abs = path.join(ROOT, src!);
    expect(fs.existsSync(abs), `missing asset ${src}`).toBeTruthy();
  }
  const first = page.locator("[data-lightbox]").first();
  await first.click();
  await expect(page.locator("#lightbox.open")).toBeVisible();
  await page.screenshot({ path: path.join(PAGE_SHOTS, "lightbox_open.png"), fullPage: false });
  await page.locator("[data-close]").click();
  await expect(page.locator("#lightbox.open")).toHaveCount(0);
});

test("mobile viewport and no horizontal overflow", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("index.html");
  const overflow = await page.evaluate(() => {
    return document.documentElement.scrollWidth > document.documentElement.clientWidth + 2;
  });
  expect(overflow).toBe(false);
  await expect(page.locator(".badge").first()).toBeVisible();
  await page.screenshot({ path: path.join(PAGE_SHOTS, "homepage_mobile.png"), fullPage: true });
});

test("no forbidden secrets in page text", async ({ page }) => {
  await page.goto("index.html");
  const text = await page.locator("body").innerText();
  const html = await page.content();
  for (const re of FORBIDDEN) {
    expect(text).not.toMatch(re);
    expect(html).not.toMatch(re);
  }
  expect(text).not.toMatch(/trgcc(?!_mm_uat)/);
});

test("navigation anchors work", async ({ page }) => {
  await page.goto("index.html");
  await page.locator('.nav-links a[href="#matrix"]').click();
  await expect(page.locator("#matrix")).toBeInViewport();
});
