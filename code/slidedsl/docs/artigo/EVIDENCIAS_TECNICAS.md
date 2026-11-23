# Evidências técnicas do artigo

Mapeamento das afirmações técnicas de [ARTIGO_CIENTIFICO_SLIDEDSL.md](ARTIGO_CIENTIFICO_SLIDEDSL.md)
para arquivos, funções, testes e relatórios do repositório. Caminhos relativos a `code/slidedsl/`.
Base: commit `168c29f` (ramo `slidedsl`), em 12/10/2026.

Os diretórios `outputs/` são **ignorados pelo Git** e só existem na máquina do autor. As evidências
experimentais (tabelas da seção 8) dependem deles; os documentos em `docs/` que as resumem estão
versionados.

Status: **[IC]** implementado e comprovado; **[INA]** implementado, não avaliado com modelo real;
**[EXP]** experimental/opcional; **[PLAN]** planejado.

---

## 1. Gramáticas e parser

| Afirmação | Evidência | Status |
|---|---|---|
| GLC da SlideDSL 1.1 com 18 alternativas de instrução | `src/slidedsl/grammar/slidedsl.lark` (regra `?instrucao`) | IC |
| GLC Alto com 11 tipos de slide, sem coordenadas | `src/slidedsl/grammar/slidedsl_alto.lark` (regra `?slide`) | IC |
| Parser Lark LALR com lexer contextual e posições | `parser.py::grammar_parser` (`parser="lalr"`, `propagate_positions=True`); confirmado em execução pelo Codex (`options.lexer == "contextual"`) para as duas gramáticas | IC |
| P001 com linha, coluna, contexto e terminais esperados | `parser.py::parse` (captura `UnexpectedInput`) | IC |
| P002 para valores inválidos | `parser.py::parse` (captura `ValueError`/`TypeError`) | IC |
| Parser para no primeiro erro | `docs/DIAGNOSTICO_OLLAMA.md` | IC |
| AST tipada com 14 operações, `extra="forbid"` | `ast_nodes.py` (`Command.op`, `TypedNode.model_config`) | IC |
| Testes da gramática e do parser | `tests/test_grammar.py`, `tests/test_extensions.py`, `tests/test_regressions.py` | IC |

## 2. Semântica, IR e geometria

| Afirmação | Evidência | Status |
|---|---|---|
| Semântica operacional por slide, em ordem textual | `semantic.py::analyze` (`execute`, `safe_execute`) | IC |
| Posições relativas (`abaixo de`, `a direita de`, canto) | `geometry.py::resolve_position`; `docs/SEMANTICA.md` | IC |
| Relações não reativas | `docs/SEMANTICA.md` | IC |
| Z normalizado 0..n−1 | `semantic.py::analyze.normalize` | IC |
| Códigos S001–S009 | `semantic.py::analyze` e `semantic.py::validate_ir` | IC |
| Fonte entre 10 e 96 pt (S005) | `semantic.py::analyze.execute` | IC |
| Inferência de papel por prefixo de ID, com origem | `semantic.py::infer_role`; campo `Element.role_origin` em `ir.py` | IC |
| Imagens só locais, PNG/JPEG, sem travessia | `docs/SEMANTICA.md`; `paths.py::asset_path` | IC |
| IR Pydantic, canvas fixo 1280×720 | `ir.py` (`Canvas.width: Literal[1280]`, `height: Literal[720]`) | IC |
| JSON Schema da IR idêntico ao do Pydantic | `src/slidedsl/schemas/ir.schema.json`; conferido pelo Codex (`SCHEMA_EQUAL True`) | IC |
| Igualdade canônica e *round-trip* IR→DSL→IR | `ir.py::semantic_snapshot`; `serializer.py`; `tests/test_ir_roundtrip.py` | IC |

## 3. Regras de design e validação visual

| Afirmação | Evidência | Status |
|---|---|---|
| D001–D010 com severidades e limiares | `design_rules.py::check_design`; `config/design_rules.yaml` | IC |
| Contraste pela fórmula WCAG, mínimo 4,5 | `design_rules.py::luminance`, `contrast`; `contrast_minimum: 4.5` | IC |
| Contraste INDETERMINADO como INFORMAÇÃO | `design_rules.py::known_background` e ramo `bg is None` | IC |
| Overflow por largura média 0,52 e altura de linha 1,2 | `design_rules.py::estimated_overflow` | IC |
| Modo estrito bloqueia D002, D008, D010 | `strict_codes` em `config/design_rules.yaml`; `diagnostics.py::failed`; `pipeline.py::ValidationResult.success` | IC |
| V001–V006 | `visual_validation.py`; descrição em `docs/EVOLUCAO_CONFIABILIDADE.md` e `docs/EVOLUCAO_VISUAL_CONTEXTUAL.md` | IC |
| Medição de texto com Arial local via Pillow, margem 4% | `text_metrics.py`; `docs/EXPRESSIVIDADE_PLANEJAMENTO.md` | IC |
| Testes de regras | `tests/test_design.py`, `tests/test_geometry.py` | IC |

