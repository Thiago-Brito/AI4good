# Plano para o Codex — slides bons e baratos + comparação com "IA faz tudo"

Data: 01/11/2026 · Planejador: Claude · Executor: Codex · Branch: `feature/slidedsl-api-voz-mobile`.
Leia antes: `AGENTS.md`, `docs/CONTINUIDADE_API_VOZ_MOBILE.md`, `docs/PLANO_API_VOZ_MOBILE.md` (seção 10).

## Objetivo

1. Melhorar a qualidade dos decks gerados pelo fluxo Alto com OpenAI (texto e imagem)
   sem aumentar muito o consumo.
2. Medir, com o mesmo pedido e o mesmo modelo, o fluxo **B (IA planeja conteúdo, compilador
   compõe)** contra o fluxo **A (IA escreve a SlideDSL 1.1 detalhada, "faz tudo")**.

## Regras

- Rodar tudo a partir de `code/slidedsl`. Python: `.\.venv\Scripts\python.exe`.
- Nunca imprimir, copiar ou registrar o conteúdo de `.env` ou `OPENAI_API_KEY`.
- Nunca desativar verificação TLS (`verify=False` é proibido).
- Não fazer commit, push, stash, `git add .` nem limpar arquivos não rastreados.
- Não sobrescrever resultados antigos em `outputs/`; criar pastas novas.
- **Orçamento de API do experimento inteiro: US$ 1,00.** Abortar se a soma observada passar disso.
  Modelo: `gpt-4.1-mini` (tarifa já configurada no `.env`). Uso ausente = desconhecido, nunca zero.
- pytest no sandbox: `-p no:cacheprovider --basetemp outputs\_pt` e apagar `outputs\_pt` no fim.

## Tarefa 1 — Rede atrás do antivírus (pré-requisito para imagens)

O Kaspersky intercepta TLS; o Windows confia na raiz dele, o `certifi` não. `openai_model.py`
já usa `ssl.create_default_context()`. Centralizar isso num helper pequeno e aplicá-lo aos
clientes HTTPS de `research.py` e `media.py` (Wikimedia/busca). Teste unitário: o cliente
recebe `SSLContext` com `CERT_REQUIRED`. Verificar de verdade: uma busca de imagem
real (`media.automatic_search`) deve funcionar.

## Tarefa 2 — Qualidade barata no fluxo Alto (`alto_generation.py`)

Cada item precisa de teste offline (modelo simulado) e não pode adicionar chamadas extras
no caminho feliz.

1. **Capa sem autoria inventada.** O modelo não pode inventar autor/organização/data.
   Só usar autor se estiver no pedido; caso contrário, campo vazio. Reforçar no prompt e
   validar no código (descartar autor ausente do pedido).
2. **Sem repetição entre slides.** O prompt de cada slide recebe o roteiro e um resumo curto
   (título + itens) dos slides já escritos, com instrução de não repetir. Checagem local
   determinística de sobreposição de itens (ex.: tokens normalizados/Jaccard); só se passar
   do limiar, um reparo direcionado, dentro do limite de reparos existente.
3. **Imagens úteis.** Com `images=True` e deck ≥ 4 slides, o roteiro deve propor ao menos um
   slide `imagem` com `busca_imagem` concreta em inglês. A imagem vem da Wikimedia licenciada
   (`resolve_images`, custo de tokens zero). Se não houver imagem, o fallback em tópicos atual continua.
4. Conferir que o texto cabe (já existem regras de design/overflow): não aumentar o limite,
   apenas garantir que o prompt peça itens curtos condizentes com o layout.

## Tarefa 3 — Experimento comparativo

Criar `scripts/comparar_alto_vs_sld.py` (fora do pytest; cobra API) e briefs congelados em
`experiments/comparacao/briefs/` (criar a pasta): **3 temas × 5 slides**, em português,
cada um com público e objetivo. Sugestão: fotossíntese para ensino médio; introdução a Git
para calouros; energia solar residencial para leigos. Mesmo texto do brief para todas as condições.

Condições (mesmo modelo, temperatura 0.2, seed 42):

| Id | Descrição | Como |
| --- | --- | --- |
| A | IA faz tudo: escreve `.sld` 1.1 completo (layout, coordenadas, estilos) | `generation.generate_file(provider="openai", repair_max=2)` com o brief |
| B | IA planeja conteúdo; compilador compõe; sem imagens | `create_presentation` Alto, candidatos=1, reparos=1, sem pesquisa |
| B+img | Igual a B, com imagens Wikimedia | `images=True` |

Para A, usar `models.model_usage.RecordedModel` (ou equivalente) para somar uso de todas as
rodadas, inclusive reparos; não usar só o último `metadata.usage`. Compilar o `.sld` válido
para PPTX pelo mesmo renderer. Se A não validar após os reparos, registrar como falha (com custo).

Métricas por execução (CSV + JSON): condição, tema, chamadas, tokens de entrada/saída/cache,
custo USD, tempo, válido (sim/não), rodadas de reparo, diagnósticos ERRO/AVISO por tipo
(overflow, sobreposição, fora da área etc.), slides entregues vs pedidos, imagens incluídas,
caracteres de texto visível, repetição entre slides (mesma métrica da tarefa 2.2),
PPTX gerado (sim/não).

Visual: gerar PNG de cada slide (usar ferramenta existente: `scripts/preview_powerpoint.ps1`
via PowerPoint COM, ou `ir_preview`/`capture_visual_comparison.mjs`; dizer qual foi usada) e
uma folha de contato por execução, para inspeção humana. Prévia não é prova do PPTX final:
registrar qual renderizador foi usado.

Saída: `outputs/comparacao_alto_sld/<AAAAMMDD-HHMM>/` com `resultados.csv`, `resultados.json`,
uma pasta por execução (brief, artefatos, uso, PNGs) e `RELATORIO.md` com:
tabela por condição (médias e valores individuais), custo por slide válido, economia
`1 - custo_B / custo_A`, falhas, observações visuais e **limitações** (amostra de 3 temas,
1 repetição, um modelo; A não tem busca de imagem; não generalizar).

## Tarefa 4 — Verificação e registros

- Rodar pytest completo e `ruff check src tests scripts`; tudo deve passar.
- Atualizar `docs/CONTINUIDADE_API_VOZ_MOBILE.md`, `ROADMAP.md` e `docs/PROGRESSO.md` com o
  que foi feito, números reais e caminhos de evidência. Nada de promessa não medida.

## Mensagem final esperada

Resumo curto: arquivos alterados, testes (contagem), custo total gasto, tabela A vs B vs B+img
(tokens, custo, válidos, diagnósticos), caminho do relatório e das PNGs, problemas encontrados.
