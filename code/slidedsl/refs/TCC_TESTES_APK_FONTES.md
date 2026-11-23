# Fontes do plano de testes e APK (TCC)

Conferidas em busca web em 22/11/2026 (título, autores, identificador). "Uso" diz em qual teste
do [plano](../docs/PLANO_TCC.md) a fonte entra. Só a página de resumo/metadados foi conferida; os
números citados no artigo devem ser tirados do texto completo antes de entrar no texto.

## Já registradas no projeto (docs/REFERENCIAS.md)

| Fonte | Uso |
|---|---|
| Ge, J. et al. *AutoPresent: Designing Structured Visuals from Scratch*. CVPR 2025. arXiv:2501.00912 | T2 (taxa de execução, nota zero para falha), T5 (nota sem referência), T7 (refinamento) |
| Zheng, H. et al. *PPTAgent: Generating and Evaluating Presentations Beyond Text-to-Slides*. arXiv:2501.03936, 2025 | T5 (PPTEval: conteúdo, design, coerência) |
| Tam, Z. R. et al. *Let Me Speak Freely?* arXiv:2408.02442, 2024 | T3 (restrição de formato e raciocínio); já em docs/artigo/REFERENCIAS.md |

## Novas, conferidas

- **Agyemang, J. O. et al.** *When Agents Go Quiet: Output Generation Capacity and Format-Cost
  Separation for LLM Document Synthesis.* arXiv:2604.16736, submetido em 17/04/2026 (cs.AI).
  https://arxiv.org/abs/2604.16736
  - Conceito: separa tokens de conteúdo e de formato; "renderização adiada" tira os tokens de
    formato da saída do modelo (Format-Cost Separation Theorem). Implementação: GEN-PILOT (MCP).
  - Uso: T1 (multiplicador de custo por formato) e T2. É a fonte mais próxima da tese do SlideDSL
    ("o modelo propõe, o compilador decide" = renderização adiada).
- **Dong, Y. et al.** *XGrammar: Flexible and Efficient Structured Generation Engine for Large
  Language Models.* arXiv:2411.15100 (v3, 12/05/2025). https://arxiv.org/abs/2411.15100
  - Conceito: autômato de pilha em nível de byte para GLC; tokens independentes de contexto são
    pré-checados. Ganhos de velocidade são autodeclarados.
  - Uso: T3 (custo da gramática) e Etapa 2 da APK (WebLLM usa XGrammar).
- **Laskaridis, S.; Katevas, K.; Minto, L.; Haddadi, H.** *MELTing Point: Mobile Evaluation of
  Language Transformers.* MobiCom 2024. arXiv:2403.12844. https://arxiv.org/abs/2403.12844
  - Conceito: inferência no celular é limitada por memória; quantização viabiliza com perda de
    acurácia; energia e temperatura impedem uso contínuo.
  - Uso: T4 (prefill × geração, energia, temperatura).
- **Tummalapalli, P.; Arayakandy, S.; Pal, R.; Kundan, K.** *LLM Inference at the Edge: Mobile,
  NPU, and GPU Performance Efficiency Trade-offs Under Sustained Load.* arXiv:2603.23640,
  24/03/2026 (cs.DC). https://arxiv.org/abs/2603.23640
  - Conceito: carga sustentada e temperatura, não o pico, determinam o desempenho na borda.
    Os autores relatam que a medida de energia pela API de bateria do Android não foi confiável
    sob carga de GPU (cuidado para o T4).
  - Uso: T4 (protocolo de iterações seguidas e aviso sobre medida de energia).
- **Li, Y. et al.** *PalmBench: A Comprehensive Benchmark of Compressed Large Language Models on
  Mobile Platforms.* ICLR 2025. arXiv:2410.05315. https://arxiv.org/abs/2410.05315
  - Conceito: efeito da quantização em memória, energia, qualidade e alucinação no celular.
  - Uso: T4 (matriz de quantização Q4_K_M × Q8_0).
- **Masciari, E.; Moscato, V.; Napolitano, E. V.; Orlando, G. M.; Perillo, M.; Russo, D.**
  *Are LLMs Ready for TOON? Benchmarking Structural Correctness-Sustainability Trade-offs in Novel
  Structured Output Formats.* arXiv:2601.12014, 17/01/2026. https://arxiv.org/abs/2601.12014
  - Conceito: métrica GCS_env, que combina acerto estrutural e eficiência (tokens, tempo, carbono);
    formatos compactos perdem acerto em modelos sem suporte nativo.
  - Uso: T6 (nota combinada). **Correção:** o documento de instruções citava esta obra só como
    "avaliação de formatos com foco em sustentabilidade"; o título real está acima.

## Candidatas (não conferidas a fundo)

- *The Format Tax*, arXiv:2604.03616 (2026): diz que a instrução de formato sozinha causa a maior
  parte da perda de acurácia. Pode reforçar a discussão do T3. Ler antes de citar.

## Software (citar pela documentação oficial; conferir versão na data do uso)

llama.cpp/llama-server (GBNF, `/tokenize`, `timings`), Ollama (`/api/chat`), llama.rn, WebLLM,
wllama, PptxGenJS, python-pptx, Termux, Chaquopy (avaliação da APK), LibreOffice headless (T5).
