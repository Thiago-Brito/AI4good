import { useEffect, useState } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  ReactFlowProvider,
  type Connection,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import {
  compileDeck,
  download,
  exportDeck,
  importSource,
  updateRelation,
  validateDeck,
} from "./api";
import { DomainCard, graphFor, validConnection } from "./graph";
import { Preview } from "./Preview";
import { GenerationPanel } from "./GenerationPanel";
import type { Deck, Diagnostic, Element, RelationKind } from "./types";

const nodeTypes = { domain: DomainCard };
const initial =
  'apresentacao "Nova apresentação" {\n  tema claro\n  slide 1 {\n    adicionar texto id titulo "Meu slide" em (80,80) tamanho (1100,100) fonte titulo cor texto\n  }\n}\n';

export default function App() {
  const [source, setSource] = useState(initial),
    [deck, setDeck] = useState<Deck | null>(null),
    [slideNumber, setSlideNumber] = useState(1),
    [selected, setSelected] = useState("");
  const [diagnostics, setDiagnostics] = useState<Diagnostic[]>([]),
    [status, setStatus] = useState("Abra um programa para começar."),
    [busy, setBusy] = useState(false);
  const [relationType, setRelationType] = useState<RelationKind>("below"),
    [reference, setReference] = useState(""),
    [margin, setMargin] = useState(24),
    [idDraft, setIdDraft] = useState("");
  const slide = deck?.slides.find((s) => s.number === slideNumber);
  const element = slide?.elements.find((e) => e.id === selected);
  const graph = deck ? graphFor(deck) : { nodes: [], edges: [] };
  useEffect(() => {
    if (new URLSearchParams(window.location.search).get("demo") !== "1") return;
    let active = true;
    setBusy(true);
    void (async () => {
      try {
        const response = await fetch("/api/local-demo");
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail ?? "Demo indisponível.");
        const parsed = await importSource(data.source);
        if (!active) return;
        setSource(data.source);
        setDeck(parsed.ir);
        setDiagnostics(parsed.report.diagnostics);
        setSlideNumber(1);
        const id = parsed.ir.slides[0].elements[0]?.id ?? "";
        setSelected(id);
        setIdDraft(id);
        setStatus("Apresentação gerada pelo SLM importada.");
      } catch (e) {
        if (active) setStatus(e instanceof Error ? e.message : String(e));
      } finally {
        if (active) setBusy(false);
      }
    })();
    return () => {
      active = false;
    };
  }, []);
  const run = async (action: () => Promise<void>) => {
    setBusy(true);
    try {
      await action();
    } catch (e) {
      setStatus(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };
  const select = (id: string, n = slideNumber) => {
    setSlideNumber(n);
    setSelected(id);
    setIdDraft(id);
    setReference("");
  };
  const open = () =>
    run(async () => {
      const data = await importSource(source);
      setDeck(data.ir);
      setDiagnostics(data.report.diagnostics);
      setSlideNumber(1);
      select(data.ir.slides[0].elements[0]?.id ?? "", 1);
      setStatus("Programa importado.");
    });
  const edit = (key: keyof Element, value: string | number | null) => {
    if (!deck || !slide || !element) return;
    setDeck({
      ...deck,
      slides: deck.slides.map((s) =>
        s.number !== slideNumber
          ? s
          : {
              ...s,
              elements: s.elements.map((e) =>
                e.id !== selected ? e : { ...e, [key]: value },
              ),
            },
      ),
    });
    setDiagnostics([]);
    setStatus("Alterações pendentes de validação.");
  };
  const rename = () => {
    if (!deck || !slide || !element) return;
    if (
      !/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(idDraft) ||
      slide.elements.some((e) => e.id === idDraft && e.id !== selected) ||
      slide.groups.some((g) => g.id === idDraft)
    ) {
      setStatus("ID inválido ou duplicado.");
      return;
    }
    const old = selected;
    setDeck({
      ...deck,
      slides: deck.slides.map((s) =>
        s.number !== slideNumber
          ? s
          : {
              ...s,
              elements: s.elements.map((e) =>
                e.id === old ? { ...e, id: idDraft } : e,
              ),
              groups: s.groups.map((g) => ({
                ...g,
                members: g.members.map((m) => (m === old ? idDraft : m)),
              })),
              relations: s.relations.map((r) => ({
                ...r,
                target: r.target === old ? idDraft : r.target,
                reference: r.reference === old ? idDraft : r.reference,
              })),
            },
      ),
    });
    select(idDraft);
    setDiagnostics([]);
    setStatus("ID e referências atualizados.");
  };
  const applyRelation = (
    ref = reference,
    target = selected,
    kind = relationType,
  ) =>
    run(async () => {
      if (!deck || !ref || !target) {
        setStatus("Escolha alvo e referência.");
        return;
      }
      const data = await updateRelation(deck, slideNumber, {
        target,
        reference: ref,
        kind,
        margin,
        source_line: null,
        source_column: null,
      });
      setDeck(data.ir);
      setDiagnostics([]);
      setStatus("Relação aplicada à geometria.");
    });
  const connect = (c: Connection) => {
    if (!validConnection(c)) {
      setStatus("Portas incompatíveis.");
      return;
    }
    if (c.sourceHandle === "spatial") {
      const ref = c.source?.split(":")[1] ?? "",
        target = c.target?.split(":")[1] ?? "";
      const n = Number(c.source?.split(":")[0].slice(1));
      if (n !== slideNumber) {
        setStatus("Selecione o slide da relação antes de conectar.");
        return;
      }
      void applyRelation(ref, target);
    } else setStatus("A hierarquia já pertence ao documento.");
  };
  return (
    <main>
      <header>
        <div>
          <span className="eyebrow">PORTUGUÊS CONTROLADO → POWERPOINT</span>
          <h1>
            SlideDSL <span>Editor visual</span>
          </h1>
        </div>
        <span className="badge">16:9 · 1280 × 720</span>
      </header>
      <GenerationPanel
        disabled={busy}
        onBusy={setBusy}
        onStatus={setStatus}
        onResult={(result) => {
          setDiagnostics(result.report.diagnostics);
          setSource(result.source ?? "");
          setDeck(result.ir);
          select(result.ir?.slides[0].elements[0]?.id ?? "", 1);
          setStatus(
            result.report.compile_success
              ? "Apresentação da IA carregada. Revise os requisitos e o conteúdo."
              : "Geração encerrada com pendências. Consulte os diagnósticos.",
          );
        }}
      />
      <section className="toolbar">
        <label className="file-button">
          Abrir .sld
          <input
            aria-label="Abrir arquivo .sld"
            type="file"
            accept=".sld,.txt"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file)
                void run(async () => {
                  const text = await file.text();
                  setSource(text);
                  const data = await importSource(text);
                  setDeck(data.ir);
                  setDiagnostics(data.report.diagnostics);
                  select(data.ir.slides[0].elements[0]?.id ?? "", 1);
                  setStatus("Arquivo importado.");
                });
            }}
          />
        </label>
        <button disabled={busy} onClick={open}>
          Importar DSL
        </button>
        <button
          disabled={busy || !deck}
          onClick={() =>
            run(async () => {
              const r = await validateDeck(deck!);
              setDiagnostics(r.diagnostics);
              setStatus(
                r.valid
                  ? "Validação concluída: válido."
                  : "Validação concluída: corrija os erros.",
              );
            })
          }
        >
          Validar
        </button>
        <button
          disabled={busy || !deck}
          onClick={() =>
            run(async () => {
              const r = await exportDeck(deck!);
              setSource(r.source);
              download(
                new Blob([r.source], { type: "text/plain;charset=utf-8" }),
                "apresentacao.sld",
              );
              setStatus("DSL exportada.");
            })
          }
        >
          Exportar DSL
        </button>
        <button
          className="primary"
          disabled={busy || !deck}
          onClick={() =>
            run(async () => {
              await compileDeck(deck!);
              setStatus("PPTX gerado.");
            })
          }
        >
          Gerar PPTX
        </button>
      </section>
      <p className="status" role="status">
        {busy ? "Processando…" : status}
      </p>
      <div className="workspace">
        <aside className="slides-panel">
          <h2>Slides</h2>
          {deck?.slides.map((s) => (
            <button
              key={s.number}
              className={s.number === slideNumber ? "active" : ""}
              onClick={() => select(s.elements[0]?.id ?? "", s.number)}
            >
              <span>{String(s.number).padStart(2, "0")}</span>
              <strong>
                {s.elements.find((e) => e.role === "titulo")?.text ??
                  "Slide " + s.number}
              </strong>
              {diagnostics.some(
                (d) => d.slide === s.number && d.severity === "ERRO",
              ) && <b className="error-dot">!</b>}
            </button>
          ))}
          <h2>Elementos</h2>
          {slide?.elements.map((e) => (
            <button
              className={e.id === selected ? "active" : ""}
              key={e.id}
              onClick={() => select(e.id)}
            >
              {e.id}
            </button>
          ))}
        </aside>
        <section className="canvas-panel">
          <div className="panel-title">
            <h2>Preview geométrico</h2>
            <span>Slide {slideNumber}</span>
          </div>
          {deck && slide ? (
            <Preview
              deck={deck}
              slide={slide}
              selected={selected}
              diagnostics={diagnostics}
              onSelect={(id) => select(id)}
            />
          ) : (
            <div className="empty">
              Importe um programa .sld para visualizar a cena.
            </div>
          )}
          <details open className="source-panel">
            <summary>Programa SlideDSL</summary>
            <textarea
              aria-label="Programa SlideDSL"
              value={source}
              onChange={(e) => setSource(e.target.value)}
              spellCheck={false}
            />
          </details>
        </section>
        <aside className="properties">
          <h2>Propriedades</h2>
          {element ? (
            <>
              <label>
                ID
                <input
                  aria-label="ID"
                  value={idDraft}
                  onChange={(e) => setIdDraft(e.target.value)}
                  onBlur={rename}
                />
              </label>
              <p className="type-label">
                {element.type} · papel {element.role ?? "não definido"}
              </p>
              {element.type === "text" && (
                <label>
                  Texto
                  <textarea
                    aria-label="Texto"
                    value={element.text ?? ""}
                    onChange={(e) => edit("text", e.target.value)}
                  />
                </label>
              )}
              {element.type === "image" && (
                <label>
                  Arquivo
                  <input
                    aria-label="Arquivo"
                    value={element.file ?? ""}
                    onChange={(e) => edit("file", e.target.value)}
                  />
                </label>
              )}
              <div className="property-grid">
                {(
                  [
                    ["x", "X"],
                    ["y", "Y"],
                    ["width", "Largura"],
                    ["height", "Altura"],
                    ["z", "Z"],
                  ] as const
                ).map(([key, label]) => (
                  <label key={key}>
                    {label}
                    <input
                      aria-label={label}
                      type="number"
                      step={key === "z" ? "1" : "0.5"}
                      value={element[key]}
                      onChange={(e) => edit(key, Number(e.target.value))}
                    />
                  </label>
                ))}
                {element.type === "text" && (
                  <label>
                    Fonte
                    <input
                      aria-label="Fonte"
                      type="number"
                      value={element.font_size ?? 24}
                      onChange={(e) =>
                        edit("font_size", Number(e.target.value))
                      }
                    />
                  </label>
                )}
              </div>
              {element.type !== "image" && (
                <label>
                  Cor
                  <input
                    aria-label="Cor"
                    value={element.color ?? ""}
                    onChange={(e) => edit("color", e.target.value)}
                  />
                </label>
              )}
              <label>
                Papel
                <select
                  aria-label="Papel"
                  value={element.role ?? ""}
                  onChange={(e) => edit("role", e.target.value || null)}
                >
                  <option value="">Não definido</option>
                  {["titulo", "corpo", "decoracao", "background"].map((r) => (
                    <option key={r}>{r}</option>
                  ))}
                </select>
              </label>
              <h3>Relação espacial</h3>
              <label>
                Tipo de relação
                <select
                  aria-label="Tipo de relação"
                  value={relationType}
                  onChange={(e) =>
                    setRelationType(e.target.value as RelationKind)
                  }
                >
                  {[
                    ["below", "Abaixo de"],
                    ["right", "À direita de"],
                    ["left", "Alinhar à esquerda"],
                    ["align_right", "Alinhar à direita"],
                    ["center", "Centro horizontal"],
                    ["top", "Topo"],
                  ].map(([v, t]) => (
                    <option value={v} key={v}>
                      {t}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Referência
                <select
                  aria-label="Referência"
                  value={reference}
                  onChange={(e) => setReference(e.target.value)}
                >
                  <option value="">Selecione…</option>
                  {slide?.elements
                    .filter((e) => e.id !== selected)
                    .map((e) => <option key={e.id}>{e.id}</option>)}
                </select>
              </label>
              <label>
                Margem
                <input
                  type="number"
                  aria-label="Margem"
                  value={margin}
                  onChange={(e) => setMargin(Number(e.target.value))}
                />
              </label>
              <button disabled={busy} onClick={() => void applyRelation()}>
                Aplicar relação
              </button>
            </>
          ) : (
            <p>Selecione um objeto.</p>
          )}
        </aside>
      </div>
      <section className="diagnostics">
        <h2>
          Diagnósticos <span>{diagnostics.length}</span>
        </h2>
        {diagnostics.length ? (
          diagnostics.map((d, i) => (
            <button
              key={i}
              className={
                d.severity === "ERRO" ? "diagnostic error" : "diagnostic"
              }
              onClick={() => d.element && d.slide && select(d.element, d.slide)}
            >
              <b>
                {d.code} · {d.severity}
              </b>{" "}
              Slide {d.slide} / {d.element ?? "cena"}: {d.message}
              <small>{d.suggestion}</small>
            </button>
          ))
        ) : (
          <p>Nenhum diagnóstico exibido. Valide após editar.</p>
        )}
      </section>
      <section className="graph-panel">
        <div className="panel-title">
          <h2>Grafo do documento</h2>
          <span>
            Portas tipadas · contém_slide · contém_elemento ·
            referência_espacial
          </span>
        </div>
        <div className="graph">
          <ReactFlowProvider>
            <ReactFlow
              nodes={graph.nodes}
              edges={graph.edges}
              nodeTypes={nodeTypes}
              fitView
              isValidConnection={validConnection}
              onConnect={connect}
              onNodeClick={(_, node) => {
                const data = node.data as { id?: string; slide?: number };
                if (data.id && data.slide) select(data.id, data.slide);
              }}
            >
              <Background />
              <Controls />
            </ReactFlow>
          </ReactFlowProvider>
        </div>
      </section>
    </main>
  );
}
