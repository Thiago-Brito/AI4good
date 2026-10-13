# Fontes consultadas em 2026-10-08

## Investigação de conteúdo — 11/10/2026
- Código base fea5a52; evidências lidas: docs/EVOLUCAO_SEMANTICA.md, outputs/semantic/review_05/{arquitetura,ciencias,educacao,processos}/B/plan.json e C/semantic_review/attempt_*/{before_audit,candidate_audit,normalized_response,validation,decision}. Análise local de código e candidatos, sem alterar arquivos históricos.
- Decomposição é hipótese de engenharia: https://arxiv.org/abs/2205.10625 (Least-to-Most Prompting). Resultados do artigo não se transferem automaticamente ao Qwen3 4B nem à SlideDSL.
- Limites da autocorreção em modelos pequenos: https://arxiv.org/abs/2404.17140. Não oferece certificado de correção para nosso revisor.
- Rubrica de arquitetura: https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/microservices (responsabilidades, contratos, isolamento condicionado e custo operacional).
- Rubrica de frações: https://openstax.org/books/intermediate-algebra-2e/pages/1-3-fractions (numerador, denominador, partes iguais; não confundir medida matemática com justiça).
- Rubrica de ciências: https://www.usgs.gov/water-science-school/science/evaporation-and-water-cycle?page=1 (evaporação e fatores ambientais; não usar limiar universal inventado).
- Páginas consultadas via busca web nesta etapa; fontes usadas na inspeção, não fornecidas ao modelo nas condições livres.
- Fotossíntese: https://openstax.org/books/concepts-biology/pages/5-1-overview-of-photosynthesis e https://openstax.org/books/biology-2e/pages/8-1-overview-of-photosynthesis. Busca binária: https://xlinux.nist.gov/dads/HTML/binarySearch.html. Consulta nesta etapa; usadas na inspeção qualitativa dos pedidos reservados, sem fornecer suas páginas ao gerador.
- Densidade: https://openstax.org/books/university-physics-volume-1/pages/14-1-fluids-density-and-pressure (massa/volume e unidades). Pilhas e filas: https://xlinux.nist.gov/dads/HTML/stack.html e https://xlinux.nist.gov/dads/HTML/queue.html (LIFO/FIFO). Consultadas para a inspeção dos dois pedidos novos, sem alteração do código baseada nesses casos; não fornecidas ao gerador.

## Refinamento visual — consulta 11/10/2026
- Base confirmada antes de editar: f05fc8a4021b5169342c8498772956f5ccbe0d34, origin/dsl-visual. Diagnóstico sobre outputs/planning_visual/delivery_03 e suas cinco capturas: grade incompleta de três cards, rótulos e funções no mesmo tamanho, títulos repetidos na capa/conclusão, corpo mínimo 18 pt. Não se usa quantidade de formas como nota de qualidade.
- Microsoft Open XML, conexões ancoradas: https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.presentation.nonvisualconnectorshapedrawingproperties.startconnection?view=openxml-3.0.1 e https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.presentation.nonvisualconnectorshapedrawingproperties.endconnection?view=openxml-3.0.1 . a:stCxn/a:endCxn relacionam conectores aos IDs nativos e sítios das formas; o código local PptxGenJS 4.0.1 não expõe essa associação.
- LibreOffice, conversão PDF Impress: https://help.libreoffice.org/latest/en-GB/text/shared/guide/pdf_params.html . Investigação local de COM, executáveis e WSL; disponibilidade será registrada nas evidências, sem equiparar preview a renderização PPTX.
- Mayer/Fiorella e Alley/Penn State permanecem as fontes de coerência, proximidade e hierarquia da seção anterior. Pesos de equilíbrio, espaço livre, distribuição, dimensões e escolha de variantes são heurísticas de engenharia, sem validação estética ou de aprendizagem.

