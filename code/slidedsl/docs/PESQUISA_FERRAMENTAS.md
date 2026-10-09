# Pesquisa de ferramentas — 2026-10-08
Fontes registradas antes da redação em [refs/FONTES.md](../refs/FONTES.md).
Consulte a matriz por operação em [MATRIZ_CAPACIDADES.csv](MATRIZ_CAPACIDADES.csv).
Cada célula informa capacidade, operação, URL, data e estado do teste.

PptxGenJS gera novos arquivos com `addSlide`, `addText`, `addShape`, `addImage` e
`writeFile`; posições são em polegadas e fontes em pontos. Executa offline em Node.
Edição lógica e camadas são resolvidas na IR antes da geração. Não se promete
importar um PPTX existente. Compilação local da demo e do catálogo de operações,
testes Node e inspeção dos XMLs confirmaram criação/exportação e objetos editáveis.
O arquivo [delivery.json](../outputs/delivery.json) registra a inspeção de cinco slides.
[Documentação oficial](https://gitbrent.github.io/PptxGenJS/docs/usage/).

PowerPoint COM oferece acesso a apresentações, slides, shapes e texto no aplicativo
Windows instalado. Office.js executa dentro do Office e depende do requisito da API;
Microsoft Graph trata arquivos DriveItem, não fornece neste levantamento um editor
universal de objetos PPTX. COM pode oferecer preview opcional, separado do compilador.
[COM](https://learn.microsoft.com/en-us/office/vba/api/powerpoint.presentation),
[Office.js](https://learn.microsoft.com/en-us/office/dev/add-ins/powerpoint/powerpoint-add-ins),
[Graph](https://learn.microsoft.com/en-us/graph/api/resources/driveitem).

Canva CLI usa `canva api`, login de conta e os contratos REST. Criar designs e
exportações está documentado. A consulta não confirmou manipulação irrestrita de
todos os objetos por REST. Apps SDK usa `openDesign` dentro de app, com sessão,
tipos suportados e sincronização. O MCP tem catálogo próprio, limites por ferramenta
e restrições de plano. Esses canais não são intercambiáveis; nenhum comando
`canva run add img` foi assumido. Não houve autenticação ou smoke test Canva.
[CLI](https://www.canva.dev/docs/apps/canva-cli/making-rest-api-requests/),
[SDK](https://www.canva.dev/docs/apps/design-editing/),
[MCP](https://www.canva.dev/docs/apps/mcp/tools/).

Google Slides usa OAuth e `presentations.create`/`batchUpdate`. Requests incluem
criação, exclusão, texto, transformações, agrupamento e Z. Imagens exigem uma URL
acessível pelo serviço, não um caminho Windows. Exportação PPTX usa Drive; quotas
e rede são requisitos externos. Não houve teste autenticado.
[Requests](https://developers.google.com/workspace/slides/api/reference/rest/v1/presentations/request),
[exportação](https://developers.google.com/workspace/drive/api/guides/ref-export-formats).

## Desenho dos adaptadores futuros
Contrato `render(PresentationIR, destination)` e relatório de capacidades. Google:
IDs globais derivados de slide+ID, unidades convertidas para PT, upload de assets,
requests em lote e export Drive. Canva: criar/importar design via REST, edição
elementar somente por canal comprovado, declarar perdas e capacidades indisponíveis.
Ambos devem receber IR validada, sem interpretar linguagem natural. Não implementados
como backends v1; decisão de escopo normativa, não bloqueio da geração offline.
