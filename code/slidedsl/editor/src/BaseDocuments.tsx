import { useRef, useState } from "react";
import { request } from "./api";

export type BaseDocument = { id: string; name: string; chunk_count: number };

export function BaseDocuments({
  documents,
  onChange,
  disabled,
  onWorking,
}: {
  documents: BaseDocument[];
  onChange: (documents: BaseDocument[]) => void;
  disabled: boolean;
  onWorking: (working: boolean) => void;
}) {
  const [error, setError] = useState("");
  const [working, setWorking] = useState(false);
  const uploading = useRef(false);
  const upload = async (files: FileList | null) => {
    if (!files || disabled || uploading.current) return;
    uploading.current = true;
    setWorking(true);
    onWorking(true);
    setError("");
    const next = [...documents];
    const selectedFiles = Array.from(files);
    try {
      if (next.length + selectedFiles.length > 8)
        throw new Error("Selecione até oito arquivos.");
      for (const file of selectedFiles) {
        const limit = /\.docx$/i.test(file.name) ? 5 : 2;
        if (file.size > limit * 1024 * 1024)
          throw new Error(`${file.name}: limite de ${limit} MiB.`);
        const base64 = await new Promise<string>((resolve, reject) => {
          const reader = new FileReader();
          reader.onerror = reject;
          reader.onload = () => resolve(String(reader.result).split(",")[1]);
          reader.readAsDataURL(file);
        });
        next.push(
          await request<BaseDocument>("documents", {
            name: file.name,
            data_base64: base64,
          }),
        );
        onChange([...next]);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      uploading.current = false;
      setWorking(false);
      onWorking(false);
    }
  };
  return (
    <fieldset
      disabled={disabled || working}
      className="base-documents"
      onDragOver={(e) => e.preventDefault()}
      onDrop={(e) => {
        e.preventDefault();
        void upload(e.dataTransfer.files);
      }}
    >
      <legend>Arquivos de base</legend>
      <p>
        Arraste ou selecione TXT, MD, PDF textual e DOCX. Até 8 arquivos, 2 MiB
        cada (DOCX: 5 MiB).
      </p>
      <input
        aria-label="Arquivos de base"
        type="file"
        multiple
        accept=".txt,.md,.pdf,.docx"
        onChange={(e) => {
          void upload(e.target.files);
          e.target.value = "";
        }}
      />
      <p>
        O conteúdo vai ao provedor escolhido somente nos trechos usados. A
        extração e a seleção são locais.
      </p>
      <ul>
        {documents.map((doc) => (
          <li key={doc.id}>
            {doc.name} · {doc.chunk_count} trechos{" "}
            <button
              type="button"
              aria-label={`Remover ${doc.name}`}
              onClick={() => onChange(documents.filter((d) => d.id !== doc.id))}
            >
              Remover
            </button>
          </li>
        ))}
      </ul>
      {working && <p role="status">Lendo arquivos…</p>}
      {error && <p role="alert">{error}</p>}
    </fieldset>
  );
}