## 4. Geração de PPTX

| Afirmação | Evidência | Status |
|---|---|---|
| Renderer Node/PptxGenJS, layout 1280/96 × 720/96 pol. | `renderer/render.mjs` (`pres.defineLayout({width:1280/96,height:720/96})`) | IC |
| Objetos nativos com `objectName` = ID | `renderer/render.mjs` (`addText`, `addShape`, `addImage`) | IC |
| Imagens com `sizing: contain` | `renderer/render.mjs` | IC |
| `altText` da imagem = ID do elemento | `renderer/render.mjs` (`altText:e.id`) | IC (limitação) |
| Renderer rejeita objeto fora do canvas | `renderer/render.mjs` (verificação inicial) | IC |
| Notas com texto do apresentador e créditos | `renderer/render.mjs` (`addNotes`) | IC |
| Conectores OOXML `p:cxnSp` com `a:stCxn`/`a:endCxn` | `connections.py`; `docs/REFINAMENTO_VISUAL.md` | IC (XML conferido; comportamento no Office não testado) |
| Orquestração Python → Node | `compiler.py` | IC |
| Testes de exportação | `renderer/render.test.mjs` (2); `tests/test_compile_pptx.py` | IC |
| Prévia PNG sem Office | `ir_preview.py` (Pillow); `alto_cli.py` (`previa`) | IC (aproximação) |
| Renderização Office/LibreOffice indisponível | `preview.py`; `outputs/*/rendering*/rendering.json` (`rendered=false`, `engine=geometric`) | — |

## 5. Modelos e geração estruturada

| Afirmação | Evidência | Status |
|---|---|---|
| Adaptadores Ollama, llama.cpp, OpenAI e mock | `src/slidedsl/models/*.py`; `models/factory.py` | IC (OpenAI não executado) |
| JSON Schema enviado no campo `format` do Ollama | `models/ollama_model.py` (`payload["format"] = response_schema`) | IC |
| Descoberta de `think` por `/api/show` | `models/ollama_model.py` (`thinking_controls`) | IC |
| Registro de `done_reason`, tokens e tamanho do *thinking* | `models/ollama_model.py` (metadados por chamada) | IC |
| GBNF enviada como `grammar` ao llama-server | `models/llamacpp_model.py` (`payload["grammar"]`, `grammar_constrained`) | **INA** |
| Conversão Lark EBNF → GBNF sem recursão à esquerda | `gbnf.py::lark_to_gbnf`, `alto_gbnf`, `low_level_gbnf` | INA |
| Reconhecedor GBNF próprio para testes | `gbnf.py::GBNFMatcher`; `tests/test_alto.py` | IC (como teste da conversão) |
| Nenhuma execução real com `grammar_constrained=true` | busca em `outputs/` por `"grammar_constrained": true` sem resultados | — |
| GLC e exemplos no prompt do modo direto | `prompts/system_dsl.txt` | IC |
| Configuração de modelos do benchmark histórico | `config/models.yaml` (T=0, seed 42) | IC |

## 6. Fluxo SlideDSL Alto

