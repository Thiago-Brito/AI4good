# Fontes — rodada 4 de design (10/11/2026)

Registradas antes da implementação. Plano: `docs/PLANO_CODEX_RODADA4_DESIGN.md`.
Evidência de partida: `outputs/api_voz_mobile/visual3_reciclagem_0003/previa.png/previa.png`
e `outputs/estilos/*/previa.png` (estilos diferem só na paleta; cartões ocupando metade
da área útil; slide de seção "01" num deck de 6; Arial fixa).

## Geração de slides com LLM e layout
- Cui et al. Design First, Code Later: Aesthetically Pleasing Template-Free Slides
  Generation. Findings of ACL 2026.
  https://preview.aclanthology.org/ingest-acl/2026.findings-acl.1524/
  Uso: separar o desenho da página da implementação (no SlideDSL: modelo escolhe o
  conteúdo, compilador escolhe a composição).
- AeSlides: Incentivizing Aesthetic Layout in LLM-Based Slide Generation via Verifiable
  Rewards. arXiv 2604.22840. https://arxiv.org/pdf/2604.22840
  Uso: restrições estéticas explícitas e verificáveis evitam layouts "planos".
- Xu et al. Textual-to-Visual Iterative Self-Verification for Slide Generation.
  arXiv 2502.15412. https://arxiv.org/html/2502.15412v1
- Zheng et al. PPTAgent. arXiv 2501.03936. https://arxiv.org/abs/2501.03936
  Não adotado: depende de decks de referência de terceiros.

## Crítica visual (trabalho futuro, não implementado nesta rodada)
- DesignLab. arXiv 2507.17202. https://arxiv.deeppaper.ai/papers/2507.17202v1
- SlideAudit (UIST 2025). arXiv 2508.03630. https://arxiv.org/html/2508.03630v1
  Taxonomia layout/tipografia/cor/imagem; LLMs sem taxonomia detectam mal (F1 ~0,48–0,66).
- VLM-SlideEval. arXiv 2510.22045. https://arxiv.org/pdf/2510.22045v1
- ReDeck. arXiv 2609.00194. https://arxiv.org/pdf/2609.00194

## Métricas estéticas de layout
- Patentes "Method for measuring and quantizing document quality" (Xerox), ex.:
  https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/7266222
  Fatores em [0,1]: equilíbrio (centro de peso visual × centro), fração de espaço vazio,
  alinhamento, regularidade; combinação não linear para que um fator ruim domine.
  As próprias patentes reconhecem não ter validação psicofísica: usar como heurística.

## Sistema de design e regras
- Beautiful.ai — layouts que aplicam regras de espaçamento, alinhamento, hierarquia e
  limitam conteúdo (fonte comercial):
  https://www.beautiful.ai/blog/ai-can-build-slides-fast--but-great-presentations-still-need-design-rules
- BrightCarbon — espaço vazio em apresentações:
  https://www.brightcarbon.com/blog/presentation-whitespace/
- First Ascent Design — grade (3/12 colunas), tudo alinhado a uma margem ou linha:
  https://firstascentdesign.com/presentation-design-principles/
- PptxGenJS — `fontFace` por texto; masters não usados (defeito de reparo relatado):
  https://gitbrent.github.io/PptxGenJS/docs/masters ·
  https://github.com/gitbrent/PptxGenJS/issues/1449

## Ferramenta avaliada e não adotada
- kiwisolver (Cassowary, BSD): https://libraries.io/pypi/kiwisolver
  Não adotado: empilhamento em grade com espaçamentos fixos não exige solucionador, e
  evitamos dependência nova.
