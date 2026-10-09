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
                    e.type === "rectangle" || e.type === "ellipse"
                      ? (e.color ?? "transparent")
                      : "transparent",
                  borderRadius: e.type === "ellipse" ? "50%" : 0,
                  color: e.color ?? undefined,
                  fontSize: ((e.font_size ?? 24) * 96) / 72,
                  fontFamily: e.font_face,
                  textAlign: "left",
                  padding: e.type === "text" ? 8 : 0,
                  whiteSpace: "pre-wrap",
                  lineHeight: 1.2,
                }}
              >
                {e.type === "text" ? (
                  e.text
                ) : e.type === "image" ? (
                  <img
                    alt={e.id}
                    src={"/assets/" + e.file?.replace(/^assets\//, "")}
                    draggable={false}
                  />
                ) : null}
              </button>
            );
          })}
      </div>
    </div>
  );
}