| Afirmação | Evidência | Status |
|---|---|---|
| Parser, AST, impressão e validação A0xx | `alto.py` | IC |
| Limites por tipo (`LIMITS`) e por campo (`TEXT_LIMITS`) | `alto.py` (constantes no início do módulo) | IC |
| A001–A009, A012, A015 | `alto.py` (função de validação) | IC |
| A010 (não cabe no layout) | `alto_layout.py::Builder.fit` e `alto_generation.py::check_slide` | IC |
| A011 (imagem não resolvida) | `alto_layout.py` | IC |
| A013 (campo truncado no limite do schema) | `alto_generation.py::check_slide`; `alto_quality.py::truncated_paths` | IC no código; **INA** em experimento |
| A014 (sustentação pelo SLM) | `alto_quality.py::check_support`, `support_diagnostics`, `apply_corrections` | IC no código; **INA** em experimento |
| A016 (tópico ausente) | `alto_quality.py::extract_topics`, `coverage_diagnostics` | IC no código; **INA** em experimento |
| Roteiro com enum de IDs de fatos e tipos de dados condicionais | `alto_generation.py::outline_schema`, `data_kind_supported`, `fix_outline` | IC |
| Prompt do roteiro mostra o texto de no máximo 8 fatos (trechos ≤ 300 caracteres) | `alto_generation.py::facts_block` (`chosen[:8]`), chamado com `all_facts=True` no roteiro | IC (limitação) |
| Altura de texto no layout Alto = máximo entre estimativa D010 e medição Pillow | `alto_layout.py::needed_height` → `text_metrics.py::text_height` | IC |
| Aceitação conservadora e rollback (não usados no fluxo Alto) | `reliability.py::accept_candidate`; `semantic_planning.py::review_plan`; `refinement.py::refine_slides` | IC |
| Schema por tipo de slide | `alto_generation.py::slide_schema`, `json_to_slide` | IC |
| Melhor de N e pesos | `alto_generation.py::score_slide` (`weights = {"A007": 15, "A012": 8, "A008": 5, "A009": 4, "A011": 3}`; −100 por erro; −2 demais avisos) | IC |
| Temperatura dos candidatos: base e base+0,5 (≤1,0) | `alto_generation.py::generate_alto` (`temp = temperature if c == 0 else min(1.0, temperature + 0.5)`) | IC |
| Remoção de IDs de fatos do texto visível | `alto_generation.py::strip_fact_ids`, `clean_visible` | IC |
| Erro quando não há fatos (sem `--sem-fatos`) | `alto_generation.py::NoFactsError`; casos `*_curto` etc. em `outputs/testes_multitemas_20261012/` | IC |
| Layout por tipo, fonte uniforme por papel | `alto_layout.py` (`fit`, `uniform`; sequências [42, 38, 34, 32], [24, 22, 20, 18, 16]) | IC |
| Variação de capa por `crc32(título) % 3` | `alto_layout.py` (`zlib.crc32(...) % 3`) | IC |
| Margens e limite de conteúdo | `alto_layout.py` (`W, H, M = 1280, 720, 64`; `CONTENT_BOTTOM = 636`) | IC |
| Cadeia Alto → 1.1 → validação → PPTX | `alto_compile.py` | IC |
| Comandos CLI `criar`, `pesquisar`, `alto-compile`, `previa`, `gbnf` | `alto_cli.py` | IC |
| API `POST /api/criar`, `GET /api/criar/{id}`, `POST /api/alto/parse`, `GET /api/searxng/status` | `server.py`, `alto_jobs.py` | IC |
| Testes do fluxo Alto (modelos simulados, HTTP falso) | `tests/test_alto.py` (36 funções de teste) | IC |
| Exemplos Alto compilam sem avisos no modo estrito | `examples/alto/*.slda`; `docs/MUDANCAS_2026-10-12.md` | IC |

## 7. Pesquisa e verificação de fatos

| Afirmação | Evidência | Status |
|---|---|---|
| SearXNG local como buscador padrão | `research.py`; `searxng/docker-compose.yml`, `settings.yml`; `scripts/iniciar_searxng.cmd` | IC |
| Wikipedia, Tavily e Brave apenas para comparação | `research.py`; `docs/SLIDEDSL_ALTO.md` | INA |
| Regras de aceitação de fichas | `research.py::verify_fact` | IC |
| Trecho literal ≥ 85% contíguo | `research.py::quote_found` | IC |
| Extração heurística sem modelo (modo offline) | `research.py::heuristic_facts` | IC |
| Download seguro (HTTPS, IP fixado, limites) | `media.py::fetch_public` | IC |
| Cache de pesquisa | `outputs/research/cache/` | IC |

## 8. Planejamento (gerações G3–G6)

