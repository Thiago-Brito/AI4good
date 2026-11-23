# Referências do artigo científico sobre o SlideDSL

Bibliografia usada em [ARTIGO_CIENTIFICO_SLIDEDSL.md](ARTIGO_CIENTIFICO_SLIDEDSL.md), em formato
próximo da ABNT NBR 6023. Para cada obra, o registro indica:

- **Conceito usado** — o que a obra diz e que o artigo aproveita;
- **Relação com o SlideDSL** — se a obra foi **inspiração** (orientou o projeto), se descreve um
  mecanismo **efetivamente implementado** no código ou se é **apenas contexto teórico** acrescentado
  pelo artigo;
- **Verificação** — como a referência foi conferida.

Legenda de verificação:

- **[V-web]**: título, autores, veículo e identificador conferidos em busca web em 12/10/2026
  (registro bibliográfico; não equivale a leitura integral);
- **[V-proj]**: conferida pelo projeto em `docs/REFERENCIAS.md` ou `refs/FONTES.md`, com link
  registrado;
- **[Clássica]**: obra de referência consolidada da área, citada pela edição usual; recomenda-se
  confirmar paginação na edição física usada no TCC.

Nenhuma referência foi incluída sem uma dessas verificações. Números citados no artigo que vêm
dessas obras foram restritos ao que o projeto ou a busca registraram.

---

## 1. Linguagens formais e compiladores

**CHOMSKY, N. Three models for the description of language. *IRE Transactions on Information
Theory*, v. 2, n. 3, p. 113–124, 1956. DOI: 10.1109/TIT.1956.1056813.** [Clássica]
- Conceito: hierarquia de gramáticas; gramáticas de estrutura sintagmática (origem das GLCs).
- Relação: contexto teórico da seção 2.1. Não foi citada pelo projeto.

**HOPCROFT, J. E.; MOTWANI, R.; ULLMAN, J. D. *Introduction to Automata Theory, Languages, and
Computation*. 3. ed. Boston: Addison-Wesley, 2006.** [Clássica]
- Conceito: definição formal G = (V, Σ, P, S), derivações, árvores de derivação, ambiguidade.
- Relação: contexto teórico da seção 2.1.

**AHO, A. V.; LAM, M. S.; SETHI, R.; ULLMAN, J. D. *Compilers: Principles, Techniques, and Tools*.
2. ed. Boston: Pearson/Addison-Wesley, 2006.** [Clássica]
- Conceito: análise léxica, análise sintática LR/LALR, AST, representação intermediária, análise
  semântica e geração de código.
- Relação: contexto teórico da seção 2.2; o pipeline do SlideDSL (parser → AST → IR → validações →
  geração) segue essa decomposição clássica.

**DeREMER, F. L. *Practical Translators for LR(k) Languages*. Tese (Doutorado) — Massachusetts
Institute of Technology, Cambridge, 1969.** [Clássica]
- Conceito: origem do método LALR (*look-ahead LR*).
- Relação: contexto teórico; o projeto usa LALR por meio do Lark.

**LARK. *Lark — a parsing toolkit for Python*. Documentação.** Disponível em:
https://lark-parser.readthedocs.io/. [V-proj]
- Conceito: parser LALR(1) com lexer contextual, `propagate_positions`, aliases `->` e regras
  inline `?`.
- Relação: **implementado** — `src/slidedsl/parser.py` (`grammar_parser`) e
  `src/slidedsl/alto.py` carregam as gramáticas `.lark` com `parser="lalr"`.

**MERNIK, M.; HEERING, J.; SLOANE, A. M. When and how to develop domain-specific languages. *ACM
Computing Surveys*, v. 37, n. 4, p. 316–344, 2005. DOI: 10.1145/1118890.1118892.** Disponível em:
https://ir.cwi.nl/pub/4109/. [V-proj]
- Conceito: DSLs trocam generalidade por expressividade e possibilidade de análise no domínio;
  padrões de decisão, análise, projeto e implementação.
- Relação: **inspiração** declarada para a SlideDSL e para a separação em dois níveis (Alto × 1.1).

**FOWLER, M. *Domain-Specific Languages*. Boston: Addison-Wesley, 2010.** [Clássica]
- Conceito: DSLs externas, modelo semântico separado da sintaxe.
- Relação: contexto teórico (a IR do SlideDSL funciona como modelo semântico). Não citada pelo
  projeto.

## 2. Modelos de linguagem, SLMs e inferência local

