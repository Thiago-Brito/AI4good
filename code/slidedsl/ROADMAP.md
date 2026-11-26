# Roadmap — SlideDSL

## TCC: testes e APK — 22/11/2026
- [x] [Plano do TCC](docs/PLANO_TCC.md): tese, perguntas P1–P6, ordem F0–F9 com linha mínima, decisão da APK e capítulos.
- [x] [Especificação dos testes e da APK](docs/PLANO_TESTES_E_APK.md) salva no projeto; fontes conferidas em [refs/TCC_TESTES_APK_FONTES.md](refs/TCC_TESTES_APK_FONTES.md) (arXiv:2601.12014 corrigido para *Are LLMs Ready for TOON?*).
- [x] F0 (implementado, não medido com modelo real): tempo de prefill/decode/carga do Ollama (ns → ms), `timings` do llama.cpp, `reasoning_tokens` da OpenAI e `wall_ms` por chamada; `Call.usage` em `chamadas.jsonl`; `custo.json` com totais e divisão por etapa (reparo = slide com tentativa > 0). Desconhecido fica `null`, com contagem de lacunas.
- [x] F0: 6 testes novos (`tests/test_custo_fase0.py`); suíte com 713 pytest passou, Ruff limpo, testes Node do renderer passaram.
- [ ] F0 medido: rodar um `slidedsl criar` real com Ollama e com llama-server e conferir `custo.json`.
- [x] F1 (implementado): 12 pedidos em `benchmark/format_requests.json` (4 temas × 3 níveis, 5 sementes), `experiment_runner.py` (plano pareado com ordem sorteada, CSV linha a linha, retomável, erro vira linha) e `scripts/build_dossiers.py` (dossiê fixo por pedido, retomável). 5 testes offline.
- [ ] F1 (executar): `scripts\iniciar_searxng.cmd` e `scripts/build_dossiers.py`; não rodou porque o Docker Desktop estava fechado.
- [x] Decisões: APK obrigatória; avaliação humana adiada; APK com porte TS só do caminho do app + paridade de IR ([rodada 1](docs/PLANO_CODEX_TCC_APK1_CORE.md), Codex em execução).
- [x] APK rodada 1 (Codex, revisado): `packages/slidedsl-core` em TypeScript — `buildAlto` (validação A0xx, layout, D001–D010, IR) e `renderPptx` sem APIs de Node. Porte gerado do Python por `scripts/port_core.py` (Python segue como fonte da verdade); larguras de texto por tabela exportada (`font_metrics.json`, 6,2 MB). **Medido e conferido pelo revisor:** paridade de IR 24/24 fixtures e **261/261 no corpus** (247 IR + 14 rejeições iguais); 43 testes do pacote; 718 pytest (relato do Codex). [Relatório](docs/APK_CORE_RELATORIO.md).
- [x] Ambiente Android em `D:ndroid` (JDK 17, SDK, caches; C: com 4,6 GB livres): `scripts/android_env.ps1` e `scripts/mobile_build.ps1` (fonte em `mobile/app`, build em `D:\slidedsl-mobile`).
- [x] App v0 (`mobile/app`, Expo 58/RN 0.88.1): pedido por texto ou **voz** (`expo-speech-recognition`, pt-BR, offline no aparelho quando o modelo de voz está instalado; botão para baixar a voz offline). llama.rn 0.13 instalado (JNI pré-compilado).
- [x] APK rodada 2 (Codex, revisado): geração no app — escolha/download do modelo (Qwen3 0.6B/1.7B/4B Q4_K_M; URLs, tamanhos e SHA-256 **conferidos no Hugging Face pelo revisor**), llama.rn com JSON Schema → gramática e thinking desligado, roteiro + 1 chamada por slide + no máximo 1 reparo, fontes (nenhuma / texto colado / Wikipedia), salvar e compartilhar `.pptx`, exportar dados de teste (tokens e `timings`). 36 testes do app e typecheck passaram (reexecutados pelo revisor). APK 0.2.0 assinado: `D:\slidedsl-mobile\SlideDSL-release.apk` (175 MB). [Relatório](docs/APK_APP_RELATORIO.md).
- [ ] APK medido em aparelho real: inferência, RAM, velocidade, voz, download, PPTX abrindo no PowerPoint/Google Slides.
- [ ] Reduzir o APK (só arm64-v8a no release; hoje inclui x86_64).
- [ ] Otimizar `font_metrics.json` para o app (carregamento sob demanda ou formato compacto).
- [x] Teste 1 medido (23/11): 127 decks/694 slides, tokenizador Qwen3 — Alto 2,04× o texto visível, JSON 2,15×, SlideDSL 1.1 9,22×, python-pptx 18,45× (Wilcoxon p≈1e-22). [Resultados](docs/RESULTADOS_T1.md).
- [x] Edição localizada de um slide medida (23/11, Qwen3 4B local, 4 decks × 3 instruções): achado — com todos os tipos liberados o modelo reduzia 11/12 slides a `secao`; corrigido (`allowed_kinds`): tipo cumprido 11/11, conteúdo preservado 11/11, ≈7% do custo de gerar o deck. [Resultados](docs/RESULTADOS_EDICAO.md).
- [x] Artigo do TCC (LNCS, português) no Overleaf com Teste 1 e edição; pendentes: Teste 3 e Teste 4.
- [x] Teste 3 medido (23/11, llama.cpp b12648, Qwen3-4B-Instruct-2507, 12 pedidos × 3 modos × 2 sementes): válidos JSON 19/24, gramática 19/24 (0 erro de sintaxe), direto 10/24 (12 de sintaxe; McNemar p=0,012); gramática −32% tokens de saída e −26% tempo vs JSON, mas +18% tokens de entrada (+11% no total, n.s.); +15,4% ms/token. [Resultados](docs/RESULTADOS_T3.md).
- [x] Revisão do artigo (23/11): tokens de entrada no mecanismo de restrição, testes nomeados pelo que medem (sem "Teste 1/3/4"), modelos identificados por artefato, resumo com 230 palavras, 721 testes, limite de texto (A005) como falha dominante e extensões na discussão.
- [x] Teste 2 grupo A medido (23/11): Qwen3-4B-Instruct-2507 escreve python-pptx (até 2 correções), verificador único `scripts/pptx_checks.py` (B1–B4 estrutura; B5 texto maior que a caixa, medido com `text_metrics`). A: 24/24 estrutural, **1/24 sem estouro** (4,9 caixas estouradas/deck), ~2,8 mil tokens, 20 s. C (Teste 3, recompilado): 19/24 em ambos os níveis, 0 estouro, ~68–75 mil tokens, 104–141 s. McNemar estrito C×A 18–0, p≈8e-6.
- [x] Correção do compilador achada pelo verificador: blocos de cartões (conclusão em colunas e tópicos em cartões) não conferiam o limite inferior e encostavam no número da página (4/38 decks). `check_block_bottom` emite A010 e a variante é recusada. Decks do Teste 3 recompilados sem chamar o modelo (`scripts/recompilar_teste3.py`): validade igual (19/19/10), verificador 38/38. 727 pytest; porte TS regenerado, 44 testes TS, paridade 351/351.
- [x] Teste 2 condição C-mínimo (`scripts/teste2_minimo.py`, regra fixada antes de rodar): 13/24 válidos, todos sem estouro; tokens de saída e tempo iguais ao grupo A (1.344 × 1.380; 19,6 × 19,8 s; p = 0,98/0,93); estrito 13–1 contra A (p = 0,002); 15 mil tokens e 36 s por deck válido estrito (A: 67 mil e 476 s). Falha de protocolo registrada: limite de 36 caracteres do rótulo da linha do tempo ausente do prompt. [Resultados](docs/RESULTADOS_T2.md).
- [x] Artigo reenquadrado (23/11): a vantagem medida da linguagem é garantia sobre o arquivo a custo equivalente, não economia de tokens; seção "Geração direta de código", correção do compilador, paridade 351/351.
- [ ] Limites de texto e número de slides dentro da gramática (atacaria as falhas restantes do C-mínimo).
- [x] Conferido no PowerPoint pelo autor (23/11): texto do grupo A estoura em todas as páginas dos 3 decks, inclusive no deck sem estouro medido (a medição é conservadora). Google Slides não conferido.
- [ ] APK: rebuild com o núcleo TS corrigido (o APK 0.2.0 ainda tem o layout antigo).
- [ ] Limite de tamanho dentro da restrição (`maxLength`/repetição limitada) e gramática reduzida ao tipo do slide no prompt.
- [x] App: compilador monta o slide quando a IA falha no reparo (F001), em vez de abortar o deck (achado do emulador com Qwen3 0.6B).
- [x] Teste 4 em celular físico (24/11): moto g(8) power lite, 4 GB, Android 10, Qwen3 1.7B CPU, `agua.txt`, 5 slides — sucesso em 63 min, 12 chamadas, 0 reparos, verificador estrito ok; prompt 3,9 tok/s, geração 1,5 tok/s; leitura do documento 46% do tempo; bateria 95→77%. Conteúdo repetitivo e com afirmações fora do documento (2 erradas). [Resultados](docs/RESULTADOS_T4.md).
- [ ] Modo rápido no app: documento curto em 1 leitura, saída das leituras limitada, deck em 1 chamada; medir de novo.
- [ ] (opcional) 2ª execução no celular com GPU ligada.