## Planejamento visual — consulta 11/10/2026
- Mayer/Fiorella, capítulo sobre coerência, sinalização e contiguidade espacial: https://www.cambridge.org/core/books/cambridge-handbook-of-multimedia-learning/principles-for-reducing-extraneous-processing-in-multimedia-learning-coherence-signaling-redundancy-spatial-contiguity-and-temporal-contiguity-principles/C98AB3A6CE760DD63C048936EA0B3B44 . Resumo consultado; não se afirma ter lido o capítulo pago integralmente.
- Michael Alley e equipe, Assertion–Evidence: https://www.assertion-evidence.org/tutorial.html e https://writing.engr.psu.edu/AE_Classroom_Teaching_Slides_Notes.pdf . Mensagem em título de frase, sustentada por evidência visual; o tutorial sinaliza migração para Craft of Scientific Communication.
- Confirmação primária acessível: https://writing.engr.psu.edu/assertion_evidence_EA.html e https://www.writing.engr.psu.edu/AE_checklist.pdf . Mensagens completas e evidência visual. O PDF das notas de aula acima retornou timeout na leitura direta; não se atribui leitura integral a ele.
- Diagnóstico próprio anterior às alterações: outputs/planning_visual/before_01/plan.json, report.json e initial/; Qwen3 4B, quatro title_content/uma comparison, zero diagnósticos, apenas slides/margens (2/2). Base e44961ed3fb53f513ff6485533cba2b5f57fb975 confirmada no remoto.
- Margens, paleta, tamanhos, grid, limites de nós e associação intenção/componente são heurísticas de engenharia. Essas fontes não validam a estética ou aprendizagem das apresentações geradas.

## Evolução visual/contextual — consulta em 11/10/2026
- PptxGenJS, imagens: https://gitbrent.github.io/PptxGenJS/docs/api-images.html . Na versão instalada 4.0.1 o código e os tipos confirmam `sizing: {type: 'contain', w, h}`; a função `imageSizingContain` não existe. Setas usam `ShapeType.downArrow`.
- Openverse, API, limites anônimos e metadados: https://api.openverse.org/v1/ . Busca paginada; respostas 429; sem scraping.
- MediaWiki, Imageinfo: https://www.mediawiki.org/wiki/API:Imageinfo . URLs, dimensões, MIME e extmetadata de arquivos Commons.
- NASA Image and Video Library, API v1.22: https://images.nasa.gov/docs/images.nasa.gov_api_docs.pdf . Busca e assets; distinto de serviços NASA que exigem chave.
- NASA, termos de imagens: https://www.nasa.gov/nasa-brand-center/images-and-media/ . Material de terceiros, marcas e pessoas requerem revisão; crédito não implica endosso. Seleção NASA exige revisão individual.
- pypdf, extração textual: https://github.com/py-pdf/pypdf/blob/main/docs/user/extract-text.md . OCR de páginas digitalizadas fica fora desta etapa.
- LibreOffice, execução: https://help.libreoffice.org/latest/en-GB/text/shared/guide/start_parameters.html . Conversão headless opcional.
- Evidências executadas: outputs/contextual/api_probe/ (Openverse/NASA reais; Commons HTTP 403), experiment_20261011_final/evaluation.json e audit.json (17 chamadas, 462 hashes conferidos), ui_generation.json e ui-tests-final/results.json. Fontes sintéticas: benchmark/reference_aurora.txt; instrumento humano ainda não aplicado em docs/AVALIACAO_HUMANA_CONTEXTUAL.md.
- Ambiente final: Python 3.12.10, Node 24.14.0, PptxGenJS 4.0.1, pypdf 6.20.0, Pillow 12.3.0, psutil 7.1.0; versões e fontes executadas preservadas nos snapshots. Regressão: outputs/tests/contextual-final.xml.

## Evolução SLM — consulta em 2026-10-10
- Ollama Structured Outputs: https://docs.ollama.com/capabilities/structured-outputs.
  A API local aceita JSON Schema em `format`; o schema deve também orientar o prompt.
  A validação local da resposta continua necessária. Não foi encontrada uma opção
  pública de `chat` para receber diretamente a gramática Lark da SlideDSL.
- Ollama chat: https://docs.ollama.com/api/chat. Campos `format`, `options`, `think`,
  `done` e `done_reason`; controles de thinking descobertos por `/api/show`.
- Evidência prévia: docs/RESULTADOS_INCREMENTAIS.md e outputs/evaluation_incremental/.
- Evidência inicial desta etapa: 123 testes Python passaram; serviço local respondeu
  versão 0.40.2 e possui qwen3:4b-instruct, digest
  0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0.
- Layouts, IDs automáticos e correções por caminhos são decisões locais de engenharia;
  seus efeitos serão medidos em um protocolo novo, separado do histórico A/B/C.
- Evidências finais da etapa: outputs/evolution/experiment_20261010/evaluation.json
  e audit.json/audit.csv (40 execuções, 122 respostas HTTP, 19 PPTX nativos; fontes
  executadas/hashes em sources_snapshot). Resultados interpretados em docs/EVOLUCAO_SLM.md.
