# Fontes consultadas em 2026-10-08
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
