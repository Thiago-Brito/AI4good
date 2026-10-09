import type { Deck, Report } from "./types";

export async function request<T>(url: string, body: unknown): Promise<T> {
  const response = await fetch("/api/" + url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok)
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : JSON.stringify(data.detail),
    );
  return data as T;
}
export const importSource = (source: string) =>
  request<{ ir: Deck; report: Report }>("parse", { source });
export const validateDeck = (ir: Deck) => request<Report>("validate", { ir });
export const exportDeck = (ir: Deck) =>
  request<{ source: string }>("export", { ir });
export const updateRelation = (ir: Deck, slide: number, relation: unknown) =>
  request<{ ir: Deck }>("relation", { ir, slide, relation });
export function download(bytes: Blob, name: string) {
  const url = URL.createObjectURL(bytes);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export async function compileDeck(ir: Deck) {
  const response = await fetch("/api/compile", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ir }),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(JSON.stringify(error.detail));
  }
  download(await response.blob(), "apresentacao.pptx");
}