- Verificações: outputs/tests/evolution-final.xml (141 Python), outputs/ui-tests/results.json
  (7 Playwright), outputs/evolution/ui_generation.json e production_editor_check.json.

Registro anterior à redação acadêmica. Documentação consultada pela ferramenta web;
smoke tests autenticados de Canva, Google e OpenAI ainda não executados.

- Contrato local: ../../academy/papers/dsl-visual-ia/SLIDEDSL_CODEX_DO_ZERO.md.
- PptxGenJS: https://gitbrent.github.io/PptxGenJS/docs/api-text/ (addText, unidades).
- Canva SDK: https://www.canva.dev/docs/apps/design-editing/ (openDesign, sessions).
- Canva CLI: https://www.canva.dev/docs/apps/canva-cli/making-rest-api-requests/.
- Canva REST criar: https://www.canva.dev/docs/apps/rest-apis/reference/designs/create-design/.
- Canva exportar: https://www.canva.dev/docs/apps/rest-apis/reference/exports/create-design-export-job/.
- Canva MCP: https://www.canva.dev/docs/apps/mcp/.
- Google: https://developers.google.com/workspace/slides/api/guides/overview.
- Google requests: https://developers.google.com/workspace/slides/api/reference/rest/v1/presentations/request.
- PowerPoint COM: https://learn.microsoft.com/en-us/office/vba/api/powerpoint.shape.
- Office.js: https://learn.microsoft.com/en-us/office/dev/add-ins/powerpoint/powerpoint-add-ins.
- WCAG: https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html.
- Ollama chat: https://docs.ollama.com/api/chat.
- OpenAI modelos: https://developers.openai.com/api/docs/models/gpt-4.1-mini e https://developers.openai.com/api/docs/models/gpt-4.1.
- OpenAI Chat Completions: https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create.
- Texpace: https://github.com/lsfcin/spacemantics; diretórios dsl/, checker/, bench/, tests/.

As heurísticas de papel, densidade e overflow são decisões locais da especificação;
não são uma escala validada de beleza. A análise limita-se às páginas efetivamente lidas.

## Consulta complementar — 2026-10-08
- https://reactflow.dev/api-reference/react-flow e https://reactflow.dev/examples/interaction/validation.
- https://fastapi.tiangolo.com/tutorial/static-files/.
- https://playwright.dev/docs/test-webserver e https://playwright.dev/docs/release-notes (Node 24 e versão 1.60).
- https://developers.google.com/workspace/slides/api/reference/rest/v1/presentations/create.
- https://learn.microsoft.com/en-us/office/vba/api/powerpoint.shaperange.group.
- https://learn.microsoft.com/en-us/office/vba/api/powerpoint.shaperange.align.
- https://learn.microsoft.com/en-us/office/vba/api/powerpoint.slide.delete.
- https://learn.microsoft.com/en-us/office/vba/api/powerpoint.shape.zorder.
- https://learn.microsoft.com/en-us/office/vba/api/powerpoint.presentation.saveas.
- https://www.canva.dev/docs/apps/exporting-designs/.

Evidência própria: outputs/tests/pytest.xml, outputs/ui-tests/results.json,
outputs/delivery.json, outputs/pptx_inspection.json e outputs/reports/benchmark.json.
Os arquivos são produzidos por testes/demo, não substituem experimento de modelos.

## Instalação e experimento local Ollama — 2026-10-08
- Windows, instalação por usuário e API localhost: https://docs.ollama.com/windows.
- Pacote oficial fixado para a execução: https://github.com/ollama/ollama/releases/tag/v0.40.1.
- Catálogo Qwen3: https://ollama.com/library/qwen3 (tags 0.6b e 4b).
- Contexto e parâmetros: https://docs.ollama.com/context-length e
  https://docs.ollama.com/modelfile (`num_ctx`, `num_predict`).
- Controle de thinking e descoberta por `/api/show`: https://docs.ollama.com/capabilities/thinking.
- Manifesto winget consultado: Ollama.Ollama 0.40.1; URL oficial OllamaSetup.exe e
  SHA256 5a157ce5a0697bd885186f0683f39c55deb4bf3eebd28ab90bab0ffeccb6132a.
- Evidência local de instalação/modelos e hardware em outputs/ollama/; os resultados
  do benchmark devem ser lidos no relatório da nova execução, preservando o anterior.

