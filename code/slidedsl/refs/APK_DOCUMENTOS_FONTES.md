# Fontes da rodada APK 3 — consultadas em 23/11/2026

- Código local `src/slidedsl/documents.py`: extração, trechos de 900 caracteres,
  TF-IDF lexical, conferência literal e seções. Portado sem alterar o Python.
- [Expo DocumentPicker SDK 58](https://docs.expo.dev/versions/latest/sdk/document-picker/):
  seleção de MIME, URI e cópia para cache. API também conferida no pacote instalado.
- [Expo Modules API](https://docs.expo.dev/modules/module-api/): `OnNewIntent`,
  `AsyncFunction` e eventos; assinaturas conferidas no expo-modules-core instalado.
- [Módulos locais Expo](https://docs.expo.dev/modules/get-started/): autolinking em `modules/`.
- [PdfBox-Android](https://github.com/TomRoush/PdfBox-Android): porta Android,
  Apache-2.0, inicialização `PDFBoxResourceLoader` e `PDFTextStripper`. O README
  documenta JP2Android como opcional para imagens JPX, não incluído por padrão;
  extração textual usa regra R8 restrita a `com.gemalto.jp2.JP2Decoder` ausente.
- [Maven Central](https://central.sonatype.com/artifact/com.tom-roush/pdfbox-android):
  versão publicada 2.0.27.0. A versão estável é antiga; não se presume manutenção recente.
- [Android: receber dados](https://developer.android.com/training/sharing/receive):
  ACTION_SEND/EXTRA_STREAM e permissões temporárias de URI.
- [JSZip StreamHelper](https://stuk.github.io/jszip/documentation/api_streamhelper.html):
  leitura incremental limitada do XML descompactado, sem executar conteúdo do DOCX.

Decisão: módulo Expo local em Kotlin com PdfBox-Android 2.0.27.0, offline e por
página. PDF.js exigiria adaptar worker, streams e APIs web ao Hermes, sem vantagem
para esta extração. Não há OCR; PDF sem camada textual é recusado. Nenhum serviço
externo recebe os documentos. JSZip 3.10.1 já existia transitivamente e passa a ser
dependência direta porque agora o app o importa. `expo-modules-core` também é
declarado diretamente na versão do SDK por fornecer a ponte do módulo local.
