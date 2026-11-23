# Plano Codex — APK, rodada 3: slides a partir de um documento enviado ao app

Pedido do autor (23/11/2026): "o slide gerado a partir de um documento que vou mandar para o app".
Depende das rodadas 1 e 2 (núcleo TS, pipeline no app, `src/pipeline/sources.ts` com modo `paste`).

## Estado de partida

- A fonte "Colar texto" existe, mas só usa os primeiros 2600 caracteres
  (`sources.ts`, aviso "Extração limitada…").
- No PC, `src/slidedsl/documents.py` já resolve o problema para o pipeline Python: extração de PDF e
  DOCX, divisão em trechos (`chunks` com id, título de seção e número), recuperação por relevância
  (`retrieve`, TF-IDF simples), extração de fatos por trecho com o modelo e conferência literal
  (`verify_fact`), e seções do documento (`document_sections`). Fatos de documento citam
  `documento:<nome>` (A032 avisa slide sem fato documental).
- Correção de 23/11 em `src/llm/llamaRn.ts`: o adaptador passa `prompt` formatado + `response_format`
  (gramática estrita nativa), não `messages`. **Não reverter.**
- Contexto do modelo no celular: 4096 tokens por chamada.

## Regras

As mesmas das rodadas 1 e 2 (disco C: quase cheio, usar D: via `scripts/android_env.ps1`; não mudar o
Python; módulos puros testáveis em Node; relatório em `docs/APK_DOCUMENTOS_RELATORIO.md`; sem commit).
Dependências novas só se necessárias e com justificativa no relatório. Rodar `scripts/mobile_build.ps1`
apenas no fim; se houver outro `java`/Gradle ativo, esperar.

## Tarefas

### T1. Receber o documento
- Botão "Escolher documento" na fonte do conteúdo (novo modo `document`), com `expo-document-picker`
  (já instalado): PDF, DOCX, TXT e MD.
- **Compartilhar para o app:** o SlideDSL aparece em "Compartilhar" de outros apps (Arquivos, Drive,
  WhatsApp, e-mail) para esses tipos. Intent filters `ACTION_SEND`/`ACTION_VIEW` via config plugin do
  Expo (escrever um plugin local em `mobile/app/plugins/` se não houver um pronto e mantido). Ao
  receber, abrir a tela do pedido com o documento já selecionado e o nome visível.
- Limites claros (ex.: 10 MB, 200 mil caracteres extraídos) com mensagem em português.

### T2. Extrair texto no aparelho
- TXT/MD: decodificação UTF-8 (com fallback Latin-1).
- DOCX: ZIP + `word/document.xml` (JSZip já vem com o PptxGenJS), parágrafos e títulos (estilos
  Heading/Título) preservados para virar seções.
- PDF: avaliar e escolher, registrando a decisão: (a) módulo nativo Expo local em Kotlin com
  PdfBox-Android (extração de texto por página); (b) pdf.js rodando no Hermes; (c) outra opção mantida.
  PDF escaneado (sem texto) → mensagem "PDF sem texto selecionável".
- Testes Node com arquivos pequenos gerados nos próprios testes (TXT, MD, DOCX; PDF se a opção
  escolhida permitir teste fora do aparelho).

### T3. Documento longo dentro de 4096 tokens
Portar o método do `documents.py`, com o perfil celular:
1. dividir em trechos com título de seção e número;
2. pontuar os trechos pelo pedido (TF-IDF simples, como `retrieve`); se o pedido for vazio ou genérico
   ("resuma este documento"), cobrir o documento em ordem, distribuindo os trechos pelas seções;
3. extrair fatos trecho a trecho, cada chamada dentro do orçamento de contexto, com teto de chamadas
   (ex.: até 6 chamadas de extração) e conferência literal do trecho (`verify_fact`);
4. usar as seções do documento para sugerir o roteiro quando o pedido for "apresente este documento";
5. fatos citam `documento:<nome do arquivo>` (o rodapé já mostra o nome do arquivo).
- O pedido pode ficar vazio quando há documento: o app usa "Apresente os pontos principais do
  documento <nome>".
- Teste Node com modelo simulado: documento de ~30 mil caracteres gera deck válido sem estourar o
  contexto em nenhuma chamada; fatos inexistentes no texto são rejeitados.

### T4. Interface e dados
- Mostrar nome, tipo, nº de páginas/caracteres e quantos trechos/fatos foram usados.
- Progresso por etapa ("Lendo documento", "Extraindo fatos 2/6", "Planejando roteiro", "Slide 3/5").
- Dados de teste incluem tipo/tamanho do documento e as chamadas de extração (etapa
  `document_extract`, mesmo nome do Python).

### T5. Build e relatório
Typecheck, testes Node (app e núcleo), `scripts/mobile_build.ps1` gerando APK, relatório separando o
que foi testado em Node do que só o aparelho confirma.