**LU, Z. et al. Small Language Models: Survey, Measurements, and Insights. arXiv:2409.15790, 2024.**
Disponível em: https://arxiv.org/abs/2409.15790. [V-proj]
- Conceito: levantamento de SLMs abertos (100M–5B parâmetros); lacunas em raciocínio complexo;
  efeito da quantização na latência.
- Relação: **inspiração** para decompor a tarefa em chamadas curtas.

**YANG, A. et al. Qwen3 Technical Report. arXiv:2505.09388, 2025.** Disponível em:
https://arxiv.org/abs/2505.09388. [V-proj]
- Conceito: família Qwen3, pesos abertos.
- Relação: documentação do modelo efetivamente usado (`qwen3:4b-instruct`, `qwen3:0.6b`, `qwen3:4b`).

**BELCAK, P. et al. Small Language Models are the Future of Agentic AI. arXiv:2506.02153, 2025.
DOI: 10.48550/arXiv.2506.02153.** Disponível em: https://arxiv.org/abs/2506.02153. [V-web]
- Conceito: artigo de posição defendendo SLMs para tarefas especializadas e repetitivas, com
  sistemas heterogêneos quando há necessidade de capacidade geral.
- Relação: contexto teórico acrescentado pelo artigo. É um artigo de **posição**, não um resultado
  experimental; não sustenta superioridade de SLMs.

**KAPOOR, S. et al. Position: On the Societal Impact of Open Foundation Models. In: *Proceedings of
the 41st International Conference on Machine Learning (ICML)*. PMLR, v. 235, p. 23082–23104, 2024.**
Disponível em: https://proceedings.mlr.press/v235/kapoor24a.html. [V-proj]
- Conceito: benefícios e riscos de modelos com pesos abertos.
- Relação: motivação (execução local, auditabilidade).

**MASLEJ, N. et al. *The AI Index 2024 Annual Report*. Stanford: Stanford HAI, 2024.** Disponível em:
https://aiindex.stanford.edu/report/. [V-proj]
- Conceito: estimativas de custo de treinamento de modelos de fronteira.
- Relação: motivação. Os números vêm, no projeto, de cobertura jornalística da Fortune
  (registrada em `docs/REFERENCIAS.md`); o artigo os cita apenas como motivação.

**STANFORD HAI. *AI Index 2025: State of AI in 10 Charts*. 2025.** Disponível em:
https://hai.stanford.edu/news/ai-index-2025-state-of-ai-in-10-charts. [V-proj]
- Conceito: queda de custo de inferência e melhora de modelos pequenos.
- Relação: motivação.

**SCHWARTZ, R.; DODGE, J.; SMITH, N. A.; ETZIONI, O. Green AI. *Communications of the ACM*, v. 63,
n. 12, p. 54–63, 2020.** Preprint: https://arxiv.org/abs/1907.10597. [V-proj]
- Conceito: eficiência como critério de avaliação; relatar custo computacional.
- Relação: motivação para registrar chamadas, tokens e tempos.

**STRUBELL, E.; GANESH, A.; McCALLUM, A. Energy and Policy Considerations for Deep Learning in NLP.
In: *Proceedings of the 57th Annual Meeting of the ACL*. Florença: ACL, 2019. p. 3645–3650.**
Disponível em: https://aclanthology.org/P19-1355/. [V-proj]
- Relação: motivação (custo ambiental e financeiro).

**OLLAMA. Structured outputs. Documentação oficial.** Disponível em:
https://docs.ollama.com/capabilities/structured-outputs (anúncio: https://ollama.com/blog/structured-outputs,
6 dez. 2024). [V-proj]
- Conceito: o campo `format` da API aceita um JSON Schema que restringe a saída.
- Relação: **implementado** — `src/slidedsl/models/ollama_model.py` envia `payload["format"]`; é o
  modo padrão (`json`) dos fluxos planejados e do fluxo Alto.

**OLLAMA. Chat API e Thinking. Documentação oficial.** Disponível em: https://docs.ollama.com/api/chat
e https://docs.ollama.com/capabilities/thinking. [V-proj]
- Relação: **implementado** — parâmetros `options` (temperatura, seed, `num_ctx`, `num_predict`),
  `think`, `done_reason` e contagens de tokens registradas pelo adaptador.

**GGML-ORG. llama.cpp — GBNF Guide (grammars/README.md) e server README.** Disponível em:
https://github.com/ggml-org/llama.cpp/blob/master/grammars/README.md e
https://github.com/ggml-org/llama.cpp/tree/master/tools/server. [V-proj]
- Conceito: gramáticas GBNF que restringem a amostragem; recursão à esquerda não suportada;
  parâmetros `grammar` e `json_schema` no servidor.
