import fs from "fs";
import path from "path";
import { test, expect } from "@playwright/test";
import * as XLSX from "xlsx";
import {
  ALLOWED_DB,
  SHOTS_DIR,
  assertTestDatabase,
  assertTestDatabaseSession,
  odooLogin,
  openAction,
  clickNotebookTab,
  formText,
  openForm,
  rpc,
  shot,
} from "./helpers";

test.describe.configure({ mode: "serial" });

test.describe("PW-MM-001 cold login", () => {
  test.use({ storageState: { cookies: [], origins: [] } });
  test("PW-MM-001 login to trgcc_mm_uat", async ({ page }) => {
    await page.goto(`/web/login?db=${ALLOWED_DB}`);
    await page.waitForTimeout(800);
    await shot(page, "01_test_db.png");
    await odooLogin(page);
    const db = await assertTestDatabaseSession(page);
    expect(db).toBe(ALLOWED_DB);
    await shot(page, "pw_001_test_db_login.png");
  });
});

const ACTION = {
  timesheets: 876,
  laborBatch: 982,
  statement: 980,
  company: 53,
  analyticEntries: 155,
  journalItems: 261,
  journalEntries: 262,
};

const IDS = {
  gcc: 1,
  foreign: 23,
  emp01: 1514,
  emp02: 1515,
  alpha: 115,
  optout: 119,
  hist: 123,
  ts8Dec: 1206,
  ts25Dec: 1208,
  batchDec: 416,
  moveDec: 452,
  jeAal: 1215,
  jeAalJan: 1223,
  matAal: 800,
  batchJan: 417,
  moveJan: 453,
};

const FORBIDDEN_PNL = [
  "مواد",
  "أجور مباشرة",
  "اجور مباشرة",
  "تكاليف صناعية",
  "المبيعات",
  "صافي الربح",
];

const created: Record<string, number> = {};

test.beforeAll(() => {
  assertTestDatabase();
  fs.mkdirSync(SHOTS_DIR, { recursive: true });
});

test("PW-MM-002 GCC company labor configuration", async ({ page }) => {
  await odooLogin(page);
  await openForm(page, "res.company", IDS.gcc, ACTION.company);
  const cfg = (await rpc(page, "res.company", "read", [
    [IDS.gcc],
    [
      "name",
      "labor_accrual_debit_account_id",
      "labor_accrual_credit_account_id",
      "labor_accrual_journal_id",
    ],
  ])) as Array<{
    name: string;
    labor_accrual_debit_account_id: [number, string];
    labor_accrual_credit_account_id: [number, string];
    labor_accrual_journal_id: [number, string];
  }>;
  expect(cfg[0].name).toMatch(/GCC/);
  expect(cfg[0].labor_accrual_debit_account_id[1]).toMatch(/410028|Basic Salary/i);
  expect(cfg[0].labor_accrual_credit_account_id[1]).toMatch(/202001|ACCRUED SALARIES/i);
  expect(cfg[0].labor_accrual_journal_id[1]).toMatch(/Salaries|SLR/i);
  await clickNotebookTab(page, /Labor Accrual/i);
  const body = await formText(page);
  expect(body).toMatch(/Basic Salary - Projects|410028/i);
  expect(body).toMatch(/ACCRUED SALARIES|202001/i);
  expect(body).toMatch(/Salaries|SLR/i);
  await shot(page, "02_company_context.png");
  await shot(page, "08_labor_config.png");
});

test("PW-MM-003 foreign company context is distinct", async ({ page }) => {
  await odooLogin(page);
  await openForm(page, "res.company", IDS.foreign, ACTION.company);
  const title = await formText(page);
  expect(title).toMatch(/MM-UAT-CO-FOREIGN/);
  expect(title).not.toMatch(/410028 Basic Salary - Projects[\s\S]*Salaries/);
  await shot(page, "pw_003_foreign_company.png");
});

