# Editor visual

O formulário principal apresenta pedido, modelo, estilo opcional e imagens
automáticas. Em C/D, a SLM escolhe mensagens e estruturas visuais antes do conteúdo.
Estratégias/validação e orçamento de reparo ficam recolhidos; provedores, pesquisa
manual, cache, anexos e recursos continuam nas configurações avançadas.
Veja [planejamento visual e capturas reais](EVOLUCAO_PLANEJAMENTO_VISUAL.md).

O painel opcional de contexto permite personalização, anexos TXT/MD/PDF e
imagens do catálogo/API. Corrigir pendências combina a IR editada com o reparo,
preservando alterações e mostrando conflitos. Seleção por slot troca a imagem
sem regenerar o deck. Fontes, licença e limitações aparecem no resultado.
Veja [uso, privacidade local e evidências](EVOLUCAO_VISUAL_CONTEXTUAL.md).

O painel **Gerar com IA local** consulta modelos Ollama instalados, recebe o pedido
em português e oferece as estratégias A/B/C/D. D planeja conteúdo sem coordenadas,
resolve IDs/layouts e permite até dois reparos por campos diagnosticados. O painel
acompanha o progresso por `/api/generations/{id}` e carrega a IR/fonte efetivamente
gerada. Validação estrita vem habilitada. Diagnósticos, edição e exportação usam
os controles existentes. [Contrato e resultados](EVOLUCAO_SLM.md).
React/Vite/TypeScript e @xyflow/react. Servidor FastAPI compartilha parser, IR,
checker e compilador da CLI. APIs: /api/parse, validate, export, compile, relation,
health e examples/{nome}. Build usa /editor-assets; imagens usam /assets.

Após build, `slidedsl serve` serve a API e o editor em http://127.0.0.1:8000.
Durante desenvolvimento, iniciar API e `npm run dev` em editor/; Vite usa proxy
local sem credenciais. React Flow mostra apresentação, slides, elementos, grupos
e relações; handles bloqueiam tipos incompatíveis e referências entre slides.
Conectar portas espaciais aplica o tipo escolhido no painel ao slide ativo.

Abrir arquivo .sld ou colar texto e Importar DSL. Selecione slide e objeto no
preview, lista ou grafo. Edite ID, texto, cor, X/Y, largura/altura, fonte, Z e papel.
Renomear ID atualiza referências e grupos. Relação escolhida no painel é aplicada
pela API com as mesmas equações geométricas. Validar destaca erros e mostra
diagnósticos. Exportar DSL salva o estado visual canônico e atualiza a área textual;
Gerar PPTX baixa o arquivo criado pelo backend validado. A área textual mantém a
última importação/exportação enquanto propriedades estão sendo editadas.

Teste: importar negativo_fora.sld, Validar (D001), mudar X de 1300 para 80, Validar,
Exportar DSL e compilar. Capturas antes/depois em outputs/. Playwright automatiza
esse percurso e o deck de cinco slides, com download real. Testes da API verificam
equivalência semântica após edição/exportação, tipos incompatíveis e assets locais.
Preview é geométrico HTML; não é renderização do PowerPoint nem métrica de glifos.

Não há colaboração, animação, edição de PPTX existente ou WYSIWYG completo.
Grupos não se tornam grupo nativo no PPTX: seus membros continuam editáveis.
