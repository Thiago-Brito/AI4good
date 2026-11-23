# SlideDSL: plano de testes e APK para celular

Especificação técnica dos testes e da APK. A ordem de execução e o recorte do TCC estão em
[PLANO_TCC.md](PLANO_TCC.md); as fontes conferidas, em
[../refs/TCC_TESTES_APK_FONTES.md](../refs/TCC_TESTES_APK_FONTES.md).

## Como trabalhar

- Leia antes `README.md`, `ROADMAP.md`, `AGENTS.md` e `docs/SLIDEDSL_ALTO.md`.
- Trabalhe em etapas pequenas, uma fase por vez. Ao terminar cada fase, rode a suíte (`pytest`,
  testes Node e Playwright, como em `scripts/test_windows.ps1`) e confirme que nada quebrou.
- Não faça commit de modelos (`.gguf`), de saídas grandes (`outputs/`), de chaves de API nem do
  `searxng/.env`.
- Registre cada fase no `ROADMAP.md` no mesmo estilo das entradas atuais e documente resultados em
  `docs/`. Não declare melhora sem dados reais: separe "implementado" de "medido".
- Tudo o que roda o modelo de verdade deve ter um modo simulado (modelo mock) para os testes.
- O ambiente do autor é Windows (scripts `.ps1`). Mantenha os comandos compatíveis.
- No Windows, use `--basetemp` curto (ex.: `outputs/tests/t<hora>`): caminhos longos estouram o
  limite de 260 caracteres em `test_documentos_edicao_r7.py`.

---

# Parte 1: Testes

## Base comum

- **Pedidos:** 12, cobrindo 4 temas em 3 níveis de detalhe (só o tema, detalhado, detalhado com
  itens obrigatórios), em `benchmark/format_requests.json`.
- **Dossiê fixo:** rodar a pesquisa uma vez por pedido e salvar em `benchmark/dossies/<id>.json`.
  Todos os grupos e modos usam o mesmo dossiê; a pesquisa não entra na medição.
- **Repetições:** 5 sementes por condição.
- **Desenho pareado:** o mesmo pedido passa por todas as condições, em ordem sorteada com semente
  registrada.
- **Saída:** uma linha por execução num CSV, mais prompts e respostas preservados (como em
  `outputs/criar/<id>/`).
- **Execução retomável:** se o processo cair, continuar de onde parou sem sobrescrever.

## Fase 0: tokens e tempo por chamada — IMPLEMENTADA em 22/11/2026

O `RecordedModel` (`model_usage.py`) já gravava tokens e segundos por chamada em
`uso_chamadas.jsonl`. Foi completado com:

- Ollama: `prompt_eval_duration`, `eval_duration`, `load_duration`, `total_duration` (ns → ms) e
  `finish_reason` (= `done_reason`).
- llama.cpp: objeto `timings` (`prompt_ms`, `predicted_ms`; contagens de reserva `prompt_n`,
  `predicted_n` quando não há `usage`).
- OpenAI: `reasoning_tokens` de `completion_tokens_details`.
- Formato único por chamada: `input_tokens`, `cached_input_tokens`, `output_tokens`,
  `reasoning_tokens`, `prefill_ms`, `decode_ms`, `load_ms`, `server_total_ms`, `wall_ms`
  (`perf_counter`), `provider`, `model_*`, `finish_reason`, `thinking` (`RecordedModel.last_usage()`).
- `Call.usage` em `alto_generation.py` → cada linha de `chamadas.jsonl` traz o uso.
- `custo.json` por deck (`slidedsl.custo.v1`): totais e divisão por etapa (`research_plan`,
  `research_extract`, `document_extract`, `topicos`, `roteiro`, `lote`, `slide`, `reparo` =
  `slide` com tentativa > 0, `sustentacao`). Valores desconhecidos ficam `null` e o número de
  chamadas sem o campo é informado (`*_unknown_calls`); nunca se soma zero inventado.
- Testes: `tests/test_custo_fase0.py` (6 testes, servidores simulados).

## Teste 1: custo do formato (a IA não roda)

**Pergunta:** quantos tokens a IA precisaria escrever, em cada formato, para chegar ao mesmo slide?
**Base:** Agyemang et al. (2026), arXiv:2604.16736.

`scripts/format_cost.py`:
1. Entrada: 20 a 30 decks `.slda` (`examples/alto/` + decks gerados).
2. Compilar cada deck até a IR final com `alto_compile.py`.
3. Exportar o mesmo deck em: SlideDSL Alto (normalizado pelo printer); SlideDSL 1.1; JSON do
   conteúdo (da AST do Alto); código python-pptx gerado da IR (posições, tamanhos, fontes, cores,
   alinhamento, fundo); texto puro (régua).
