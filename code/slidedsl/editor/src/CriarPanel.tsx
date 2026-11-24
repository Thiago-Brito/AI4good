import { useEffect, useRef, useState } from "react";
import { request } from "./api";
import type { Deck, Diagnostic, Usage } from "./types";
import { UsageSummary } from "./UsageSummary";
import { BaseDocuments } from "./BaseDocuments";
import type { BaseDocument } from "./BaseDocuments";
import { AltoSlideEdits } from "./AltoSlideEdits";

type Provider = "ollama" | "llamacpp" | "openai";
const LEGACY_OPENAI_DEFAULT = "gpt-4.1-mini";
type Estilo =
  | "auto"
  | "claro"
  | "escuro"
  | "editorial"
  | "vibrante"
  | "natural"
  | "noturno";
type Providers = { openai: { configured: boolean; default_model: string } };

type Fact = {
  id: string;
  claim: string;
  kind: string;
  value: string;
  url: string;
  source_title: string;
};
type CriarResult = {
  folder: string;
  report: {
    valid: boolean;
    theme?: string;
    pptx?: string;
    facts?: number;
    sources?: number;
    calls: number;
    seconds: number;
    usage?: Usage;
    errors?: { code: string; message: string }[];
    coverage?: {
      topico: string;
      coberto: boolean;
      slides_visiveis: number[];
    }[];
    unsupported?: { slide: number; texto: string; motivo: string }[];
  };
  facts?: Fact[];
  alto?: string;
  source?: string;
  ir?: Deck | null;
  diagnostics?: Diagnostic[];
};
type CriarJob = {
  id: string;
  state: "queued" | "running" | "completed" | "failed";
  events: { message: string; at: string }[];
  result: CriarResult | null;
  error: string | null;
  usage?: Usage | null;
  history?: string[];
};

function stored(key: string, fallback: string) {
  try {
    return window.localStorage.getItem("slidedsl." + key) ?? fallback;
  } catch {
    return fallback;
  }
}
function store(key: string, value: string) {
  try {
    window.localStorage.setItem("slidedsl." + key, value);
  } catch {
    /* armazenamento indisponível: apenas não lembra a preferência */
  }
}

