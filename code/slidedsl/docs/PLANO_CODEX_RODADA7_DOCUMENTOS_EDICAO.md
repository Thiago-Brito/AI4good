# Plano para o Codex — rodada 7: documentos do usuário, edição de slide, fotos e estilo automático

Data: 11/11/2026 · Planejador: Claude · Executor: Codex. Regras de `docs/PLANO_CODEX_COMPARACAO.md`
e princípio da rodada 4 (o modelo decide o QUE; o compilador decide COMO; PPTX editável; sem
commit/push/stash). pytest: `--basetemp outputs\_tmp_r7`. Teto de API da rodada: **US$ 0,60**.
Antes de escrever, registrar fontes em `refs/DOCUMENTOS_EDICAO_R7.md` (ex.: Lewis et al. 2020 RAG,
já em `docs/REFERENCIAS.md`; especificação OOXML/ECMA-376 para DOCX; documentação do Commons API
para `categories`/`extmetadata`).

## Contexto (o que existe)
- `src/slidedsl/documents.py`: upload TXT/MD/PDF ≤ 2 MiB, extração local, recuperação lexical.
  Usado só no fluxo antigo (`generation_jobs.py:197`, `editor/src/ContextPanel.tsx`).
- Fluxo Alto (principal): `alto_generation.py`, `alto_jobs.py`, `/api/criar`, `editor/src/CriarPanel.tsx`.
  Fatos F1..Fn vêm de `research.py` (`Dossier`, `Fact`, `verify_fact` com trecho literal);
  `slidedsl criar --dossie` reaproveita dossiê.
- Testes reais da r6: `outputs/testes_reais/20261111-0103/INDICE.md` (revisão do planejador no fim).

## Tarefa 1 — Documentos do usuário como base do deck (RAG local)
1. Aceitar **TXT, MD, PDF textual e DOCX**. DOCX sem dependência nova: `zipfile` +
   `xml.etree` lendo `word/document.xml` (parágrafos, títulos por estilo `Heading*`/`Título*`,
   tabelas como linhas de texto). Limites: 8 arquivos, 2 MiB cada (DOCX: 5 MiB), recusar
   macros (`.docm`) e arquivos cifrados; testes com DOCX sintético criado no teste.
2. Construir um **`Dossier` a partir dos documentos** (função nova, ex. `dossier_from_documents`):
   passagens recuperadas → extração de fatos com o mesmo schema e `verify_fact` (trecho literal
   obrigatório). Fonte do fato = `documento:<nome>#trecho-N` (sem caminho absoluto).
   Modo `documentos` (só documentos), `documentos+internet` (mescla; documento tem prioridade
   em conflito). Quando há documentos, a pesquisa na internet fica desligada por padrão.
3. Roteiro e slides do Alto recebem os fatos e devem **citar F#** nas afirmações; o prompt
   proíbe inventar dados do projeto que não estejam nos fatos (nomes, números, resultados).
   Checagem local: números no slide que não aparecem em nenhum fato → aviso (reparo existente).
4. CLI: `slidedsl criar "pedido" --documento a.pdf --documento b.docx [--fontes documentos|documentos+internet]`.
5. API/UI: `/api/criar` aceita ids de documentos; **CriarPanel** ganha área "Arquivos de base"
   (arrastar/selecionar, lista com remover, mensagem de privacidade: o conteúdo vai ao provedor
   escolhido somente nos trechos usados). Reutilizar o componente/rota de `ContextPanel` se possível.
6. Notas do apresentador: listar as fontes F# usadas com nome do documento.

## Tarefa 2 — Refazer um slide específico com instrução
1. Função `refazer_slide(deck_slda, numero, instrucao, fatos, modelo)` em módulo novo
   (ex. `alto_edit.py`): reaproveita o prompt de geração de UM slide com o roteiro, o slide atual,
   os vizinhos (para não repetir) e a instrução; pode mudar o tipo do slide se a instrução pedir
   ("vire uma comparação"). Valida com a gramática, `check_slide`, reparo existente (≤ 1).
   Os outros slides ficam **byte a byte iguais** no `.slda` (teste).
2. Ajustes sem modelo (custo zero): trocar estilo do deck; trocar/remover a foto de um slide
   (nova busca com consulta dada ou arquivo local); mover slide; excluir slide.
