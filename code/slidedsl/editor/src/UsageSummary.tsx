import type { Usage } from "./types";

export function UsageSummary({ usage }: { usage?: Usage | null }) {
  if (!usage) return null;
  return (
    <div
      className="usage-summary"
      aria-label="Consumo da execução"
      aria-live="polite"
    >
      <p>
        {usage.calls}/{usage.max_calls} chamadas · {usage.failed_calls} com
        falha
      </p>
      <p>
        Tokens informados: {usage.known_input_tokens.toLocaleString("pt-BR")} de
        entrada
        {" · "}
        {usage.known_output_tokens.toLocaleString("pt-BR")} de saída.
        {usage.unknown_usage_calls > 0 &&
          ` Uso desconhecido em ${usage.unknown_usage_calls} chamada(s); totais parciais.`}
      </p>
      {(usage.image_calls ?? 0) > 0 && (
        <p>
          Imagens geradas por IA: {usage.image_calls} · US${" "}
          {(usage.image_cost_usd ?? 0).toFixed(4)}
          {(usage.unknown_image_cost ?? 0) > 0 &&
            ` (${usage.unknown_image_cost} com custo desconhecido)`}
          .
        </p>
      )}
      <p>
        {usage.cost_usd === null
          ? "Custo total indisponível: tarifa ou uso não informado."
          : (usage.image_calls ?? 0) > 0
            ? `Custo total calculado (texto + imagens): US$ ${usage.cost_usd.toFixed(6)}.`
            : `Custo de texto calculado: US$ ${usage.cost_usd.toFixed(6)}. Busca e infraestrutura à parte.`}
      </p>
    </div>
  );
}