## Ajustes para o seminário 2 (sem2) — 11/11/2026
- [x] Comparação aceita 1–4 itens por lado (validação e schema); prompt pede 1 ou 2 e proíbe repetir item.
- [x] A023 (item repetido no slide) e A024 (lado com nome genérico, ex. "X") como avisos que acionam reparo.
- [x] Rodapé: referência com rótulo próprio ("Execução: ...") sem "Fonte:"; fato de documento mostra o nome do arquivo.
- [x] `scripts/medir_execucao.py`: tempo total, pico de RAM (SlideDSL e Ollama) e VRAM, com commit e máquina.
- [x] Medição real (Ollama, Qwen3 4B, i5-10400, RTX 3060): demo com documento curto válida em 160 s, 44 chamadas;
  artigo completo (138 mil caracteres) inválido em 298 s por A010/D001. Evidência em `outputs/sem2/`.
- [x] Verificador de sustentação: correção igual ao veredito ("parcial") ou com menos de 3 palavras é descartada.
- [x] Medição com API paga (gpt-5.4-mini, mesmo documento): válida em 65,7 s, 29 chamadas, 35.141/6.311 tokens, US$ 0,051.
- [x] Botão e comando **Google Slides**: OAuth com PKCE, escopo drive.file, conversão PPTX → Slides pelo Drive; sem dependência nova ([guia](docs/GOOGLE_SLIDES.md)). 5 testes com Google simulado.
- [x] Envio real ao Google testado em 11/11/2026: login OAuth e conversão do deck sem2 v4 em Google Slides funcionaram.
- [ ] Pré-validar layout (A010) durante a escrita de cada slide (a falha mostrada no sem2).

## Rodada 4 de design — 10/11/2026

- [x] T1: corpus preservado e linha de base em `outputs/design_r4/20261110-234240/antes/`.
- [x] T2–T6: grade/tokens, estilos tipográficos, variantes pontuadas, ritmo e resolução.
- [x] T7: três ciclos visuais e comparação pareada offline.
  Ciclo 1 inspecionado: 15/16 PPTX; próximos ajustes em métrica familiar e marcador.
  Ciclo 2 inspecionado: 15/16 PPTX; corrigir largura da comparação e ritmo da conclusão.
- [x] T8: 591 pytest (87,47 s), Ruff limpo, 2 testes Node, registros finais.
- Ciclo 3: 16/16 PPTX, 89 slides, A010/A019/D010=0 e A031=8.
  Nota 0,7966→0,8353; ocupação 0,6079→0,4966; variantes/deck 4,625→4,875;
  repetição consecutiva 3→0. Evidência `outputs/design_r4/20261110-234240/`.
- [ ] Persistem monotonia de listas, fotos pequenas/irrelevantes, transições
  esparsas, corpo denso 16 pt; avaliação estética humana/Office continua futura.
  Encerramento pelo limite de três ciclos. Offline, US$ 0, sem commit/push/stash.
- Auditoria: 652 textos nativos, 298 formas, 19 imagens; fontes/tamanhos IR=PPTX
  e hashes dos originais preservados. Temporário `outputs/_tmp_r4` mantido porque
  a remoção foi bloqueada pela revisão automática (`blocked by policy`).

## Rodada 5: modelo, imagens por IA e visual — 02/11/2026
- [x] Pesquisa desligada por padrão com OpenAI; lote e fonte/qualidade de imagem selecionáveis na interface e CLI, com preço.
- [x] Imagens por IA (gpt-image-2 / gpt-image-1-mini) com custo somado ao consumo; filtro de retratos e consultas simplificadas no Commons.
- [x] Capa/conclusão em paleta invertida, maiúscula inicial, rótulo de comparação sem invadir o detalhe, recomposição de slide de imagem que não cabe.
- [x] `gpt-5.4-mini` testado e definido como padrão local (texto mais concreto; ~US$ 0,012 por deck de 6 slides).
- [ ] Repetir a comparação A × B-lote com gpt-5.4-mini e avaliação humana cega.

## Rodada 3 de design — 01/11/2026
- [x] Legibilidade (corpo ≥ 16 pt), fotos na capa, caixa de frase, ocupação; 3 ciclos em `outputs/design_r3/20261101-2216/`.
- [x] Comparação 4 temas × 3 seeds: B 12/12 válidos e 17% mais barato por slide válido; 22% mais tokens que A.
- [x] Corrigir rótulo vazio/minúsculo vindo dos tópicos e faixa decorativa da capa sem foto; remover regras sob medida dos temas.
- [x] Medir B-lote: 41% menos tokens e 45% menos custo que A (4 temas × 3 seeds, `20261101-2307_r4/`).
- [ ] Pré-validar layout (A010) durante a geração para reparar antes da compilação final.
- [ ] Afirmações dependentes de lugar: exigir fato com fonte (pesquisa opcional) em vez de regra de prompt.
- [ ] Avaliação humana cega de A × B-lote.

## Comparação Alto × SLD — 01/11/2026
- [x] Tarefas 1–2: TLS do sistema centralizado; autoria condicionada ao pedido,
  contexto anterior, repetição Jaccard com reparo limitado e roteiro com imagem Commons.
  Onze testes offline passaram. Busca real registrada em
  `outputs/comparacao_alto_sld/rede_20261101-211932/`: Commons HTTP 403;
  Openverse timeout. Download real ainda não comprovado nesta rede.
