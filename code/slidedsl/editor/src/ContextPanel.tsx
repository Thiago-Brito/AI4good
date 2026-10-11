import { useEffect, useState } from "react";
import { request } from "./api";

export type ContextOptions = {
  theme?: string;
  audience?: string;
  objective?: string;
  detail?: string;
  visual_style?: string;
  tone?: string;
  components?: string;
  slides?: number | null;
  research?: string;
  selection?: string;
  provider?: string;
  assets?: string[];
  documents?: string[];
  grounding?: string;
  supplement?: boolean;
  share_queries?: boolean;
};
type ImageRecord = {
  id: string;
  title: string;
  author: string;
  license: string;
  license_url: string;
  page: string;
  asset?: string;
  review_required?: boolean;
  attribution?: string;
  lexical_score?: number;
};
type DocumentRecord = { id: string; name: string; chunk_count: number };

export function ContextPanel({
  disabled,
  value,
  onChange,
  plan,
  bindings,
  onBindings,
}: {
  disabled: boolean;
  value: ContextOptions | null;
  onChange: (value: ContextOptions) => void;
  plan?: Record<string, unknown> | null;
  bindings: Record<string, string>;
  onBindings: (bindings: Record<string, string>) => void;
}) {
  const [images, setImages] = useState<ImageRecord[]>([]);
  const [results, setResults] = useState<ImageRecord[]>([]);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");
  const [working, setWorking] = useState(false);
  const [reviewed, setReviewed] = useState<string[]>([]);
  const [localAuthor, setLocalAuthor] = useState("");
  const [localLicense, setLocalLicense] = useState("");
  const [localRights, setLocalRights] = useState(false);
  const settings = value ?? {};
  const mediaSlides = Array.isArray(plan?.slides)
    ? (plan.slides as {
        title: string;
        media?: { query: string; asset: string }[];
      }[])
    : [];
  const change = (patch: ContextOptions) => onChange({ ...settings, ...patch });
  useEffect(() => {
    void fetch("/api/images/cache")
      .then((r) => r.json())
      .then((data) => setImages(data.results ?? []))
      .catch(() => {});
  }, []);
  const search = async (offline: boolean) => {
    setWorking(true);
    setError("");
    try {
      const data = await request<{ results: ImageRecord[] }>("images/search", {
        query,
        provider: settings.provider ?? "openverse",
        offline,
      });
      setResults(data.results);
      if (!data.results.length)
        setError(
          "Nenhum candidato disponível. Continue sem imagem ou altere a consulta.",
        );
    } catch (e) {
      setError(String(e));
    } finally {
      setWorking(false);
    }
  };
  const select = async (image: ImageRecord) => {
    setWorking(true);
    setError("");
    try {
      const selected = await request<ImageRecord>("images/select", {
        id: image.id,
        reviewed: reviewed.includes(image.id),
      });
      setImages((old) => [
        ...old.filter((i) => i.id !== selected.id),
        selected,
      ]);
      change({
        assets: [...new Set([...(settings.assets ?? []), selected.id])],
      });
    } catch (e) {
      setError(String(e));
    } finally {
      setWorking(false);
    }
  };
  const upload = async (files: FileList | null) => {
    if (!files) return;
    setWorking(true);
    setError("");
    try {
      if (documents.length + files.length > 8)
        throw new Error("Até oito documentos por apresentação.");
      const added = [];
      for (const file of files) {
        if (file.size > 2 * 1024 * 1024)
          throw new Error("Cada documento deve ter até 2 MiB.");
        const base64 = await new Promise<string>((resolve, reject) => {
          const reader = new FileReader();
          reader.onerror = reject;
          reader.onload = () => resolve(String(reader.result).split(",")[1]);
          reader.readAsDataURL(file);
        });
        const doc = await request<DocumentRecord>("documents", {
          name: file.name,
          data_base64: base64,
        });
        added.push(doc);
        setDocuments((old) => [...old, doc]);
      }
      change({
        documents: [...(settings.documents ?? []), ...added.map((d) => d.id)],
        grounding:
          settings.grounding === "restricted" ? "restricted" : "grounded",
      });
    } catch (e) {
      setError(String(e));
    } finally {
      setWorking(false);
    }
  };
  const uploadImage = async (file?: File) => {
    if (!file) return;
    setWorking(true);
    setError("");
    try {
      if (file.size > 2 * 1024 * 1024)
        throw new Error("Imagem local deve ter até 2 MiB.");
      const base64 = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onerror = reject;
        reader.onload = () => resolve(String(reader.result).split(",")[1]);
        reader.readAsDataURL(file);
      });
      const image = await request<ImageRecord>("images/local", {
        name: file.name,
        data_base64: base64,
        author: localAuthor,
        license_note: localLicense,
        rights_confirmed: localRights,
      });
      setImages((old) => [...old.filter((i) => i.id !== image.id), image]);
      change({ assets: [...new Set([...(settings.assets ?? []), image.id])] });
    } catch (e) {
      setError(String(e));
    } finally {
      setWorking(false);
    }
  };
  return (
    <details className="context-panel">
      <summary>Configurações avançadas, imagens e fontes (opcional)</summary>
      <div className="generation-options">
        {(
          [
            ["theme", "Tema"],
            ["audience", "Público"],
            ["objective", "Objetivo"],
            ["detail", "Nível de detalhe"],
            ["visual_style", "Estilo visual"],
            ["tone", "Tom"],
            ["components", "Componentes desejados"],
          ] as const
        ).map(([key, label]) => (
          <label key={key}>
            {label}
            <input
              aria-label={label}
              value={settings[key] ?? ""}
              maxLength={key === "detail" || key === "tone" ? 100 : 200}
              disabled={disabled || working}
              onChange={(e) => change({ [key]: e.target.value })}
            />
          </label>
        ))}
        <label>
          Número de slides (opcional)
          <input
            aria-label="Número de slides"
            type="number"
            min={1}
            max={12}
            value={settings.slides ?? ""}
            disabled={disabled || working}
            onChange={(e) =>
              change({ slides: e.target.value ? Number(e.target.value) : null })
            }
          />
        </label>
        <label>
          Pesquisa de imagens
          <select
            aria-label="Pesquisa de imagens"
            value={settings.research ?? "off"}
            disabled={disabled || working}
            onChange={(e) => change({ research: e.target.value })}
          >
            <option value="off">Desativada · offline</option>
            <option value="on">Ativada</option>
            <option value="auto">Automática conforme o plano</option>
          </select>
        </label>
        <label>
          Seleção de imagens
          <select
            aria-label="Seleção de imagens"
            value={settings.selection ?? "manual"}
            disabled={disabled || working}
            onChange={(e) => change({ selection: e.target.value })}
          >
            <option value="manual">Manual</option>
            <option value="auto">Automática conservadora</option>
          </select>
        </label>
        <label>
          Provedor
          <select
            aria-label="Provedor de imagens"
            value={settings.provider ?? "openverse"}
            disabled={disabled || working}
            onChange={(e) => change({ provider: e.target.value })}
          >
            <option value="openverse">Openverse</option>
            <option value="commons">Wikimedia Commons</option>
            <option value="nasa">NASA · temas espaciais</option>
          </select>
        </label>
      </div>
      <h3>Imagens e licenças</h3>
      <details>
        <summary>Importar imagem própria · offline</summary>
        <label>
          Autor ou crédito
          <input
            aria-label="Autor da imagem local"
            value={localAuthor}
            maxLength={200}
            disabled={disabled || working}
            onChange={(e) => setLocalAuthor(e.target.value)}
          />
        </label>
        <label>
          Licença ou permissão de uso
          <input
            aria-label="Permissão da imagem local"
            value={localLicense}
            maxLength={300}
            disabled={disabled || working}
            onChange={(e) => setLocalLicense(e.target.value)}
          />
        </label>
        <label>
          <input
            type="checkbox"
            checked={localRights}
            disabled={disabled || working}
            onChange={(e) => setLocalRights(e.target.checked)}
          />
          Confirmo que tenho permissão para utilizar esta imagem
        </label>
        <label>
          Imagem PNG ou JPEG, até 2 MiB
          <input
            aria-label="Imagem local"
            type="file"
            accept=".png,.jpg,.jpeg"
            disabled={
              disabled || working || !localRights || !localLicense.trim()
            }
            onChange={(e) => void uploadImage(e.target.files?.[0])}
          />
        </label>
      </details>
      <label>
        <input
          type="checkbox"
          checked={settings.share_queries ?? false}
          disabled={disabled || working}
          onChange={(e) => change({ share_queries: e.target.checked })}
        />
        Autorizar consultas de imagens derivadas dos documentos
      </label>
      <p>
        A busca online envia somente a consulta ao provedor. Documentos
        permanecem locais. Relevância e termos individuais precisam de revisão.
      </p>
      <label>
        Consulta de imagem
        <input
          aria-label="Consulta de imagem"
          value={query}
          maxLength={200}
          disabled={disabled || working}
          onChange={(e) => setQuery(e.target.value)}
        />
      </label>
      <button
        disabled={disabled || working || !query.trim()}
        onClick={() => void search(false)}
      >
        Buscar online
      </button>
      <button
        disabled={disabled || working || !query.trim()}
        onClick={() => void search(true)}
      >
        Consultar busca em cache
      </button>
      <ul>
        {results.map((image) => (
          <li key={image.id}>
            {image.title} · {image.author} ·{" "}
            <a href={image.page} target="_blank" rel="noreferrer">
              Origem
            </a>{" "}
            ·{" "}
            <a href={image.license_url} target="_blank" rel="noreferrer">
              {image.license}
            </a>
            {image.review_required && (
              <label>
                <input
                  type="checkbox"
                  checked={reviewed.includes(image.id)}
                  onChange={(e) =>
                    setReviewed((old) =>
                      e.target.checked
                        ? [...old, image.id]
                        : old.filter((id) => id !== image.id),
                    )
                  }
                />
                Revisei os direitos desta imagem e os termos de uso
              </label>
            )}
            <button
              disabled={
                disabled ||
                working ||
                (!!image.review_required && !reviewed.includes(image.id))
              }
              onClick={() => void select(image)}
            >
              Selecionar e armazenar
            </button>
          </li>
        ))}
      </ul>
      <ul aria-label="Imagens locais">
        {images.map((image) => (
          <li key={image.id}>
            <label>
              <input
                type="checkbox"
                checked={(settings.assets ?? []).includes(image.id)}
                disabled={disabled || working}
                onChange={(e) =>
                  change({
                    assets: e.target.checked
                      ? [...(settings.assets ?? []), image.id]
                      : (settings.assets ?? []).filter((id) => id !== image.id),
                  })
                }
              />
              {image.title} · {image.license}
            </label>
            <button
              disabled={
                disabled ||
                working ||
                (settings.assets ?? []).includes(image.id)
              }
              onClick={() =>
                void fetch("/api/images/cache/" + image.id, {
                  method: "DELETE",
                })
                  .then((r) => {
                    if (!r.ok) throw new Error("Não foi possível excluir");
                    setImages((old) => old.filter((i) => i.id !== image.id));
                  })
                  .catch((e) => setError(String(e)))
              }
            >
              Excluir cache da imagem
            </button>
          </li>
        ))}
      </ul>
      <p>
        Excluir o cache pode afetar apresentações que usam a imagem. O PPTX
        exportado incorpora o arquivo.
      </p>
      {mediaSlides.map((slide, si) =>
        (slide.media ?? []).map((media, mi) => {
          const field = `slides.${si}.media.${mi}.asset`;
          return (
            <label key={field}>
              Imagem do slide {si + 1}, posição {mi + 1}: {media.query}
              <select
                aria-label={`Imagem do slide ${si + 1} posição ${mi + 1}`}
                value={bindings[field] ?? ""}
                disabled={disabled || working}
                onChange={(e) => {
                  const updated = { ...bindings };
                  if (e.target.value) updated[field] = e.target.value;
                  else delete updated[field];
                  onBindings(updated);
                  if (e.target.value)
                    change({
                      assets: [
                        ...new Set([
                          ...(settings.assets ?? []),
                          e.target.value,
                        ]),
                      ],
                    });
                }}
              >
                <option value="">Manter imagem atual / pendente</option>
                {images.map((image) => (
                  <option key={image.id} value={image.id}>
                    {image.title} · {image.license}
                  </option>
                ))}
              </select>
            </label>
          );
        }),
      )}
      {mediaSlides.some((s) => s.media?.length) && (
        <p>
          Use Corrigir pendências para aplicar estas seleções ao plano atual,
          preservando edições manuais.
        </p>
      )}
      <h3>Materiais de referência locais</h3>
      <label>
        Anexar TXT, Markdown ou PDF textual
        <input
          aria-label="Materiais de referência"
          type="file"
          multiple
          accept=".txt,.md,.pdf"
          disabled={disabled || working}
          onChange={(e) => void upload(e.target.files)}
        />
      </label>
      <label>
        Fundamentação
        <select
          aria-label="Fundamentação"
          value={settings.grounding ?? "free"}
          disabled={disabled || working}
          onChange={(e) => change({ grounding: e.target.value })}
        >
          <option value="free">Livre</option>
          <option value="grounded">Fundamentado nos documentos</option>
          <option value="restricted">Restrito a trechos das fontes</option>
        </select>
      </label>
      <label>
        <input
          type="checkbox"
          checked={settings.supplement ?? false}
          disabled={disabled || working || settings.grounding === "restricted"}
          onChange={(e) => change({ supplement: e.target.checked })}
        />
        Autorizar complemento com conhecimento do modelo
      </label>
      <ul>
        {documents.map((doc) => (
          <li key={doc.id}>
            {doc.name} · {doc.chunk_count} trechos{" "}
            <button
              disabled={disabled || working}
              onClick={() =>
                void fetch("/api/documents/" + doc.id, { method: "DELETE" })
                  .then((r) => {
                    if (!r.ok) throw new Error("Exclusão falhou");
                    setDocuments((old) => old.filter((d) => d.id !== doc.id));
                    change({
                      documents: (settings.documents ?? []).filter(
                        (id) => id !== doc.id,
                      ),
                    });
                  })
                  .catch((e) => setError(String(e)))
              }
            >
              Excluir documento
            </button>
          </li>
        ))}
      </ul>
      <p>
        Trechos utilizados ficam nos registros da geração até a exclusão do
        trabalho. Fontes registradas não comprovam automaticamente os fatos.
      </p>
      {working && <p role="status">Processando localmente…</p>}
      {error && <p role="alert">{error}</p>}
    </details>
  );
}
