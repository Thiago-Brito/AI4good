import { test, expect } from "@playwright/test";
import path from "node:path";
import fs from "node:fs/promises";
import { validConnection } from "../src/graph";

const root = path.resolve("..");
test("importa cinco slides, edita, valida, exporta DSL e gera PPTX real", async ({
  page,
  request,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await page
    .getByLabel("Abrir arquivo .sld")
    .setInputFiles(path.join(root, "examples/cinco_slides.sld"));
  await expect(page.getByRole("status")).toHaveText("Arquivo importado.");
  await expect(page.getByText("Grafo do documento")).toBeVisible();
  await page
    .getByRole("button", { name: "Selecionar titulo", exact: true })
    .click();
  await page
    .getByLabel("Texto", { exact: true })
    .fill("Título editado pelo teste");
  await page.getByRole("button", { name: "Validar", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("válido");
  const exported = page.waitForEvent("download");
  await page.getByRole("button", { name: "Exportar DSL", exact: true }).click();
  const dsl = await exported;
  const location = await dsl.path();
  const source = await fs.readFile(location!, "utf8");
  expect(source).toContain("Título editado pelo teste");
  const parsed = await request.post("http://127.0.0.1:8000/api/parse", {
    data: { source },
  });
  expect(parsed.ok()).toBeTruthy();
  const deck = (await parsed.json()).ir;
  expect(deck.slides).toHaveLength(5);
  const pptx = page.waitForEvent("download");
  await page.getByRole("button", { name: "Gerar PPTX", exact: true }).click();
  const download = await pptx;
  expect(
    (await fs.readFile((await download.path())!)).subarray(0, 2).toString(),
  ).toBe("PK");
  await page.screenshot({
    path: path.join(root, "outputs/editor_demo.png"),
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
      .screenshot({ path: path.join(root, `outputs/preview_slide_${n}.png`) });
  }
  expect(errors).toEqual([]);
});

test("corrige objeto fora do slide pelo painel de propriedades", async ({
  page,
}) => {
  await page.goto("/");
  await page
    .getByLabel("Abrir arquivo .sld")
    .setInputFiles(path.join(root, "examples/negativo_fora.sld"));
  await expect(page.getByRole("status")).toHaveText("Arquivo importado.");
  await page.getByRole("button", { name: "Validar", exact: true }).click();
  await expect(page.locator(".diagnostics")).toContainText("D001");
  await page.screenshot({
    path: path.join(root, "outputs/editor_antes.png"),
    fullPage: true,
  });
  await page.getByLabel("X", { exact: true }).fill("80");
  await page.getByRole("button", { name: "Validar", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("válido");
  await expect(page.locator(".diagnostics")).not.toContainText("D001");
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Exportar DSL", exact: true }).click();
  const source = await fs.readFile((await (await download).path())!, "utf8");
  expect(source).toContain("em (80, 80)");
  await page.screenshot({
    path: path.join(root, "outputs/editor_depois.png"),
    fullPage: true,
  });
});

test("portas tipadas bloqueiam conexões incompatíveis e entre slides", () => {
  const connection = {
    source: "s1:a",
    target: "s1:b",
    sourceHandle: "spatial",
    targetHandle: "spatial",
  };
  expect(validConnection(connection)).toBe(true);
  expect(validConnection({ ...connection, target: "s2:b" })).toBe(false);
  expect(
    validConnection({ ...connection, targetHandle: "contains_element" }),
  ).toBe(false);
  expect(
    validConnection({
      source: "presentation",
      target: "slide-1",
      sourceHandle: "contains_slide",
      targetHandle: "contains_slide",
    }),
  ).toBe(true);
});