4. Equivalência: rodar o python-pptx gerado e comparar com o PPTX do compilador (formas, textos,
   posições com tolerância). Se não bater, registrar como falha do exportador e não contar.
5. Tokens com o tokenizador do Qwen3: `POST /tokenize` do `llama-server` ou
   `transformers.AutoTokenizer.from_pretrained("Qwen/Qwen3-4B")` com `add_special_tokens=False`
   (dependência opcional).
6. Contar também os tokens das instruções de cada formato (gramática/exemplo, JSON Schema, nada).
7. Saída: `outputs/teste1/format_cost.csv` (slide × formato) e tabela Markdown com média, IC95% e
   multiplicador.
8. Wilcoxon pareado slide a slide entre Alto e cada formato.

## Teste 2: com e sem SlideDSL, com a IA gerando de verdade

**Base:** AutoPresent (taxa de execução, nota zero para falha); Agyemang et al. (2026).

Grupos: **A** Qwen3 local sem SlideDSL (programa python-pptx); **B** IA grande pela API sem SlideDSL
(opcional, só com chave); **C** Qwen3 local com o pipeline SlideDSL.

`src/slidedsl/format_experiment.py` + comando `slidedsl experimento-formatos`:
1. Mesmo prompt para A e B, com o dossiê: *"Escreva um programa Python usando python-pptx que crie
   uma apresentação de N slides sobre [pedido], usando estes fatos: [dossiê]. Responda só com o
   código."*
2. Execução segura: subprocesso em diretório temporário, limite de 60 s, sem rede. Guardar stdout,
   stderr e PPTX.
3. Até 2 correções devolvendo o erro ao modelo (mesmo limite de reparo do pipeline).
4. Verificador único (`scripts/pptx_checks.py`) para todos os grupos: texto fora do slide, caixas
   sobrepostas, slides faltando em relação a N, slides vazios; pontuação comparável.
5. Métricas por deck: tokens de entrada/saída, chamadas, reparos, gerou PPTX, passou no verificador,
   tempo total e **tokens por PPTX válido** (incluindo tentativas falhas).
6. Saída: `outputs/teste2/results.csv` e artefatos.

## Teste 3: tipo de restrição da saída

**Base:** Tam et al. (2024), arXiv:2408.02442; Dong et al. (2024), arXiv:2411.15100.

1. Pipeline nos modos `json`, `gramatica` (llama.cpp + GBNF) e `direto`.
2. Novo modo opcional `nl2format` (desligado por padrão): texto livre por slide e segunda chamada
   que converte para Alto.
3. Registrar acerto na primeira tentativa, reparos e notas do Teste 5.
4. `scripts/grammar_overhead.py`: mesmo prompt 20 vezes com e sem GBNF no `llama-server`,
   comparando `predicted_ms / predicted_n`. Host como parâmetro (para rodar contra o celular).
5. Friedman entre os 4 modos (pareado por pedido) e Wilcoxon dois a dois.

## Teste 4: desempenho no celular

**Base:** MELT (arXiv:2403.12844); Tummalapalli et al. (arXiv:2603.23640: 20 iterações seguidas,
modelo carregado, 1 s de intervalo); PalmBench (arXiv:2410.05315).

Primeira forma (sem APK): Termux rodando `llama-server`, pipeline no PC com `--provider llamacpp`.

1. `docs/CELULAR_TERMUX.md`: Termux, llama.cpp, GGUF (Qwen3 0.6B, 1.7B, 4B; Q4_K_M e Q8_0),
   `llama-server --host 0.0.0.0 --port 8080`.
2. `scripts/mobile_bench.py` contra host remoto: aquecimento descartado; 20 iterações com 1 s de
   intervalo gravando `timings`; 3 decks completos no modo celular (Teste 7).
3. Medidas: tempo até o primeiro token (streaming), prefill e geração em tokens/s, queda da 1ª para
   a 20ª iteração, falhas (memória, processo morto).
4. Bateria e temperatura via `adb shell dumpsys battery` antes e depois de cada bloco, ou valores
   manuais. Atenção: Tummalapalli et al. relatam leitura de energia não confiável pela API de
   bateria do Android sob carga; tratar energia como estimativa.
5. Matriz aparelho × tamanho × quantização, com modelo do aparelho e RAM no CSV.
6. Protocolo: bateria 80–100%, sem carregador na medição de energia, brilho mínimo, apps fechados,
   celular esfriado antes de cada bloco.

## Teste 5: qualidade dos slides

**Base:** AutoPresent (nota 0–5 por modelo de visão, validada com humanos); PPTEval do PPTAgent.

1. `scripts/render_slides.py`: PPTX → PNG (LibreOffice headless); sem ele, usar a prévia existente e
   marcar como aproximado.
