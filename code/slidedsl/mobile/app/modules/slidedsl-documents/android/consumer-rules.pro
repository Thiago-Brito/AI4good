# JP2Android é opcional no PdfBox-Android (README upstream). Não renderizamos
# imagens JPEG2000: PDFTextStripper extrai apenas texto. Regra exata do R8,
# sem suprimir avisos de outras classes ou introduzir o repositório JCenter.
-dontwarn com.gemalto.jp2.JP2Decoder
