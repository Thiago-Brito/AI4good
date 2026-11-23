# Rodada 6 — fontes e protocolo

Registro em 11/11/2026 antes da documentação dos resultados; texto operacional.
- Requisitos: docs/PLANO_CODEX_RODADA6_DESIGN.md e PLANO_CODEX_COMPARACAO.md.
- Base: outputs/design_r5/20261111-001430/RELATORIO.md e corpus/ (16 decks/89 slides).
- Método local: refs/DESIGN_RODADA4.md e DESIGN_RODADA5.md; métricas heurísticas,
  altura-x dos TTF locais. Não alegar preferência humana ou qualidade absoluta.
- Evidências: outputs/design_r6/20261111-004533/ciclo_1/, ciclo_2/, comparacao/,
  auditoria_pptx.json e pytest_aprovacao.xml; 32 folhas abertas pelo executor.
- Parte A offline; Parte B: teto total US$ 0,50, sem imagens por IA, sem pesquisa.
- Documentação oficial consultada somente na Parte B em 11/11/2026:
  https://developers.openai.com/api/docs/models/gpt-5.4-mini
  https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.4
  Modelo solicitado preservado com tarifa datada configurada. Não copiar .env.
- Preflight por deck: conhecido + reservas de uso desconhecido + estimativa de
  dez chamadas. Antes de cada HTTP: bytes UTF-8 + schema +4096 e limite de saída.
  Ausência de uso não é custo zero. Retomada carrega reservas do ledger anterior.
- Falha observada: seis HTTP 401 antes dos roteiros, sem tokens/custos retornados.
  outputs/testes_reais/20261111-0050/orcamento.json reserva US$ 0,09354600.
- Não editar manualmente conteúdo gerado; falhas não são decks entregues.
