# SlideDSL no Android — rodada 2

Fonte versionada nesta pasta; dependências, Android gerado e APK ficam em
`D:\slidedsl-mobile`, nunca no C:/OneDrive. A partir da raiz do repositório:

```powershell
. ./scripts/android_env.ps1
.venv/Scripts/python.exe scripts/export_mobile_prompts.py --check
powershell.exe -NoProfile -File scripts/mobile_build.ps1
```

O script compila `@slidedsl/core`, roda typecheck e testes, faz prebuild e gera
`D:\slidedsl-mobile\SlideDSL-release.apk`. Antes de iniciar, aguarde terminar outro
build Java/Gradle. Não use `npm install` nesta pasta do repositório.
Para repetir somente as verificações, depois de sincronizar os fontes para D::

```powershell
. ./scripts/android_env.ps1
Set-Location D:/slidedsl-mobile/app
npm run typecheck
npm test
```

As dependências `expo-network` e `expo-battery` fornecem a política Wi-Fi e a
medição da bateria; versões são as do SDK 58 instalado. `llama.rn` está fixado
em 0.13.0-rc.12. `metro.config.js` observa o núcleo irmão e inclui seus JSONs;
PptxGenJS usa seu mapa browser para desativar dependências de Node no bundle.

No app: abra **Modelo**, selecione e baixe um GGUF; por padrão só Wi-Fi, GPU
desligada. O SHA-256 é calculado nativamente, em blocos de 64 KiB. Interrompa
com **Pausar** e continue em **Baixar / retomar**; o estado é persistido em
`documentDirectory`. Sair da tela, ir ao segundo plano ou perder a rede permitida
pausa o download. A retomada não é automática. **Apagar** remove modelo e parcial.

Em **Pedido**, digite ou dite em pt-BR, escolha 4–8 slides e a fonte. Sem pesquisa
é o padrão, com aviso explícito. Texto colado usa os primeiros 2600 caracteres;
Wikipedia pede um título de página exato em pt/en e conexão à internet. A extração
aceita até três fatos com trechos normalizados literalmente contidos na fonte.
Ela não prova que toda paráfrase do modelo está semanticamente sustentada.

O pipeline faz uma chamada de roteiro, uma por slide e até um reparo por slide.
Extração de texto colado/Wikipedia acrescenta uma chamada. Tetos: `1 + 2*N`
ou `2 + 2*N`. Documento acrescenta até seis: teto `7 + 2*N`.
Não há melhor de N nem verificação de sustentação por outro modelo. Não há busca
de imagens nesta rodada. O adaptador confere os tokens do prompt contra o
contexto 4096 e recusa prompts que não deixam 512 tokens para a resposta.
Prompts excessivos e slides que continuam inválidos produzem erro, sem PPTX.

O resultado mostra miniaturas geométricas em Views, avisos do compilador e botões
para salvar por SAF ou compartilhar. **Exportar dados do teste** também aparece
após falha/cancelamento: JSON `slidedsl.custo.v1` com chamadas, timings, total,
aparelho e bateria antes/depois. Campos não disponíveis ficam `null`; temperatura
não é exposta pelo Expo Battery. Cancelar uma inicialização aguarda a API nativa
retornar para liberar o contexto; durante completion chama `stopCompletion`.

Evidências e limites de validação estão em `docs/APK_APP_RELATORIO.md`, na raiz
do projeto. Os testes de adaptadores simulam apenas as fronteiras nativas e não
substituem JNI, Wi-Fi, voz, SAF, PowerPoint e medição em aparelho real.

Documentos (APK 0.3.0): em **Escolher documento**, selecione PDF, DOCX, TXT ou MD;
também é possível **Compartilhar → SlideDSL** ou abrir o arquivo com o app no
Android. O nome aparece no pedido; com pedido vazio, o app apresenta os pontos
principais. Limites: 10 MB e 200 mil caracteres extraídos. TXT/MD aceitam UTF-8
e fallback Latin-1; DOCX preserva parágrafos e títulos; PDF usa PdfBox-Android
2.0.27.0 no módulo Expo local `modules/slidedsl-documents`, sem OCR. PDF escaneado
produz “PDF sem texto selecionável”. O prebuild deve incluir esse módulo e
`plugins/withDocuments.js`; Expo Go não o contém.

Cada documento vira trechos de até 900 caracteres. Pedidos específicos usam
TF-IDF; pedidos gerais distribuem até seis trechos entre seções, em ordem. Há uma
extração por trecho selecionado, sem truncar o documento aos primeiros 2600
caracteres. A amostragem não garante cobrir todos os detalhes. Fatos inventados
ou com citações ausentes são rejeitados. Nome, tipo, tamanho, caracteres, páginas
(PDF), trechos e fatos ficam no resultado e nos dados do teste. Paginação de
TXT/MD/DOCX é indisponível, pois depende de layout. Receber outro documento
durante uma geração o seleciona quando a operação atual termina. O original
permanece com seu provedor; a cópia privada é apagada ao trocar de documento.

Resultados desta rodada e pendências do aparelho: `docs/APK_DOCUMENTOS_RELATORIO.md`.