- [x] Tarefa 3: nove execuções no lote `outputs/comparacao_alto_sld/20261101-2131/`,
  A 1/3 válidos, B 3/3, B+img 2/3; seis PPTX, 35 PNGs e sete folhas de contato.
  Lote US$ 0,0569728; experimento inteiro US$ 0,0703364 conhecidos, total exato
  desconhecido (18 chamadas sem uso), teto conservador US$ 0,2325972 < US$ 1.
  B reduziu custo em 10,79%, mas aumentou tokens em 9,25%; não generalizar.
- [x] Tarefa 4: 421 testes Python passaram (91,50 s), Ruff limpo; continuidade,
  progresso e relatório atualizados. Evidência em `20261101-2131/pytest_final.xml`.
  Remoção dos temporários rejeitada pela política do ambiente; `outputs/_pt` permanece.
  Sem commit/push e sem alterações nos resultados antigos.
- [ ] Pendências externas/observadas: busca Commons funcional nesta rede, erro A010
  medido, renderização real de PPTX e avaliação humana/factual. Não são resultados comprovados.
  Limpeza de `outputs/_pt` bloqueada pelo ambiente.

## Planejamento de APIs, voz e celular — 01/11/2026
- [x] Inspecionar a base e registrar fontes; incorporar a transcrição fornecida e comparar Taiga-S1 com SlideDSL.
- [x] Criar [plano de evolução](docs/PLANO_API_VOZ_MOBILE.md), com diagnóstico, fases, edição localizada e protocolo de custo/qualidade.
- [ ] Recuperar a referência visual do Claude; acesso indisponível nesta análise.
- [x] Criar primeiro `feature/slidedsl-api-voz-mobile`, a partir de `168c29f`; preservar arquivos preexistentes.
- [x] Integrar OpenAI no painel/API com schema estrito, validação local, uso por chamada, limites e `.env` ignorado pelo Git.
- [x] Validar HTTP simulado com PPTX real e testes de navegador; [continuidade e comandos](docs/CONTINUIDADE_API_VOZ_MOBILE.md).
- [x] Concluir piloto OpenAI remoto: falha HTTPS era inspeção TLS do Kaspersky; adaptador passou a usar o repositório de certificados do sistema. Piloto `piloto_5ab371e27016`: 3 slides, 5 chamadas, US$ 0,0028, PPTX exportado.
- [ ] Implementar estado persistido com revisões, seleção e ajustes manuais explícitos (fase 2).
- [ ] Implementar edição por texto, experiência móvel/voz e avaliação controlada, conforme as dependências do plano.

## Revisão e preparação do commit — 12/10/2026
- [x] Revisar o fluxo Alto, pesquisa, sustentação/cobertura, editor e documentação.
- [x] Conferir 388 testes Python, dois Node e 11 Playwright; cinco testes reais de interface optativos não executados.
- [x] Validar Ruff, ESLint, TypeScript/build e formatação; adaptar testes ao fluxo anterior e à porta configurada.
- [x] Retirar o segredo do YAML do SearXNG e validar inicialização com `.env` local ignorado pelo Git.
- [x] Atualizar os registros do lote multitemas, distinguindo resultados anteriores aos ajustes e pendências de avaliação.

## SearXNG local — 12/10/2026
- [x] Iniciar Docker Desktop já instalado, baixar a imagem do SearXNG e subir o serviço em `127.0.0.1:8888`.
- [x] Validar `/healthz` (HTTP 200), busca JSON (27 resultados para `microsservicos`) e detecção pelo SlideDSL (`Buscador: searxng`).

## SlideDSL Alto, pesquisa e geração restrita — 12/10/2026
- [x] Extensões 1.1: `negrito`, `alinhado`, `arredondado`, `notas` (parser, printer, IR, editor, renderer).
- [x] GLC de alto nível com 11 tipos de slide, validação A0xx e layouts com fonte uniforme por papel.
- [x] Pesquisa (Wikipedia/Tavily/Brave/SearXNG) com fichas verificadas por trecho literal e cache.
- [x] Roteiro + conteúdo por slide com contrato editorial; JSON Schema, GBNF (llama.cpp) ou direto.
- [x] Reparo por campo, best-of-N, prévia PNG sem Office e comando `criar` com auditoria completa.
- [x] Testes offline (modelos simulados e HTTP falso); [documentação](docs/SLIDEDSL_ALTO.md).
- [x] Testes reais multitemas (Qwen3 + SearXNG); segunda e terceira rodadas de qualidade
  (sustentação, cobertura, truncamento, citação literal, relevância); SearXNG como buscador único.
- [x] Registro do dia em [docs/MUDANCAS_2026-10-12.md](docs/MUDANCAS_2026-10-12.md) e referências em [docs/REFERENCIAS.md](docs/REFERENCIAS.md).
- [ ] Repetir os casos multitemas com o código final; comparar antigo × Alto × Alto+GBNF; avaliação humana.
- [ ] Crítica visual por modelo de visão, botão no editor e fine-tune LoRA em SlideDSL Alto.

## Rastreabilidade e cobertura — 11/10/2026
- [x] Investigar estruturas reais, preservar estado conceitual B e registrar diagnóstico antes das alterações.
- [x] Contrato tipado de conteúdo com origem, IDs e cláusulas por seção; C001–C005 separados de validade estrutural.
- [x] Projeção e evidência literal por campo/caminho até IR/PPTX; cumprimento semântico permanece não verificado.
- [x] Recuperação por acréscimo de registros existentes, sem chamadas SLM, com veto de geometria/contrato/regressões.
- [x] Flags experimentais na CLI/API/editor, desativadas por padrão; recuperação desativável.
- [ ] Concluir regressão e comparação A/B/C congelada, duas seeds, replay pareado e auditoria de custos/textos/hashes.
- [ ] Registrar inspeção qualitativa, limitações e relatório final em docs/EVOLUCAO_COBERTURA.md.
- [ ] Avaliação humana independente, verificadores de domínio e extração mais completa de requisitos em português.

## Investigação e planejamento conceitual — 11/10/2026
- [x] Investigar fluxo, contratos, prompts e seis patches reais antes das alterações; registrar causas e hipóteses.
- [x] Percurso opcional conteúdo → alocação, duas chamadas locais, projeção literal e rastro de registros descartados.
- [x] Revisão de um slide por chamada com feedback da rejeição e proteção contra atalhos de condição; rollback mantido.
- [x] Comparar seis pares reais e quatro revisões dos mesmos planos históricos; 3/6 → 6/6 PPTX, sem ganho geral de conteúdo; 0/6 revisões históricas aceitas.
- [x] Auditoria de bytes, schemas, hashes, custo, rollback e 13 PPTX; preservar pilotos/negativos e repetição UTF-8.
- [x] 325 Python, dois Node, dez Playwright ordinários; teste real pelo editor/exportação passou; lint/build; [relatório](docs/EVOLUCAO_CONTEUDO.md).
- [ ] Cobertura por seção e seleção obrigatória de exemplos/síntese; evitar descarte de conteúdo solicitado na alocação.
- [ ] Corrigir critérios/condições de domínio com fontes por afirmação; calibrar revisão com avaliação independente.
- [ ] Mais pedidos/seeds e ablações; avaliação humana de completude/correção/clareza e renderização Office real.

