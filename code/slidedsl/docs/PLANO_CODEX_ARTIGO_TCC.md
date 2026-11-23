# Plano Codex — artigo do TCC (LNCS, português, Overleaf)

Decisão do autor (23/11/2026): o TCC é **só o artigo**, entregue em **27/11/2026**, escrito no projeto
Overleaf já clonado em `academy/papers/artigo-overleaf/`, **no estilo LNCS que está lá**
(`llncs.cls`, `splncs04.bst`), **substituindo** o relatório do Ordered GNN (o histórico Git preserva).

## Fontes do conteúdo (ler antes)

- Rascunho principal (≈20 mil palavras): `code/slidedsl/docs/artigo/ARTIGO_CIENTIFICO_SLIDEDSL.md`.
- Evidências: `docs/artigo/EVIDENCIAS_TECNICAS.md`, `docs/artigo/LACUNAS_DA_PESQUISA.md`, `ROADMAP.md`,
  `docs/PROGRESSO.md`.
- Plano e enquadramento: `docs/PLANO_TCC.md` (tese, P1–P6, decisões), `docs/orientacao/AVALIACAO_DO_TCC.md`
  (motivação = **dependência**, não "indisponibilidade").
- Novidades desde o rascunho: Fase 0 (custo por chamada), F1, núcleo TS com paridade
  (`docs/APK_CORE_RELATORIO.md`: 24/24 fixtures, 261/261 corpus), app Android (`docs/APK_APP_RELATORIO.md`;
  voz; geração no aparelho; importação de GGUF) e o achado do teste no emulador de 23/11 (abaixo).
- Referências: **somente** as registradas em `docs/artigo/REFERENCIAS.md`, `docs/REFERENCIAS.md`,
  `refs/FONTES.md` e `refs/TCC_TESTES_APK_FONTES.md`. Não acrescentar obra que não esteja nesses
  arquivos. BibTeX em `academy/papers/artigo-overleaf/refs/references.bib`.

Achado de 23/11 (registrar no texto como observação qualitativa, não como experimento): no emulador,
com o llama.rn recebendo `messages` + modelo de chat Jinja do Qwen3, a gramática derivada admitia um
bloco `<think>` antes do JSON; o roteiro falhou com erro de parse após ~5 min. Passando o prompt já
formatado com raciocínio desligado e o JSON Schema como gramática estrita nativa, o bloco deixa de ser
possível. Ilustra que *como* a restrição é aplicada importa (liga com Tam et al. e XGrammar).

## Estrutura (≈16 páginas LNCS; português)

1. **Título, resumo (≤250 palavras) e palavras-chave.** Título sugerido: "SlideDSL: geração de
   apresentações editáveis por modelos de linguagem pequenos, locais e móveis, guiados por gramáticas".
   Autor: Thiago Barbosa (como no arquivo atual). Instituição: manter a do arquivo atual se houver,
   senão `\institute{}` com marcador `\pendente{instituição}`.
2. **Introdução**: dependência de IA paga; pergunta; contribuições (lista numerada, só o que há
   evidência ou está marcado pendente).
3. **Fundamentação e trabalhos relacionados** (condensar as seções 2 e 3 do rascunho): GLC/LALR/DSL;
   SLMs e inferência local; geração restrita (Willard & Louf, XGrammar, Tam et al.); custo do formato
   (Agyemang et al., Masciari et al.); geração de slides (AutoPresent, PPTAgent); IA no celular (MELT,
   PalmBench, Tummalapalli et al.).
4. **SlideDSL**: duas camadas (Alto → 1.1 → IR), compilador determinístico, validações A0xx/D001–D010,
   pipeline com pesquisa e fatos verificados. Uma figura TikZ do fluxo (sem imagem externa). Um trecho
   curto de Alto (listing) do apêndice A do rascunho.
5. **Versão móvel**: núcleo TS gerado do Python + paridade de IR; app (llama.rn, JSON Schema →
   gramática, modo celular com ≤1 reparo, voz, importação/download do modelo com SHA-256, exportação de
   dados); achado do `<think>`.
6. **Método**: protocolo pareado (12 pedidos × 4 temas × 3 níveis, 5 sementes, ordem sorteada), Fase 0
   (métricas), estatística prevista (Wilcoxon, McNemar, Friedman, IC95% bootstrap).
7. **Resultados**: (a) resultados já medidos do rascunho (E3 0/10→10/10, E11 12/12, síntese dos
   reparos, testes automatizados — atualizar contagem para os números atuais do ROADMAP), paridade
   261/261; (b) **Teste 1, Teste 3 e Teste 4 como subseções com tabela vazia e `\pendente{...}`**
   dizendo o que será medido. Nunca inventar número.
8. **Discussão, limitações e trabalhos futuros**: avaliação humana adiada, Teste 2 completo, T5, T7.
9. **Conclusão**.
10. Referências (splncs04). Apêndice opcional só se couber.

## Regras

- `\newcommand{\pendente}[1]{\textcolor{red}{[PENDENTE: #1]}}` no preâmbulo; usar para tudo que
  depende de teste não executado ou dado faltante.
- Toda afirmação numérica deve vir de um arquivo de evidência; em comentário LaTeX ao lado
  (`% fonte: docs/...`), para o revisor conferir.
- Linguagem: português claro, frases curtas, sem exageros ("revolucionário", "garante qualidade").
  "Válido" ≠ "bom": manter essa distinção.
- Remover do projeto os arquivos que só servem ao Ordered GNN (`samplepaper.tex` vira o artigo novo;
  figuras `fig1.eps`, `grafico_rede.png`, `configuracao_rede.png`, `samplepaper.log`, `APRESENTACAO.md`,
  `apresentacao-notas.md`, `history.txt` saem). **Não apagar** `outputs/` nem `refs/` antigos (mover
  para `arquivo-ordered-gnn/` se atrapalharem). Atualizar `ROADMAP.md` do projeto Overleaf com a nova
  entrega e `refs/fontes.md` com as fontes do artigo.
- Compilar localmente com MiKTeX: `latexmk -pdf samplepaper.tex` (ou pdflatex+bibtex). Zero erros;
  sem referências indefinidas (`??`). Conferir o PDF (nº de páginas, figura, tabelas).
- **Não fazer `git commit`, `git push` nem nada no Overleaf** — o revisor faz.
- Relatório curto em `academy/papers/artigo-overleaf/RELATORIO_ARTIGO_TCC.md`: estrutura, páginas,
  lista de `\pendente`, fontes usadas, avisos de compilação.
