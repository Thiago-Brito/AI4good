# Fontes e decisões — rodada 7

Consultadas em 11/11/2026, antes da implementação e dos registros desta rodada.

- Lewis et al. (2020), Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks: https://arxiv.org/abs/2005.11401. Fundamenta recuperação com proveniência; aqui a recuperação é lexical local, sem embeddings ou treinamento RAG.
- ECMA-376, Office Open XML: https://ecma-international.org/publications-and-standards/standards/ecma-376/. DOCX é pacote ZIP; somente word/document.xml é interpretado, sem executar conteúdo.
- Microsoft, estrutura WordprocessingML: https://learn.microsoft.com/en-us/office/open-xml/word/structure-of-a-wordprocessingml-document. Parágrafos p, runs r, texto t e tabelas são extraídos na ordem do corpo.
- MediaWiki Categories: https://www.mediawiki.org/wiki/API:Categories. Categorias são metadados de página; não representam classificação visual comprovada.
- CommonsMetadata: https://www.mediawiki.org/wiki/Extension:CommonsMetadata. extmetadata complementa título/descrição/licença; categorias e descrição entram no filtro lexical conservador.

Contrato: arquivos locais limitados, até oito documentos; apenas passagens recuperadas são enviadas ao modelo escolhido. Fatos de documentos exigem citação normalizada literalmente contida no trecho e passam por verify_fact. Internet é opt-in quando há documentos. Na mescla, fatos de documentos precedem e suprimem suplementos web lexicalmente conflitantes. Isso não constitui verificação semântica completa.

Edição usa posições do parser LALR para substituir somente um bloco. Histórico conserva fontes e artefatos em pastas novas; desfazer não devolve créditos consumidos. Estilo auto é uma regra local ordenada, documentada em docs/REGRAS_DESIGN.md.