## Planejamento semântico — 11/10/2026
- [x] Snapshot e push prévios: 64a49f4cdfc68ebe4614579dc8af74f93f74e13b.
- [x] Diagnóstico; contrato opcional de papéis, referências explícitas e fontes por nó.
- [x] Revisor limitado com patches autorizados, validação de candidatos e rollback.
- [x] Comparação real A/B/C em quatro domínios; planos B/C compartilhados, A 1/4 e B/C 3/4 PPTX; seis revisões finais rejeitadas, sem ganho demonstrado.
- [x] Regressão 311 Python, dois Node e nove Playwright (quatro optativos omitidos); documentação em [EVOLUCAO_SEMANTICA.md](docs/EVOLUCAO_SEMANTICA.md).
- [ ] Calibrar sinais/aceitação do revisor; corrigir conteúdo conceitual além dos tipos, ampliar domínios/seeds e auditoria documental.
- [ ] Avaliação humana de correção conceitual e clareza; renderização Office real.

## Expressividade do planejamento — 11/10/2026
- [x] Diagnóstico prévio dos limites de nós, textos, estruturas, mídia e associação intenção/composição.
- [x] Percurso opcional com rótulo/descrição/explicação, variantes medidas, quantidades concisas/detalhadas e slots de imagens, preservando DSL e validadores.
- [x] Medição local de palavras/fontes e correção dos cortes encontrados nas capturas; corpo ≥22 pt.
- [x] Comparação Qwen3 local, recompilação com conteúdo fixo, imagens offline e auditoria de evidências; 271 Python, dois Node e oito Playwright passaram (quatro optativos omitidos).
- [x] Documentar resultados/falhas em [EXPRESSIVIDADE_PLANEJAMENTO.md](docs/EXPRESSIVIDADE_PLANEJAMENTO.md).
- [ ] Papéis semânticos dos nós, sustentação editorial, revisão humana e renderização real; os proxies não comprovam qualidade factual/estética.

## Diagnóstico das próximas melhorias — 11/10/2026
- [x] [Três limitações, evidências, módulos e ordem de implementação](docs/PROXIMAS_MELHORIAS.md), usando resultados existentes, sem novas chamadas Ollama ou alterações de código.
- [ ] Prioridades propostas: contrato editorial e profundidade; variantes por intenção; imagens integradas à mensagem. Implementação fora do escopo desta etapa.

## Refinamento visual — 11/10/2026
- [x] Base f05fc8a4 limpa, push confirmado; documentação e PPTX recente inspecionados.
- [x] Refinamento determinístico, hierarquia e conexões nativas, preservando relações, conteúdo e critérios já atendidos.
- [x] Comparações com conteúdo fixo, nova geração Qwen3, cinco pares de capturas; COM/LibreOffice indisponíveis inclusive no Ubuntu WSL.
- [x] Regressão (241 Python/2 Node/11 Playwright), REFINAMENTO_VISUAL.md e arquivos apropriados preparados para commit/push.
- [ ] Renderização real, movimento das âncoras no Office e avaliação humana de estética, leitura e conteúdo.

## Planejamento visual — 11/10/2026
- [x] Base limpa e44961ed confirmada por push/ls-remote; diagnóstico real preservado em outputs/planning_visual/before_01.
- [x] Intenções visuais pela SLM, componentes determinísticos e imagens com provedores automáticos.
- [x] Formulário simples, geração real antes/depois, capturas e verificações específicas.
- [x] Regressão (224 Python/2 Node/11 Playwright), documentação, auditoria e artefatos prontos para commit/push.
- [ ] Avaliação humana factual/estética, renderização Office/LibreOffice e ampliação dos pedidos/seeds.

## Evolução visual/contextual — 11/10/2026
- [x] Base limpa: 9b6a8edf80ce4b76c54c13bcbb7fc0e768aab847; hash confirmado em origin/dsl-visual, sem commit vazio.
- [x] Imagens de APIs oficiais, segurança, cache e seis layouts editáveis; Openverse/NASA consultados, Commons real indisponível (403).
- [x] Personalização opcional, referências locais e rastreabilidade; restrito extrativo validado com SLM real.
- [x] Validação V004–V006, renderização opcional e preservação conservadora de edições com conflitos.
- [x] Experimento novo: 20 avaliações estruturais, 17 chamadas reais; cinco planos compartilhados, auditoria e documentação.
- [x] Regressão: 209 Python, dois Node e onze Playwright; lint/formatação/build; upload de imagem própria offline.
- [x] Revisão final para commit/push na branch dsl-visual; confirmação no relatório de entrega.
- [ ] Renderização COM/LibreOffice real, avaliação humana, maior amostra, GPU, conectores ancorados e sincronização completa plano/IR.

## Núcleo e fases históricas

- [x] Fase 0: ambiente e pesquisa oficial
- [x] Fase 1: GLC, AST e printer
- [x] Fase 2: semântica, IR, geometria e extensões 1.1
- [x] Fase 3: regras D001–D010
- [x] Fase 4: PowerPoint editável de cinco slides
- [x] Fase 5: adaptadores e geração
- [x] Fase 6: benchmark, ablação e relatório real
- [x] Fase 7: editor visual e teste UI
- [x] Fase 8: integração, documentação e defesa
- [x] Instalar Ollama 0.40.1 e baixar qwen3:0.6b/qwen3:4b na máquina
- [x] Completar experimento local: cinco repetições por Qwen3, A/B/C e até dois reparos; ambos 0/5 parse inicial/final
- [ ] Experimento remoto: aguarda credencial/acesso OpenAI
- [x] Diagnosticar e reproduzir P001 nas 30 respostas físicas originais
- [x] Implementar geração incremental direta/JSON restrito, parser/semântica existentes e até dois reparos explícitos
- [x] Validar uma demonstração SLM real de cinco slides, PPTX editável e editor
- [x] Comparar três modelos, dois modos e cinco repetições por configuração: 317 respostas auditadas, quatro PPTX no pedido complexo; demonstrações estritas separadas
- [x] Explicar no README o fluxo do projeto e a GLC, com exemplo executável validado e compilado

## Evolução SLM — 10/10/2026
- [x] Analisar arquitetura/evidências e verificar base: 123 testes Python passaram; Ollama 0.40.2 disponível.
- [x] Implementar plano sem coordenadas, IDs determinísticos, três layouts e validação pela cadeia original; 24 testes de etapa passaram, incluindo PPTX reais.
- [x] Implementar estratégias A/B sem reparos e C/D com planejamento; D aplica patches em campos diagnosticados, com limite de dois reparos.
- [x] Integrar geração, modelos locais e progresso à interface existente; fluxo real de geração/edição/exportação verificado no navegador.
- [x] Executar comparação A/B/C/D: 40 execuções, 122 respostas auditadas; PPTX estrito A 0/10, B 0/10, C 10/10, D 9/10. Nenhum pedido complexo atingiu 17/17.
- [x] Verificar regressão (141 Python, 2 Node, 7 Playwright), demonstração real e editor de produção; documentar em EVOLUCAO_SLM.md.
- [ ] Ampliar pedidos/seeds e isolar reparos a partir do mesmo plano inicial; corrigir omissões de requisitos (formas/camadas) e avaliar conteúdo com pessoas.