- Relação: **implementado, não avaliado com modelo real** — `src/slidedsl/gbnf.py` e
  `src/slidedsl/models/llamacpp_model.py`.

## 3. Geração estruturada e decodificação restrita por gramática

**GENG, S.; JOSIFOSKI, M.; PEYRARD, M.; WEST, R. Grammar-Constrained Decoding for Structured NLP
Tasks without Finetuning. In: *Proceedings of EMNLP 2023*. Singapura: ACL, 2023. p. 10932–10952.**
Disponível em: https://aclanthology.org/2023.emnlp-main.674. DOI: 10.18653/v1/2023.emnlp-main.674. [V-proj][V-web]
- Conceito: gramáticas formais descrevem o espaço de saída; decodificação restrita permite que
  modelos sem ajuste fino produzam saídas estruturadas válidas.
- Relação: **inspiração** para o modo `gramatica` (GLC → GBNF).

**WILLARD, B. T.; LOUF, R. Efficient Guided Generation for Large Language Models.
arXiv:2307.09702, 2023.** Disponível em: https://arxiv.org/abs/2307.09702. [V-proj]
- Conceito: geração guiada como transições de autômato com indexação do vocabulário (Outlines).
- Relação: contexto para explicar como JSON Schema e GBNF restringem tokens.

**SCHOLAK, T.; SCHUCHER, N.; BAHDANAU, D. PICARD: Parsing Incrementally for Constrained
Auto-Regressive Decoding from Language Models. In: *Proceedings of EMNLP 2021*. ACL, 2021.
p. 9895–9901.** Disponível em: https://aclanthology.org/2021.emnlp-main.779. DOI: 10.18653/v1/2021.emnlp-main.779. [V-proj][V-web]
- Conceito: rejeitar, durante a decodificação, tokens que levariam a programas inválidos.
- Relação: precedente para validar saídas de modelos com um parser.

**WANG, B. et al. Grammar Prompting for Domain-Specific Language Generation with Large Language
Models. In: *Advances in Neural Information Processing Systems 36 (NeurIPS 2023)*.** Disponível em:
https://arxiv.org/abs/2305.19234. [V-proj]
- Conceito: incluir uma gramática BNF especializada no prompt melhora a geração de programas de DSL.
- Relação: **inspiração/implementado** — `prompts/system_dsl.txt` inclui a GLC e exemplos no modo
  de geração direta.

**TAM, Z. R. et al. Let Me Speak Freely? A Study on the Impact of Format Restrictions on Performance
of Large Language Models. In: *Proceedings of EMNLP 2024: Industry Track*. Miami: ACL, 2024.
p. 1218–1236. DOI: 10.18653/v1/2024.emnlp-industry.91.** Disponível em:
https://aclanthology.org/2024.emnlp-industry.91/. [V-web]
- Conceito: restrições de formato (JSON, XML, YAML) podem degradar o raciocínio de LLMs; restrições
  mais estritas tendem a causar maior degradação.
- Relação: contexto crítico acrescentado pelo artigo; sustenta a discussão de que restringir a forma
  não garante qualidade do conteúdo. Não foi testado no SlideDSL.

## 4. Recuperação, alucinação, decomposição e autocorreção

**LEWIS, P. et al. Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. In: *Advances
in Neural Information Processing Systems 33 (NeurIPS 2020)*.** Disponível em:
https://arxiv.org/abs/2005.11401. [V-proj]
- Relação: **inspiração** para o passo de pesquisa (SearXNG → trechos → fatos).

**JI, Z. et al. Survey of Hallucination in Natural Language Generation. *ACM Computing Surveys*,
v. 55, n. 12, art. 248, 2023. DOI: 10.1145/3571730.** Disponível em: https://arxiv.org/abs/2202.03629. [V-proj]
- Relação: **inspiração** para fichas com trecho literal verificado (`research.verify_fact`), avisos
  A007/A012 e verificação de sustentação A014.

**ZHOU, D. et al. Least-to-Most Prompting Enables Complex Reasoning in Large Language Models. In:
*International Conference on Learning Representations (ICLR)*, 2023.** Disponível em:
https://arxiv.org/abs/2205.10625. [V-proj]
- Relação: o projeto registra a decomposição como **hipótese de engenharia** inspirada nessa linha;
  os resultados do artigo não se transferem automaticamente ao Qwen3 4B.

