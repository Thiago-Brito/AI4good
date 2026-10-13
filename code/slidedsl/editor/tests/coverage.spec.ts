import { openLegacyFlow } from "./helpers";
import { test, expect } from "@playwright/test";

test("cobertura experimental envia flags e desativa ao sair do modo conceitual", async ({
  page,
}) => {
  await page.route("**/api/models", (route) =>
    route.fulfill({
      json: { available: true, models: [{ name: "qwen3:4b-instruct" }] },
    }),
  );
  let submitted: {
    context?: { coverage_validation?: boolean; coverage_recovery?: boolean };
  } = {};
  await page.route("**/api/generations", (route) => {
    submitted = route.request().postDataJSON();
    return route.fulfill({
      status: 202,
      json: {
        id: "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
        state: "failed",
        events: [],
        error: "Transporte simulado",
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
  await expect(
    page.getByLabel("Validar cobertura de conteúdo"),
  ).not.toBeChecked();
  await page.getByLabel("Validar cobertura de conteúdo").check();
  await expect(page.getByLabel("Recuperar conteúdo descartado")).toBeChecked();
  await page.getByLabel("Recuperar conteúdo descartado").uncheck();
  await page
    .getByRole("button", { name: "Gerar apresentação", exact: true })
    .click();
  await expect.poll(() => submitted.context?.coverage_validation).toBe(true);
  expect(submitted.context?.coverage_recovery).toBe(false);
  await page.getByLabel("Planejamento conceitual").uncheck();
  await page.getByLabel("Planejamento conceitual").check();
  await expect(
    page.getByLabel("Validar cobertura de conteúdo"),
  ).not.toBeChecked();
});
