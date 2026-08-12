import path from "path";
import { test as setup } from "@playwright/test";
import { odooLogin } from "./helpers";

const authFile = path.join(__dirname, "../playwright/.auth/user.json");

setup("authenticate on trgcc_mm_uat", async ({ page }) => {
  await odooLogin(page);
  await page.context().storageState({ path: authFile });
});