| Afirmação | Evidência | Status |
|---|---|---|
| Plano sem coordenadas e IDs posicionais | `planning.py`; `layouts.py`; `docs/EVOLUCAO_SLM.md` | IC |
| Estratégias A/B/C/D e harness | `evolution.py`; `evolution_experiment.py` | IC |
| Requisitos tipados congelados antes da chamada | `requirements.py`; `reliability.py`; `docs/EVOLUCAO_CONFIABILIDADE.md` | IC |
| Reparo determinístico, aceitação conservadora e rollback | `reliability.py` | IC |
| Patches `edits: [{path, value}]` restritos aos caminhos diagnosticados | `evolution.py`; `edits.py` | IC |
| Planejamento visual em duas chamadas | `visual_planning.py`; `composition.py`; `contextual.py` | IC |
| Refinamento visual com conservação | `refinement.py` | IC |
| Planejamento expressivo | `expressive_composition.py` | EXP |
| Planejamento semântico (papéis, relações, K/Q) | `semantic_planning.py` | EXP |
| Planejamento conceitual | `conceptual_planning.py` | EXP |
| Cobertura e projeção literal | `coverage.py` | EXP |
| Documentos locais e recuperação lexical | `documents.py` | IC/EXP |
| Imagens Openverse/Commons/NASA | `media.py` | IC (Commons respondeu 403) |
| Mesclagem de três estados após edição manual | `edits.py`; `generation_jobs.py` | IC |

## 9. Editor visual

| Afirmação | Evidência | Status |
|---|---|---|
| React + Vite + TypeScript + @xyflow/react | `editor/package.json`; `editor/src/graph.tsx` | IC |
| Painel Criar com pesquisa | `editor/src/CriarPanel.tsx` | IC |
| Painéis de geração e contexto | `editor/src/GenerationPanel.tsx`, `ContextPanel.tsx` | IC |
| Prévia geométrica | `editor/src/Preview.tsx` | IC (aproximação) |
| API compartilhada com a CLI | `src/slidedsl/server.py`; `api/main.py` | IC |
| Ciclo D001 → corrigir X → revalidar → exportar | `editor/tests/editor.spec.ts`; `examples/negativo_fora.sld` (X = 1300) | IC |
| 16 testes Playwright em 7 arquivos | `editor/tests/*.spec.ts` | IC (5 com modelo real são optativos) |
| Proteção de origem e limite de corpo nos POSTs | `docs/EVOLUCAO_VISUAL_CONTEXTUAL.md`; `server.py` | IC |

## 10. Experimentos (seção 8)

| ID | Documento | Dados brutos (locais) |
|---|---|---|
| E1 | `docs/RESULTADOS_OLLAMA.md`, `docs/DIAGNOSTICO_OLLAMA.md` | `outputs/reports_ollama_20261008/` (`benchmark.json`, `benchmark.csv`, `ANALISE.md`); `outputs/diagnostico_ollama/` |
| E2 | `docs/RESULTADOS_INCREMENTAIS.md`, `docs/SLM_LOCAL_FUNCIONAL.md` | `outputs/evaluation_incremental/` (`evaluation.json`, `audit_analysis.json`, `ANALISE_AUDITADA.md`) |
| E3 | `docs/EVOLUCAO_SLM.md` | `outputs/evolution/experiment_20261010/` |
| E4 | `docs/EVOLUCAO_CONFIABILIDADE.md` | `outputs/reliability/experiment_20261011_final/` |
| E5 | `docs/EVOLUCAO_VISUAL_CONTEXTUAL.md` | `outputs/contextual/experiment_20261011_final/` |
| E6 | `docs/EVOLUCAO_PLANEJAMENTO_VISUAL.md` | `outputs/planning_visual/` |
| E7 | `docs/REFINAMENTO_VISUAL.md` | `outputs/refinement/` |
| E8 | `docs/EXPRESSIVIDADE_PLANEJAMENTO.md` | `outputs/expressiveness/` |
| E9 | `docs/EVOLUCAO_SEMANTICA.md` | `outputs/semantic/review_05/`, `outputs/semantic/audit_05/` |
| E10 | `docs/EVOLUCAO_CONTEUDO.md`, `docs/INVESTIGACAO_CONTEUDO.md` | `outputs/conceptual/audit_12/`, `final_08/`, `final_11/` |
| E11 | `docs/MUDANCAS_2026-10-12.md`, `README.md` §6 | `outputs/testes_multitemas_20261012/` (`RELATORIO.md`, `REVISAO.md`, `resumo.csv`, `comparacao.json`, `configuracao.json`) |

## 11. Testes automatizados

