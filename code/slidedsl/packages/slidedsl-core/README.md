# @slidedsl/core

Núcleo TypeScript ESM do caminho Alto JSON → AST de layout → IR 1.1 → PPTX.
Sem I/O no código de produção. O chamador fornece fatos, dimensões/metadados
das imagens para compilar e data URIs para renderizar.

```ts
import { buildAlto, renderPptx } from '@slidedsl/core';

const result = buildAlto({
  title: 'Minha apresentação',
  theme: 'natural',
  slides: [{ kind: 'capa', title: 'Uma mensagem clara' }],
}, {}, {});

if (result.ir && !result.diagnostics.some(d => d.severity === 'ERRO')) {
  const pptx: ArrayBuffer = await renderPptx(result.ir, { images: {} });
  // O aplicativo decide como salvar/compartilhar o ArrayBuffer.
}
```

`facts` omitido/null preserva o comportamento do Python: não confere IDs do dossiê.
`{}` ativa essa conferência contra um dossiê vazio. `images` associa o caminho
relativo a `{width,height,metadata?}` ou `{missing:true}`. Na renderização,
`images` associa o mesmo caminho a `data:image/png;base64,...` ou JPEG.

Da raiz do projeto:

```powershell
.venv/Scripts/python.exe scripts/export_parity.py
.venv/Scripts/python.exe scripts/port_core.py
Set-Location packages/slidedsl-core
npm ci
npm test
npm run parity:full
```

No sandbox Windows desta execução foi necessário definir antes de rodar npm:
`$env:NODE_OPTIONS='--preserve-symlinks --preserve-symlinks-main'`, pois o
resolvedor de caminhos do Node tentou consultar diretórios ancestrais sem permissão.
Para instalar sem acesso ao cache global: `npm ci --cache ../../outputs/npm-cache`.

`src/port.ts` é código TypeScript gerado das funções puras atuais, com auxiliares
explícitos para a semântica numérica e de coleções do Python. Não há interpretador,
subprocesso, consulta às fixtures ou execução de Python no pacote. Modificações
nessa parte devem ser feitas em `scripts/port_core.py` e regeneradas. Os módulos
`alto.ts`, `semantic.ts`, `images.ts`, `textMetrics.ts`, `render.ts` e `index.ts`
contêm contratos e adaptações escritos para a nova execução.

As métricas incluem todos os pares de caracteres exportados e tabelas de raster
de 10–96 pt inteiros, suficientes para todos os tamanhos emitidos pelo Builder.
Fontes ausentes na máquina de exportação preservam o fallback registrado. Textos
com novos caracteres fora da tabela usam a largura de `?`; outros alfabetos,
shaping complexo e confirmação no Office precisam de nova medição.

O aplicativo React Native/Metro, llama.rn e um APK Android continuam sendo a
próxima rodada. PptxGenJS expõe um mapa `browser` para seus módulos de plataforma;
a resolução desse mapa e os polyfills do ambiente devem ser verificados no Metro.
O resultado comprovado desta rodada é a paridade de IR e PPTX sob Node 22.
