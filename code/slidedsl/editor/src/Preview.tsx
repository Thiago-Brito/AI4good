import { useLayoutEffect, useRef, useState } from "react";
import type { Deck, Diagnostic, Slide } from "./types";

export function Preview({
  deck,
  slide,
  selected,
  diagnostics,
  onSelect,
}: {
  deck: Deck;
  slide: Slide;
  selected: string;
  diagnostics: Diagnostic[];
  onSelect: (id: string) => void;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(0.5);
  useLayoutEffect(() => {
    const node = ref.current;
    if (!node) return;
    const resize = new ResizeObserver((entries) =>
      setScale(entries[0].contentRect.width / 1280),
    );
    resize.observe(node);
    return () => resize.disconnect();
  }, []);
  return (
    <div ref={ref} className="preview-shell" data-testid="preview">
      <div
        className="slide-canvas"
        style={{
          width: 1280,
          height: 720,
          transform: `scale(${scale})`,
          background: deck.theme === "claro" ? "#F6F8FC" : "#14233D",
        }}
      >
        {[...slide.elements]
          .sort((a, b) => a.z - b.z)
          .map((e) => {
            const inline = e.id.endsWith("_ref_inline")
              ? (e.text ?? "").indexOf(": ")
              : -1;
            const linked =
              e.type === "arrow" &&
              slide.relations.filter(
                (r) => r.kind === "below" && r.target === e.id,
              ).length === 1 &&
              slide.relations.filter(
                (r) => r.kind === "below" && r.reference === e.id,
              ).length === 1;
            const error = diagnostics.some(
              (d) =>
                d.slide === slide.number &&
                d.element === e.id &&
                d.severity === "ERRO",
            );
            return (
              <button
                key={e.id}
                title={e.id}
                aria-label={"Selecionar " + e.id}
                className={
                  "preview-element " +
                  (selected === e.id ? "selected " : "") +
                  (error ? "error" : "")
                }
                onClick={() => onSelect(e.id)}
                style={{
                  left: e.x,
                  top: e.y,
                  width: e.width,
                  height: e.height,
                  zIndex: e.z + 1,
                  background:
                    e.type === "rectangle" ||
                    e.type === "ellipse" ||
                    (e.type === "arrow" && !linked)
                      ? (e.color ?? "transparent")
                      : "transparent",
                  borderRadius: e.type === "ellipse" ? "50%" : 0,
                  clipPath:
                    e.type === "arrow" && !linked
                      ? "polygon(30% 0,70% 0,70% 50%,100% 50%,50% 100%,0 50%,30% 50%)"
                      : undefined,
                  color: e.color ?? undefined,
                  fontSize: ((e.font_size ?? 24) * 96) / 72,
                  fontFamily: e.font_face,
                  fontWeight: e.id.endsWith("_ref_label") ? 700 : 400,
                  textAlign: "left",
                  padding: e.type === "text" ? 8 : 0,
                  whiteSpace: "pre-wrap",
                  lineHeight: 1.2,
                }}
              >
                {e.type === "text" ? (
                  inline < 0 ? (
                    e.text
                  ) : (
                    <>
                      <strong>{e.text?.slice(0, inline + 2)}</strong>
                      {e.text?.slice(inline + 2)}
                    </>
                  )
                ) : e.type === "image" ? (
                  <img
                    alt={e.id}
                    src={"/assets/" + e.file?.replace(/^assets\//, "")}
                    draggable={false}
                  />
                ) : linked ? (
                  <svg
                    style={{ display: "block" }}
                    width="100%"
                    height="100%"
                    viewBox={`0 0 ${e.width} ${e.height}`}
                    aria-hidden="true"
                  >
                    <defs>
                      <marker
                        id={`head_${e.id}`}
                        markerWidth="6"
                        markerHeight="6"
                        refX="5"
                        refY="3"
                        orient="auto"
                      >
                        <path
                          d="M0,0 L6,3 L0,6 Z"
                          fill={e.color ?? "#2563EB"}
                        />
                      </marker>
                    </defs>
                    <line
                      x1={e.width / 2}
                      y1="0"
                      x2={e.width / 2}
                      y2={Math.max(1, e.height - 3)}
                      stroke={e.color ?? "#2563EB"}
                      strokeWidth="2"
                      markerEnd={`url(#head_${e.id})`}
                    />
                  </svg>
                ) : null}
              </button>
            );
          })}
      </div>
    </div>
  );
}
