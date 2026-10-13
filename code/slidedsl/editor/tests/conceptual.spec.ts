import { openLegacyFlow } from "./helpers";
import { test, expect } from "@playwright/test";
import fs from "node:fs/promises";
import path from "node:path";

test("opção conceitual implica semântica e respeita modo restrito", async ({
  page,
}) => {
  await page.route("**/api/models", (route) =>
    route.fulfill({
      json: {
        available: true,
        models: [{ name: "qwen3:4b-instruct" }],
      },
    }),
  );
  let submitted: {
    context?: { conceptual_planning?: boolean; semantic_planning?: boolean };
  } = {};
  await page.route("**/api/generations", (route) => {
    submitted = route.request().postDataJSON();
    return route.fulfill({
      status: 202,
      json: {
        id: "cccccccccccccccccccccccccccccccc",
        state: "failed",
        events: [],
        error: "Somente transporte simulado",
        result: null,
      },
    });
  });
  await page.goto("/");
  await openLegacyFlow(page);
  await page
    .getByText("Configurações avançadas, imagens e fontes (opcional)", {
      exact: true,
    })
    .click();
  await page.getByLabel("Planejamento conceitual").check();
  await expect(page.getByLabel("Planejamento semântico")).toBeChecked();
  await page
    .getByRole("button", { name: "Gerar apresentação", exact: true })
    .click();
  await expect.poll(() => submitted.context?.conceptual_planning).toBe(true);
  expect(submitted.context?.semantic_planning).toBe(true);
  await page
    .getByLabel("Fundamentação", { exact: true })
    .selectOption("restricted");
  await expect(page.getByLabel("Planejamento conceitual")).not.toBeChecked();
  await expect(page.getByLabel("Planejamento conceitual")).toBeDisabled();
});

test("editor gera conceitos com Qwen local e exporta DSL e PPTX", async ({
  page,
  request,
}) => {
  test.skip(
    process.env.SLIDEDSL_TEST_CONCEPTUAL !== "1",
    "Geração local real opt-in",
  );
  test.setTimeout(240000);
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await openLegacyFlow(page);
  await page
    .getByText("Configurações avançadas, imagens e fontes (opcional)", {
      exact: true,
    })
    .click();
  await page.getByLabel("Planejamento conceitual").check();
  await page.getByLabel("Revisão semântica", { exact: true }).selectOption("2");
  await page.getByLabel("Imagens automáticas", { exact: true }).uncheck();
  await page
    .getByLabel("Pedido da apresentação")
    .fill(
      "Crie dois slides sobre frações para estudantes iniciantes. Slide 1: diferencie numerador e denominador, com um exemplo concreto de partes iguais. Slide 2: conclua por que partes iguais são necessárias e apresente uma aplicação do conceito. Sem imagens ou rodapé.",
    );
  const response = page.waitForResponse(
    (r) =>
      r.url().endsWith("/api/generations") && r.request().method() === "POST",
  );
  await page
    .getByRole("button", { name: "Gerar apresentação", exact: true })
    .click();
  const submitted = await response;
  const submission = await submitted.json();
  await test.info().attach("generation-submission", {
    body: JSON.stringify(submission),
    contentType: "application/json",
  });
  expect(submitted.ok(), JSON.stringify(submission)).toBe(true);
  const id = submission.id;
  await expect(
    page.getByRole("button", { name: "Revalidar requisitos" }),
  ).toBeEnabled({ timeout: 180000 });
  const job = await (
    await request.get(new URL("/api/generations/" + id, page.url()).href)
  ).json();
  const folder = path.resolve("..", job.result.path);
  await fs.writeFile(
    path.join(folder, "ui_evidence.json"),
    JSON.stringify(
      {
        id,
        path: job.result.path,
        report: job.result.report,
        javascript_errors: errors,
      },
      null,
      2,
    ),
  );
  expect(job.result.report.is_mock).toBe(false);
  expect(job.result.report.compile_success).toBe(true);
  expect(job.result.report.conceptual_plan).toBeTruthy();
  expect(job.result.ir.slides).toHaveLength(2);
  for (const [name, file] of [
    ["Exportar DSL", "ui_export.sld"],
    ["Gerar PPTX", "ui_export.pptx"],
  ]) {
    const download = page.waitForEvent("download");
    await page.getByRole("button", { name, exact: true }).click();
    await fs.copyFile(
      (await (await download).path())!,
      path.join(folder, file),
    );
  }
  await page.screenshot({
    path: path.join(folder, "ui_editor.png"),
    fullPage: true,
  });
  expect(errors).toEqual([]);
});
