import { test, expect } from "@playwright/test";
import fs from "node:fs/promises";
import path from "node:path";

test("requisitos, correção e edição com Ollama real", async ({
  page,
  request,
}) => {
  test.skip(
    process.env.SLIDEDSL_TEST_RELIABILITY !== "1",
    "Geração real opt-in",
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
      "Crie um slide sobre camadas. No primeiro slide coloque duas formas coloridas de cores distintas, uma imagem local assets/imagem_demo.png e uma demonstração de camadas: imagem inicialmente atrás e depois à frente de um retângulo, com sobreposição parcial. Use title_content com UMA coluna, dois textos curtos, heading vazio e sem rodapé. Só use back e front para a imagem, reference vazio, nenhuma relação next. Preserve margens.",
    );
  await page.getByLabel("Limite de correções").fill("0");
  const submitted = page.waitForResponse(
    (r) =>
      r.url().endsWith("/api/generations") && r.request().method() === "POST",
  );
  await page
    .getByRole("button", { name: "Gerar apresentação", exact: true })
    .click();
  const firstId = (await (await submitted).json()).id;
  await expect(page.getByLabel("Requisitos do pedido")).toBeVisible({
    timeout: 180000,
  });
  await expect(
    page.getByRole("button", { name: "Corrigir pendências" }),
  ).toBeDisabled();
  await page.getByLabel("Limite de correções").fill("2");
  const corrected = page.waitForResponse(
    (r) =>
      r.url().endsWith("/api/generations") && r.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Corrigir pendências" }).click();
  const correctionResponse = await corrected;
  const correctionPayload = correctionResponse.request().postDataJSON();
  expect(correctionPayload.plan).toBeTruthy();
  expect(correctionPayload.requirements).toHaveLength(5);
  const id = (await correctionResponse.json()).id;
  await expect(
    page.getByRole("button", { name: "Revalidar requisitos" }),
  ).toBeEnabled({ timeout: 180000 });
  const job = await (
    await request.get(`http://127.0.0.1:8000/api/generations/${id}`)
  ).json();
  expect(job.result.report.is_mock).toBe(false);
  expect(job.result.report.compile_success).toBe(true);
  const title = job.result.ir.slides[0].elements.find(
    (e: { role: string }) => e.role === "titulo",
  );
  await page
    .getByRole("button", { name: `Selecionar ${title.id}`, exact: true })
    .click();
  await page.getByLabel("X", { exact: true }).fill("-10");
  await page.getByRole("button", { name: "Revalidar requisitos" }).click();
  await expect(page.getByLabel("Requisitos do pedido")).toContainText(
    "Pendente: Margens",
  );
  await page.getByLabel("X", { exact: true }).fill(String(title.x));
  await page.getByLabel("Texto", { exact: true }).fill("Camadas revisadas");
  await page.getByRole("button", { name: "Revalidar requisitos" }).click();
  await page.getByRole("button", { name: "Validar", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("válido");
  const folder = path.resolve("..", job.result.path);
  for (const [label, file] of [
    ["Exportar DSL", "editor_modified.sld"],
    ["Gerar PPTX", "editor_modified.pptx"],
  ]) {
    const downloaded = page.waitForEvent("download");
    await page.getByRole("button", { name: label, exact: true }).click();
    await fs.copyFile(
      (await (await downloaded).path())!,
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
  await fs.mkdir(path.resolve("../outputs/reliability"), { recursive: true });
  await fs.writeFile(
    path.resolve(
      process.env.SLIDEDSL_UI_RELIABILITY_OUTPUT ??
        "../outputs/reliability/ui_generation.json",
    ),
    JSON.stringify(
      {
        firstId,
        id,
        path: job.result.path,
        javascript_errors: errors,
        real_model: true,
        requirements_revalidated_on_edited_ir: true,
      },
      null,
      2,
    ),
  );
});
