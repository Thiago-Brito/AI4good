import { test, expect } from "@playwright/test";
import fs from "node:fs/promises";
import path from "node:path";
import { apiBaseURL } from "./helpers";

test("arquivos de base fazem upload e desligam internet por padrão", async ({
  page,
}) => {
  let payload: Record<string, unknown> = {};
  await page.route("**/api/models", (route) =>
    route.fulfill({ json: { models: [{ name: "mock" }] } }),
  );
  await page.route("**/api/criar", async (route) => {
    payload = route.request().postDataJSON();
    await route.fulfill({
      json: {
        id: "a".repeat(32),
        state: "completed",
        result: null,
        events: [],
        error: null,
      },
    });
  });
  await page.goto("/");
  await page.getByLabel("Arquivos de base", { exact: true }).setInputFiles({
    name: "base-r7.md",
    mimeType: "text/markdown",
    buffer: Buffer.from(
      "SlideDSL é uma linguagem formal para apresentações editáveis.",
    ),
  });
  await expect(
    page.getByRole("button", { name: "Remover base-r7.md" }),
  ).toBeVisible();
  await page.getByText("Pesquisa e opções avançadas", { exact: true }).click();
  await expect(
    page.getByLabel("Pesquisar na internet com o SearXNG local"),
  ).not.toBeChecked();
  await page
    .getByRole("button", { name: "Criar apresentação", exact: true })
    .click();
  await expect.poll(() => payload.fontes).toBe("documentos");
  expect(payload.documentos).toHaveLength(1);
  expect(payload).toMatchObject({
    tema: "auto",
    buscador: "nenhum",
    permitir_sem_fatos: false,
  });
  await page.getByRole("button", { name: "Remover base-r7.md" }).click();
  await expect(
    page.getByRole("button", { name: "Remover base-r7.md" }),
  ).toHaveCount(0);
});

test("refazer um slide envia instrução e permite desfazer com consumo acumulado", async ({
  page,
  request,
}) => {
  const source = await fs.readFile(
    path.resolve("../examples/cinco_slides.sld"),
    "utf8",
  );
  const response = await request.post(apiBaseURL + "/api/parse", {
    data: { source },
  });
  const ir = (await response.json()).ir;
  const usage = {
    calls: 5,
    max_calls: 12,
    failed_calls: 0,
    known_usage_calls: 5,
    unknown_usage_calls: 0,
    known_input_tokens: 500,
    known_output_tokens: 150,
    cost_usd: 0.01,
  };
  const job = {
    id: "c".repeat(32),
    state: "completed",
    events: [],
    error: null,
    history: [] as string[],
    usage,
    result: {
      source,
      alto: 'deck "fixture" { capa { titulo "fixture" } }',
      ir,
      diagnostics: [],
      folder: "outputs/fixture",
      report: { valid: true, calls: 5, seconds: 1, theme: "claro", usage },
    },
  };
  await page.route("**/api/models", (route) =>
    route.fulfill({ json: { models: [{ name: "mock" }] } }),
  );
  await page.route("**/api/criar", (route) => route.fulfill({ json: job }));
  let payload: Record<string, unknown> = {};
  await page.route("**/api/criar/*/editar", async (route) => {
    payload = route.request().postDataJSON();
    job.history =
      payload.acao === "desfazer" ? [] : ["versoes/fixture/anterior.json"];
    job.usage = { ...usage, calls: 6, cost_usd: 0.012 };
    await route.fulfill({ json: job });
  });
  await page.goto("/");
  await page
    .getByRole("button", { name: "Criar apresentação", exact: true })
    .click();
  const slide = page.getByRole("article", {
    name: "Editar slide 3",
    exact: true,
  });
  await slide
    .getByLabel("Instrução para o slide 3")
    .fill("Transforme em comparação");
  await slide.getByRole("button", { name: "Refazer este slide" }).click();
  await expect(page.getByLabel("Consumo da execução")).toContainText(
    "6/12 chamadas",
  );
  expect(payload).toMatchObject({
    acao: "refazer",
    slide: 3,
    instrucao: "Transforme em comparação",
  });
  await page.getByRole("button", { name: "Desfazer a última edição" }).click();
  await expect.poll(() => payload.acao).toBe("desfazer");
  await expect(
    page.getByRole("button", { name: "Desfazer a última edição" }),
  ).toBeDisabled();
  await expect(page.getByLabel("Consumo da execução")).toContainText(
    "6/12 chamadas",
  );
});