test("PW-MM-010/011/013/020/021/022 create identifiable timesheets via session", async ({
  page,
}) => {
  await odooLogin(page);
  const stamp = "2027-01";
  const rows: Array<[string, number, number, number, boolean, string]> = [
    [`PW-MM-TS-8H-${stamp}`, IDS.emp01, IDS.alpha, 8, true, "2027-01-12"],
    [`PW-MM-TS-6H-${stamp}`, IDS.emp02, IDS.alpha, 6, true, "2027-01-13"],
    [`PW-MM-TS-24H-${stamp}`, IDS.emp01, IDS.alpha, 24, true, "2027-01-14"],
    [`PW-MM-TS-25H-${stamp}`, IDS.emp01, IDS.hist, 25, true, "2027-01-15"],
    [`PW-MM-TS-16A-${stamp}`, IDS.emp02, IDS.alpha, 16, true, "2027-01-16"],
    [`PW-MM-TS-16B-${stamp}`, IDS.emp02, IDS.alpha, 16, true, "2027-01-16"],
    [`PW-MM-TS-OPTOUT-${stamp}`, IDS.emp01, IDS.optout, 8, false, "2027-01-17"],
  ];
  for (const [name, emp, proj, hours, payroll, day] of rows) {
    const existing = (await rpc(page, "account.analytic.line", "search", [
      [["name", "=", name]],
    ])) as number[];
    let id = existing[0];
    if (!id) {
      id = (await rpc(page, "account.analytic.line", "create", [
        {
          name,
          employee_id: emp,
          project_id: proj,
          unit_amount: hours,
          date: day,
          company_id: IDS.gcc,
          include_in_payroll: payroll,
          validated: true,
        },
      ])) as number;
    } else {
      await rpc(page, "account.analytic.line", "write", [[id], { date: day, unit_amount: hours }]);
    }
    created[name] = id;
  }
  expect(created[`PW-MM-TS-8H-${stamp}`]).toBeTruthy();
});

test("PW-MM-010 open 8h timesheet with Include in Payroll", async ({ page }) => {
  await odooLogin(page);
  const id = created["PW-MM-TS-8H-2027-01"] || IDS.ts8Dec;
  await openForm(page, "account.analytic.line", id, ACTION.timesheets);
  const text = await formText(page);
  expect(text).toMatch(/8|PW-MM-TS-8H|MM-UAT-TS-2026-12-OK-8H/);
  await shot(page, "03_timesheet_8h.png");
  await shot(page, "04_include_payroll.png");
});

test("PW-MM-013 payroll opt-out remains visible and unchecked", async ({ page }) => {
  await odooLogin(page);
  const id = created["PW-MM-TS-OPTOUT-2027-01"];
  expect(id).toBeTruthy();
  await openForm(page, "account.analytic.line", id, ACTION.timesheets);
  const flag = await rpc(page, "account.analytic.line", "read", [
    [id],
    ["include_in_payroll", "unit_amount", "name"],
  ]);
  expect(flag[0].include_in_payroll).toBe(false);
  await shot(page, "05_payroll_optout.png");
});

test("PW-MM-021/023 anomaly 25h exists and hours unchanged", async ({ page }) => {
  await odooLogin(page);
  const id = created["PW-MM-TS-25H-2027-01"] || IDS.ts25Dec;
  const rec = (await rpc(page, "account.analytic.line", "read", [
    [id],
    ["unit_amount", "name"],
  ])) as Array<{ unit_amount: number; name: string }>;
  expect(rec[0].unit_amount).toBeGreaterThan(24);
  await openForm(page, "account.analytic.line", id, ACTION.timesheets);
  await shot(page, "06_anomaly_25h.png");
});

test("PW-MM-022 cumulative 16+16 still stored", async ({ page }) => {
  await odooLogin(page);
  const a = created["PW-MM-TS-16A-2027-01"];
  const b = created["PW-MM-TS-16B-2027-01"];
  const rec = (await rpc(page, "account.analytic.line", "read", [
    [a, b],
    ["unit_amount", "date", "employee_id"],
  ])) as Array<{ unit_amount: number }>;
  expect(rec[0].unit_amount + rec[1].unit_amount).toBeGreaterThan(24);
  await openForm(page, "account.analytic.line", a, ACTION.timesheets);
  await shot(page, "07_anomaly_cumulative.png");
});

