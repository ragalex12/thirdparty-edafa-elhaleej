import * as fs from "fs";
import * as path from "path";

export function loadSeed() {
  const p = path.join(__dirname, "..", ".playwright-seed.json");
  return JSON.parse(fs.readFileSync(p, "utf-8")) as {
    employee_id: number;
    payslip_id?: number;
    structure_id: number;
    expected_net: number;
  };
}
