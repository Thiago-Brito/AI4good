import { test, expect } from "@playwright/test";
import fs from "node:fs/promises";
import path from "node:path";

test("anexa documentos locais e exclui sem exigir configurações", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByLabel("Público", { exact: true })).not.toBeVisible();
  await page
    .getByText("Configurações avançadas, imagens e fontes (opcional)", {
      exact: true,
    })
    .click();
  await page
    .getByLabel("Materiais de referência", { exact: true })
    .setInputFiles([
      {
        name: "local_a.txt",
        mimeType: "text/plain",
        buffer: Buffer.from("Processo local de treinamento."),
      },
      {
        name: "local_b.md",
        mimeType: "text/markdown",
        buffer: Buffer.from("# Guia\n\nTreinamento com prática."),
      },
    ]);
  await expect(page.getByLabel("Fundamentação", { exact: true })).toHaveValue(
    "grounded",
  );
  await expect(page.locator(".context-panel")).toContainText("local_a.txt");
  await expect(page.locator(".context-panel")).toContainText("local_b.md");
  await page.getByRole("button", { name: "Excluir documento" }).last().click();
  await expect(page.locator(".context-panel")).not.toContainText("local_b.md");
  await page.getByRole("button", { name: "Excluir documento" }).click();
  await expect(page.locator(".context-panel")).not.toContainText("local_a.txt");
});

test("importa imagem própria offline com permissão e exclusão", async ({
  page,
}) => {
  await page.goto("/");
  await page
    .getByText("Configurações avançadas, imagens e fontes (opcional)", {
      exact: true,
    })
    .click();
  await page
    .getByText("Importar imagem própria · offline", { exact: true })
    .click();
  await expect(page.getByLabel("Imagem local", { exact: true })).toBeDisabled();
  await page.getByLabel("Autor da imagem local").fill("SlideDSL teste");
  await page
    .getByLabel("Permissão da imagem local")
    .fill("Criação própria para teste");
  await page
    .getByLabel("Confirmo que tenho permissão para utilizar esta imagem")
    .check();
  await page.getByLabel("Imagem local", { exact: true }).setInputFiles({
    name: "imagem_local_teste.png",
    mimeType: "image/png",
    buffer: await fs.readFile(path.resolve("../assets/imagem_demo.png")),
  });
  const row = page
    .getByLabel("Imagens locais", { exact: true })
    .getByRole("listitem")
    .filter({ hasText: "imagem_local_teste.png" });
  await expect(row).toBeVisible();
  await expect(row.getByRole("checkbox")).toBeChecked();
  await row.getByRole("checkbox").uncheck();
  await row.getByRole("button", { name: "Excluir cache da imagem" }).click();
  await expect(row).toHaveCount(0);
});

