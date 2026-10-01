# Fontes — estudo detalhado do InstructPipe

Registro em 01/10/2026, antes da redação do guia.

## P1 — publicação fornecida pelo usuário

ZHOU, Zhongyi et al. **InstructPipe: Generating Visual Blocks Pipelines with Human Instructions and LLMs.** CHI Conference on Human Factors in Computing Systems (CHI ’25), Yokohama, 26 abril–1 maio 2025. ACM, 22 páginas. DOI: [10.1145/3706598.3713905](https://doi.org/10.1145/3706598.3713905).

- Original preservado: `C:/Users/brito/Downloads/3706598.3713905.pdf`.
- Cópia de estudo: [3706598.3713905.pdf](3706598.3713905.pdf), 6.405.344 bytes.
- SHA-256 de ambos: `42c207655989379c49e48d3b9e0195b1a27f2bafe059b81a4cc2d80b61cc5c89`.
- Versão publicada: 22 páginas, conforme referência impressa na p. 2. Corpo principal nas pp. 1–13, referências nas pp. 13–15 e apêndices A–D nas pp. 16–22.
- Leitura das seções 1–9 e dos quatro apêndices; não se afirma leitura dos trabalhos da bibliografia ou execução dos materiais suplementares.
- Inspeção visual das 15 figuras, 4 tabelas e do Algoritmo 1. Recortes com legendas e manifesto de páginas/coordenadas em `../outputs/figuras-tabelas/`; páginas completas e texto por página em `../outputs/paginas/`.
- A extração textual corrompe alguns símbolos do pseudocódigo; figuras, algoritmo e números das tabelas foram conferidos nas renderizações.
- O PDF indica licença CC BY 4.0. Imagens do guia são recortes atribuídos a Zhou et al., com links para a fonte e sem alteração do conteúdo além do recorte.

## Fontes auxiliares

| ID | Fonte primária | Uso |
| --- | --- | --- |
| S1 | NASA. [NASA Task Load Index](https://www.nasa.gov/human-systems-integration-division/nasa-task-load-index-tlx/). Consulta em 01/10/2026. | Natureza subjetiva do instrumento e seis dimensões; a aplicação Raw-TLX específica é descrita no artigo. |
| S2 | NIST. [Signed Rank Test](https://www.itl.nist.gov/div898/software/dataplot/refman1/auxillar/signrank.htm). Consulta em 01/10/2026. | Contexto do teste de Wilcoxon para comparações pareadas; nenhum teste foi recalculado. |
| L1 | [Guia local de Oakes et al.](../../02-workflows-ml/GUIA-DETALHADO.md). | Comparação entre intenção, workflow e implementação. |
| L2 | [Guia local do ChainForge](../../03-chainforge/GUIA-DETALHADO.md). | Comparação entre construção assistida e experimentação/avaliação. |

## Escopo e convenções

- Rumo solicitado: **como transformar a intenção do usuário em um fluxo visual que ele consiga compreender, corrigir e completar**. É uma formulação orientadora do guia, não uma citação literal do artigo.
- Exemplos próprios, interpretação crítica e propostas para a DSL são rotulados. Resultados dos autores recebem seção e página.
- O artigo avalia o sistema completo; não isola o efeito do layout, do pseudocódigo ou de cada módulo de geração.
- A razão de 18,9% mede operações estruturais mínimas estimadas; não mede diretamente tempo, esforço mental ou toda interação da interface.
- Nenhum modelo/API foi executado, nenhum resultado foi reproduzido e não houve coleta de dados pessoais ou acesso aos serviços citados.
- Pontos de atenção registrados: referências trocadas às Figuras 14/15 no apêndice D.2; lista ocupacional do workshop soma 20 apesar de 23 participantes declarados; parâmetro textual em `input_text` é uma exceção à exclusão geral de geração de parâmetros; a seção 6.4.2 não detalha suficientemente como tratar operações redundantes na contagem de interações dos usuários.
