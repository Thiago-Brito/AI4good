import { useEffect, useRef, useState } from "react";
import { request } from "./api";
import type { Deck, Diagnostic } from "./types";

type GenerationResult = {
  source: string | null;
  ir: Deck | null;
  report: {
    compile_success: boolean;
    valid: boolean;
    diagnostics: Diagnostic[];
    corrections: number;
    availability: string;
    requirements: { numerator: number; denominator: number; all_met: boolean };
  };
  path: string;
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
}: {
  disabled: boolean;
  onBusy: (value: boolean) => void;
  onResult: (result: GenerationResult) => void;
  onStatus: (value: string) => void;
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
  const generate = async () => {
    onBusy(true);
    setError("");
    setJob(null);
    onStatus("Geração local em andamento…");
    try {
      let current = await request<Job>("generations", {
        model,
        prompt,
        strategy,
        strict,
      });
      while (active.current) {
        setJob(current);
        if (current.state === "failed")
          throw new Error(current.error ?? "Geração interrompida.");
        if (current.state === "completed") {
          if (current.result) onResult(current.result);
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
            <option value="D">D · Plano, layouts e até dois reparos</option>
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
      <button
        className="primary"
        disabled={disabled || !model || !prompt.trim()}
        onClick={() => void generate()}
      >
        Gerar apresentação
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
                    ? `Correção ${event.round} de 2`
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
              básicos: {job.result.report.requirements.numerator}/
              {job.result.report.requirements.denominator}. Revise o conteúdo e
              o atendimento ao pedido.
            </p>
          )}
        </div>
      )}
    </section>
  );
}