test("SLM real com imagem licenciada, fontes e reparo preservando edição", async ({
  page,
  request,
}) => {
  test.skip(
    process.env.SLIDEDSL_TEST_CONTEXTUAL !== "1",
    "Ollama e imagem real em cache são opt-in",
  );
  test.setTimeout(240000);
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const cache = await (
    await request.get("http://127.0.0.1:8000/api/images/cache")
  ).json();
  expect(cache.results.length).toBeGreaterThan(0);
  await page.goto("/");
  await page
    .getByText("Configurações avançadas, imagens e fontes (opcional)", {
      exact: true,
    })
    .click();
  await page.getByLabel("Público", { exact: true }).fill("Público geral");
  await page
    .getByLabel("Objetivo", { exact: true })
    .fill("Informar sobre exploração lunar");
  await page
    .getByLabel("Imagens locais")
    .locator('input[type="checkbox"]')
    .first()
    .check();
  await page
    .getByLabel("Materiais de referência", { exact: true })
    .setInputFiles({
      name: "apollo_reference.txt",
      mimeType: "text/plain",
      buffer: Buffer.from(
        "Apollo 11 é o tema desta apresentação de exploração lunar.\n\nA imagem foi selecionada no catálogo licenciado local.\n\nA apresentação permite editar o título e exportar objetos para PowerPoint.",
      ),
    });
  await expect(page.getByLabel("Fundamentação", { exact: true })).toHaveValue(
    "grounded",
  );
  await page
    .getByLabel("Autorizar complemento com conhecimento do modelo")
    .check();
  await page
    .getByLabel("Pedido da apresentação")
    .fill(
      "Crie um slide sobre Apollo 11 e exploração lunar, usando text_image, exatamente UMA imagem selecionada image1 e UMA coluna com DOIS itens de até 90 caracteres, heading vazio. Legenda curta. Sem rodapé, decorations ou relations. Use os trechos fornecidos e cite sources. Preserve margens.",
    );
  const submitted = page.waitForResponse(
    (r) =>
      r.url().endsWith("/api/generations") && r.request().method() === "POST",
  );
  await page
    .getByRole("button", { name: "Gerar apresentação", exact: true })
    .click();
  const id = (await (await submitted).json()).id;
  await expect(
    page.getByRole("button", { name: "Revalidar requisitos" }),
  ).toBeEnabled({ timeout: 180000 });
  const job = await (
    await request.get("http://127.0.0.1:8000/api/generations/" + id)
  ).json();
  expect(job.result.report.is_mock).toBe(false);
  expect(job.result.report.compile_success).toBe(true);
  expect(job.result.report.images).toHaveLength(1);
  expect(job.result.report.source_audit.associations.length).toBeGreaterThan(0);
  const title = job.result.ir.slides[0].elements.find(
    (e: { role: string }) => e.role === "titulo",
  );
  await page
    .getByRole("button", { name: "Selecionar " + title.id, exact: true })
    .click();
  await page
    .getByLabel("Texto", { exact: true })
    .fill("Exploração lunar revisada");
  await expect(
    page.getByRole("button", { name: "Corrigir pendências" }),
  ).toBeEnabled();
  const repaired = page.waitForResponse(
    (r) =>
      r.url().endsWith("/api/generations") && r.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Corrigir pendências" }).click();
  const repairResponse = await repaired;
  expect(
    repairResponse
      .request()
      .postDataJSON()
      .current_ir.slides[0].elements.find(
        (e: { id: string }) => e.id === title.id,
      ).text,
  ).toBe("Exploração lunar revisada");
  const repairId = (await repairResponse.json()).id;
  await expect(
    page.getByRole("button", { name: "Revalidar requisitos" }),
  ).toBeEnabled({ timeout: 180000 });
  await expect(page.getByLabel("Programa SlideDSL")).toHaveValue(
    /Exploração lunar revisada/,
  );
  const final = await (
    await request.get("http://127.0.0.1:8000/api/generations/" + repairId)
  ).json();
  expect(final.result.report.compile_success).toBe(true);
  expect(
    final.result.report.manual_edits.some(
      (e: { field: string }) => e.field === "text",
    ),
  ).toBe(true);
  await page.getByRole("button", { name: "Revalidar requisitos" }).click();
  await page.getByRole("button", { name: "Validar", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("válido");
  const folder = path.resolve("..", final.result.path);
  for (const [button, file] of [
    ["Exportar DSL", "editor_modified.sld"],
    ["Gerar PPTX", "editor_modified.pptx"],
  ]) {
    const download = page.waitForEvent("download");
    await page.getByRole("button", { name: button, exact: true }).click();
    await fs.copyFile(
      (await (await download).path())!,
      path.join(folder, file),
    );
  }
  await page.screenshot({
    path: path.join(folder, "editor.png"),
    fullPage: true,
  });
  await page
    .getByTestId("preview")
    .screenshot({ path: path.join(folder, "preview.png") });
  expect(errors).toEqual([]);
  await fs.mkdir(path.resolve("../outputs/contextual"), { recursive: true });
  await fs.writeFile(
    path.resolve("../outputs/contextual/ui_generation.json"),
    JSON.stringify(
      {
        id,
        repairId,
        path: final.result.path,
        real_model: true,
        licensed_image: true,
        source_trace: true,
        manual_title_preserved: true,
        javascript_errors: errors,
      },
      null,
      2,
    ),
  );
});