2. `scripts/judge.py`: modelo de visão **diferente** do gerador, rubrica fixa (texto, imagem,
   layout, cor; conteúdo, design, coerência), 3 repetições, média e resposta bruta.
3. `scripts/human_eval_pack.py`: pacote cego (3 pedidos × 3 grupos), embaralhado e renomeado,
   planilha para ordenar de 1 a 5 e anotar erros de informação; mapa de identificação separado.
4. Spearman entre juiz automático e pessoas.

## Teste 6: nota combinada de acerto e eficiência

**Base:** Masciari et al. (2026), *Are LLMs Ready for TOON?*, arXiv:2601.12014 (GCS_env).

Por grupo/modo: acerto (PPTX válido ou nota do verificador); eficiência (tokens ou energia por deck,
normalizados); nota combinada 0,5/0,5 e sensibilidade 0,3/0,7 e 0,7/0,3; dois tempos (só geração =
`decode_ms`, e total).

## Teste 7: quantos reparos valem a pena

**Base:** refinamento iterativo do AutoPresent.

1. Gerar e guardar o primeiro rascunho de cada pedido.
2. Reaplicar 0, 1, 2 e 3 rodadas de reparo sobre o mesmo rascunho (replay), com melhor de N ligado e
   desligado.
3. Registrar por rodada: validade, nota, tokens e tempo extras.
4. Curva ganho × custo e perfil **modo celular** na CLI (`--perfil celular`).

## Análise final

`scripts/analyze_experiments.py` (scipy opcional): média e IC95% bootstrap; Wilcoxon pareado,
McNemar, Friedman; tabelas e PNG em `outputs/analise/`; `docs/RESULTADOS_TESTES.md` separando
medido de interpretação.

---

# Parte 2: APK para celular

| Etapa | O que é | Precisa de APK? |
|---|---|---|
| 1. Termux | Celular só roda o modelo; pipeline no PC | Não |
| 2. Prova de conceito web | WebLLM/wllama no navegador gerando 1 slide com gramática | Não |
| 3. APK | App completo, offline, instalável | Sim |

## Etapa 2: prova de conceito web (opcional)

`mobile/web-poc/` com WebLLM (WebGPU) e wllama (WASM, GGUF, gramática llama.cpp). Qwen3 0.6B ou 1.7B
(confirmar nome na lista do WebLLM). GBNF de `slidedsl gbnf`, adaptada para o EBNF do XGrammar se
preciso. Mostrar texto, `usage`, tempo e tokens/s. Documentar aparelhos (WebGPU: Chrome 121+ no
Android 12+; wllama não funciona no Safari).

## Etapa 3: APK

Arquitetura proposta no documento original:

```
App React Native (Android)
 ├─ Interface: pedido → progresso → resultado → baixar/compartilhar .pptx
 ├─ LLM: llama.rn (llama.cpp), GGUF baixado no primeiro uso
 ├─ Compilador SlideDSL portado para TypeScript (packages/slidedsl-core/)
 ├─ PPTX: PptxGenJS (o mesmo do renderer)
 └─ Pesquisa: API da Wikipedia (sem chave); Brave/Tavily opcional
```

**Decisão pendente (ver PLANO_TCC.md, F8):** antes de portar o compilador, fazer um spike de 2 dias
com Python embarcado (Chaquopy) para evitar o porte e os testes de paridade. Só portar para
TypeScript se o spike falhar.

Passos se o porte for escolhido: parser Alto/1.1 em TS (avaliar lark.js; senão parser descendente),
validação A0xx, `alto_layout.py`, Alto → 1.1 → IR, semântica, D001–D010; **testes de paridade
obrigatórios** (IR JSON Python × TS em todos os exemplos); extrair IR → PPTX de
`renderer/render.mjs` (polyfills ou WebView); app bare/Expo prebuild (llama.rn é nativo); download
do modelo com progresso, Wi-Fi, checksum, escolha 0.6B/1.7B/4B pela RAM; GBNF como recurso;
pipeline modo celular (Teste 7); pesquisa Wikipedia com `verify_fact` portado, texto colado offline,
ou aviso "conteúdo sem fontes"; exportar dados de teste (tokens, `timings`, aparelho, bateria);
build arm64 assinado; requisitos (Android 10+, 6 GB para 1.7B, 8 GB para 4B). iOS fica para depois.

### Critérios de pronto da APK

- Instala num Android intermediário, baixa o modelo e gera um deck de 5–6 slides **offline**.
- Com internet, usa a Wikipedia como fonte, com fatos citados nas notas.
- O `.pptx` abre no PowerPoint e no Google Slides com objetos editáveis.
- Paridade Python × TS em todos os exemplos (se houver porte).
- Exportar dados de teste gera JSON com tokens e tempos por chamada.
