import { useEffect, useRef, useState } from "react";
import { request } from "./api";
import type { Deck, Diagnostic } from "./types";

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
    pptx?: string;
    facts?: number;
    sources?: number;
    calls: number;
    seconds: number;
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
  const [model, setModel] = useState(
    stored("criar.model", "qwen3:4b-instruct"),
  );
  const [provider, setProvider] = useState<"ollama" | "llamacpp">("ollama");
  const [pedido, setPedido] = useState(
    "Monolito ou microsserviços para uma startup: quando cada um compensa",
  );
  const [slides, setSlides] = useState(6);
  const [candidatos, setCandidatos] = useState(2);
  const [tema, setTema] = useState<"claro" | "escuro">("claro");
  const [pesquisar, setPesquisar] = useState(true);
  const [searx, setSearx] = useState<{ ok: boolean; message: string } | null>(
    null,
  );
  const [imagens, setImagens] = useState(false);
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
        setModel((old) =>
          names.includes(old) || !names.length ? old : names[0],
        );
      } catch {
        /* sem Ollama: o usuário ainda pode digitar o modelo ou usar llama.cpp */
      }
    })();
    return () => {
      active.current = false;
    };
  }, []);

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
    store("criar.model", model);
    onStatus("Criando apresentação com pesquisa…");
    try {
      let current = await request<CriarJob>("criar", {
        pedido,
        model: provider === "llamacpp" ? model || "local" : model,
        provider,
        slides,
        candidatos,
        buscador: pesquisar ? "searxng" : "nenhum",
        tema,
        imagens,
        permitir_sem_fatos: semFatos || !pesquisar,
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
      <div className="generation-options">
        <label>
          Modelo
          {provider === "ollama" && models.length ? (
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
        <label>
          Slides
          <input
            aria-label="Número de slides"
            type="number"
            min={3}
            max={12}
            value={slides}
            disabled={disabled}
            onChange={(e) =>
              setSlides(Math.max(3, Math.min(12, Number(e.target.value))))
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
            onChange={(e) => setTema(e.target.value as "claro" | "escuro")}
          >
            <option value="claro">Claro</option>
            <option value="escuro">Escuro</option>
          </select>
        </label>
      </div>
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
          Provedor
          <select
            aria-label="Provedor"
            value={provider}
            disabled={disabled}
            onChange={(e) =>
              setProvider(e.target.value as "ollama" | "llamacpp")
            }
          >
            <option value="ollama">Ollama · JSON Schema</option>
            <option value="llamacpp">llama.cpp · GLC restrita (GBNF)</option>
          </select>
        </label>
        <label className="strict-option">
          <input
            type="checkbox"
            checked={imagens}
            disabled={disabled}
            onChange={(e) => setImagens(e.target.checked)}
          />
          Buscar imagens licenciadas
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
      <button
        className="primary"
        disabled={disabled || !model.trim() || pedido.trim().length < 3}
        onClick={() => void criar()}
      >
        Criar apresentação
      </button>
      {error && (
        <p className="generation-error" role="alert">
          {error}
        </p>
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
                <a href={f.url} target="_blank" rel="noreferrer">
                  {f.source_title}
                </a>
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
