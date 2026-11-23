# Plano do TCC — SlideDSL

Criado em 22/11/2026. Junta a avaliação de outubro ([orientacao/AVALIACAO_DO_TCC.md](orientacao/AVALIACAO_DO_TCC.md)),
o Plano B daquele mês ([orientacao/PLANOS_PARA_O_MES.md](orientacao/PLANOS_PARA_O_MES.md)) e a
especificação dos testes e da APK ([PLANO_TESTES_E_APK.md](PLANO_TESTES_E_APK.md)).
Fontes conferidas: [../refs/TCC_TESTES_APK_FONTES.md](../refs/TCC_TESTES_APK_FONTES.md).

## 1. Tese

> Um modelo pequeno, aberto e local, guiado por uma linguagem formal (SlideDSL Alto → 1.1 → IR),
> gera apresentações **válidas e editáveis** gastando **menos tokens** que gerar o arquivo
> diretamente, e isso é viável **até num celular**, sem depender de API paga.

Motivação: **dependência** (poucas empresas, API paga, conexão), não "indisponibilidade" da IA.
É a reformulação já combinada na avaliação de outubro.

### Perguntas de pesquisa e o teste que responde cada uma

| # | Pergunta | Teste | Já existe? |
|---|---|---|---|
| P1 | Quanto o formato pesa no custo de saída? (Alto × 1.1 × JSON × python-pptx × texto) | T1 | Não: novo, sem rodar modelo |
| P2 | Com o mesmo SLM, a SlideDSL gera mais decks válidos por token que gerar python-pptx direto? | T2 | Parcial (E3: 0/10 → 10/10) |
| P3 | Restringir pela gramática (GBNF) ajuda ou atrapalha, e quanto custa por token? | T3 | **Não: maior lacuna apontada em outubro** |
| P4 | Quantos reparos valem a pena? (define o modo celular) | T7 | Não |
| P5 | Roda num celular comum? Com que velocidade, memória e temperatura? | T4 + APK | Não |
| P6 | Os slides são bons, além de válidos? | T5 | **Não: segunda lacuna de outubro** |

T6 (nota combinada acerto × eficiência) e a análise estatística costuram P1–P5 no capítulo de
resultados.

### Contribuições que o TCC pode afirmar ao final

1. A SlideDSL em duas camadas como forma de **renderização adiada** (Agyemang et al., 2026) para
   slides, com medição do custo do formato (T1).
2. Comparação controlada SLM com × sem DSL, com estatística pareada (T2, T3).
3. Primeira medição da geração restrita por GBNF com modelo real no projeto (T3).
4. Perfil "modo celular" derivado de dados (T7) e medido em aparelho real (T4).
5. APK offline como prova de viabilidade (P5).

## 2. Recorte: o que entra e onde cortar

O cronograma está em ordem de **retorno por esforço**. Se o prazo apertar, corta-se de baixo para
cima, e o que fica acima da linha continua sendo um TCC completo.

| Ordem | Fase | Esforço | Precisa de quê |
|---|---|---|---|
| F0 | Tokens e tempo por chamada | feito | — |
| F1 | Base comum: 12 pedidos + dossiês fixos + executor retomável | 2–3 dias | SearXNG uma vez |
| F2 | T1 custo do formato | 3–4 dias | só CPU + tokenizador |
| F3 | T3 modos de restrição (inclui GBNF real) + microbenchmark | 3–4 dias | llama-server + GGUF no PC |
| F4 | T2 com × sem SlideDSL (A e C; B se houver chave) | 4–5 dias | Ollama/llama-server |
| F5 | T7 reparos → `--perfil celular` | 2–3 dias | reaproveita F3/F4 |
| F6 | T4 celular via Termux | 3–4 dias | um Android com 6 GB+ |
| — | **Linha mínima: com F0–F6 + análise, o TCC está defensável** | | |
| F7 | T5 qualidade (juiz automático; humano adiado) + T6 | 3–4 dias | modelo de visão |
| F8 | APK | 2–4 semanas | ver seção 4 |
| F9 | Escrita final, figuras, slides da defesa | contínuo; 1 semana dedicada | — |