3. CLI: `slidedsl alto-refazer deck.slda --slide 3 --instrucao "..." --out ...` e
   `slidedsl alto-ajustar deck.slda --slide 3 --foto-buscar "..." | --sem-foto | --tema editorial`.
4. API + UI: no resultado do CriarPanel, cada miniatura ganha "Refazer este slide" (campo de
   instrução) e "Trocar foto"; histórico simples de versões (desfazer a última) persistido na
   pasta do job; uso/custo somado ao consumo exibido.

## Tarefa 3 — Fotos relevantes
Evidência: r6 reais — Git (pessoa no palco), horta (rua com motos), internet (estande de castelo).
1. Relevância usa título + descrição + **categorias** do Commons (`extmetadata`/`categories`),
   não só o nome do arquivo; exigir sobreposição com termos centrais do slide (em inglês e
   português; derive termos em inglês no próprio roteiro, sem chamada extra).
2. Veto a retratos/pessoas como assunto principal (categorias `People`, `Portraits`, nomes próprios
   no título, palavras como speaker/conference/stage) salvo pedido explícito.
3. Slide `imagem` sem foto aprovada: compilar como cartões/destaque tipográfico ocupando a área
   (não duas linhas esparsas). Teste offline com metadados sintéticos.

## Tarefa 4 — Estilo automático (opcional ao usuário)
`--tema auto` (padrão novo na UI: "Automático (sugerido)"): regra determinística e documentada
sobre o pedido/roteiro — público infantil/escolar → `vibrante`; tecnologia/programação → `escuro`;
natureza/meio ambiente/alimentação → `natural`; história/humanidades/leitura → `editorial`;
acadêmico/TCC/pesquisa → `claro`; caso contrário `claro`. Sem chamada de modelo. Mostrar o estilo
escolhido e permitir trocar (Tarefa 2.2). Testes de tabela.

## Tarefa 5 — Qualidade
pytest completo, ruff, Node, `npm run build` + lint + Playwright existentes do editor (adicionar
um teste de upload de arquivo e um de "refazer slide" com modelo simulado).

## Tarefa 6 — Testes reais (guardar para o usuário ver)
Chave em `.env`. Se houver HTTP 401, verificar apenas se existe variável de ambiente
`OPENAI_API_KEY` no processo (presença, nunca valor); se existir, removê-la do ambiente do
subprocesso para que o `.env` valha, e tentar uma vez. Persistindo, registrar e parar.
Modelo `gpt-5.4-mini`, imagens Commons, sem imagens por IA. Pasta
`outputs/testes_reais/<AAAAMMDD-HHMM>_r7/` e atualizar `outputs/testes_reais/ULTIMO.txt`:
1. **Deck sobre o próprio projeto a partir de documentos**: pedido "Apresentação do meu TCC
   SlideDSL para a banca", documentos `docs/artigo/ARTIGO_CIENTIFICO_SLIDEDSL.md` e `README.md`,
   fontes `documentos`, `--tema auto`, 8 slides.
2. O mesmo pedido com um **DOCX** gerado a partir do artigo (para provar o caminho DOCX).
3. **Refazer um slide** do deck 1 (ex.: "transforme em comparação entre SLM sozinho e SLM + gramática")
   e salvar antes/depois.
4. Re-rodar 3 decks da r6 que tiveram foto ruim (git, horta, internet) com o código novo.
Para cada um: PPTX, `.slda`, contato.png, fatos usados (F# → documento/trecho), uso/custo.
`INDICE.md` com tabela e observações honestas após abrir cada folha; `galeria.png`.
Verificar: nenhum número/nome do projeto no deck 1 sem fato correspondente.

## Registros
Atualizar `README.md` (seção curta: "Usar seus documentos" e "Refazer um slide"), `docs/PROGRESSO.md`,
`ROADMAP.md` (Rodada 7), `docs/CONTINUIDADE_API_VOZ_MOBILE.md`, `docs/REGRAS_DESIGN.md` (regra de estilo auto).

## Mensagem final esperada
Arquivos alterados; como usar (CLI e UI) documentos e refazer slide; testes com números;
tabela dos testes reais (válido, fatos de documento usados, fotos, chamadas, custo); gasto total;
caminhos do `INDICE.md`, `galeria.png` e do antes/depois do slide refeito; o que continua ruim.