## Geração incremental e schema local — consulta 2026-10-08
- Tag oficial instrucional: https://ollama.com/library/qwen3:4b-instruct (digest observado localmente em model_show/report).
- Comparador instrucional: https://ollama.com/library/qwen2.5:3b-instruct.
- Schema passado em format, inclusão do schema na mensagem e validação da resposta:
  https://docs.ollama.com/capabilities/structured-outputs.
- Contrato chat: message.content, message.thinking, done, done_reason, eval_count,
  format e options: https://docs.ollama.com/api/chat.
- Evidências próprias: outputs/diagnostico_ollama/evidence.json (30 replays),
  outputs/demo_local/pilot_* (pilotos com falhas preservadas). Avaliação final
  só será descrita depois da execução completa.
- Evidências finais executadas: outputs/evaluation_incremental/evaluation.json,
  audit_analysis.json e ANALISE_AUDITADA.md (317 respostas reais, seis configurações);
  outputs/demo_local/windows_direct_final/audit.json e production_editor_check.json
  (cinco slides reais, zero diagnósticos, código direto e editor de produção).

## Confiabilidade — consulta 11/10/2026
- Contrato Ollama chat: JSON Schema, done/done_reason, prompt_eval_count e eval_count: https://docs.ollama.com/api/chat.
- Exportação real de slides pelo PowerPoint desktop: https://learn.microsoft.com/en-us/office/vba/api/powerpoint.presentation.export.
- Evidências próprias: outputs/reliability/experiment_20261011_final/configuration.json, evaluation.json, evaluation.csv, audit.json e sources_snapshot/; planos compartilhados, respostas HTTP, estados antes/depois e textos nativos de PPTX.
- Disponibilidade de renderização: outputs/reliability/rendering_availability.json. PowerPoint COM não registrado; capturas de navegador não são renderizações de PPTX pelo Office.
- Testes: outputs/tests/reliability-final.xml e outputs/ui-tests/results.json. Geração/correção/edição reais: outputs/reliability/ui_generation.json e ui_architecture.json.

## Planejamento semantico - 11/10/2026
- Fontes oficiais consultadas: https://docs.ollama.com/capabilities/structured-outputs e https://docs.ollama.com/api/chat. Contratos JSON restritos e validacao posterior; done_reason, tokens e parametros reais. Nao comprovam verdade factual.
- Evidencias locais anteriores: docs/EXPRESSIVIDADE_PLANEJAMENTO.md e outputs/expressiveness/comparison_06/; categorias abstratas, repeticoes e afirmacoes sem condicoes preservadas.
- Protocolo declarado antes das chamadas: benchmark/semantic_requests.json; resultados novos em outputs/semantic/, sem alterar os historicos.
- Inspeção de afirmações de arquitetura: https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/n-tier e https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/microservices. Separação lógica de responsabilidades não basta para garantir isolamento de falhas; implantação, contratos e operação precisam ser considerados. Essas páginas não foram fornecidas à SLM durante o experimento livre.
- Referência oficial do domínio ciências: https://www.usgs.gov/water-science-school/water-cycle. Não substitui avaliação independente dos textos gerados.

## Rastreabilidade e cobertura — consulta 11/10/2026
- Evidência primária de implementação: requirements.py, conceptual_planning.py,
  coverage.py, contextual.py, reliability.py e element_paths.json. Diagnóstico
  prévio em docs/INVESTIGACAO_COBERTURA.md; snapshot B com hashes em
  outputs/coverage/investigation_01/runtime/B. Contratos e retenção são decisões
  de engenharia; não constituem escala validada de qualidade semântica.
- Microsoft Azure Architecture Center, microservices (consultado):
  https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/microservices.
  Benefício de isolamento condicionado a tratamento de falhas nos consumidores;
  seção Challenges descreve complexidade distribuída. Fonte para inspeção, não fornecida ao modelo.
- USGS Water Science School (consultado):
  https://www.usgs.gov/water-science-school/water-cycle. Fluxos e mudanças de fase
  articulam o ciclo; uma lista de definições não demonstra essas relações.
- OpenStax, Chemistry 2e, Measurements (consultado):
  https://openstax.org/books/chemistry-2e/pages/1-4-measurements. Densidade como
  relação entre massa e volume; fonte para conferir cálculo e comparação.