| Afirmação | Evidência |
|---|---|
| 388 testes Python, 2 Node e 11 Playwright passaram (revisão de 12/10) | `docs/MUDANCAS_2026-10-12.md`, seção "Verificação" |
| 253 funções de teste Python em 25 arquivos; 388 casos coletados | contagem de `def test_` em `tests/test_*.py`; `pytest --collect-only -q -s -p no:cacheprovider` → "388 tests collected" (executado pelo Codex) |
| Registro da revisão para commit | `outputs/commit_review_20261012/validacao_commit.json` (388 Python, 2 Node, 11 Playwright, 5 Playwright reais optativos ignorados) |
| Reexecução para o artigo (12/10/2026) | `.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider --basetemp=<scratchpad>` → 382 passaram, 6 falharam por caminho > 260 caracteres; os 2 testes de `test_alto.py`/`test_benchmark_mock.py` que falharam, mais todo `test_contextual.py` (onde estavam os outros 4), repetidos com `--basetemp=outputs/tests/tmp-artigo` → 51 passaram, 0 falharam. Total: 388/388 |
| Histórico de crescimento da suíte | `docs/RESULTADOS_OLLAMA.md` (108), `docs/RESULTADOS.md` (123), `docs/EVOLUCAO_SLM.md` (141), `docs/EVOLUCAO_CONFIABILIDADE.md` (160), `docs/EVOLUCAO_VISUAL_CONTEXTUAL.md` (209), `docs/EVOLUCAO_PLANEJAMENTO_VISUAL.md` (224), `docs/REFINAMENTO_VISUAL.md` (241), `docs/EXPRESSIVIDADE_PLANEJAMENTO.md` (271), `docs/EVOLUCAO_SEMANTICA.md` (311), `docs/EVOLUCAO_CONTEUDO.md` (325), `docs/MUDANCAS_2026-10-12.md` (348 → 387/388) |
| Relatórios JUnit locais | `outputs/tests/*.xml` |

## 12. Divergências entre documentação e implementação