## Confiabilidade — 11/10/2026
- [x] Commit e push prévios: c53bb4498a6aba2812e22014bd1cf66954abfd13, origin/dsl-visual.
- [x] Requisitos tipados por slide, verificação AST/IR independente e diagnósticos R001.
- [x] D com adições determinísticas autorizadas, patches locais, limite configurável, progresso, rejeição de regressões e estados antes/depois.
- [x] Cards, sequência e fluxo; layouts anteriores preservados, geometria compacta sem cortar textos.
- [x] V001–V003 e fases separadas; investigar renderização real (PowerPoint COM indisponível).
- [x] Ablação com oito planos compartilhados, quatro pedidos e 32 avaliações: 8 respostas reais, 30 PPTX auditados; complexo 17/17 nas duas repetições após reparo.
- [x] Interface de requisitos/correções/revalidação; fluxo real com Ollama e exportação.
- [x] Documentar arquitetura, evidências e limites em docs/EVOLUCAO_CONFIABILIDADE.md.
- [ ] Ampliar amostra e avaliação humana; resolver overflow persistente, interpretação de pedidos e reparo depois de edição manual.


## Rodada 2 de design - fase 1 (01/11/2026)

Implementadas regras editoriais locais em editorial.py/alto_layout.py: capa abstrata sem barras, composicao por densidade, topicos sem numeracao, etapas conservadoras, rotulos redundantes suprimidos preservando detalhes, escala por deck e quebra medida de titulos. Fotos em meia pagina com credito visivel e recorte central no renderer/previa. Prompts com perguntas distintas e contexto brasileiro. Filtro lexical de relevancia em media.py; glifo CO2 subscrito usa Segoe UI na previa. Testes offline adicionados em test_design_r2.py; regressao parcial identificou ajustes necessarios nos exemplos densos, corrigidos sem cortar textos. Experimentos em andamento em outputs/design_r2/20261101-2154/; teto compartilhado US$ 0,40. Sem commit/push/stash. Proxima fase: inspecionar PNGs dos quatro briefs e iterar ate tres ciclos.

- Ciclo 1 inspecionado: 1/4 válidos, US$ 0,0320992 conhecidos, uma imagem no PPTX.
  Revisão: `outputs/design_r2/20261101-2154/ciclo_1/REVISAO.md`.
  Pré-validação da meia página e schema de dois itens corrigem diferenças entre
  composição sem foto e composição final. Ciclo 2 em andamento.

- Ciclo 2 concluído e inspecionado: 4/4 válidos, 0 ERRO/AVISO, uma imagem no PPTX,
  US$ 0,0261728 no ciclo. Limites semânticos/Title Case/fallback documentados em
  `outputs/design_r2/20261101-2154/ciclo_2/REVISAO.md`. Ciclo 3 em andamento.

- [x] Ciclo 3 inspecionado e encerrado no limite: 4/4 válidos, quatro imagens,
  US$ 0,0300044 próprios; gráfico inadequado de Git vetado antes do lote final.
- [x] Comparação final de quatro briefs A/B/B+img: 11/12 PPTX, 55 slides,
  três fotos Commons e um asset demonstrativo em A; 60 PNGs/12 folhas vistas.
  Evidências: `outputs/comparacao_alto_sld/20261101-2203/RELATORIO.md` e
  `REVISAO_FINAL.md`; tabela pareada com os três temas da rodada 1 no relatório.
- [x] Regressão final: 438 pytest, Ruff limpo e dois testes Node.
  Rodada: US$ 0,1787512 conhecidos, quatro usos desconhecidos, teto conservador
  US$ 0,20175 < US$ 0,40. Sem novas inferências após o lote final.
- [ ] Pendências observadas: A010 em B/Internet, Title Case/rótulos vagos,
  repetição semântica, omissões factuais e Git sem foto. Avaliação humana/Office
  e generalização continuam não demonstradas. Temporário `_tmp_r2` preservado
  porque remoção foi bloqueada pela política automática do ambiente.

## Rodada 3 ? implementa??o local (01/11/2026)

Removida redu??o global de fontes; escala Alto 42/24/20 pt, m?nimos 32/20/16 pt (subt?tulo 18 pt). Cart?es ampliam altura; dois itens em duas colunas; ocupa??o por uni?o de caixas com aviso abaixo de 0,30. Repeti??o entre irm?os/r?tulos telegr?ficos orienta reparo existente. Capa em caixa de frase com foto/cr?dito e reutiliza??o de busca. Harness aceita seeds e relata m?dias/faixas. Valida??o offline e ciclos em andamento em `outputs/design_r3/20261101-2216`.

Rodada 3: 82 testes direcionados passaram; Ruff limpo. Compatibilidade densa resolvida com perfil 20/16 pt restrito ao slide denso; os demais preservam 24/20 pt. N?o h? redu??o abaixo dos m?nimos nem redu??o global por deck. Ciclo 1 em execu??o.

Rodada 3 ? ciclo 1 inspecionado: 3/4 v?lidos, USD 0,0341444 conhecidos, 3 fotos em PPTX v?lidos. Falha A010 Internet; inconsistencia foto da capa no roundtrip corrigida na gram?tica/printer e pr?-valida??o. R?tulo telegr?fico e conclus?o repetitiva motivam ciclo 2. Evid?ncia `outputs/design_r3/20261101-2216/ciclo_1/REVISAO.md`. Regress?o de fase 1: 446 pytest passaram em 77,47s.

Rodada 3 ? ciclo 2 inspecionado: 3/4 v?lidos, cinco fotos em PPTX, USD 0,0303072 pr?prios / 0,0644516 acumulados. Capas/roundtrip e conclus?o solar melhoraram; Git A010 por duas unidades e ?cone no lugar de foto motivam escolha adaptativa da largura e filtro fotogr?fico no ciclo 3. Revis?o em `outputs/design_r3/20261101-2216/ciclo_2/REVISAO.md`.

Rodada 3 ? ciclo 3 encerrado pelo limite: 4/4 v?lidos, tr?s fotos, USD 0,0325836 pr?prios / 0,0970352 acumulados conhecidos, zero uso desconhecido. Revis?o `outputs/design_r3/20261101-2216/ciclo_3/REVISAO.md`. Persistem repeti??o conceitual, t?tulos gen?ricos e conte?do n?o verificado. Corrigida espera do Commons antes do lote final de 36 execu??es.

Rodada 3 ? quality gates finais: 452 pytest em 82,90s, Ruff limpo, 2 testes Node. Evid?ncia `outputs/design_r3/20261101-2216/pytest_final.xml`. Lote final `outputs/comparacao_alto_sld/20261101-2227/` em andamento com c?digo fixo; seed 42 registra P001 em A/Internet e A010 em B+img/solar, al?m de grafo de hyperlinks indevidamente aceito pela relev?ncia lexical. Sa?das preservadas e limita??es ser?o incorporadas ? an?lise final.

## Rodada 5 de design (11/11/2026)

- [x] Ler plano/bases r4 e preservar corpus/código de entrada com hashes.
- [x] Calibrar ocupação, fotos, cartões, ritmo de três slides e escala por altura-x.
- [x] Três ciclos offline, 48 folhas abertas, revisões e critérios (a)–(e) atingidos.
- [x] Comparação r4 antes | r4 final | r5, 614 pytest, Ruff e 2 Node; continuidade atualizada.

Resultado r5: 16/16 PPTX, 89 slides, ocupação 0,6294, rows 7/30 (23,3%), zero
A010/A019/D010/eixos mistos/repetição imediata; fotos grandes em photo40 0.
Evidências: `outputs/design_r5/20261111-001430/RELATORIO.md` e `comparacao/`.
Pendências visuais: A031 em fotos pequenas, retrato inadequado, transições esparsas,
hierarquia menor nas comparações densas; prévia não comprova aparência no Office.


