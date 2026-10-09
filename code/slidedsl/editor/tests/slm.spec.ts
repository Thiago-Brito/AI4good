import { test, expect } from "@playwright/test";
import fs from "node:fs/promises";
import path from "node:path";

const artifact = process.env.SLIDEDSL_REAL_DEMO;
test("abre a apresentação real do SLM, modifica, revalida e exporta PPTX", async ({
  page,
  request,
}) => {
  test.skip(
    !artifact,
    "Defina SLIDEDSL_REAL_DEMO para uma demonstração real já executada.",
  );
  const folder = path.resolve("..", artifact!);
  const report = JSON.parse(
    await fs.readFile(path.join(folder, "report.json"), "utf8"),
  );
  expect(report.is_mock).toBe(false);
  expect(report.compile_success).toBe(true);
  await page.goto("/?demo=1");
  await expect(page.getByRole("status")).toHaveText(
    "Apresentação gerada pelo SLM importada.",
  );
  const source = await page.getByLabel("Programa SlideDSL").inputValue();
  const expected = await fs.readFile(
    path.join(folder, "presentation.sld"),
    "utf8",
  );
  expect(source.replaceAll("\r\n", "\n")).toBe(
    expected.replaceAll("\r\n", "\n"),
  );
  const parsed = await request.post("http://127.0.0.1:8000/api/parse", {
    data: { source },
  });
  const deck = (await parsed.json()).ir;
  expect(deck.slides).toHaveLength(5);
  const title = deck.slides[0].elements.find(
    (e: { role: string }) => e.role === "titulo",
  );
  await page
    .getByRole("button", { name: `Selecionar ${title.id}`, exact: true })
    .click();
  await page
    .getByLabel("Texto", { exact: true })
    .fill("Título do SLM editado visualmente");
  await page.getByRole("button", { name: "Validar", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("válido");
  const exported = page.waitForEvent("download");
  await page.getByRole("button", { name: "Exportar DSL", exact: true }).click();
  const edited = await fs.readFile((await (await exported).path())!, "utf8");
  expect(edited).toContain("Título do SLM editado visualmente");
  await fs.writeFile(path.join(folder, "editor_modified.sld"), edited);
  const compiled = page.waitForEvent("download");
  await page.getByRole("button", { name: "Gerar PPTX", exact: true }).click();
  const bytes = await fs.readFile((await (await compiled).path())!);
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
});