| Documento | Afirmação | O que o código ou os dados mostram |
|---|---|---|
| `docs/SLIDEDSL_ALTO.md` (tabela de diagnósticos) | Lista A001–A011, com A007 como "número que não aparece nos fatos citados" | O código também emite A012, A013, A014, A015 e A016. Em `alto.py`, A007 cobre os campos `valor` e `barra` de slides de dados cujo número não aparece nos fatos citados; A012 cobre números em títulos, itens, marcos, rótulos e notas. A tabela do documento está desatualizada em relação ao código (a seção posterior do mesmo documento menciona A012–A016). |
| `docs/SLIDEDSL_ALTO.md` (best-of-N) | "−15 por A007, −5 por A008, −4 por A009" | `score_slide` também penaliza A012 (−8), A011 (−3) e demais avisos (−2) |
| `README.md` §3.5 e §3.7 | "geração restrita pela gramática"; "o modelo não consegue gerar sintaxe inválida" | Verdadeiro para o modo `gramatica` por construção, mas esse modo **nunca foi executado com modelo real**; todos os experimentos usaram JSON Schema |
| `README.md` §1 (tabela) | "Inventa sintaxe e estrutura → DSL + GLC; geração restrita pela gramática" | A compensação efetivamente medida foi JSON Schema + validação pela GLC |
| `README.md` §7 | "cada deck faz de 25 a 50 chamadas" | No E11 (código anterior às correções de qualidade), 17 a 32 chamadas por deck; a estimativa do README inclui verificação e cobertura, não medidas |
| `README.md` §3.8 | "As cores têm contraste ≥ 4,5 nos temas claro e escuro" | Garantido pela paleta onde D002 consegue medir; nos 12 decks do E11 o contraste ficou majoritariamente INDETERMINADO (D002 informativo) |
| `docs/SLIDEDSL_ALTO.md` §Limites | "Não executei SLM real nesta etapa" | Escrito antes do E11; depois, o fluxo foi executado com Qwen3 4B pelo autor (12 casos) |
| `config/models.yaml` | lista `qwen3:4b` e modelos OpenAI | Os experimentos a partir de 10/10 usam `qwen3:4b-instruct`, informado pela CLI; OpenAI nunca foi executado |
| `docs/EXPERIMENTO.md` | Contexto 8192 e saída 4096 no E2; contexto 16384 e saída 8192 no E1 | Coerente com os relatórios; o E11 usou saída de 2048 tokens (`configuracao.json`) |
| `README.md` §3.6 | "Os erros voltam ao modelo apontando o campo exato… em até 2 correções" | O feedback aponta o campo, mas o reparo Alto regenera o slide inteiro (`alto_generation.py::generate_alto.produce`); não há a garantia de patch por caminho de `evolution.py::apply_patch_response` |
| `README.md` §3.3 | "o `trecho` existir literalmente na página (≥ 85% contíguo)" | Correto, mas após normalização (`research.py::quote_found`); não é cópia exata em todos os casos |
| `README.md` §3.3 | "a afirmação for uma frase completa" | `verify_fact` exige ≥ 6 palavras e ausência de reticências/"�"; não há análise gramatical de completude |
| `prompts/system_dsl.txt` | Cópia da GLC usada no prompt de geração integral | Anterior às extensões `seta`, `notas`, `negrito`, `arredondado`, `alinhado` da gramática real |
| `docs/SLIDEDSL_ALTO.md` §Próximos passos e `ROADMAP.md` | Botão "Criar com pesquisa" no editor como pendência | Já implementado: `editor/src/CriarPanel.tsx`, `alto_jobs.py`, `POST /api/criar` |
| Documentos de 10/10 e 11/10 (antes do refinamento) | "sem conectores ancorados" | `connections.py` implementa conectores ancorados para cadeias verticais desde o refinamento (11/10) |
| `docs/EDITOR.md` e README | "Validar destaca erros" | Correto; não há validação automática a cada edição (`editor/src/App.tsx::edit` limpa diagnósticos e marca "Alterações pendentes de validação") |
| `docs/EVOLUCAO_SLM.md` | 13 erros geométricos em A | `evaluation.json` original registra 2; `audit.json` registra 13 nos 43/50 slides alcançados (agregação original corrigida pela auditoria) |
| `docs/EVOLUCAO_CONTEUDO.md` | Conceitual 6/6 PPTX | Consolidado de `final_08` (4 pares) + `final_11` (2 pares UTF-8); `final_08` isolado teve 5/6 |
| `docs/EVOLUCAO_VISUAL_CONTEXTUAL.md` | 38 PPTX auditados | Inclui cópias auxiliares; 16 exportações das condições estruturais, 19 com imagem e fontes |
| `pipeline.py` × textos que citam "D e V" | Validação inclui V001–V006 | `validate_source` executa só semântica e D001–D010; V é acrescentado nos fluxos de planejamento e em `server.report_ir` |
| README §3.6 (A013, A014, A016 no fluxo de validação) | Diagnósticos de qualidade do Alto | Gerados só durante a geração; a validação final (`alto_compile.py::build_alto`) reaplica `validate_alto` e a validação 1.1, e esses códigos não bloqueiam a exportação |
| README §3.8 "o texto nunca é cortado" | — | Exceção: rodapé "Fonte: …" truncado em 100 caracteres com "…" quando não cabe (`alto_layout.py`, rodapé) |
| Sustentação A014 | "compara cada frase com número ou nome" | No máximo 8 unidades por slide (`alto_quality.py::factual_units`, `[:8]`) |
| Layout `topicos` | "até 3 → cards" | Cards só em slides de número par; nos ímpares, lista (`alto_layout.py::layout_topicos`, `b.number % 2 == 0`) |
| D006 | — | Severidade AVISO, fora de `strict_codes`: não bloqueia exportação |
| `/api/compile` | — | Aplica validação básica; não recebe parâmetro de modo estrito (`server.py::compile_document`) |

## 13. Funcionalidades implementadas, mas não avaliadas experimentalmente

- Modo `gramatica` (GBNF/llama.cpp) e modo `direto` no fluxo Alto.
- Verificação de sustentação (A014), detecção de truncamento (A013), citação literal (A015) e
  cobertura de tópicos (A016) com modelo real — implementados após o lote E11.
- Termos centrais e filtro de relevância na pesquisa — idem.
- Buscadores Wikipedia, Tavily e Brave (exceto o 403 da Wikipedia no primeiro teste).
- Adaptador OpenAI.
- Conectores OOXML ancorados no PowerPoint real.
- `render-preview` via PowerPoint COM e `render-optional` via LibreOffice (indisponíveis na máquina).
- Opção de tema escuro em experimentos (todos os experimentos usaram tema claro).
- Rastreabilidade e recuperação de cobertura (`coverage.py`, C001–C005): protocolo `coverage-abc-v1`
  iniciado, apenas seed 42 em dois domínios, sem relatório consolidado (`outputs/coverage/abc_02/`).
- Adaptadores Canva e Google Slides: pesquisados (`docs/PESQUISA_FERRAMENTAS.md`), **não
  implementados** [PLAN].