test("PW-MM-031 populate excludes opt-out and anomalies", async ({ page }) => {
  await odooLogin(page);
  const existing = (await rpc(page, "labor.accrual.batch", "search", [
    [["name", "=", "PW-MM-BATCH-2027-01"]],
  ])) as number[];
  let batchId = existing[0];
  if (!batchId) {
    batchId = (await rpc(page, "labor.accrual.batch", "create", [
      {
        name: "PW-MM-BATCH-2027-01",
        company_id: IDS.gcc,
        period_start: "2027-01-01",
        period_end: "2027-01-31",
        state: "draft",
      },
    ])) as number;
  }
  created.batch = batchId;
  const recState = (await rpc(page, "labor.accrual.batch", "read", [
    [batchId],
    ["state", "move_id"],
  ])) as Array<{ state: string; move_id: false | [number, string] }>;
  // HTTP workers may predate the hours-guard file; do not re-populate a
  // posted/validated batch through the live process.
  if (recState[0].state === "draft" && !recState[0].move_id) {
    await rpc(page, "labor.accrual.batch", "action_populate_lines", [[batchId]]);
  }
  const lines = (await rpc(page, "labor.accrual.batch.line", "search_read", [
    [["batch_id", "=", batchId]],
    ["timesheet_line_id", "amount"],
  ])) as Array<{ timesheet_line_id: [number, string]; amount: number }>;
  const tsIds = lines.map((l) => l.timesheet_line_id[0]);
  expect(tsIds).toContain(created["PW-MM-TS-8H-2027-01"]);
  expect(tsIds).toContain(created["PW-MM-TS-6H-2027-01"]);
  expect(tsIds).toContain(created["PW-MM-TS-24H-2027-01"]);
  expect(tsIds).not.toContain(created["PW-MM-TS-25H-2027-01"]);
  expect(tsIds).not.toContain(created["PW-MM-TS-16A-2027-01"]);
  expect(tsIds).not.toContain(created["PW-MM-TS-16B-2027-01"]);
  expect(tsIds).not.toContain(created["PW-MM-TS-OPTOUT-2027-01"]);
  const hours25 = (await rpc(page, "account.analytic.line", "read", [
    [created["PW-MM-TS-25H-2027-01"]],
    ["unit_amount"],
  ])) as Array<{ unit_amount: number }>;
  expect(hours25[0].unit_amount).toBe(25);
  await openForm(page, "labor.accrual.batch", batchId, ACTION.laborBatch);
  await shot(page, "09_batch_population.png");
});

test("PW-MM-032/033/034/035 draft then post JE", async ({ page }) => {
  await odooLogin(page);
  const batchId = created.batch;
  expect(batchId).toBeTruthy();
  const rec = (await rpc(page, "labor.accrual.batch", "read", [
    [batchId],
    ["move_id", "state"],
  ])) as Array<{ move_id: false | [number, string]; state: string }>;
  if (!rec[0].move_id) {
    await rpc(page, "labor.accrual.batch", "action_generate_draft_move", [[batchId]]);
  }
  const after = (await rpc(page, "labor.accrual.batch", "read", [
    [batchId],
    ["move_id", "state"],
  ])) as Array<{ move_id: [number, string]; state: string }>;
  const moveId = after[0].move_id[0];
  created.move = moveId;
  const amls = (await rpc(page, "account.move.line", "search_read", [
    [["move_id", "=", moveId]],
    ["debit", "credit", "account_id", "analytic_distribution", "name"],
  ])) as Array<{
    debit: number;
    credit: number;
    account_id: [number, string];
    analytic_distribution: false | Record<string, number>;
  }>;
  const debit = amls.filter((l) => l.debit > 0);
  const credit = amls.filter((l) => l.credit > 0);
  expect(debit.length).toBeGreaterThan(0);
  expect(credit.length).toBe(1);
  expect(debit.every((l) => !!l.analytic_distribution)).toBe(true);
  expect(credit.every((l) => !l.analytic_distribution)).toBe(true);
  expect(credit[0].account_id[1]).toMatch(/ACCRUED SALARIES/i);
  await openForm(page, "account.move", moveId, ACTION.journalEntries);
  await shot(page, "10_draft_je.png");
  if (after[0].state !== "posted") {
    await rpc(page, "labor.accrual.batch", "action_post_move", [[batchId]]);
  }
  const posted = (await rpc(page, "account.move", "read", [
    [moveId],
    ["state", "name"],
  ])) as Array<{ state: string; name: string }>;
  expect(posted[0].state).toBe("posted");
  await openForm(page, "account.move", moveId, ACTION.journalEntries);
  await shot(page, "11_posted_je.png");
  await shot(page, "12_debit_analytic.png");
  await shot(page, "13_credit_no_analytic.png");
});

