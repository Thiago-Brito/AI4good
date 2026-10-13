import type { Page } from "@playwright/test";

export const apiBaseURL = `http://127.0.0.1:${process.env.SLIDEDSL_API_PORT ?? 8000}`;

export async function openLegacyFlow(page: Page) {
  await page
    .getByText("Fluxo anterior · Gerar com IA local (planejamento visual)", {
      exact: true,
    })
    .click();
}