export function CriarPanel({
  disabled,
  onBusy,
  onStatus,
  onLoad,
}: {
  disabled: boolean;
  onBusy: (value: boolean) => void;
  onStatus: (value: string) => void;
  onLoad: (source: string, ir: Deck, diagnostics: Diagnostic[]) => void;
}) {
  const [models, setModels] = useState<string[]>([]);
  // "celular": o mesmo pipeline do app Android, em GGUF local (src/slidedsl/motor_celular.py).
  const [motor, setMotor] = useState<"celular" | "completo">(() =>
    stored("criar.motor", "celular") === "completo" ? "completo" : "celular",
  );
  const [localModels, setLocalModels] = useState<
    { id: string; rotulo: string; disponivel: boolean; padrao?: boolean }[]
  >([]);
  const [modeloLocal, setModeloLocal] = useState(
    stored("criar.modeloLocal", "qwen3-0.6b-lora"),
  );
  const [provider, setProvider] = useState<Provider>(() => {
    const value = stored("criar.provider", "ollama");
    return value === "openai" || value === "llamacpp" ? value : "ollama";
  });
  const [providers, setProviders] = useState<Providers | null>(null);
  const [model, setModel] = useState(
    stored(
      `criar.${provider}.model`,
      provider === "openai"
        ? "gpt-4.1-mini"
        : provider === "llamacpp"
          ? "local"
          : stored("criar.model", "qwen3:4b-instruct"),
    ),
  );
  const [pedido, setPedido] = useState(
    "Monolito ou microsserviços para uma startup: quando cada um compensa",
  );
  const [slides, setSlides] = useState(6);
  const [candidatos, setCandidatos] = useState(1);
  const [maxCalls, setMaxCalls] = useState(60);
  const [maxOutput, setMaxOutput] = useState(2048);
  const [tema, setTema] = useState<Estilo>("auto");
  const [documents, setDocuments] = useState<BaseDocument[]>([]);
  const [uploading, setUploading] = useState(false);
  const [editing, setEditing] = useState(false);
  // Com API paga, o perfil econômico é sem pesquisa; ela continua disponível como opção.
  const [pesquisar, setPesquisar] = useState(provider !== "openai");
  const [searx, setSearx] = useState<{ ok: boolean; message: string } | null>(
    null,
  );
  const [imagens, setImagens] = useState(false);
  const [lote, setLote] = useState(true);
  const [imagensFonte, setImagensFonte] = useState<
    "livres" | "livres_ia" | "ia"
  >("livres");
  const [imagensQualidade, setImagensQualidade] = useState<
    "economica" | "media"
  >("economica");
  const [semFatos, setSemFatos] = useState(false);
  const [job, setJob] = useState<CriarJob | null>(null);
  const [error, setError] = useState("");
  const active = useRef(true);
  useEffect(() => {
    active.current = true;
    void (async () => {
      try {
        const response = await fetch("/api/models");
        const data = await response.json();
        if (!active.current) return;
        const names: string[] = (data.models ?? []).map(
          (m: { name: string }) => m.name,
        );
        setModels(names);
      } catch {
        /* sem Ollama: o usuário ainda pode digitar o modelo ou usar llama.cpp */
      }
    })();
    return () => {
      active.current = false;
    };
  }, []);
  useEffect(() => {
    void fetch("/api/modelos-locais")
      .then((response) => (response.ok ? response.json() : null))
      .then((data) => {
        if (!active.current || !data) return;
        const list = (data.modelos ?? []).filter(
          (m: { disponivel: boolean }) => m.disponivel,
        );
        setLocalModels(list);
        setModeloLocal((current) =>
          list.some((m: { id: string }) => m.id === current)
            ? current
            : ((list.find((m: { padrao?: boolean }) => m.padrao) ?? list[0])
                ?.id ?? current),
        );
      })
      .catch(() => {
        /* sem lista: o motor completo continua disponível */
      });
  }, []);
  useEffect(() => {
    void fetch("/api/providers")
      .then((response) => (response.ok ? response.json() : null))
      .then((data: Providers | null) => {
        if (!active.current) return;
        setProviders(data);
        // O antigo padrão salvo no navegador não deve esconder o padrão atual do servidor.
        const current = data?.openai.default_model;
        if (provider === "openai" && current) {
          setModel((m) => (m === LEGACY_OPENAI_DEFAULT ? current : m));
        }
      })
      .catch(() => {
        /* configuração desconhecida; servidor valida no envio */
      });
  }, []);

  const chooseProvider = (value: Provider) => {
    store(`criar.${provider}.model`, model);
    store("criar.provider", value);
    setProvider(value);
    setPesquisar(documents.length === 0 && value !== "openai");
    setModel(
      stored(
        `criar.${value}.model`,
        value === "openai"
          ? (providers?.openai.default_model ?? "gpt-4.1-mini")
          : value === "llamacpp"
            ? "local"
            : (models[0] ?? "qwen3:4b-instruct"),
      ),
    );
  };

  const checkSearx = async () => {
    setSearx({ ok: false, message: "Verificando o SearXNG…" });
    try {
      const response = await fetch("/api/searxng/status");
      const data = await response.json();
      if (active.current) setSearx(data);
    } catch {
      if (active.current)
        setSearx({
          ok: false,
          message: "Não foi possível consultar o servidor.",
        });
    }
  };
  useEffect(() => {
    void checkSearx();
  }, []);

  const criar = async () => {
    onBusy(true);
    setError("");
    setJob(null);
    store(`criar.${provider}.model`, model);
    store("criar.motor", motor);
    store("criar.modeloLocal", modeloLocal);
    onStatus(
      motor === "celular"
        ? "Criando apresentação com o pipeline do celular…"
        : pesquisar
          ? "Criando apresentação com pesquisa…"
          : "Criando apresentação…",
    );
    try {
      let current = await request<CriarJob>("criar", {
        pedido,
        documentos: documents.map((d) => d.id),
        fontes: documents.length
          ? pesquisar
            ? "documentos+internet"
            : "documentos"
          : null,
        model: provider === "llamacpp" ? model || "local" : model,
        provider,
        slides,
        candidatos,
        buscador: pesquisar ? "searxng" : "nenhum",
        tema,
        imagens,
        imagens_fonte: imagensFonte,
        imagens_ia_qualidade: imagensQualidade,
        lote,
        permitir_sem_fatos: semFatos || (!pesquisar && !documents.length),
        max_calls: maxCalls,
        max_output_tokens: maxOutput,
        motor,
        modelo_local: motor === "celular" ? modeloLocal : null,
      });
      while (active.current) {
        setJob(current);
        if (current.state === "failed")
          throw new Error(current.error ?? "Criação interrompida.");
        if (current.state === "completed") {
          const r = current.result;
          if (r?.source && r.ir) {
            onLoad(r.source, r.ir, r.diagnostics ?? []);
            onStatus(
              r.report.valid
                ? "Apresentação criada e carregada no editor. Revise os fatos citados."
                : "Apresentação carregada com pendências; veja os diagnósticos.",
            );
          } else onStatus("Criação terminou sem cena; veja os diagnósticos.");
          break;
        }
        await new Promise((resolve) => setTimeout(resolve, 1500));
        const response = await fetch("/api/criar/" + current.id);
        if (!response.ok)
          throw new Error("Não foi possível acompanhar a criação.");
        current = await response.json();
      }
    } catch (e) {
      const message = e instanceof Error ? e.message : String(e);
      if (active.current) {
        setError(message);
        onStatus(message);
      }
    } finally {
      if (active.current) onBusy(false);
    }
  };

  const result = job?.result;
  const edit = async (payload: Record<string, unknown>) => {
    if (!job || editing) return;
    setEditing(true);
    setError("");
    onBusy(true);
    try {
      const updated = await request<CriarJob>(
        `criar/${job.id}/editar`,
        payload,
      );
      setJob(updated);
      if (updated.result?.source && updated.result.ir)
        onLoad(
          updated.result.source,
          updated.result.ir,
          updated.result.diagnostics ?? [],
        );
      onStatus("Edição salva. O consumo inclui todas as versões.");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      // Failed model attempts are persisted and still count toward total consumption.
      const response = await fetch(`/api/criar/${job.id}`).catch(() => null);
      if (response?.ok) setJob(await response.json());
    } finally {
      setEditing(false);
      onBusy(false);
    }
  };
  return (
    <section
      className="generation-panel criar-panel"
      aria-label="Criar com pesquisa"
    >
      <h2>
        Criar com pesquisa <span className="badge">novo</span>
      </h2>
      <p className="criar-help">
        O modelo pesquisa na internet, extrai fatos com fonte, planeja o roteiro
        e escreve cada slide na SlideDSL Alto. O resultado abre aqui para
        edição.
      </p>
      <label>
        Pedido
        <textarea
          aria-label="Pedido para criar com pesquisa"
          value={pedido}
          maxLength={4000}
          disabled={disabled}
          onChange={(e) => setPedido(e.target.value)}
        />
      </label>
      <BaseDocuments
        documents={documents}
        disabled={disabled}
        onWorking={setUploading}
        onChange={(value) => {
          setDocuments(value);
          if (value.length) setPesquisar(false);
        }}
      />
      <div className="generation-options">
        <label>
          Motor
          <select
            aria-label="Motor de geração"
            value={motor}
            disabled={disabled}
            onChange={(e) => {
              const value = e.target.value as "celular" | "completo";
              setMotor(value);
              if (value === "celular")
                setSlides((n) => Math.max(4, Math.min(8, n)));
            }}
          >
            <option value="celular">Igual ao celular · modelo local</option>
            <option value="completo">Completo · pesquisa e imagens</option>
          </select>
        </label>
        {motor === "celular" ? (
          <label>
            Modelo GGUF
            <select
              aria-label="Modelo GGUF"
              value={modeloLocal}
              disabled={disabled || !localModels.length}
              onChange={(e) => setModeloLocal(e.target.value)}
            >
              {localModels.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.rotulo}
                </option>
              ))}
            </select>
          </label>
        ) : null}
        {motor === "completo" ? (
          <>
            <label>
              Provedor
              <select
                aria-label="Provedor"
                value={provider}
                disabled={disabled}
                onChange={(e) => chooseProvider(e.target.value as Provider)}
              >
                <option value="ollama">Ollama · local</option>
                <option value="llamacpp">llama.cpp · local</option>
                <option value="openai">OpenAI · API paga</option>
              </select>
            </label>
            <label>
              Modelo
              {provider === "ollama" && models.includes(model) ? (
                <select
                  aria-label="Modelo para criar"
                  value={model}
                  disabled={disabled}
                  onChange={(e) => setModel(e.target.value)}
                >
                  {models.map((m) => (
                    <option key={m}>{m}</option>
                  ))}
                </select>
              ) : (
                <input
                  aria-label="Modelo para criar"
                  value={model}
                  disabled={disabled}
                  onChange={(e) => setModel(e.target.value)}
                />
              )}
            </label>
          </>
        ) : null}
        <label>
          Slides
          <input
            aria-label="Número de slides"
            type="number"
            min={motor === "celular" ? 4 : 3}
            max={motor === "celular" ? 8 : 12}
            value={slides}
            disabled={disabled}
            onChange={(e) =>
              setSlides(
                motor === "celular"
                  ? Math.max(4, Math.min(8, Number(e.target.value)))
                  : Math.max(3, Math.min(12, Number(e.target.value))),
              )
            }
          />
        </label>
        <label>
          Versões por slide
          <input
            aria-label="Versões por slide"
            type="number"
            min={1}
            max={4}
            value={candidatos}
            disabled={disabled}
            onChange={(e) =>
              setCandidatos(Math.max(1, Math.min(4, Number(e.target.value))))
            }
          />
        </label>
        <label>
          Tema
          <select
            aria-label="Tema"
            value={tema}
            disabled={disabled}
            onChange={(e) => setTema(e.target.value as Estilo)}
          >
            <option value="auto">Automático (sugerido)</option>
            <option value="claro">Clássico (azul)</option>
            <option value="editorial">Editorial (creme e terracota)</option>
            <option value="vibrante">Vibrante (roxo e amarelo)</option>
            <option value="natural">Natural (verde)</option>
            <option value="noturno">Noturno (escuro e ciano)</option>
            <option value="escuro">Escuro (azul-marinho)</option>
          </select>
        </label>
      </div>
      {provider === "openai" && (
        <p className="criar-help" role="status">
          {providers?.openai.configured
            ? "OpenAI configurada no servidor. Cada geração pode consumir créditos da API."
            : providers
              ? "Configure OPENAI_API_KEY no ambiente do servidor e reinicie a aplicação."
              : "Configuração OpenAI ainda não verificada."}
        </p>
      )}
      <details className="generation-advanced">
        <summary>Pesquisa e opções avançadas</summary>
        <label className="strict-option">
          <input
            type="checkbox"
            checked={pesquisar}
            disabled={disabled}
            onChange={(e) => setPesquisar(e.target.checked)}
          />
          Pesquisar na internet com o SearXNG local
        </label>
        <label>
          Limite de chamadas
          <input
            aria-label="Limite de chamadas"
            type="number"
            min={1}
            max={200}
            value={maxCalls}
            disabled={disabled}
            onChange={(e) =>
              setMaxCalls(Math.max(1, Math.min(200, Number(e.target.value))))
            }
          />
        </label>
        {provider === "openai" && (
          <label>
            Máximo de tokens de saída por chamada
            <input
              aria-label="Máximo de tokens de saída"
              type="number"
              min={256}
              max={8192}
              value={maxOutput}
              disabled={disabled}
              onChange={(e) =>
                setMaxOutput(
                  Math.max(256, Math.min(8192, Number(e.target.value))),
                )
              }
            />
          </label>
        )}
        <p className="criar-help">
          Pesquisa, verificações e reparos também contam. O limite de chamadas
          não é um teto exato de gasto em dólares.
        </p>
        <label className="strict-option">
          <input
            type="checkbox"
            checked={imagens}
            disabled={disabled}
            onChange={(e) => setImagens(e.target.checked)}
          />
          Buscar imagens licenciadas
        </label>
        {imagens && motor === "completo" && (
          <div className="image-source-options">
            <label>
              Fonte das imagens{" "}
              <select
                aria-label="Fonte das imagens"
                value={imagensFonte}
                disabled={disabled}
                onChange={(e) =>
                  setImagensFonte(
                    e.target.value as "livres" | "livres_ia" | "ia",
                  )
                }
              >
                <option value="livres">
                  Só fotos livres (Openverse/NASA) · grátis
                </option>
                <option value="livres_ia">
                  Fotos livres; IA quando faltar · pago só se faltar
                </option>
                <option value="ia">Só imagens geradas por IA · pago</option>
              </select>
            </label>
            {imagensFonte !== "livres" && (
              <label>
                Qualidade da imagem por IA{" "}
                <select
                  aria-label="Qualidade da imagem por IA"
                  value={imagensQualidade}
                  disabled={disabled}
                  onChange={(e) =>
                    setImagensQualidade(e.target.value as "economica" | "media")
                  }
                >
                  <option value="economica">
                    Econômica · gpt-image-2 baixa · ~US$ 0,005 por imagem
                  </option>
                  <option value="media">
                    Média · gpt-image-1-mini média · ~US$ 0,015 por imagem
                  </option>
                </select>
              </label>
            )}
            {imagensFonte !== "livres" && (
              <p className="hint">
                Até 3 imagens por IA por apresentação (máx. ~US${" "}
                {imagensQualidade === "media" ? "0,045" : "0,015"}). Preços
                oficiais de 01/11/2026; o valor real aparece no consumo.
              </p>
            )}
          </div>
        )}
        <label className="strict-option">
          <input
            type="checkbox"
            checked={lote}
            disabled={disabled}
            onChange={(e) => setLote(e.target.checked)}
          />
          Gerar em lote (todos os slides numa chamada; menos tokens)
        </label>
        <label className="strict-option">
          <input
            type="checkbox"
            checked={semFatos}
            disabled={disabled}
            onChange={(e) => setSemFatos(e.target.checked)}
          />
          Continuar mesmo se a pesquisa não achar fatos
        </label>
      </details>
      {pesquisar && (
        <p
          className={searx?.ok ? "criar-help" : "generation-error"}
          role="status"
        >
          {searx?.message ?? "Estado do SearXNG desconhecido."}{" "}
          <button
            type="button"
            disabled={disabled}
            onClick={() => void checkSearx()}
          >
            Verificar de novo
          </button>
        </p>
      )}
      <button
        className="primary"
        disabled={
          disabled ||
          uploading ||
          !model.trim() ||
          pedido.trim().length < 3 ||
          (provider === "openai" && providers?.openai.configured === false)
        }
        onClick={() => void criar()}
      >
        Criar apresentação
      </button>
      {error && (
        <p className="generation-error" role="alert">
          {error}
        </p>
      )}
      <UsageSummary usage={job?.usage ?? result?.report.usage} />
      {result?.report.theme && <p>Estilo escolhido: {result.report.theme}</p>}
      {result?.alto && result.ir && (
        <AltoSlideEdits
          deck={result.ir}
          disabled={disabled || editing}
          canUndo={Boolean(job?.history?.length)}
          edit={edit}
        />
      )}
      {job && (
        <div className="generation-progress" aria-live="polite">
          <p>
            {job.state === "queued"
              ? "Na fila"
              : job.state === "running"
                ? "Criando…"
                : job.state === "completed"
                  ? "Concluído"
                  : "Interrompido"}
          </p>
          <ol>
            {job.events.slice(-14).map((event, i) => (
              <li key={i}>{event.message}</li>
            ))}
          </ol>
          {result && (
            <p>
              {result.report.valid
                ? "PowerPoint gerado."
                : "Terminou com pendências."}{" "}
              {result.report.facts ?? 0} fatos de {result.report.sources ?? 0}{" "}
              fontes · {result.report.calls} chamadas · {result.report.seconds}s
              · pasta <code>{result.folder}</code>
            </p>
          )}
        </div>
      )}
      {result?.report.coverage && result.report.coverage.length > 0 && (
        <details open>
          <summary>
            Cobertura do pedido (
            {result.report.coverage.filter((c) => c.coberto).length}/
            {result.report.coverage.length})
          </summary>
          <ul className="criar-facts">
            {result.report.coverage.map((c) => (
              <li key={c.topico}>
                {c.coberto ? "✔" : "✘"} {c.topico}
                {c.coberto
                  ? ` · slide ${c.slides_visiveis.join(", ")}`
                  : " · não tratado"}
              </li>
            ))}
          </ul>
        </details>
      )}
      {result?.report.unsupported && result.report.unsupported.length > 0 && (
        <details open>
          <summary>
            Frases a revisar: os fatos citados não as sustentam (
            {result.report.unsupported.length})
          </summary>
          <ul className="criar-facts">
            {result.report.unsupported.map((u, i) => (
              <li key={i}>
                <strong>Slide {u.slide}:</strong> “{u.texto}” — {u.motivo}
              </li>
            ))}
          </ul>
        </details>
      )}
      {result?.facts && result.facts.length > 0 && (
        <details>
          <summary>Fatos usados ({result.facts.length})</summary>
          <ol className="criar-facts">
            {result.facts.map((f) => (
              <li key={f.id}>
                <strong>{f.id}</strong> {f.claim}{" "}
                {f.url.startsWith("documento:") ? (
                  <span>
                    {f.source_title} · {f.url.split("#")[1]}
                  </span>
                ) : (
                  <a href={f.url} target="_blank" rel="noreferrer">
                    {f.source_title}
                  </a>
                )}
              </li>
            ))}
          </ol>
        </details>
      )}
      {result?.alto && (
        <details>
          <summary>Código SlideDSL Alto</summary>
          <pre className="criar-code">{result.alto}</pre>
        </details>
      )}
    </section>
  );
}
