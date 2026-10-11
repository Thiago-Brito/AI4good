import { useEffect, useRef, useState } from "react";
import { request } from "./api";
import type { Deck, Diagnostic } from "./types";
import { ContextPanel, type ContextOptions } from "./ContextPanel";

type GenerationResult = {
  request?: string;
  plan?: Record<string, unknown> | null;
  source: string | null;
  ir: Deck | null;
  generated_ir?: Deck | null;
  report: {
    compile_success: boolean;
    valid: boolean;
    diagnostics: Diagnostic[];
    corrections: number;
    availability: string;
    requirements: RequirementReport;
    syntax?: boolean;
    semantics?: boolean;
    geometry?: boolean | null;
    settings?: ContextOptions;
    images?: {
      id: string;
      attribution: string;
      page: string;
      license_url: string;
    }[];
    source_audit?: {
      associations: {
        id: string;
        slide: number;
        document_name: string;
        page: number | null;
        text: string;
      }[];
      issues: { code: string; message: string; slide: number }[];
    };
    manual_edits?: {
      element?: string;
      field?: string;
      decision?: string;
      conflict?: boolean | string;
    }[];
    source_conflict?: boolean;
  };
  path: string;
};
type RequirementItem = {
  id: string;
  kind: string;
  slide: number | null;
  minimum: number;
  distinct_colors: boolean;
  value: string;
  description: string;
  met: boolean;
  elements: string[];
};
type RequirementReport = {
  numerator: number;
  denominator: number;
  all_met: boolean;
  details?: RequirementItem[];
  diagnostics?: Diagnostic[];
};
type Job = {
  id: string;
  state: "queued" | "running" | "completed" | "failed";
  events: {
    stage: string;
    round?: number;
    slide?: number;
    paths?: string[];
    diagnostics?: Diagnostic[];
  }[];
  result: GenerationResult | null;
  error: string | null;
};