- OpenStax, Prealgebra 2e, Visualize Fractions (consultado):
  https://openstax.org/books/prealgebra-2e/pages/4-1-visualize-fractions.
  Partes iguais do mesmo todo e interpretação de numerador/denominador.
- Python 3.12 Tutorial, Data Structures (consultado):
  https://docs.python.org/3.12/tutorial/datastructures.html.
  Pilhas LIFO e filas FIFO, exemplos operacionais append/pop/popleft.
- Resultados desta etapa serão registrados em novas pastas outputs/coverage/;
  dados históricos não são reescritos. Avaliação independente permanece pendente.

## SlideDSL Alto, pesquisa e GBNF — 12/10/2026
- llama.cpp, GBNF Guide (grammars/README.md):
  https://github.com/ggml-org/llama.cpp/blob/master/grammars/README.md.
  Sintaxe GBNF, repetições `{m,n}` e restrição de amostragem; recursão à esquerda não suportada.
- llama.cpp server README (tools/server): https://github.com/ggml-org/llama.cpp/tree/master/tools/server.
  Parâmetros `grammar` e `json_schema` nos endpoints de completion/chat.
- MediaWiki Action API, list=search e prop=extracts (TextExtracts):
  https://www.mediawiki.org/wiki/API:Search e https://www.mediawiki.org/wiki/Extension:TextExtracts.
- Brave Search API: https://api-dashboard.search.brave.com/app/documentation/web-search/get-started.
- Tavily Search API: https://docs.tavily.com/documentation/api-reference/endpoint/search.
- SearXNG Search API (format=json): https://docs.searxng.org/dev/search_api.html.
- Conteúdo do exemplo examples/alto/microsservicos.slda (para conferência humana):
  J. Lewis e M. Fowler, "Microservices" (2014), https://martinfowler.com/articles/microservices.html;
  Netflix Technology Blog, "Completing the Netflix Cloud Migration" (2016);
  Prime Video Tech, "Scaling up the Prime Video audio/video monitoring service and reducing
  costs by 90%" (2023); M. Conway, "How Do Committees Invent?" (1968).

## Fundamentação do TCC — 12/10/2026 (noite)
Lista comentada e o uso de cada obra no projeto em [docs/REFERENCIAS.md](../docs/REFERENCIAS.md).
- Stanford HAI, AI Index 2024 (custos de treino; via Fortune): https://dc.fortune.com/2024/04/18/google-gemini-cost-191-million-to-train-stanford-university-report-estimates
- Stanford HAI, AI Index 2025 in 10 charts: https://hai.stanford.edu/news/ai-index-2025-state-of-ai-in-10-charts
- Schwartz et al., Green AI: https://arxiv.org/abs/1907.10597
- Strubell et al., Energy and Policy Considerations (ACL 2019): https://aclanthology.org/P19-1355/
- Kapoor et al., Societal Impact of Open Foundation Models (ICML 2024): https://proceedings.mlr.press/v235/kapoor24a.html
- Lu et al., Small Language Models survey: https://arxiv.org/abs/2409.15790
- Qwen3 Technical Report: https://arxiv.org/abs/2505.09388
- Mernik, Heering, Sloane, When and How to Develop DSLs: https://ir.cwi.nl/pub/4109/
- Wang et al., Grammar Prompting (NeurIPS 2023): https://arxiv.org/abs/2305.19234
- Geng et al., Grammar-Constrained Decoding (EMNLP 2023): https://aclanthology.org/2023.emnlp-main.674
- Willard & Louf, Efficient Guided Generation: https://arxiv.org/abs/2307.09702
- Scholak et al., PICARD (EMNLP 2021): https://aclanthology.org/2021.emnlp-main.779
- Ollama, Structured outputs: https://ollama.com/blog/structured-outputs
- Lewis et al., RAG (NeurIPS 2020): https://arxiv.org/abs/2005.11401
- Ji et al., Survey of Hallucination: https://arxiv.org/abs/2202.03629
- SearXNG Search API: https://docs.searxng.org/dev/search_api.html
- SearXNG, configuração do servidor e `SEARXNG_SECRET`: https://docs.searxng.org/admin/settings/settings_server.html
- Fu et al., DOC2PPT (AAAI 2022): https://ojs.aaai.org/index.php/AAAI/article/view/19943
- Ge et al., AutoPresent: https://arxiv.org/abs/2501.00912
- Zheng et al., PPTAgent: https://arxiv.org/abs/2501.03936