## Rodada 6 — Parte A concluída; Parte B bloqueada por autenticação (11/11/2026)

Plano: `docs/PLANO_CODEX_RODADA6_DESIGN.md`; fontes: `refs/DESIGN_RODADA6.md`.
Código: `alto_layout.py`, `design_system.py`; testes r3/r4/r5 atualizados e
`test_design_r6.py`, `test_reais_r6.py` adicionados. Harness pago:
`scripts/testes_reais_r6.py`; comparação offline: `scripts/comparar_design_r6.py`.

Parte A offline, US$ 0: dois ciclos, 32 folhas abertas. Critérios (a)–(e)
preservados: 16/16 PPTX, 89 slides, ocupação 0,6294→0,6664, tópicos em rows
7/30→4/30, zero A010/A019/D010/eixo misto/repetição imediata. Dez fotos internas
em photo50; oito A031 mantidos. Quinze conclusões em colunas com número interno.
Rótulos/descrições compartilham topos; cartões têm altura natural + padding32;
centro útil −5%, limitado pelo topo. Fontes começam no maior perfil válido.
Fotos ≥600 px têm variante única independente de estilo; <600 px usam texto,
inclusive capa. Transições curtas: 48–54 pt, bloco de um terço e motivo da família.

Evidências: `outputs/design_r6/20261111-004533/RELATORIO.md`, `comparacao/`,
`ciclo_1/REVISAO.md`, `ciclo_2/REVISAO.md`. Corpus idêntico por SHA-256 à r5;
gramática Alto, IR e roundtrip preservados. Refinamento de capa <600 px não
altera o corpus inspecionado: IR finais reconstruídas e comparadas, sem diferença.
Auditoria PPTX: 629 textos, 345 formas, 19 imagens, 89 slides; zero divergência
de fonte/texto. **640 pytest passaram em 156,28 s**, Ruff limpo e dois Node.
Um aviso Starlette/AnyIO preexistente; editor/renderer não alterados nesta rodada.
Temporários preservados; nenhum commit, push ou stash.

Parte B: modelo **gpt-5.4-mini**, tarifa configurada (somente presença verificada;
nenhum valor do .env exibido), seis pedidos/estilos, seis slides/seed42,
imagens livres habilitadas, pesquisa desligada, sem imagens por IA.
**6/6 tentativas recusadas com HTTP 401 antes do roteiro. Nenhum deck novo foi
gerado:** sem PPTX/SLDA/PNG de slide. Os seis contato.png e a galeria são painéis
de falha explicitamente identificados; não são folhas de decks reais.
Nenhuma busca de fotos foi alcançada. Credencial local carregada; sem chave
herdada. Não se modificou .env nem se imprimiram seu conteúdo ou a chave.

Pasta: `outputs/testes_reais/20261111-0050/`, com `INDICE.md`, `galeria.png`,
`resultados.json`, `orcamento.json`, diagnóstico e uso por tentativa.
ULTIMO.txt aponta para essa execução. Seis painéis e galeria abertos.
Gasto conhecido **US$ 0,00000000**; seis usos/custos desconhecidos; total exato
**desconhecido**; reserva conservadora **US$ 0,09354600**, dentro de US$ 0,50.
Não declarar custo total zero. Não houve retries pagos após as seis falhas.

Foi solicitada atualização local da credencial, sem enviá-la no chat.
Após corrigir a credencial, retomar da raiz em nova pasta automática:

```powershell
.\.venv\Scripts\python.exe scripts/testes_reais_r6.py --carry-budget outputs/testes_reais/20261111-0050/orcamento.json
```

O ledger conserva as seis reservas no MESMO teto total de US$ 0,50; preflight
por deck e reserva antes de cada chamada. Não iniciar outro lote com orçamento
zerado. Retomada dentro do teto já autorizado exige credencial válida, sem nova
autorização de gasto. **Parte B permanece pendente, não concluída.**

Limitações: nota geométrica caiu 0,8023→0,7048, apesar dos critérios explícitos;
vazios externos, recorte/nitidez das fotos e grafo irrelevante do corpus antigo
persistem. Sem validação Office, avaliação humana cega ou pesquisa factual.
Conteúdo gerado não foi editado à mão para esconder falhas.

## Rodada 7 — fase 1: documentos e edição (11/11/2026)
Fontes registradas em refs/DOCUMENTOS_EDICAO_R7.md. Implementados extração DOCX limitada,
dossiê documental, prioridade documental sobre suplementos web, estilo auto, substituição
local de bloco Alto, CLI/API e histórico de revisões com consumo acumulado. Interface em
integração; testes ainda não executados nesta fase. Próximo: regressão, testes UI e lote real
com teto independente autorizado de US$ 0,60, sem imagens por IA. Sem commit/push/stash.

## Rodada 7 — fase 2: verificação e primeiro lote (11/11/2026)
672 pytest passaram em 117,82 s, Ruff limpo, dois Node; build npm com --configLoader
native passou (configuração padrão do esbuild não lê um ancestral no sandbox). Os dois
novos testes Playwright passaram; encerramento da suíte UI ainda em análise.
Primeiro lote falhou no transporte: cinco chamadas sem uso conhecido e reserva
US$ 0,08191650, preservadas no ledger. Retomada via stdin/runpy alcançou a API:
primeiro deck válido, DOCX inválido por A005. Custo conhecido até aí US$ 0,13237410,
limite com reservas US$ 0,21429060. Folha mostrou foto de evento irrelevante e recuperação
excessiva de exemplos CLI. Reforçados veto de eventos e prioridade a trechos narrativos
(resumo/introdução/objetivos/resultados/limitações). Nova execução em andamento, com
ledger acumulado; não declarar conclusão antes da inspeção dos artefatos finais.

## Rodada 7 — concluída em 11/11/2026

Plano: docs/PLANO_CODEX_RODADA7_DOCUMENTOS_EDICAO.md. Fontes previamente registradas em
refs/DOCUMENTOS_EDICAO_R7.md. Alterações anteriores preservadas; sem commit, push, stash,
imagens por IA, exposição de chave ou conteúdo do .env. TLS permaneceu verificado.

- T1: TXT/MD/PDF textual e DOCX sem dependência nova, até oito arquivos, 2 MiB por arquivo
  e 5 MiB para DOCX; macros/cifra recusadas. Dossiê local com trecho literal verificado,
  fontes documento:nome#trecho-N, prioridade documental e internet opt-in; CLI/API/UI.
- T2: refazer_slide troca somente o bloco selecionado; valida gramática/check_slide,
  no máximo um reparo. Ajustes sem modelo de estilo/foto/ordem/exclusão, histórico em
  outputs/criar/<id>/versoes e desfazer persistido; consumo inclui falhas e versões desfeitas.
- T3: Commons com categorias/extmetadata, consulta central preservada nos fallbacks,
  veto de retratos/eventos/diagramas e fallback de imagem sem foto em cartões/destaque.
  Revisão conservadora rejeita PNGs da busca fotográfica e metadados sem descrição
  suficiente. Buscas adicionais de foto sem inferência obtiveram varanda e roteador.
- T4: estilo auto determinístico, padrão na UI/CLI; público infantil e contexto acadêmico
  precedem tema técnico. Regra e limites em docs/REGRAS_DESIGN.md; troca sem modelo.