**Regra de outubro mantida:** congelar o código do pipeline antes de F3. Depois disso, só correção
de erro, registrada no ROADMAP. Mudar código entre experimentos foi o que tornou os experimentos
E1–E11 não comparáveis.

**Nota sobre T5:** a avaliação humana é a lacuna mais cobrada pela banca. Se F8 atrasar, vale mais
fazer T5 que terminar a APK. Uma APK sem T5 é demonstração; um T5 sem APK continua sendo pesquisa.

## 3. Cronograma (prazo final a confirmar com o orientador)

Semanas a partir de 23/11/2026:

| Semana | Código | Escrita |
|---|---|---|
| 1 | F1, F2 | Cap. Fundamentação: formatos e custo de saída (Agyemang, TOON) |
| 2 | F3 (congelar antes), F4 iniciado | Cap. Método: protocolo pareado, sementes, estatística |
| 3 | F4, F5 | — |
| 4 | F6 (Termux), análise F2–F6 | Cap. Resultados (P1–P5), primeira versão |
| 5 | F7 (T5/T6) | Discussão e limitações |
| 6–8 | F8 (APK) | Cap. Implementação mobile; revisão geral |
| 9 | — | Versão final + slides da defesa |

Se o prazo for menor que 9 semanas: tirar F8 do escopo obrigatório e apresentar a APK como
"trabalho futuro com prova de conceito" (Termux + Etapa 2 web).

## 4. APK: decisão de arquitetura (F8)

A especificação propõe React Native + llama.rn + **porte do compilador para TypeScript** com testes
de paridade. O porte é a parte mais cara (parser Lark, A0xx, layouts, semântica, D001–D010) e é o
maior risco de não terminar.

**Proposta:** antes de portar, fazer um **spike de 2 dias** com Python embarcado no Android
(Chaquopy) rodando o próprio pacote `slidedsl`:

- Critério de sucesso: `parse → validar → compilar → IR` de `examples/alto/` dentro do app, em
  menos de 2 s por deck. Pontos de atenção: `pydantic-core` (Rust) precisa de wheel Android;
  `lark` é Python puro.
- PPTX: PptxGenJS numa WebView a partir da IR (não depende do Python).
- LLM: llama.cpp nativo (llama.rn ou JNI) servindo o mesmo GBNF.
- Se der certo: **não há porte nem paridade**, e o compilador do app é o mesmo do artigo.
- Se falhar: seguir o porte para TypeScript da especificação, começando pelo parser Alto e pelos
  testes de paridade.

Antes da APK, F6 (Termux) já responde P5 com dados. A APK é a entrega de produto, não a evidência.

## 5. Estrutura do texto do TCC

| Capítulo | Conteúdo | Evidência / referências |
|---|---|---|
| 1. Introdução | Dependência de IA paga; pergunta; contribuições | AI Index; Kapoor et al.; Schwartz et al. (Green AI) |
| 2. Fundamentação | GLC, LALR, DSL; SLMs; geração restrita; formato e custo; slides com IA; IA no celular | Aho et al.; Lark; Willard & Louf; XGrammar; Tam et al.; Agyemang et al.; Masciari et al.; AutoPresent; PPTAgent; MELT; PalmBench |
| 3. SlideDSL | Duas camadas, compilador, pipeline, pesquisa com fatos verificados | Código + E1–E11 (docs/artigo/EVIDENCIAS_TECNICAS.md) |
| 4. Método | Pedidos, dossiês fixos, pareamento, 5 sementes, métricas, estatística | F0, F1 |
| 5. Resultados | P1–P6 | `docs/RESULTADOS_TESTES.md` gerado por F2–F7 |
| 6. Celular | Termux, perfil celular, APK | F5, F6, F8; Tummalapalli et al. |
| 7. Discussão e limitações | Medido × interpretado; ameaças à validade | — |

