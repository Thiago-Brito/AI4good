# Análise de Texpace / Spacemantics
Fonte primária e snapshots: [registro](../refs/FONTES.md), `refs/texpace/` e
`refs/spacemantics-tree.json`, consultados em 2026-10-08. Licença MIT, Lucas Figueiredo.
As páginas dos subdiretórios falharam no navegador; a árvore e os documentos foram
obtidos pela API do GitHub e raw.githubusercontent.com. Leitura: dsl/SPEC.md,
checker/CONTEXT.md, bench/CONTEXT.md, tests/CONTEXT.md. Não executamos seus testes.

A especificação separa cena declarativa e afirmações espaciais; checker mantém
geometria determinística, tolerâncias e distinção entre falso e não avaliável.
O benchmark descrito mantém tarefas fixas e compara tentativas com e sem feedback.
Os testes separam direção, topologia, medidas e tempo.

Adaptação conceitual própria: `below` → abaixo de; `left/right` → relação lateral;
`occludes` → união de interseções com camadas superiores; z-order → ordem de desenho.
SlideDSL usa somente XY, origem superior esquerda e unidades lógicas. 3D, 4D,
quaternions, tempo e RCC-8 completo ficam fora do recorte. Nenhuma gramática ou
implementação daquele projeto foi copiada. Sua evidência experimental não constitui
resultado da SlideDSL; a hipótese precisa do benchmark próprio.