export function GenerationPanel({
  disabled,
  onBusy,
  onResult,
  onStatus,
  currentDeck,
  currentSource,
}: {
  disabled: boolean;
  onBusy: (value: boolean) => void;
  onResult: (result: GenerationResult) => void;
  onStatus: (value: string) => void;
  currentDeck: Deck | null;
  currentSource: string;
}) {
  const [models, setModels] = useState<string[]>([]);
  const [model, setModel] = useState("");
  const [prompt, setPrompt] = useState(
    "Crie uma apresentação de cinco slides sobre arquitetura de software, contendo introdução, componentes, comparação, vantagens e conclusão.",
  );
  const [strategy, setStrategy] = useState("D");
  const [strict, setStrict] = useState(true);
  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState("");
  const [repairMax, setRepairMax] = useState(2);
  const [context, setContext] = useState<ContextOptions | null>(null);
  const [mediaBindings, setMediaBindings] = useState<Record<string, string>>(
    {},
  );
  const [requirements, setRequirements] = useState<RequirementReport | null>(
    null,
  );
  const active = useRef(true);
  useEffect(() => {
    active.current = true;
    return () => {
      active.current = false;
    };
  }, []);
  const loadModels = async () => {
    try {
      const response = await fetch("/api/models");
      if (!response.ok)
        throw new Error("Não foi possível consultar os modelos locais.");
      const data = await response.json();
      if (!active.current) return;
      const names: string[] = data.models.map((m: { name: string }) => m.name);
      setModels(names);
      setModel((old) =>
        names.includes(old)
          ? old
          : names.includes("qwen3:4b-instruct")
            ? "qwen3:4b-instruct"
            : (names[0] ?? ""),
      );
      setError(
        data.available
          ? names.length
            ? ""
            : "Nenhum modelo instalado no Ollama."
          : data.error,
      );
    } catch (e) {
      if (active.current) setError(e instanceof Error ? e.message : String(e));
    }
  };
  useEffect(() => {
    void loadModels();
  }, []);
  const criteria = () =>
    (requirements?.details ?? []).map((r) => ({
      id: r.id,
      kind: r.kind,
      slide: r.slide,
      minimum: r.minimum,
      distinct_colors: r.distinct_colors,
      value: r.value,
      description: r.description,
    }));
  const revalidate = async () => {
    if (!currentDeck) return;
    onBusy(true);
    try {
      const result = await request<RequirementReport>("requirements/validate", {
        ir: currentDeck,
        source: currentSource,
        requirements: criteria(),
      });
      setRequirements(result);
      onStatus(
        `Requisitos verificados: ${result.numerator}/${result.denominator}.`,
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      onBusy(false);
    }
  };
  const generate = async (repair = false) => {
    const previous = job;
    if (!repair) setMediaBindings({});
    onBusy(true);
    setError("");
    setJob(null);
    onStatus("Geração local em andamento…");
    try {
      let current = await request<Job>("generations", {
        model,
        prompt: repair ? (previous?.result?.request ?? prompt) : prompt,
        strategy,
        strict,
        reliability: true,
        repair_max: repairMax,
        ...(context && (strategy === "C" || strategy === "D")
          ? {
              context: repair
                ? { ...previous?.result?.report.settings, ...context }
                : context,
            }
          : {}),
        ...(repair
          ? {
              plan: previous?.result?.plan,
              requirements: criteria(),
              base_ir: previous?.result?.generated_ir ?? previous?.result?.ir,
              current_ir: currentDeck,
              base_source: currentSource,
              media_bindings: mediaBindings,
            }
          : {}),
      });
      while (active.current) {
        setJob(current);
        if (current.state === "failed")
          throw new Error(current.error ?? "Geração interrompida.");
        if (current.state === "completed") {
          if (current.result) {
            setRequirements(current.result.report.requirements);
            onResult(current.result);
          }
          break;
        }
        await new Promise((resolve) => setTimeout(resolve, 1000));
        if (!active.current) break;
        const response = await fetch("/api/generations/" + current.id);
        if (!response.ok)
          throw new Error(
            "Não foi possível acompanhar a geração; os registros foram preservados.",
          );
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
  return (
    <section className="generation-panel" aria-label="Geração com IA local">
      <h2>Gerar com IA local</h2>
      <div className="generation-options">
        <label>
          Modelo local
          <select
            aria-label="Modelo local"
            value={model}
            disabled={disabled}
            onChange={(e) => setModel(e.target.value)}
          >
            {models.map((name) => (
              <option key={name}>{name}</option>
            ))}
          </select>
        </label>
        <button disabled={disabled} onClick={() => void loadModels()}>
          Atualizar modelos
        </button>
        <label>
          Estratégia
          <select
            aria-label="Estratégia de geração"
            value={strategy}
            disabled={disabled}
            onChange={(e) => setStrategy(e.target.value)}
          >
            <option value="A">A · Código direto</option>
            <option value="B">B · JSON com coordenadas</option>
            <option value="C">C · Plano e layouts automáticos</option>
            <option value="D">D · Plano, layouts e correções</option>
          </select>
        </label>
        <label className="strict-option">
          <input
            type="checkbox"
            checked={strict}
            disabled={disabled}
            onChange={(e) => setStrict(e.target.checked)}
          />
          Validação estrita
        </label>
      </div>
      <label>
        Pedido da apresentação
        <textarea
          aria-label="Pedido da apresentação"
          value={prompt}
          disabled={disabled}
          onChange={(e) => setPrompt(e.target.value)}
        />
      </label>
      <label>
        Limite de correções
        <input
          aria-label="Limite de correções"
          type="number"
          min={0}
          max={10}
          value={repairMax}
          disabled={disabled}
          onChange={(e) =>
            setRepairMax(Math.max(0, Math.min(10, Number(e.target.value))))
          }
        />
      </label>
      <button
        className="primary"
        disabled={disabled || !model || !prompt.trim()}
        onClick={() => void generate()}
      >
        Gerar apresentação
      </button>
      <ContextPanel
        disabled={disabled}
        value={context}
        onChange={setContext}
        plan={job?.result?.plan}
        bindings={mediaBindings}
        onBindings={setMediaBindings}
      />
      {error && (
        <p className="generation-error" role="alert">
          {error}
        </p>
      )}
      {job && (
        <div className="generation-progress" aria-live="polite">
          <p>
            {job.state === "queued"
              ? "Aguardando geração"
              : job.state === "running"
                ? "Gerando apresentação…"
                : "Execução encerrada"}
          </p>
          <ol>
            {job.events.map((event, i) => (
              <li key={i}>
                {event.stage === "planning"
                  ? "Planejamento do conteúdo"
                  : event.stage === "repair"
                    ? `Correção ${event.round} de ${repairMax}`
                    : event.stage === "slide"
                      ? `Slide ${event.slide}`
                      : "Validação"}
                {event.paths?.length ? ` · ${event.paths.join(", ")}` : ""}
                {event.diagnostics?.length
                  ? ` · ${event.diagnostics.map((d) => d.code).join(", ")}`
                  : ""}
              </li>
            ))}
          </ol>
          {job.result && (
            <p>
              {job.result.report.compile_success
                ? "PowerPoint gerado."
                : "Geração terminou com pendências."}{" "}
              Correções: {job.result.report.corrections}. Critérios estruturais
              identificados: {job.result.report.requirements.numerator}/
              {job.result.report.requirements.denominator}. Revise o conteúdo e
              o atendimento ao pedido.
            </p>
          )}
        </div>
      )}
      {requirements?.details && (
        <div aria-label="Requisitos do pedido">
          {job?.result?.report.syntax !== undefined && (
            <p>
              Sintaxe: {job.result.report.syntax ? "válida" : "pendente"}.
              Semântica: {job.result.report.semantics ? "válida" : "pendente"}.
              Geometria:{" "}
              {job.result.report.geometry === null
                ? "não alcançada"
                : job.result.report.geometry
                  ? "válida"
                  : "pendente"}
              . Qualidade visual: requer inspeção humana.
            </p>
          )}
          <h3>
            Requisitos identificados: {requirements.numerator}/
            {requirements.denominator}
          </h3>
          <p>
            Reconhecimento limitado a padrões em português. Revise requisitos
            não identificados, conteúdo e aparência.
          </p>
          <ul>
            {requirements.details.map((r) => (
              <li key={r.id}>
                {r.met ? "Atendido" : "Pendente"}: {r.description}
                {r.slide ? ` · slide ${r.slide}` : ""}
                {r.elements.length ? ` · ${r.elements.join(", ")}` : ""}
              </li>
            ))}
          </ul>
          <button
            disabled={disabled || !currentDeck}
            onClick={() => void revalidate()}
          >
            Revalidar requisitos
          </button>
          <button
            disabled={
              disabled ||
              !job?.result?.plan ||
              (repairMax === 0 && Object.keys(mediaBindings).length === 0) ||
              !currentDeck
            }
            onClick={() => void generate(true)}
          >
            Corrigir pendências
          </button>
          {job?.result?.plan &&
            JSON.stringify(currentDeck) !== JSON.stringify(job.result.ir) && (
              <p>
                Há edições manuais. A correção preserva campos editados por ID e
                registra conflitos; revalide a cena combinada.
              </p>
            )}
        </div>
      )}
      {job?.result?.report.source_conflict && (
        <p role="alert">
          Há conteúdo sem suporte nas fontes declaradas. O PPTX desta geração
          foi bloqueado; revise os trechos e os diagnósticos.
        </p>
      )}
      {job?.result?.report.source_audit && (
        <details>
          <summary>Rastreabilidade das fontes</summary>
          <ul>
            {job.result.report.source_audit.associations.map((s, i) => (
              <li key={i}>
                Slide {s.slide} · {s.document_name} ·{" "}
                {s.page ? `página ${s.page}` : "sem paginação"} · {s.id}
                <blockquote>{s.text}</blockquote>
              </li>
            ))}
          </ul>
          <ul>
            {job.result.report.source_audit.issues.map((s, i) => (
              <li key={i}>
                {s.code} · slide {s.slide}: {s.message}
              </li>
            ))}
          </ul>
        </details>
      )}
      {job?.result?.report.images?.length ? (
        <details>
          <summary>Créditos das imagens usadas</summary>
          <ul>
            {job.result.report.images.map((image, i) => (
              <li key={i}>
                {image.attribution} ·{" "}
                <a href={image.page} target="_blank" rel="noreferrer">
                  Origem
                </a>{" "}
                ·{" "}
                <a href={image.license_url} target="_blank" rel="noreferrer">
                  Licença
                </a>
              </li>
            ))}
          </ul>
        </details>
      ) : null}
      {job?.result?.report.manual_edits?.length ? (
        <details>
          <summary>Edições preservadas e conflitos</summary>
          <ul>
            {job.result.report.manual_edits.map((e, i) => (
              <li key={i}>
                {e.element} {e.field}: {e.decision}{" "}
                {e.conflict ? ` · conflito: ${e.conflict}` : ""}
              </li>
            ))}
          </ul>
        </details>
      ) : null}
      {job?.state === "completed" && (
        <button
          disabled={disabled}
          onClick={() =>
            void fetch("/api/generations/" + job.id, { method: "DELETE" })
              .then((r) => {
                if (!r.ok) throw new Error("Exclusão falhou");
                setJob(null);
                onStatus(
                  "Registros do trabalho excluídos; a cena atual permanece no editor.",
                );
              })
              .catch((e) => setError(String(e)))
          }
        >
          Excluir registros deste trabalho
        </button>
      )}
    </section>
  );
}