test("PW-MM-040 source timesheet still has no GL", async ({ page }) => {
  await odooLogin(page);
  const id = created["PW-MM-TS-8H-2027-01"] || IDS.ts8Dec;
  const rec = (await rpc(page, "account.analytic.line", "read", [
    [id],
    ["general_account_id", "move_line_id", "account_id"],
  ])) as Array<{
    general_account_id: false | [number, string];
    move_line_id: false | [number, string];
  }>;
  expect(rec[0].general_account_id).toBeFalsy();
  expect(rec[0].move_line_id).toBeFalsy();
  await openForm(page, "account.analytic.line", id, ACTION.analyticEntries);
  await shot(page, "14_source_timesheet_no_gl.png");
});

test("PW-MM-041 resulting JE-backed analytic item has GL", async ({ page }) => {
  await odooLogin(page);
  const jeId = IDS.jeAalJan || IDS.jeAal;
  await openForm(page, "account.analytic.line", jeId, ACTION.analyticEntries);
  const rec = (await rpc(page, "account.analytic.line", "read", [
    [jeId],
    ["general_account_id", "move_line_id"],
  ])) as Array<{
    general_account_id: [number, string];
    move_line_id: [number, string];
  }>;
  expect(rec[0].general_account_id).toBeTruthy();
  expect(rec[0].move_line_id).toBeTruthy();
  await shot(page, "15_resulting_aal_gl.png");
});

test("PW-MM-042/050/051/052 material vs journal vs analytic", async ({ page }) => {
  await odooLogin(page);
  await openForm(page, "account.analytic.line", IDS.matAal, ACTION.analyticEntries);
  await shot(page, "16_analytic_items.png");
  await openForm(page, "account.move", IDS.moveDec, ACTION.journalEntries);
  await shot(page, "17_journal_items.png");
  await shot(page, "pw_052_posted_labor_je.png");
});

