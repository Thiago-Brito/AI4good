# Regras de design automatizadas
Referência para contraste: WCAG, [fontes](../refs/FONTES.md). As outras regras são
heurísticas quantitativas da especificação, não validação de qualidade estética.
Configuração: `config/design_rules.yaml`; severidades, limites e avisos estritos.

| Código | Medição / decisão |
|---|---|
| D001 | Caixa ultrapassa 0..1280 e 0..720; igualdade no limite é aceita. |
| D002 | sRGB linearizado, luminância 0.2126R+0.7152G+0.0722B; (Lmax+.05)/(Lmin+.05) <4.5. |
| D003 | Título conhecido compara tamanho, cor e família com tema. |
| D004 | Eixo de alinhamento declarado desvia >2 px. |
| D005 | Maior distância euclidiana entre bordas de membros do grupo >120 px. |
| D006 | Fonte de título conhecida menor que maior fonte de corpo. |
| D007 | União das caixas cortadas no canvas / área do canvas >0.8. |
| D008 | União de interseções com shapes/imagens acima / área da caixa >0.2. |
| D009 | Largura ou altura ≤0, inclusive após edição de IR. |
| D010 | Estimativa de linhas e altura supera caixa interna. |

União por varredura X é exata para caixas alinhadas aos eixos; não soma interseções
duas vezes. Elipse e imagem usam AABB, sem máscara/alpha real. Texto sem fill não
cobre a caixa inteira. Background não conta na densidade nem recebe aviso de oclusão;
decoração não recebe D008, mas continua podendo encobrir objetos relevantes.

D002 procura retângulo sólido conhecido abaixo do texto; imagem, elipse ou cobertura
parcial produzem INDETERMINADO/INFORMAÇÃO. Sem objetos abaixo, usa fundo do tema.
Não existe aprovação falsa para fundo desconhecido. Papéis vêm de anotação ou
heurística de prefixo de ID; origem fica registrada. Sem papel não há D003/D006.

Overflow usa padding 8 px, fonte pt×96/72, largura média 0.52×fonte_px e altura de
linha 1.2×fonte_px. É aproximação, não medição de glifos; confira no aplicativo final.
Relatórios contêm código, gravidade, slide, elemento, origem, coordenadas, evidência
e proposta de correção. `--strict` falha para D002/D008/D010 configurados, mantendo
a gramática e a gravidade original do diagnóstico.