**ZHANG, Y. et al. Small Language Models Need Strong Verifiers to Self-Correct Reasoning. In:
*Findings of the Association for Computational Linguistics: ACL 2024*.** Disponível em:
https://arxiv.org/abs/2404.17140. [V-proj][V-web]
- Conceito: a autocorreção de modelos pequenos depende de verificadores fortes; verificadores fracos
  (o próprio modelo) limitam o ganho.
- Relação: fundamenta a escolha de verificadores **determinísticos** (parser, semântica, regras) e a
  ressalva de que A014 usa o próprio SLM como verificador.

**SEARXNG. Search API. Documentação oficial.** Disponível em: https://docs.searxng.org/dev/search_api.html. [V-proj]
- Relação: **implementado** — buscador local (`research.py`, `searxng/`).

## 5. Design de apresentações e aprendizagem multimídia

**ALLEY, M.; SCHREIBER, M.; RAMSDELL, K.; MUFFO, J. How the design of headlines in presentation
slides affects audience retention. *Technical Communication*, v. 53, n. 2, p. 225–234, 2006.** [V-web]
- Conceito: estudo piloto em curso de geologia comparando títulos em frase com evidência visual
  versus título-tópico com marcadores; o grupo com títulos em frase teve maior acerto em questões
  específicas (o estudo compara turmas de anos diferentes).
- Relação: **inspiração** para o título-mensagem (contrato editorial da SlideDSL Alto). O SlideDSL
  não replica nem mede esse efeito.

**GARNER, J. K.; ALLEY, M. P. How the design of presentation slides affects audience comprehension:
a case for the assertion-evidence approach. *International Journal of Engineering Education*, v. 29,
n. 6, p. 1564–1579, 2013.** Disponível em: https://writing.engr.psu.edu/ae_comprehension.pdf. [V-web]
- Conceito: experimento com 110 estudantes de engenharia; slides assertion–evidence associados a
  melhor compreensão, menos concepções errôneas e menor carga cognitiva percebida.
- Relação: **inspiração** para títulos como afirmações e corpo como evidência. Uma crítica a essa
  linha de pesquisa aponta comparações com exemplos de controle fracos; o artigo registra isso como
  limite da evidência externa.

**ALLEY, M. et al. Assertion–Evidence Approach (tutorial e checklist).** Disponível em:
https://www.assertion-evidence.org/tutorial.html, https://writing.engr.psu.edu/assertion_evidence_EA.html
e https://www.writing.engr.psu.edu/AE_checklist.pdf. [V-proj]
- Relação: **inspiração** — consultado em 11/10/2026 para o planejamento visual (mensagem em
  título de frase sustentada por evidência visual). O projeto registra que um PDF de notas de aula não
  pôde ser lido integralmente.

**ALLEY, M. *The Craft of Scientific Presentations*. 2. ed. New York: Springer, 2013.** [Clássica]
- Relação: obra de referência do autor; contexto. Não foi lida pelo projeto.

**MAYER, R. E.; FIORELLA, L. Principles for reducing extraneous processing in multimedia learning:
coherence, signaling, redundancy, spatial contiguity, and temporal contiguity principles. In: MAYER,
R. E. (ed.). *The Cambridge Handbook of Multimedia Learning*. 2. ed. Cambridge: Cambridge University
Press, 2014.** Disponível em: https://www.cambridge.org/core/books/cambridge-handbook-of-multimedia-learning/principles-for-reducing-extraneous-processing-in-multimedia-learning-coherence-signaling-redundancy-spatial-contiguity-and-temporal-contiguity-principles/C98AB3A6CE760DD63C048936EA0B3B44. [V-proj]
- Conceito: coerência, sinalização, contiguidade espacial.
- Relação: **inspiração** para o planejamento visual. O projeto declara ter consultado apenas o
  resumo do capítulo.

**W3C. *Web Content Accessibility Guidelines (WCAG) 2.2* — Understanding SC 1.4.3: Contrast
(Minimum).** Disponível em: https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html. [V-proj]
- Conceito: razão de contraste (L1 + 0,05)/(L2 + 0,05), mínimo 4,5:1 para texto normal.
- Relação: **implementado** — `design_rules.py` (`luminance`, `contrast`, D002) com
  `contrast_minimum: 4.5`.

**MICROSOFT. Tips for creating and delivering an effective presentation. Microsoft Support.**
Disponível em: https://support.microsoft.com/en-us/office/tips-for-creating-and-delivering-an-effective-presentation-f43156b0-20d2-4c51-8345-0c337cefb88b. [V-web]
- Conceito: fontes simples (Arial, Calibri), evitar fontes menores que 18 pt, alto contraste entre
  fundo e texto, tema consistente, frases curtas, gráficos com moderação.
