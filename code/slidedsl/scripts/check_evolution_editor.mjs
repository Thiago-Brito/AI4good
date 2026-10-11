import { chromium } from "../editor/node_modules/playwright/index.mjs";
import fs from "node:fs/promises";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "..");
const info = JSON.parse(await fs.readFile(path.join(root, "outputs/evolution/ui_generation.json"), "utf8"));
const browser = await chromium.launch({ headless: true, executablePath: process.env.SLIDEDSL_BROWSER ?? "C:/Program Files/Google/Chrome/Application/chrome.exe" });
const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
try {
  await page.goto("http://127.0.0.1:8000");
  await page.getByRole("heading", { name: "Gerar com IA local", exact: true }).waitFor();
  await page.getByLabel("Modelo local").selectOption("qwen3:4b-instruct");
  await page.getByLabel("Abrir arquivo .sld").setInputFiles(path.join(root, info.path, "presentation.sld"));
  await page.getByRole("status").filter({ hasText: "Arquivo importado." }).waitFor();
  const buttons = page.locator(".slides-panel").getByRole("button");
  for (let n = 1; n <= 5; n++) {
    await buttons.filter({ hasText: String(n).padStart(2, "0") }).first().click();
    await page.getByTestId("preview").screenshot({ path: path.join(root, "outputs/evolution", `production_preview_${n}.png`) });
  }
  await page.screenshot({ path: path.join(root, "outputs/evolution/production_editor.png"), fullPage: true });
  if (errors.length) throw new Error(JSON.stringify(errors));
  const result = { url: page.url(), source: info.path, slides: 5, javascript_errors: errors, model_selector: true, generation_form: true };
  await fs.writeFile(path.join(root, "outputs/evolution/production_editor_check.json"), JSON.stringify(result, null, 2));
  process.stdout.write(JSON.stringify(result));
} finally { await browser.close(); }