- T5: 678 pytest passaram em 112,72 s (um aviso Starlette/AnyIO preexistente), Ruff limpo,
  dois Node, npm build e lint passaram. Build usou --configLoader native por restrição
  do esbuild no sandbox. Playwright final: 15 passaram em 17,1 s, cinco testes locais
  opcionais pulados; inclui upload real e edição com modelo simulado. A primeira suíte
  exigiu encerrar sua própria árvore de servidor na porta 8777; a final usou servidor
  separado na porta 8778 e encerrou os testes normalmente. Logs em outputs/rodada7/.
- T6: seis PPTX finais, 42 slides, duas fotos Commons. Folhas finais, galeria e comparação
  antes/depois abertas. Original de documento/DOCX desta execução falhou em A005/A010;
  os slides 1/6 e 5 foram refeitos em pastas novas, sem editar o texto manualmente.
  Slide 3 refeito em uma chamada por US$ 0,00516750; outros sete blocos idênticos em bytes.

Evidência principal: outputs/testes_reais/20261111-0131_r7/INDICE.md, galeria.png,
03_refeito_revisado/antes_depois_slide3.png e preservacao.json. Antes em antes.slda e
antes.pptx; depois em apresentacao.slda e apresentacao.pptx na mesma pasta de edição.
ULTIMO.txt aponta para essa execução. ARQUIVOS_ALTERADOS.md e manifesto_sha256.json
relacionam arquivos e artefatos. Auditoria do deck do projeto encontrou zero números
visíveis ausentes dos fatos e conferiu os nomes técnicos; não prova toda paráfrase.

| Caso final | Válido | Fatos documentais usados | Fotos | Chamadas | USD |
|---|---|---:|---:|---:|---:|
| Artigo + README | sim | 19 | 0 | 37 | 0,06522735 |
| DOCX do artigo | sim | 19 | 0 | 34 | 0,06548055 |
| Refazer slide 3 | sim | 20 | 0 | 1 | 0,00516750 |
| Git | sim | 0 | 0 | 8 | 0,01478985 |
| Horta | sim | 0 | 1 | 7 | 0,01352625 |
| Internet | sim | 0 | 1 | 10 | 0,01797705 |

A tabela soma geração e reparos por caso; refazer é apenas o custo adicional de edição.
Casos finais US$ 0,18216855; tentativas anteriores US$ 0,13237410. Rodada inteira:
176 tentativas, 171 com uso conhecido; US$ 0,31454265 conhecidos. Cinco falhas iniciais
no transporte têm uso/custo desconhecidos, reserva US$ 0,08191650. Total exato desconhecido;
limite com reservas US$ 0,39645915 <= teto US$ 0,60. Nenhuma chamada de imagem por IA.
Ledgers anteriores preservados e acumulados, nunca reiniciados. Não houve HTTP 401 nesta
rodada. Retomada via stdin/runpy funcionou; causa das falhas de transporte não foi comprovada.
Lote encerrado: não fazer novas inferências para melhorar a amostra sem outra solicitação.

Continuam ruins: filtros lexicais perdem fotos úteis; a foto do roteador tem recorte apertado
com marca em destaque, e a varanda contém plantas ornamentais. Há comparações de aspectos
não equivalentes, repetição e generalizações (por exemplo, modelos menores e conexão sempre
ativa). O RAG inicial recuperava comandos CLI demais; priorizar trechos narrativos melhorou
o assunto, mas oito passagens não cobrem todo o artigo. Verificação por modelo tem falsos
positivos e custa chamadas. Validade formal não implica sustentação semântica nem beleza.
Prévias IR/Pillow, sem validação Office ou avaliação humana cega. Git/horta/internet não
usaram pesquisa factual. Projeto com IDs estáveis, reabertura pela UI, voz e celular
continuam como etapas futuras do plano maior; o histórico desta rodada é específico dos jobs Alto.

## Seminário 3 — teste dos diagramas SVG (18/11/2026)
- [x] SVG pelo compilador para etapas, ciclo e grafico (`alto-svg`), com testes.
- [x] Pedidos congelados com gabarito, script A × B e conferidor automático.
- [x] Teste pequeno rodou uma vez (Qwen3 4B local; API com 401).
- [x] Chave nova; teste pequeno com gpt-4.1-mini: A 0/3, B 3/3 (18/11).
- [x] Decks do seminário gerados com local e API e revisados (`academy/ai4good/va2/sem3/`).
- [ ] Congelar o código num commit (24/11) e rodar 12 pedidos × 3 seeds × 2 condições (25/11).
- [ ] Conferir ciclos à mão e checagem às cegas com 3 colegas (27/11); tabela no pitch (02/12).

## App no celular — gramática e frases (24/11/2026)
- [x] App 0.4.0: slides em SlideDSL Alto com gramática e limites do compilador (Teste 5, `docs/RESULTADOS_T5.md`).
- [x] Gramática funciona no llama.rn no emulador (`docs/NOITE_24_11.md`).
- [x] App 0.5.0: leitura do documento por frases numeradas; total projetado no celular 72,3 → 53,5 min (−26%),
      24/24 válidos (Teste 6, `docs/RESULTADOS_T6.md`).
- [ ] Medir o 0.5.0 no celular (agua.txt, 1.7B, 5 slides) e comparar com os 63 min do 0.3.0.
- [x] Dica de formato só com "…" (marcadores eram copiados por 1.7B e 0.6B); app 0.5.1 (Teste 7).
- [x] Bancada do 0.6B sem treino × 1.7B: válido 24/24, mas conteúdo pior (`docs/RESULTADOS_T7.md`).
- [x] LoRA no 0.6B destilado do 4B (pipeline do app): 22/24 completas (1.7B: 13; 0.6B: 8), 20,6 min projetados
      (1.7B: 53,5); app 0.6.0 importa o .gguf (Teste 8, `docs/RESULTADOS_T8.md`).
- [ ] Medir no celular o 0.6B + LoRA (velocidade real e qualidade) com o app 0.6.0.
- [ ] "como em F1" (id interno do fato) aparece no texto em 14/24 decks (1.7B e LoRA): corrigir no prompt.
- [ ] Exemplo "cresceu 30%" do prompt de conteúdo vaza para slides (1–2 de 24).

## PC e celular parecidos, fotos e edição no celular (24/11/2026)
- [x] Celular limpa o texto visível como o PC (sem "como em F1", caixa de frase); paridade conferida contra
      saídas do Python (`scripts/export_editorial_cases.py`, `test/editorial.test.mjs`).
- [x] PC ganha o motor "igual ao celular": o mesmo `generate()` do app (`bench/motor_pc.mjs`) em GGUF local
      escolhido no editor (`config/modelos_locais.json`, `src/slidedsl/motor_celular.py`); o editor do PC edita o
      resultado como no fluxo completo.
- [x] Celular edita slide a slide: refazer com IA (mesmo prompt/gramática, com instrução), editar texto, mover,
      excluir, desfazer (`src/pipeline/edit.ts`).
- [x] Fotos da internet no celular (opcional): slides "imagem" com foto livre do Openverse/NASA e crédito
      (`src/pipeline/images.ts`); também no motor do celular no PC (`--imagens`).
- [x] Imagens do PC voltaram a funcionar: a busca estava presa no Wikimedia Commons, que responde 403 sem
      contato no User-Agent; e a gramática de geração permitia `arquivo` inexistente (agora só `buscar`).