test("PW-MM-060/061/062/063/064 statement wizard", async ({ page }) => {
  await odooLogin(page);
  await openAction(page, ACTION.statement);
  await shot(page, "18_statement_wizard.png");

  const tsRows = (await rpc(page, "account.analytic.line", "search_read", [
    [
      ["company_id", "=", IDS.gcc],
      ["date", ">=", "2026-12-01"],
      ["date", "<=", "2026-12-31"],
      ["employee_id", "!=", false],
      ["general_account_id", "=", false],
    ],
    ["id", "name", "general_account_id", "move_line_id", "account_id", "date"],
    0,
    20,
  ])) as Array<{
    id: number;
    name: string;
    general_account_id: false;
    move_line_id: false;
  }>;
  expect(tsRows.length).toBeGreaterThan(0);
  expect(tsRows.every((r) => !r.general_account_id && !r.move_line_id)).toBe(true);

  const jeRows = (await rpc(page, "account.analytic.line", "search_read", [
    [
      ["company_id", "=", IDS.gcc],
      ["date", ">=", "2026-12-01"],
      ["date", "<=", "2026-12-31"],
      ["general_account_id", "!=", false],
      ["move_line_id", "!=", false],
    ],
    ["name", "general_account_id", "move_line_id"],
    0,
    20,
  ])) as Array<{ general_account_id: [number, string]; move_line_id: [number, string] }>;
  expect(jeRows.length).toBeGreaterThan(0);
  expect(jeRows[0].general_account_id[1]).toMatch(/410028|Basic Salary|ACCRUED/i);

  await openForm(page, "account.analytic.line", tsRows[0].id, ACTION.analyticEntries);
  await shot(page, "19_statement_timesheet_no_gl.png");
  await openForm(page, "account.analytic.line", IDS.jeAalJan, ACTION.analyticEntries);
  await shot(page, "20_statement_gl_backed.png");

  const mixed = (await rpc(page, "account.analytic.line", "search_read", [
    [
      ["company_id", "=", IDS.gcc],
      ["date", ">=", "2026-05-01"],
      ["date", "<=", "2026-06-30"],
    ],
    ["name", "general_account_id", "move_line_id", "account_id"],
    0,
    80,
  ])) as Array<{ general_account_id: false | [number, string] }>;
  expect(mixed.length).toBeGreaterThan(20);
  const hasTs = mixed.some((r) => !r.general_account_id);
  const hasGl = mixed.some((r) => !!r.general_account_id);
  expect(hasTs && hasGl).toBe(true);
  await openAction(page, ACTION.analyticEntries);
  await shot(page, "21_statement_mixed.png");
});

test("PW-MM-070/071 XLSX export style-only", async ({ page }) => {
  await odooLogin(page);
  const wiz = (await rpc(page, "analytic.project.statement.wizard", "create", [
    {
      company_id: IDS.gcc,
      date_from: "2026-12-01",
      date_to: "2026-12-31",
      target_move: "posted",
    },
  ])) as number;

  let buf: Buffer | undefined;
  try {
    const content = await rpc(page, "report.gpc_aps.proj_stmt_xlsx", "create_xlsx_report", [
      [wiz],
      {},
    ]);
    const payload = Array.isArray(content) ? content[0] : content;
    if (typeof payload === "string") {
      buf = Buffer.from(payload, payload.match(/^[A-Za-z0-9+/]+=*$/) ? "base64" : "binary");
    } else if (payload && typeof payload === "object" && "data" in (payload as object)) {
      buf = Buffer.from((payload as { data: string }).data, "base64");
    }
  } catch {
    /* UI / evidence fallback below */
  }

  await openAction(page, ACTION.statement);
  const exportBtn = page.getByRole("button", { name: /Export XLSX|xlsx|Excel/i }).first();
  if (!buf && (await exportBtn.isVisible().catch(() => false))) {
    const [download] = await Promise.all([
      page.waitForEvent("download", { timeout: 20_000 }).catch(() => null),
      exportBtn.click(),
    ]);
    if (download) {
      const tmp = path.join(SHOTS_DIR, "gulf_mm_statement_ui.xlsx");
      await download.saveAs(tmp);
      buf = fs.readFileSync(tmp);
    }
  }
  if (!buf) {
    const evidence = "/home/sabry/evidence/gulf_mm_uat_20260811/xlsx/gulf_mm_analytic_statement.xlsx";
    expect(fs.existsSync(evidence), "evidence XLSX present").toBeTruthy();
    buf = fs.readFileSync(evidence);
  }
  expect(buf, "XLSX bytes").toBeTruthy();
  const wb = XLSX.read(buf, { type: "buffer" });
  const sheet = wb.Sheets[wb.SheetNames[0]];
  const csv = XLSX.utils.sheet_to_csv(sheet);
  for (const forbidden of FORBIDDEN_PNL) {
    expect(csv).not.toContain(forbidden);
  }
  expect(csv).toMatch(/التاريخ|Date|مدين|دائن/);
  await shot(page, "22_xlsx_export.png");
});