Referências: o artigo existente já tem a base teórica conferida (docs/artigo/REFERENCIAS.md). As
novas entram de [../refs/TCC_TESTES_APK_FONTES.md](../refs/TCC_TESTES_APK_FONTES.md). Copiar o
BibTeX para o artigo só quando a fonte for de fato citada (regra de `academy/refs/CONTEXT.md`).

## 6. Riscos

| Risco | Efeito | Mitigação |
|---|---|---|
| Prazo | APK incompleta | Linha mínima em F6; APK por último |
| GBNF do Alto não funcionar no llama-server com modelo real | T3 sem o modo `gramatica` | É um resultado negativo publicável; registrar e seguir com 3 modos |
| Celular sem RAM para 4B | Matriz T4 menor | Medir 0.6B e 1.7B; 4B só se houver aparelho |
| Energia não confiável no Android | T6 sem energia | Usar tokens e tempo de geração; energia como estimativa (aviso do Tummalapalli et al.) |
| Poucos avaliadores humanos | T5 fraco | 3 pedidos × 3 grupos, formulário curto; mínimo de 3 pessoas |
| Código mudar entre experimentos | Resultados incomparáveis | Congelar antes de F3; registrar commit em cada CSV |

## 7. Decisões de 22/11/2026 (autor)

- **APK é obrigatória.** F8 sai de "extensão" e entra no núcleo; roda em paralelo com F2–F6
  (o Codex porta o núcleo TS enquanto os testes avançam).
- **Avaliação humana (T5) fica para depois.** T5 automático (juiz por modelo de visão) continua
  possível; o pacote cego humano é adiado.
- **Prazo:** a confirmar.
- **Arquitetura da APK:** porte em TypeScript **apenas do caminho do app** (AltoDeck JSON →
  validação → layout → IR → PptxGenJS), com paridade de IR contra o Python. Chaquopy descartado por
  agora: precisaria de versões Android não oficiais de `pydantic-core`/`rpds-py` e esta máquina não
  tem Android SDK para testar. O app recebe JSON do modelo (llama.rn converte JSON Schema em GBNF),
  então não é preciso ler texto Alto/1.1 no celular na primeira versão.
  Rodada 1: [PLANO_CODEX_TCC_APK1_CORE.md](PLANO_CODEX_TCC_APK1_CORE.md).
- **Ambiente:** sem Android SDK, `adb` e `llama-server` nesta máquina. O build do APK exige instalar
  o Android SDK (ou usar o build em nuvem do Expo, com conta). Fica para a rodada 2 da APK.

## 7b. Recorte para 27/11/2026 (decisão do autor em 23/11)

- **Entrega: só o artigo** (sem monografia), LNCS em português, no projeto Overleaf já clonado
  (`academy/papers/artigo-overleaf/`, substituindo o relatório do Ordered GNN). Plano:
  [PLANO_CODEX_ARTIGO_TCC.md](PLANO_CODEX_ARTIGO_TCC.md).
- Entram: APK funcionando (voz + documento), Teste 1 (custo do formato), Teste 3 reduzido
  (gramática × JSON × direto, à noite na RTX 3060), Teste 4 no celular do autor, F0/F1.
- Ficam como trabalho futuro: Teste 2 completo, T5 (qualidade), avaliação humana, T7 medido
  (perfil celular justificado pela literatura).
- Cronograma: 23 APK + T1 · 24 T3 à noite + gerações no celular · 25 análise e texto ·
  26 revisão · 27 entrega.

## 8. Estado

- [x] F0 implementada e testada (22/11/2026).
- [x] F1 (implementado): `benchmark/format_requests.json` (12 pedidos, 5 sementes, semente de ordem),
  `src/slidedsl/experiment_runner.py` (plano pareado e execução retomável) e
  `scripts/build_dossiers.py` (dossiês fixos, retomável). 5 testes.
- [ ] F1 (executar): subir o SearXNG e gerar `benchmark/dossies/` uma vez.
- [ ] F8 rodada 1: núcleo TS + paridade (Codex).
- [ ] F2 em diante.