- Relação: **contexto acrescentado pelo artigo**. O projeto **não** cita essa página; mas várias
  decisões coincidem com ela (Arial, V003 com limite de 18 pt, corpo ≥ 22 pt no percurso
  expressivo, contraste ≥ 4,5). A coincidência não indica derivação.

**MICROSOFT. Make your PowerPoint presentations accessible to people with disabilities. Microsoft
Support.** Disponível em: https://support.microsoft.com/en-us/office/make-your-powerpoint-presentations-accessible-to-people-with-disabilities-6f7772b2-2f33-4bd2-8ca7-dae3b2b3ef25. [V-web]
- Conceito: títulos em todos os slides, ordem de leitura, texto alternativo, contraste, cor não
  pode ser o único meio de informação.
- Relação: **contexto acrescentado pelo artigo**; usado na seção de lacunas (o renderer define
  `altText` como o ID da imagem, o que não atende à recomendação de texto alternativo descritivo).

**MICROSOFT. Basic tasks for creating a PowerPoint presentation. Microsoft Support.** Disponível em:
https://support.microsoft.com/en-us/office/basic-tasks-for-creating-a-powerpoint-presentation-efbbc1cd-c5f1-4264-b48e-c8a7b0334e36. [V-web]
- Conceito: sugere que fontes abaixo de 30 pt podem ser difíceis de ler e que detalhes podem ir para as
  notas do apresentador.
- Relação: contexto; evidencia que as próprias recomendações da Microsoft variam (18 pt × 30 pt), o
  que reforça tratar limiares tipográficos como heurísticas.

## 6. Geração automática de apresentações (trabalhos relacionados)

**FU, T.-J.; WANG, W. Y.; McDUFF, D.; SONG, Y. DOC2PPT: Automatic Presentation Slides Generation
from Scientific Documents. In: *Proceedings of the AAAI Conference on Artificial Intelligence*,
v. 36, n. 1, p. 634–642, 2022.** Disponível em: https://ojs.aaai.org/index.php/AAAI/article/view/19943. DOI: 10.1609/aaai.v36i1.19943. [V-proj][V-web]
- Relação: trabalho relacionado (documento → slides).

**GE, J. et al. AutoPresent: Designing Structured Visuals from Scratch. In: *Proceedings of the
IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)*, 2025.** Disponível em:
https://arxiv.org/abs/2501.00912. [V-proj]
- Conceito: SlidesBench; geração de **programas** python-pptx em vez de imagens; LLaMA 8B ajustado
  se aproxima do GPT-4o em um cenário.
- Relação: trabalho mais próximo; reforça a escolha de gerar programa editável.

**ZHENG, H. et al. PPTAgent: Generating and Evaluating Presentations Beyond Text-to-Slides.
arXiv:2501.03936, 2025.** Disponível em: https://arxiv.org/abs/2501.03936. [V-proj]
- Conceito: geração em duas etapas por edição de referências; PPTEval (conteúdo, design, coerência).
- Relação: critérios sugeridos para a avaliação humana pendente.

## 7. Ferramentas

- PptxGenJS: https://gitbrent.github.io/PptxGenJS/ (versão local 4.0.1, segundo `refs/FONTES.md`). **Implementado** em `renderer/render.mjs`.
- ECMA-376 / Open XML — `p:cxnSp`, `a:stCxn`, `a:endCxn`:
  https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.presentation.nonvisualconnectorshapedrawingproperties.startconnection?view=openxml-3.0.1. **Implementado** em `src/slidedsl/connections.py`.
- React Flow: https://reactflow.dev/ ; FastAPI: https://fastapi.tiangolo.com/ ; Pydantic: https://docs.pydantic.dev/ ; Playwright: https://playwright.dev/.

## Fontes que não puderam ser confirmadas ou usadas

- **Leitura integral** de Mayer e Fiorella (2014) e das notas de aula de Alley em PDF não foi feita
  pelo projeto (registrado em `refs/FONTES.md`); o artigo usa apenas o que foi registrado.
- A crítica às comparações de Alley citada na seção 5 foi encontrada como texto em Academia.edu sem
  dados bibliográficos completos; por isso o artigo a menciona apenas como ressalva, sem citá-la como
  referência formal.
- Não foi encontrada no repositório nenhuma referência às diretrizes de design da Microsoft;
  elas entram no artigo como contexto comparativo, e não como fonte do projeto.
