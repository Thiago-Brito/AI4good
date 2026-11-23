# Plano Codex — Teste 1 (custo do formato) e Teste 3 reduzido (restrição da saída)

Especificação completa: [PLANO_TESTES_E_APK.md](PLANO_TESTES_E_APK.md) (Testes 1 e 3). Recorte para
27/11: [PLANO_TCC.md](PLANO_TCC.md) §7b. Base comum pronta: `benchmark/format_requests.json`,
`benchmark/dossies/` (dossiês fixos), `src/slidedsl/experiment_runner.py` (plano pareado, retomável),
Fase 0 (`custo.json`, `chamadas.jsonl` com tokens e tempos).

## Regras

- Não mudar comportamento do pipeline existente (o código está congelado para os testes); só módulos e
  scripts novos, com testes offline (modelo simulado). pytest no Windows com `--basetemp` curto.
- Sem commit/push. Downloads grandes (binários, GGUF) só em `D:\android\llama` e `D:\android\models`.
- Resultados em `outputs/teste1/` e `outputs/teste3/`; relatório em `docs/RESULTADOS_T1_T3.md` com o
  que foi medido separado da interpretação. Nenhum número sem arquivo de origem.
- Registrar commit atual (`git rev-parse HEAD` + "árvore com alterações") e máquina em cada CSV.

## Teste 1 — `scripts/format_cost.py`

Seguir a especificação (formatos: Alto normalizado, 1.1, JSON da AST, python-pptx gerado da IR, texto
puro; equivalência do python-pptx conferida contra o PPTX do compilador; tokens das instruções de cada
formato). Tokenizador: `tokenizers` + `tokenizer.json` do `Qwen/Qwen3-4B` baixado do Hugging Face para
`D:\android\models\qwen3-tokenizer\` (dependência opcional; registrar versão/hash). Corpus: os decks de
`outputs/parity/` que têm IR (247) ou um subconjunto estratificado de ≥ 30, documentado. Saídas:
`outputs/teste1/format_cost.csv`, tabela Markdown com média, IC95% bootstrap, multiplicador vs texto
puro e Wilcoxon pareado (scipy opcional; implementar fallback se faltar).

## Teste 3 reduzido — `scripts/teste3_restricao.py`

1. Baixar o binário oficial do llama.cpp para Windows com CUDA (release do GitHub `ggml-org/llama.cpp`,
   anotar a tag) para `D:\android\llama\`, e o GGUF `Qwen3-4B-Instruct-2507` Q4_K_M de repositório
   público (conferir SHA-256 publicado) para `D:\android\models\`. Subir `llama-server` na porta 8080 com
   GPU (RTX 3060).
2. Rodar o pipeline existente (`slidedsl criar`, provedor `llamacpp`) com `--dossie` fixo nos modos
   `json` (JSON Schema), `gramatica` (GBNF) e `direto`, para os 12 pedidos × 2 sementes (11, 22), em
   ordem sorteada pelo `experiment_runner` (retomável). Métricas por execução: válido (sim/não), acerto
   na 1ª tentativa, reparos, chamadas, tokens de entrada/saída, `decode_ms`, `wall_ms` (do `custo.json`).
   O modo `nl2format` fica fora.
3. Microbenchmark `scripts/grammar_overhead.py`: mesmo prompt 20× com e sem GBNF, ms/token
   (`predicted_ms/predicted_n`), host como parâmetro.
4. Análise: taxa de validade por modo (McNemar par a par), tokens e tempo (Friedman + Wilcoxon),
   IC95% bootstrap. Tabelas em `docs/RESULTADOS_T1_T3.md`.
5. Se o modo `gramatica` falhar por limitação da GBNF/servidor, registrar o erro exato como resultado
   (não contornar mudando o pipeline).

Ordem: T1 primeiro (rápido, sem GPU), depois T3 (longo; pode rodar a madrugada toda). Parar o
`llama-server` ao terminar.
