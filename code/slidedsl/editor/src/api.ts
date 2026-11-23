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
export const importAlto = (source: string) =>
  request<{ source: string; ir: Deck; report: Report }>("alto/parse", {
    source,
  });
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

type GoogleStatus = {
  configured: boolean;
  authorized: boolean;
  login: "idle" | "pending" | "authorized" | "error";
  error: string;
};
const googleStatus = async () =>
  (await (await fetch("/api/google/status")).json()) as GoogleStatus;

/**
 * Envia o deck atual ao Google Slides. A aba é aberta já no clique (antes de
 * qualquer await) para o navegador não bloquear: ela mostra o login, se preciso,
 * e depois a apresentação convertida.
 */
export async function sendToGoogleSlides(
  ir: Deck,
  onStatus: (message: string) => void,
): Promise<string> {
  const tab = window.open("about:blank", "_blank");
  try {
    let status = await googleStatus();
    if (!status.configured)
      throw new Error(
        "Google não configurado: salve config/google_client_secret.json (veja docs/GOOGLE_SLIDES.md).",
      );
    if (!status.authorized) {
      const { auth_url } = await request<{ auth_url: string }>(
        "google/login",
        {},
      );
      if (tab) tab.location.href = auth_url;
      else window.open(auth_url, "_blank");
      onStatus("Confirme o acesso na aba do Google…");
      const limit = Date.now() + 5 * 60_000;
      while (!status.authorized) {
        if (Date.now() > limit) throw new Error("Login do Google expirou.");
        await new Promise((r) => setTimeout(r, 1000));
        status = await googleStatus();
        if (status.login === "error") throw new Error(status.error);
      }
    }
    onStatus("Enviando ao Google Slides…");
    const result = await request<{ url: string; name: string }>(
      "google/slides",
      { ir, title: ir.title },
    );
    if (tab) tab.location.href = result.url;
    return result.url;
  } catch (error) {
    tab?.close();
    throw error;
  }
}
