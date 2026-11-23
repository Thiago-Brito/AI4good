import { expect, test } from "@playwright/test";
import fs from "node:fs/promises";
import path from "node:path";
import { apiBaseURL } from "./helpers";

test("OpenAI envia limites, mantém modelo remoto e mostra consumo parcial", async ({
  page,
  request,
}) => {
  const source = await fs.readFile(
    path.resolve("../examples/cinco_slides.sld"),
    "utf8",
  );
  const imported = await request.post(apiBaseURL + "/api/parse", {
    data: { source },
  });
  const ir = (await imported.json()).ir;
  await page.route("**/api/providers", (route) =>
    route.fulfill({
      json: {
        openai: { configured: true, default_model: "fixture-remote-model" },
      },
    }),
  );
  await page.route("**/api/models", (route) =>
    route.fulfill({
      json: {
        available: true,
        models: [{ name: "fixture-local-model" }],
      },
    }),
  );
  let payload: Record<string, unknown> | null = null;
  const usage = {
    calls: 4,
    max_calls: 9,
    failed_calls: 1,
    known_usage_calls: 3,
    unknown_usage_calls: 1,
    known_input_tokens: 450,
    known_output_tokens: 90,
    cost_usd: null,
  };
  await page.route("**/api/criar", async (route) => {
    payload = route.request().postDataJSON();
    await route.fulfill({
      json: {
        id: "a".repeat(32),
        state: "completed",
        events: [],
        usage,
        error: null,
        result: {
          source,
          ir,
          diagnostics: [],
          folder: "outputs/fixture",
          report: { valid: true, calls: 4, seconds: 1, usage },
        },
      },
    });
  });
  await page.goto("/");
  await page.getByLabel("Provedor", { exact: true }).selectOption("openai");
  await expect(
    page.getByLabel("Modelo para criar", { exact: true }),
  ).toHaveValue("fixture-remote-model");
  await page.getByText("Pesquisa e opções avançadas", { exact: true }).click();
  await page.getByLabel("Pesquisar na internet com o SearXNG local").uncheck();
  await page.getByLabel("Limite de chamadas", { exact: true }).fill("9");
  await page
    .getByRole("button", { name: "Criar apresentação", exact: true })
    .click();
  await expect(page.getByLabel("Consumo da execução")).toContainText(
    "4/9 chamadas",
  );
  await expect(page.getByLabel("Consumo da execução")).toContainText(
    "totais parciais",
  );
  await expect(page.getByLabel("Consumo da execução")).toContainText(
    "Custo total indisponível",
  );
  expect(payload).toMatchObject({
    provider: "openai",
    model: "fixture-remote-model",
    max_calls: 9,
    max_output_tokens: 2048,
    candidatos: 1,
    buscador: "nenhum",
  });
  await expect(page.locator(".slides-panel > button:has(> span)")).toHaveCount(
    5,
  );
  await page.reload();
  await expect(page.getByLabel("Provedor", { exact: true })).toHaveValue(
    "openai",
  );
  await expect(
    page.getByLabel("Modelo para criar", { exact: true }),
  ).toHaveValue("fixture-remote-model");
});

test("chave ausente fica visível e impede envio pela interface", async ({
  page,
}) => {
  await page.route("**/api/providers", (route) =>
    route.fulfill({
      json: {
        openai: { configured: false, default_model: "fixture-model" },
      },
    }),
  );
  await page.goto("/");
  await page.getByLabel("Provedor", { exact: true }).selectOption("openai");
  await expect(
    page.getByText(
      "Configure OPENAI_API_KEY no ambiente do servidor e reinicie a aplicação.",
    ),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Criar apresentação", exact: true }),
  ).toBeDisabled();
});
