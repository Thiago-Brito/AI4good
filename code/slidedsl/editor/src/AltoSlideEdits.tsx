import { useState } from "react";
import type { Deck, Slide } from "./types";
import { Preview } from "./Preview";

function SlideEdit({
  deck,
  slide,
  disabled,
  edit,
}: {
  deck: Deck;
  slide: Slide;
  disabled: boolean;
  edit: (payload: Record<string, unknown>) => Promise<void>;
}) {
  const [instruction, setInstruction] = useState("");
  const [photo, setPhoto] = useState("");
  const number = slide.number;
  return (
    <article aria-label={`Editar slide ${number}`}>
      <h4>Slide {number}</h4>
      <Preview
        deck={deck}
        slide={slide}
        selected=""
        diagnostics={[]}
        onSelect={() => {}}
      />
      <label>
        Instrução para o slide {number}
        <input
          value={instruction}
          disabled={disabled}
          maxLength={2000}
          onChange={(e) => setInstruction(e.target.value)}
        />
      </label>
      <button
        disabled={disabled || !instruction.trim()}
        onClick={() =>
          void edit({ acao: "refazer", slide: number, instrucao: instruction })
        }
      >
        Refazer este slide
      </button>
      <label>
        Nova foto do slide {number}
        <input
          value={photo}
          disabled={disabled}
          maxLength={200}
          placeholder="Consulta para foto livre"
          onChange={(e) => setPhoto(e.target.value)}
        />
      </label>
      <button
        disabled={disabled || !photo.trim()}
        onClick={() =>
          void edit({ acao: "ajustar", slide: number, foto_buscar: photo })
        }
      >
        Trocar foto
      </button>
      <button
        disabled={disabled}
        onClick={() => void edit({ acao: "sem_foto", slide: number })}
      >
        Remover foto
      </button>
      <button
        disabled={disabled || number === 1}
        onClick={() =>
          void edit({ acao: "ajustar", slide: number, mover_para: number - 1 })
        }
      >
        Mover antes
      </button>
      <button
        disabled={disabled || number === deck.slides.length}
        onClick={() =>
          void edit({ acao: "ajustar", slide: number, mover_para: number + 1 })
        }
      >
        Mover depois
      </button>
      <button
        disabled={disabled || deck.slides.length === 1}
        onClick={() => void edit({ acao: "excluir", slide: number })}
      >
        Excluir slide
      </button>
    </article>
  );
}

export function AltoSlideEdits({
  deck,
  disabled,
  canUndo,
  edit,
}: {
  deck: Deck;
  disabled: boolean;
  canUndo: boolean;
  edit: (payload: Record<string, unknown>) => Promise<void>;
}) {
  return (
    <section aria-label="Revisões da apresentação">
      <h3>Editar apresentação</h3>
      <button
        disabled={disabled || !canUndo}
        onClick={() => void edit({ acao: "desfazer" })}
      >
        Desfazer a última edição
      </button>
      <label>
        Trocar estilo
        <select
          aria-label="Trocar estilo"
          disabled={disabled}
          defaultValue=""
          onChange={(e) => {
            if (e.target.value)
              void edit({ acao: "ajustar", tema: e.target.value });
            e.target.value = "";
          }}
        >
          <option value="">Escolher…</option>
          {[
            "auto",
            "claro",
            "escuro",
            "editorial",
            "vibrante",
            "natural",
            "noturno",
          ].map((theme) => (
            <option key={theme}>{theme}</option>
          ))}
        </select>
      </label>
      <div className="alto-slide-edits">
        {deck.slides.map((slide) => (
          <SlideEdit
            key={slide.number}
            deck={deck}
            slide={slide}
            disabled={disabled}
            edit={edit}
          />
        ))}
      </div>
    </section>
  );
}
