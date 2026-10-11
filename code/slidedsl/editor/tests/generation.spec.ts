import { test, expect } from "@playwright/test";
import fs from "node:fs/promises";
import path from "node:path";

test("gera pelo formulário com SLM real, edita e exporta PowerPoint", async ({
  page,
  request,
}) => {
  test.skip(
    process.env.SLIDEDSL_TEST_LOCAL_GENERATION !== "1",
    "Habilite explicitamente a geração real local.",
  );
  test.setTimeout(240000);
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await expect(page.getByLabel("Modelo local")).toHaveValue(
    "qwen3:4b-instruct",
  );
  await page
    .getByLabel("Pedido da apresentação")
    .fill(
      "Crie uma apresentação de cinco slides sobre arquitetura de software, contendo introdução, componentes, comparação, vantagens e conclusão.",
    );
  await page.getByLabel("Estratégia de geração").selectOption("D");
  const submitted = page.waitForResponse(
    (r) =>
      r.url().endsWith("/api/generations") && r.request().method() === "POST",
  );
  await page
    .getByRole("button", { name: "Gerar apresentação", exact: true })
    .click();
  const id = (await (await submitted).json()).id;
  await expect(page.getByRole("status")).toHaveText(
    "Apresentação da IA carregada. Revise os requisitos e o conteúdo.",
    { timeout: 180000 },
  );
  const job = await (
    await request.get("http://127.0.0.1:8000/api/generations/" + id)
  ).json();
  expect(job.result.report.is_mock).toBe(false);
  expect(job.result.report.compile_success).toBe(true);
  expect(job.result.ir.slides).toHaveLength(5);
  expect(
    job.events.some((e: { stage: string }) => e.stage === "validation"),
  ).toBe(true);
  const folder = path.resolve("..", job.result.path);
  const original = await fs.readFile(
    path.join(folder, "presentation.sld"),
    "utf8",
  );
  expect(
    (await page.getByLabel("Programa SlideDSL").inputValue()).replaceAll(
      "\r\n",
      "\n",
    ),
  ).toBe(original.replaceAll("\r\n", "\n"));
  const title = job.result.ir.slides[0].elements.find(
    (e: { role: string }) => e.role === "titulo",
  );
  await page
    .getByRole("button", { name: `Selecionar ${title.id}`, exact: true })
    .click();
  await page
    .getByLabel("Texto", { exact: true })
    .fill("Arquitetura revisada no editor");
  await page.getByRole("button", { name: "Validar", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("válido");
  const dslDownload = page.waitForEvent("download");
  await page.getByRole("button", { name: "Exportar DSL", exact: true }).click();
  const modified = await fs.readFile(
    (await (await dslDownload).path())!,
    "utf8",
  );
  expect(modified).toContain("Arquitetura revisada no editor");
  await fs.writeFile(path.join(folder, "editor_modified.sld"), modified);
  const pptxDownload = page.waitForEvent("download");
  await page.getByRole("button", { name: "Gerar PPTX", exact: true }).click();
  const bytes = await fs.readFile((await (await pptxDownload).path())!);
  expect(bytes.subarray(0, 2).toString()).toBe("PK");
  await fs.writeFile(path.join(folder, "editor_modified.pptx"), bytes);
  await page.screenshot({
    path: path.join(folder, "editor.png"),
    fullPage: true,
  });
  for (let n = 1; n <= 5; n++) {
    await page
      .locator(".slides-panel")
      .getByRole("button")
      .filter({ hasText: String(n).padStart(2, "0") })
      .first()
      .click();
    await page
      .getByTestId("preview")
      .screenshot({ path: path.join(folder, `preview_${n}.png`) });
  }
  expect(errors).toEqual([]);
  await fs.writeFile(
    path.resolve("../outputs/evolution/ui_generation.json"),
    JSON.stringify(
      {
        id,
        path: job.result.path,
        source_equal: true,
        javascript_errors: errors,
        slides: 5,
        pptx_bytes: bytes.length,
      },
      null,
      2,
    ),
  );
});

test("mostra indisponibilidade do Ollama e mantém importação manual acessível", async ({
  page,
}) => {
  await page.route("**/api/models", (route) =>
    route.fulfill({
      json: { available: false, models: [], error: "Ollama indisponível" },
    }),
  );
  await page.goto("/");
  await expect(page.getByRole("alert")).toContainText("Ollama indisponível");
  await expect(
    page.getByRole("button", { name: "Gerar apresentação", exact: true }),
  ).toBeDisabled();
  await page.getByRole("button", { name: "Importar DSL", exact: true }).click();
  await expect(page.getByRole("status")).toHaveText("Programa importado.");
});

test("exibe caminhos e diagnósticos das correções sem substituir por exemplo manual", async ({
  page,
}) => {
  await page.route("**/api/models", (route) =>
    route.fulfill({
      json: { available: true, models: [{ name: "modelo-de-teste" }] },
    }),
  );
  const job = {
    id: "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    state: "completed",
    error: null,
    events: [
      { stage: "planning", round: 0 },
      { stage: "validation", round: 0, diagnostics: [{ code: "L002" }] },
      { stage: "repair", round: 1, paths: ["slides.0.relations.0"] },
      { stage: "validation", round: 1, diagnostics: [{ code: "L002" }] },
      { stage: "repair", round: 2, paths: ["slides.0.relations.0"] },
    ],
    result: {
      source: null,
      ir: null,
      path: "teste",
      report: {
        compile_success: false,
        valid: false,
        diagnostics: [],
        corrections: 2,
        requirements: { numerator: 0, denominator: 5, all_met: false },
      },
    },
  };
  await page.route("**/api/generations", (route) =>
    route.fulfill({ status: 202, json: job }),
  );
  await page.goto("/");
  await expect(page.getByLabel("Modelo local")).toHaveValue("modelo-de-teste");
  await page
    .getByRole("button", { name: "Gerar apresentação", exact: true })
    .click();
  await expect(page.locator(".generation-progress")).toContainText(
    "Correção 1 de 2",
  );
  await expect(page.locator(".generation-progress")).toContainText(
    "Correção 2 de 2",
  );
  await expect(page.locator(".generation-progress")).toContainText(
    "slides.0.relations.0",
  );
  await expect(page.locator(".generation-progress")).toContainText("L002");
  await expect(page.getByLabel("Programa SlideDSL")).toHaveValue("");
  await expect(
    page.getByRole("button", { name: "Gerar PPTX", exact: true }),
  ).toBeDisabled();
});
