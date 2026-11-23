# Fontes e protocolo da comparação — 01/11/2026

Registro anterior ao relatório experimental. Trata-se de medição local de software,
sem novas alegações científicas ou pesquisa factual dos temas dos slides.

- Protocolo autorizado: `docs/PLANO_CODEX_COMPARACAO.md`, tarefas 1–4.
- Contexto e limitações: `docs/PLANO_API_VOZ_MOBILE.md`, seção 10.
- Norma do projeto: `../../academy/papers/dsl-visual-ia/SLIDEDSL_CODEX_DO_ZERO.md`.
- Tarifas: configuração local já existente, identificada por modelo/data/moeda;
  copiar somente a tarifa pública para `uso.json`, nunca credenciais ou `.env`.
- Uso: respostas reais de Chat Completions normalizadas por `model_usage.py`;
  cache é subconjunto da entrada, todas as tentativas são somadas.
- Design: `config/design_rules.yaml` e `docs/REGRAS_DESIGN.md`.
- Repetição: implementação própria em `src/slidedsl/repetition.py`; Jaccard de
  tokens sem acentos/caixa/palavras funcionais, mínimo quatro tokens, limiar 0,72.
- Renderização: `compiler.py`/PptxGenJS para PPTX; `ir_preview.py`/Pillow para
  PNGs geométricos. PNG da IR não é evidência da renderização do arquivo no Office.
- Rede real: `outputs/comparacao_alto_sld/rede_20261101-211932/`; Commons 403,
  Openverse timeout. A política do provedor não foi contornada.

Os briefs congelados não são fontes factuais. A ausência de pesquisa limita a
confiabilidade do conteúdo; não usar os decks como referência técnica ou financeira.
