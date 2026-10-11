import { chromium } from "../editor/node_modules/playwright/index.mjs";
import fs from "node:fs/promises";
import path from "node:path";

const [before, after, output] = process.argv.slice(2);
if (!before || !after || !output) throw new Error("Informe pastas antes, depois e saída.");
await fs.mkdir(output, { recursive: false });
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.SLIDEDSL_BROWSER ?? "C:/Program Files/Google/Chrome/Application/chrome.exe",
});
const page = await browser.newPage({ viewport: { width: 1600, height: 1100 } });
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
try {
  for (const [label, folder] of [["before", before], ["after", after]]) {
    await page.goto("http://127.0.0.1:8000");
    const source = path.resolve(folder, "presentation.sld");
    await page.getByLabel("Abrir arquivo .sld").setInputFiles(source);
    await page.getByRole("status").filter({ hasText: "Arquivo importado." }).waitFor();
    await page.addStyleTag({ content: ".preview-element.selected { outline: none !important; }" });
    if ((await page.getByLabel("Programa SlideDSL").inputValue()).replaceAll("\r\n", "\n") !== (await fs.readFile(source, "utf8")).replaceAll("\r\n", "\n")) {
      throw new Error("A fonte exibida diverge da geração.");
    }
    for (let n = 1; n <= 5; n++) {
      await page.locator(".slides-panel").getByRole("button").filter({ hasText: String(n).padStart(2, "0") }).first().click();
      await page.getByTestId("preview").screenshot({ path: path.join(output, `${label}_${n}.png`) });
    }
    await page.screenshot({ path: path.join(output, `${label}_editor.png`), fullPage: true });
  }
  if (errors.length) throw new Error(JSON.stringify(errors));
  let html = '<!doctype html><meta charset="utf-8"><title>SlideDSL: antes e depois</title><style>body{font:18px Arial;background:#edf1f5;margin:32px}section{display:grid;grid-template-columns:1fr 1fr;gap:24px;margin:32px 0}img{width:100%;border:1px solid #ccd}h1{font-size:28px}</style><h1>Pedido de arquitetura: antes e depois</h1><p>Capturas do preview geométrico do editor. Não são renderizações Office nem avaliação estética com participantes.</p>';
  for (let n = 1; n <= 5; n++) {
    html += `<section>`;
    for (const label of ["before", "after"]) {
      const png = await fs.readFile(path.join(output, `${label}_${n}.png`));
      html += `<div><p>${label === "before" ? "Antes" : "Depois"} · slide ${n}</p><img src="data:image/png;base64,${png.toString("base64")}"></div>`;
    }
    html += "</section>";
  }
  await fs.writeFile(path.join(output, "comparison.html"), html);
  await fs.writeFile(path.join(output, "capture.json"), JSON.stringify({ before, after, javascript_errors: errors, slides: 5, rendering: "geometric editor preview", source_equal: true, selection_outline_hidden: true }, null, 2));
} finally { await browser.close(); }
