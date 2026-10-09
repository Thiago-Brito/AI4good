# Editor visual
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