- [ ] LoRA no Qwen3-4B-Instruct (QLoRA em 4 bits) para o PC: treino em andamento; converter, medir na bancada.
- [ ] Commons: informar contato (SLIDEDSL_CONTACT) se o usuário quiser fotos do Wikimedia de volta.
- [ ] Testar a edição e as fotos no emulador/celular (APK 0.7.0).
- [ ] O LoRA do 0.6B não viu slides "imagem" no treino: com fotos ligadas, gerar dataset com imagem.
- [x] Diagramas no próprio slide: etapas em caixas com setas e ciclo em círculo, formas editáveis, iguais no PC e
      no celular (paridade 356/356); geração pode escolher "ciclo" (`docs/DIAGRAMAS_NO_SLIDE.md`).
- [x] Código do teste SVG do Seminário 3 congelado na tag `sem3-svg-congelado`.
- [ ] Ciclo de 5 fases sai como lista (não cabe); avaliar composição 3+2.


## Teste no celular e documento longo (25/11/2026)

- Teste real no moto g8 power lite com o 0.6B LoRA e o `agua.txt`: levou 48 min. O interruptor "Gramática" estava desligado (modo JSON), e houve 4 reparos (18,5 min). Os slides 3 e 5 viraram divisórias vazias por A005.
- App 0.7.2:
  - o LoRA roda sempre no modo gramática;
  - erro só de tamanho depois do reparo encurta o texto na palavra inteira (F002);
  - o slide do compilador usa os fatos planejados em tópicos.
- Teste com o PDF do próprio TCC (`docs/TESTE_TCC_DOCUMENTO_LONGO.md`): os decks são válidos, mas o conteúdo é raso ou inventado nos 3 modelos locais. O GPT-4.1-mini cobriu tudo.
- Causa principal: o roteiro do app só vê os 3 primeiros fatos (o PC vê 32).
- Pendentes (decisão do autor):
  1. o roteiro do app ver todos os fatos (só as afirmações);
  2. pular as referências e seguir as seções do documento, sempre com o resumo;
  3. limpar a hifenização e os cabeçalhos do PDF;
  4. ~~sobreposição na capa~~: falso alarme, era só a prévia do VS Code (no PowerPoint fica correto).
- App 0.7.3: aplica as correções 1–3 dos pendentes acima e mais três (TCC refeito em `docs/TESTE_TCC_DOCUMENTO_LONGO.md`, rodada 4):
  - a gramática aceita só os caracteres que o compilador mede;
  - número inventado bloqueia em números/gráfico;
  - texto cortado perde só a palavra pela metade.
- Teste no celular com o 0.7.2 (0.6B LoRA, `agua.txt`): 17,8 min, contra 48 min antes, sem reparos. Mas 3 slides repetiam evaporação/condensação.
- App 0.7.4, para a repetição:
  - fatos diferentes por slide depois do roteiro (`distributeFacts`);
  - o pedido de cada slide lista os itens já escritos;
  - item com o mesmo texto de outro pede reparo, e a cópia sai se persistir.
  - Medido no caso da água (0.6B LoRA, sementes 11/22/33, `outputs/repeticao_agua/`): pares de slides repetidos (Jaccard ≥ 0,3) foram de 5 para 1, e os fatos usados, de 5–6 para 7–8. Os erros de conteúdo do 0.6B continuam.
- Teste 9 (`docs/RESULTADOS_T9.md`): bancada do app 0.7.5 contra T7/T8.
  - **Ganhos:** fatos citados por deck 2,3–2,9 → 5,3–7,7; completas 8 → 16 (0.6B) e 13 → 17 (1.7B); slides de seção quase zero; pares de slides parecidos no LoRA 12 → 6.
  - **Custo:** cerca de 10% a mais de tempo projetado no celular (LoRA 20,6 → 22,9 min).
- **Código congelado (25/11, 05h30): tag `artigo-v1`, app 0.7.6.**
  - Verificação: pytest 755/755, app 97/97, núcleo 44/44, editor 15 (+5 pulados), paridade PC/celular 861/861, contratos mobile em sincronia.
  - Emulador: APK 0.7.5 gerou 5 slides com o 0.6B base (19,0 min) e com o LoRA (20,5 min).
  - Bancada do 0.7.6 igual à do 0.7.5 (T9).
- **App 0.7.7 (25/11, tarde):** capa com título centralizado agora fica no centro do slide (antes centrava nas 10 colunas da esquerda). Vale para PC e celular, pois o núcleo é o mesmo. Só muda a posição da capa nos estilos centralizados; os números do T9 continuam valendo. pytest 755/755, núcleo 44/44, paridade 866/866.
- **Código congelado para o artigo: tag `artigo-v2` e branch `congelado/artigo-v2` (commit 498a537, app 0.7.7).** Bancada T9 repetida (`outputs/teste9_v077_*`): igual ao 0.7.6. Com testes pareados, a vantagem do LoRA em completas deixou de ser significativa (20 × 17 do 1.7B, p = 0,45); o tempo segue significativo (22,9 × 58,9 min, p < 0,001). Artigo atualizado (LoRA, gramática com limites, leitura por frases, celular 17,8/20,7 min).
- **Fluxo do PC com documento (25/11, noite, depois do `artigo-v2`):** um .md curto com muitas seções saía com slides vazios ou invertidos ("a garantia não veio de graça"). Causas e correções: (1) só 12 trechos eram lidos → documento que cabe em `max_chars` é lido inteiro, na ordem; (2) o roteiro via só os 32 primeiros fatos → com mais de 32, todos, compactos; (3) 4 fatos por slide → 6; (4) o modelo deixava seções de fora → roteiro segue as seções quando elas cabem; (5) slide da seção sem os resultados → os fatos com números da seção entram. GPT-5.4-mini, mesmo .md: 38 → 61 fatos, os 4 testes e as limitações com os números certos. pytest 760/760.
- **App: leitura de documento (26/11, branch `exp/celular-documento`):** porte das correções 1, 2, 4 e 5 do PC sem chamadas a mais (documento curto lido inteiro em até 6 leituras de trechos vizinhos; seções e resultados no roteiro) e citação de número em qualquer campo. Com o .md do professor: 4B foi de 2 para 7 dos 9 números, 0.6B LoRA de 2/7 para 6/7 seções, e 4 de 5 modelos ficaram mais rápidos. No `agua.txt`: de 7% a 25% mais lento, com mais números do documento. App 103/103. Detalhes em `docs/CELULAR_DOCUMENTO_26NOV.md`. Falta testar no aparelho.
- **App (26/11, segunda rodada):** leitura literal (o modelo só escolhe a frase; a afirmação é a frase original), corte de palavra perto do limite e título copiado do prompt. O erro "modelo de 4B treinado" sumiu. Todos os modelos ficaram mais rápidos que antes do branch (4B: 52,6 → 38,5 s no .md e 32,7 → 24,8 s no agua.txt), com mais números do documento (4B: 8 de 9). App 105/105.
- **App (26/11, terceira rodada):** nos modelos pequenos (0.6B, 1.7B), o detalhe de cada item vira a frase do fato que mais combina com ele, e item sem fato sai; texto copiado do prompt sai em todos os modelos. As inversões de número sumiram no 0.6B LoRA e no 1.7B; 0.6B LoRA com 7/7 seções. O 0.6B base continua fraco. App 109/109. `docs/CELULAR_DOCUMENTO_26NOV.md`.
