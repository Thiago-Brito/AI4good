# Referências comentadas para o TCC

Levantamento feito em 12/10/2026 para fundamentar as decisões do projeto. Para cada obra:
a referência (formato próximo da ABNT NBR 6023), o que ela diz e **em que parte do SlideDSL
ela se apoia**. Os links foram abertos e conferidos nessa data; os números citados vêm das
próprias páginas. Antes de usar no texto final, confira a versão publicada (anais/periódico)
e a paginação.

## 1. Custo da IA e democratização (motivação do TCC)

**MASLEJ, N. et al. *The AI Index 2024 Annual Report*. Stanford: Institute for Human-Centered
AI, Stanford University, 2024.** Disponível em: https://aiindex.stanford.edu/report/.
Estima o custo de computação para treinar o GPT-4 em cerca de US$ 78 milhões e o Gemini
Ultra em cerca de US$ 191 milhões, contra cerca de US$ 900 do Transformer original de 2017
(números conforme a cobertura da Fortune, 18 abr. 2024: https://dc.fortune.com/2024/04/18/google-gemini-cost-191-million-to-train-stanford-university-report-estimates).
→ **Uso:** mostra a concentração: só poucas empresas treinam modelos de fronteira; justifica
buscar alternativas que rodem com modelos pequenos e abertos.

**STANFORD HAI. *AI Index 2025: State of AI in 10 Charts*. 2025.** Disponível em:
https://hai.stanford.edu/news/ai-index-2025-state-of-ai-in-10-charts.
O custo de inferência de um modelo com desempenho de GPT-3.5 no MMLU caiu de US$ 20 para
US$ 0,07 por milhão de tokens entre nov./2022 e out./2024 (redução de mais de 280 vezes);
o Phi-3-mini, com 3,8 bilhões de parâmetros, passou de 60% no MMLU, patamar que em 2022
exigia o PaLM de 540 bilhões (redução de 142 vezes no tamanho).
→ **Uso:** evidência de que modelos pequenos ficaram capazes o bastante para tarefas
estruturadas — premissa central do uso de SLMs locais.

**SCHWARTZ, R.; DODGE, J.; SMITH, N. A.; ETZIONI, O. Green AI. *Communications of the ACM*,
v. 63, n. 12, p. 54–63, 2020.** Preprint: https://arxiv.org/abs/1907.10597.
Defende eficiência como critério de avaliação ao lado da acurácia e propõe reportar o
"preço" (custo financeiro) de desenvolver, treinar e executar modelos, para tornar a IA mais
verde e inclusiva, inclusive para pesquisadores de economias emergentes; cita aumento de
300.000× no cômputo de deep learning entre 2012 e 2018.
→ **Uso:** fundamenta medir custo (chamadas, tempo, tamanho do modelo) junto da qualidade;
argumento de inclusão para quem não tem acesso a APIs pagas.

**STRUBELL, E.; GANESH, A.; McCALLUM, A. Energy and Policy Considerations for Deep Learning
in NLP. In: *Proceedings of the 57th Annual Meeting of the ACL*. Florença: ACL, 2019.
p. 3645–3650.** Disponível em: https://aclanthology.org/P19-1355/.
Estima custos financeiros e ambientais de treinar grandes redes de PLN e propõe formas de
reduzi-los e tornar a pesquisa mais equitativa.
→ **Uso:** custo ambiental/financeiro como motivação para modelos menores.

**KAPOOR, S.; BOMMASANI, R. et al. Position: On the Societal Impact of Open Foundation
Models. In: *Proceedings of the 41st International Conference on Machine Learning (ICML)*.
PMLR, v. 235, p. 23082–23104, 2024.** Disponível em: https://proceedings.mlr.press/v235/kapoor24a.html.
Modelos com pesos abertos trazem benefícios de inovação, competição, distribuição do poder
de decisão e transparência (com ressalvas de risco).
→ **Uso:** argumento de democratização: pesos abertos (como o Qwen3) permitem rodar
localmente, auditar e não depender de um fornecedor.

## 2. Modelos de linguagem pequenos (SLMs)

**LU, Z. et al. Small Language Models: Survey, Measurements, and Insights. arXiv:2409.15790,
2024.** Disponível em: https://arxiv.org/abs/2409.15790.
Analisa 70 SLMs abertos de 100M a 5B parâmetros: qualidade dos dados pesa mais que a
arquitetura; de 2022 a 2024 os SLMs melhoraram mais rápido que a série LLaMA-7B; ainda há
lacunas em matemática e raciocínio complexo; quantização em 4 bits reduz bastante a latência.
→ **Uso:** justifica decompor a tarefa em passos curtos (o SLM é fraco em raciocínio longo)
e rodar quantizado (Q4_K_M) no Ollama.

**YANG, A. et al. Qwen3 Technical Report. arXiv:2505.09388, 2025.** Disponível em:
https://arxiv.org/abs/2505.09388.
Relatório técnico da família Qwen3, de pesos abertos.
→ **Uso:** referência do modelo usado nos experimentos (qwen3:4b-instruct via Ollama).

## 3. DSL e gramáticas

**MERNIK, M.; HEERING, J.; SLOANE, A. M. When and How to Develop Domain-Specific Languages.
*ACM Computing Surveys*, v. 37, n. 4, p. 316–344, 2005.** Disponível em: https://ir.cwi.nl/pub/4109/.
Padrões de decisão, análise, projeto e implementação de DSLs; DSLs trocam generalidade por
expressividade e possibilidades de análise no domínio.
→ **Uso:** fundamenta a SlideDSL e, sobretudo, a separação em dois níveis: a SlideDSL Alto
expressa a intenção do domínio (tópicos, comparação, números) e a 1.1, a geometria.

**WANG, B. et al. Grammar Prompting for Domain-Specific Language Generation with Large
Language Models. In: *Advances in Neural Information Processing Systems 36 (NeurIPS 2023)*.**
Disponível em: https://arxiv.org/abs/2305.19234.
Incluir uma gramática BNF especializada no prompt ajuda o modelo a gerar programas de DSL
com poucos exemplos; ainda há distância para o uso da gramática "oráculo".
→ **Uso:** apoia colocar a gramática da SlideDSL Alto no prompt (modos `direto`/`gramatica`).

## 4. Geração restrita por gramática (GLC no decodificador)

**GENG, S.; JOSIFOSKI, M.; PEYRARD, M.; WEST, R. Grammar-Constrained Decoding for Structured
NLP Tasks without Finetuning. In: *Proceedings of EMNLP 2023*. ACL, 2023.**
Disponível em: https://aclanthology.org/2023.emnlp-main.674 (preprint: https://arxiv.org/abs/2305.13971).
Gramáticas formais descrevem o espaço de saída de tarefas estruturadas; com decodificação
restrita, modelos sem ajuste fino superam modelos sem restrição e às vezes modelos ajustados.
→ **Uso:** principal base teórica da conversão GLC → GBNF e do modo `gramatica` (llama.cpp):
a saída é sintaticamente válida por construção, sem treinar o modelo.

**WILLARD, B. T.; LOUF, R. Efficient Guided Generation for Large Language Models.
arXiv:2307.09702, 2023.** Disponível em: https://arxiv.org/abs/2307.09702.
Formula a geração como transições de uma máquina de estados finitos e indexa o vocabulário
para guiar a geração por expressões regulares ou GLCs com pouco custo (biblioteca Outlines).
→ **Uso:** explica como JSON Schema/GBNF restringem tokens de forma eficiente — mecanismo
usado pelo Ollama (structured outputs) e pelo llama.cpp.

**SCHOLAK, T.; SCHUCHER, N.; BAHDANAU, D. PICARD: Parsing Incrementally for Constrained
Auto-Regressive Decoding from Language Models. In: *Proceedings of EMNLP 2021*. ACL, 2021.**
Disponível em: https://aclanthology.org/2021.emnlp-main.779.
Rejeita, durante a geração, tokens que levariam a um programa SQL inválido, usando um parser
incremental.
→ **Uso:** precedente de validar a saída do modelo com um parser durante/após a geração.

**OLLAMA. Structured outputs. 6 dez. 2024.** Disponível em: https://ollama.com/blog/structured-outputs.
O parâmetro `format` aceita um JSON Schema e restringe a saída do modelo a ele.
→ **Uso:** mecanismo do modo `json` (padrão). Observação do projeto: `maxLength` do schema
corta o texto no limite — por isso os limites ficaram folgados (ver MUDANCAS_2026-10-12.md).

## 5. Pesquisa e fundamentação do conteúdo

**LEWIS, P. et al. Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. In:
*Advances in Neural Information Processing Systems 33 (NeurIPS 2020)*.**
Disponível em: https://arxiv.org/abs/2005.11401.
Combina um gerador com recuperação de documentos para tarefas que exigem conhecimento,
melhorando factualidade e permitindo citar a origem.
→ **Uso:** base do passo de pesquisa: o SLM não precisa "lembrar" o assunto; recebe trechos
recuperados pelo SearXNG e escreve a partir deles.

**JI, Z. et al. Survey of Hallucination in Natural Language Generation. *ACM Computing
Surveys*, v. 55, n. 12, 2023.** Disponível em: https://arxiv.org/abs/2202.03629.
Define e classifica alucinações (conteúdo não sustentado pela fonte) e métodos de
mitigação e medição.
→ **Uso:** fundamenta as fichas com trecho literal verificado, o aviso A012 (número sem
fonte) e a verificação de sustentação (A014).

**SEARXNG. Search API. Documentação oficial.** Disponível em: https://docs.searxng.org/dev/search_api.html.
O SearXNG repassa a consulta a vários buscadores ("engines") e devolve os resultados; a API
aceita `GET /search?q=...&format=json`, e o formato JSON precisa estar habilitado em
`settings.yml` (senão responde 403).
→ **Uso:** buscador do projeto: roda localmente em Docker, sem chave nem custo, coerente com
o objetivo de reduzir dependência de serviços pagos.

## 6. Geração automática de slides (trabalhos relacionados)

**FU, T.-J.; WANG, W. Y.; McDUFF, D.; SONG, Y. DOC2PPT: Automatic Presentation Slides
Generation from Scientific Documents. In: *Proceedings of the AAAI Conference on Artificial
Intelligence*, v. 36, 2022.** Disponível em: https://ojs.aaai.org/index.php/AAAI/article/view/19943.
Gera slides a partir de artigos científicos (documento → slides).
→ **Uso:** trabalho relacionado anterior aos LLMs; difere do SlideDSL por partir de um
documento pronto, não de um pedido em linguagem natural com pesquisa.

**GE, J. et al. AutoPresent: Designing Structured Visuals from Scratch. In: *Proceedings of
CVPR 2025*.** Disponível em: https://arxiv.org/abs/2501.00912.
Cria o SlidesBench (cerca de 7 mil exemplos de treino e 585 de teste, 310 decks, 10 domínios);
os modelos geram **programas** Python (python-pptx) que produzem PPTX editável, o que supera a
geração de imagem; um LLaMA-3.1-8B ajustado com LoRA se aproxima do GPT-4o
(55,0 vs. 58,0 num dos cenários); todos ficam abaixo de slides feitos por pessoas.
→ **Uso:** o trabalho mais próximo. Confirma que gerar *programa* em vez de imagem é o
caminho para slides editáveis. Diferença do SlideDSL: em vez de Python genérico, uma DSL
própria com GLC (validável e restringível), modelo de 4B sem ajuste fino e pesquisa local.

**ZHENG, H. et al. PPTAgent: Generating and Evaluating Presentations Beyond Text-to-Slides.
arXiv:2501.03936, 2025.** Disponível em: https://arxiv.org/abs/2501.03936.
Abordagem em duas etapas baseada em edição de slides de referência e o PPTEval, que avalia
conteúdo, design e coerência.
→ **Uso:** inspira os critérios de avaliação (conteúdo, design, coerência) sugeridos para a
avaliação humana do TCC.

## 7. Ferramentas usadas (documentação técnica)

- Lark (parser LALR para a GLC): https://lark-parser.readthedocs.io/
- llama.cpp, gramáticas GBNF: https://github.com/ggml-org/llama.cpp/blob/master/grammars/README.md
- PptxGenJS (geração do PowerPoint): https://gitbrent.github.io/PptxGenJS/
- Ollama (execução local de modelos): https://ollama.com/

## Como as referências se encaixam no argumento do TCC

1. **Problema:** IA de ponta é cara e concentrada (AI Index 2024; Strubell 2019; Schwartz 2020).
2. **Oportunidade:** SLMs abertos ficaram bons e baratos de rodar (AI Index 2025; Lu 2024;
   Kapoor 2024), mas são fracos em raciocínio longo e alucinam (Lu 2024; Ji 2023).
3. **Proposta:** compensar as fraquezas do SLM com estrutura formal — DSL do domínio (Mernik
   2005), gramática no prompt (Wang 2023) e no decodificador (Geng 2023; Willard & Louf 2023;
   Scholak 2021) — e com recuperação de fontes (Lewis 2020) via buscador local (SearXNG).
4. **Comparação:** AutoPresent e PPTAgent mostram o estado da arte com modelos maiores ou
   ajustados; o SlideDSL testa até onde um SLM local sem ajuste fino chega com essas restrições.
