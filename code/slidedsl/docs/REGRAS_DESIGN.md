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
| D006 | Fonte de título conhecida menor que maior fonte de corpo; corpo conhecido abaixo de 16 pt. |
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

## Rodada 6 de design: acabamento vigente

Esta seção substitui as regras de cartões, fotos, conclusão e transição da r5.
Fonte/protocolo: [DESIGN_RODADA6.md](../refs/DESIGN_RODADA6.md). Gramática Alto,
roundtrip, esquema IR, pisos de fontes e pesos da nota geométrica preservados.

- Cartões irmãos têm o mesmo topo de rótulo. A descrição começa no topo comum
  + maior altura de rótulo do grupo + **12 px**. Reservar o slot do irmão mais alto
  mantém a leitura por papéis; não ancorar rótulos curtos pela base.
- Altura natural = padding superior/inferior de **32 px** + slots medidos de
  rótulo/descrição + gap. Não há fração mínima de altura de cartão. Para uma grade,
  somar as alturas de linha e gutters de 24 px. Centro do bloco = centro útil
  **−5% da altura útil**, limitado pelo topo quando o conteúdo já ocupa quase tudo.
  Usar primeiro o maior perfil válido (usual Calibri 26/22); compacto é fallback.
- Tópicos curtos (2–3 itens, rótulo ≤36 e detalhe ≤110 caracteres) preferem cards
  válidos, preservando alternância imediata. Conclusão prefere actions_columns
  válidas; linhas são fallback. A030 mantém notas e candidatas completas e informa
  `selection_policy=content|geometry`. Não alterar a nota para disfarçar a preferência.
- Imagem com lado maior **≥600 px** usa somente **photo50**, independentemente de
  estilo, proporção ou nota. Quadro (664,0,616,600), recorte central, inclusive com
  A031 (<1000 px). Abaixo de 600 px, usar texto sem foto; capa recupera sua largura
  tipográfica. A031 continua visível. Nenhuma foto contida pequena é oferecida.
  Legenda de crédito e atribuição/licença nas notas são preservadas.
- Conclusão: número de dois dígitos **32 pt**, dentro do cartão, na cor principal,
  com a mesma borda esquerda do rótulo. Não acrescentar outro marcador numérico.
- Seção em deck <8: frase **48–54 pt** ajustada por família, bloco soft de um terço
  do canvas e motivo da família (lateral/base, duplo, degraus, ramo ou canto).
  D003 reconhece o token próprio `transicao`; o numeral gigante não retorna.

Evidência: `outputs/design_r6/20261111-004533/comparacao/`: 16/16 PPTX, 89 slides,
ocupação 0,6294→0,6664, rows 7/30→4/30, zero A010/A019/D010/eixo misto,
10/10 fotos internas em photo50 e oito A031. Todos os critérios (a)–(e) preservados.
A nota geométrica recalculada caiu de 0,8023 para 0,7048; critérios explícitos não
demonstram preferência humana. Persistem vazios externos, recortes agressivos e
problemas de conteúdo do corpus antigo. Prévia IR/Pillow não comprova Office.

## Rodada 5 de design: calibragem histórica

Evidências e método registrados em [DESIGN_RODADA5.md](../refs/DESIGN_RODADA5.md).
Esta seção substitui os parâmetros da rodada 4 abaixo; a seção antiga fica como
histórico da comparação. Não há validação psicofísica nem chamadas de API.

Ocupação continua sendo união exata de AABBs úteis cortadas pela região entre
fim do título +16 e y=636, x=64..1216. Fundo, título e créditos ficam fora.
Imagem conta pelo viewport inteiro (incluindo barras de `contain`); o manifesto
e o relatório distinguem quadro e foto efetivamente visível. Não se trata de
medida de tinta nem de informação percebida. O platô é **0,55–0,78**, com nota 1:

- f < 0,45: `0,8 × (max(0,f)/0,45)²` (queda mais íngreme que a linear anterior);
- 0,45 ≤ f < 0,55: `0,8 + 2 × (f−0,45)`;
- 0,78 < f ≤ 1: `(1−f)/0,22`.

Pesos: ocupação **35%**, equilíbrio **20%**, alinhamento **15%**, regularidade
**15%**, ritmo **15%**. Mantém-se a média de potência p=−2, piso numérico 0,01.
Ritmo: 0,1 se repetir imediatamente; 0,45 se repetir em qualquer um dos três
slides anteriores; 0,55 para classe visual igual à anterior; 1 nos demais casos
(nessa ordem de precedência). Bônus de diversidade = `0,03 × variantes_distintas
após candidata / slides_até_aqui`, inclusive a candidata. A soma é limitada a 1.
Desempate pela ordem, e proibição de repetir a anterior quando há alternativa válida.

Para tópicos com 2–3 itens, cada rótulo com até 36 caracteres e descrição até 110,
cards ganha 0,08 e rows tem nota limitada a 0,70. Com 4+ itens ou descrições
longas, não há bônus de cards nem teto para rows: a geometria/ritmo decide.
Conclusão: actions_columns ganha 0,12; actions_rows tem teto 0,65 e permanece
fallback quando as colunas não cabem. Esses ajustes são preferências explícitas
do compilador, registradas com os fatores no A030, e não evidência de beleza.

Cartões ocupam pelo menos 82% da altura disponível quando há espaço, mantendo
padding 32 e gap tipográfico 12. Rows distribui primeiro a altura entre as linhas,
com gap entre 8 e 64 px. Só depois centraliza a sobra opticamente, limitando o
início a 48 px abaixo da área após o título (inclusive quando ocupação <0,55).
Overflow continua explícito; não se corta texto. A altura disponível é comparada
no pixel lógico arredondado, como a geometria serializada, evitando falso A010
por frações como 81,99999999999989 versus 82.

Fotos paisagem/quadradas (`largura ≥ altura`) com lado maior ≥1000 px só oferecem
photo50: meia página sangrada com recorte central, mantendo crédito e notas.
Photo40 só é elegível para retratos ou A031; oferece quadro contido de cinco
colunas (466 px, ≥40% de 1152) e altura ≥50% da altura útil. A proporção original
é preservada dentro dele; retratos extremos ainda podem ter largura visível menor
que a do quadro. Photo50 também pode vencer para imagem pequena. Não se busca
imagem nova nesta rodada. Há testes com sete proporções/resoluções sintéticas.

Títulos de conteúdo e fio de destaque compartilham x=64 e alinhamento à esquerda,
em todos os estilos. O corpo segue esse eixo de composição (com padding interno
de cartões e recuos de marcadores). Centro só em capas/transições/citações;
capas/transições centralizam também marca, subtítulo e autor no mesmo grupo.
Noturno perde o alinhamento à direita e ganha um fio vertical de 4 px em x=24.
Os atributos restantes dos seis estilos permanecem, inclusive serifas, soft e marcadores.

### Escala óptica medida por família

Pillow/FreeType mede o glifo `x` normal a 1000 px nos arquivos locais, incluindo
overshoot: `bbox.bottom−bbox.top`. Razão r = altura da família / Arial. A mesma
compensação de família vale para os dois pesos. Tamanho = `round(referência/r)`
a 1 pt, nunca abaixo do mínimo do papel. Para corpo soma-se o piso
`ceil(18/r)`, garantindo **18 pt efetivos relativos a Arial**. Não é medição Office.

Referências: título 42, rótulo usual **23,5**, corpo usual 20; rótulo/corpo densos
20/18. O rótulo de referência foi ajustado de 24 para 23,5 para obter os 26 pt
Calibri exigidos pelo plano (24/r resultava em 27 pt). Arial arredonda para 24.
Pisos físicos permanecem título 32, rótulo 20, corpo 16, subtítulo 18. Créditos e
paginação continuam em 12 pt, fora do corpo. A tabela mostra o perfil se a família
for usada nesse papel; os estilos atuais têm corpo Calibri.

| Família | Razão x/Arial | Título | Rótulo usual | Corpo usual | Rótulo denso | Corpo denso |
|---|---:|---:|---:|---:|---:|---:|
| Arial | 1,000000 | 42 | 24 | 20 | 20 | 18 |
| Calibri | 0,905588 | 46 | 26 | 22 | 22 | 20 |
| Cambria | 0,899807 | 47 | 26 | 22 | 22 | 21 |
| Georgia | 0,928709 | 45 | 25 | 22 | 22 | 20 |
| Trebuchet MS | 1,007707 | 42 | 23 | 20 | 20 | 18 |
| Verdana | 1,050096 | 40 | 22 | 19 | 20 | 18 |

Calibri usual 22 pt equivale a 19,923 pt Arial pela altura-x; o denso 20 equivale
a 18,112 pt. Razões e hashes são recalculados dos arquivos locais no manifesto.
Na ausência de fonte continua o fallback Arial registrado, com margem de largura.
O compilador escolhe o maior perfil válido por composição; usa o compacto apenas
localmente. Comparações e cronologias densas usam o perfil compacto. Não há redução
global por deck nem relaxamento de D002/D010/mínimos.

Comparação ganha `comparison_text`, células de frase contínua rótulo — detalhe,
somente quando columns e pairs não são válidas. A cronologia de quatro ou mais
marcos também pode usar data + frase contínua em onze colunas quando a tabela de
três colunas não cabe. Os campos permanecem inteiros, em texto nativo e editável;
a hierarquia interna é menor. Nenhuma alteração de gramática/roundtrip/contrato IR.

Reprodução: `scripts/auditar_design_r4.py --run outputs/design_r5/<ts> --phase ciclo_N`
com corpus r4 copiado previamente; `scripts/comparar_design_r5.py --run <pasta>
--phase ciclo_N` gera três colunas r4-antes | r4-final | r5 e auditoria ZIP/XML.
Métricas históricas ficam preservadas; a comparação também recalcula a nota
geométrica r5 nas três IR, sem bônus de preferência por conteúdo. A taxonomia de
variantes de r4-antes é inferida, portanto seu ritmo/diversidade é aproximado.

## Rodada 4 de design: histórico do sistema e seleção offline

Fontes registradas antes da implementação em [DESIGN_RODADA4.md](../refs/DESIGN_RODADA4.md).
As métricas abaixo são heurísticas de composição. Não têm validação psicofísica e
não permitem afirmar que uma nota maior equivale a maior beleza ou preferência humana.
O modelo escolhe conteúdo Alto; o compilador escolhe geometria. Gramática Alto,
roundtrip `.slda` e esquema IR permanecem iguais; usa-se `font_face` já existente.
Textos, formas e gráficos continuam nativos/editáveis no PPTX.

`design_system.py` define 12 colunas entre x=64 e 1216, gutter 24, coluna com
74 px e `col(i, span)` com índice 0..11. Escala de espaço: 8/16/24/32/48/64 px.
Exceções nomeadas: distância rótulo–descrição de 12 px e fio de 4 px. Título comum
ancorado em y=64; conteúdo começa ao fim de sua caixa +16 e termina em y=636.
`distribute` reserva pelo menos 60% da altura disponível para blocos com dois ou
mais itens, se couberem; o espaço restante distribui-se com centro óptico a 44%
da folga. Conteúdo excessivo continua gerando A010; não é escondido ou truncado.
Cartões têm padding 32. Rótulos menores terminam no fim do slot de rótulo;
descrições irmãs começam no mesmo y, 12 px após o fim da caixa de cada rótulo.
Isso pode deixar os topos dos rótulos desnivelados quando há números de linhas diferentes.

| Estilo | Título / corpo | Raio | Cartão | Marcador | Alinhamento | Motivo sem foto |
|---|---|---:|---|---|---|---|
| claro | Calibri / Calibri | 0 | preenchido | barra | esquerda | lateral |
| escuro | Calibri / Calibri | arredondado | preenchido | ponto | centro | base |
| editorial | Georgia / Calibri | 0 | fio superior, sem fundo | número | esquerda | duplo |
| vibrante | Trebuchet MS / Calibri | arredondado | preenchido sobre soft | número | centro | degraus |
| natural | Cambria / Calibri | 0 | bloco com faixa lateral | ponto | esquerda | ramo |
| noturno | Calibri / Calibri | 0 | fio superior, sem fundo | barra | direita | canto |

Paletas comum e de destaque são independentes; capa/conclusão usam destaque.
Todos os pares diferem em três ou mais atributos não cromáticos, verificados em teste.
Escuro difere de claro em raio, marcador, alinhamento e motivo. Quando há foto de
capa, ela tem prioridade sobre o motivo. Nem todo atributo aparece em todo tipo de slide.

`font_file(family, bold)` procura a família no Windows, macOS e Linux. Inclui Arial,
Calibri, Cambria, Georgia, Trebuchet MS e Verdana, com arquivos normal/negrito.
Na ausência, usa Arial, registra no log e manifesto e aplica margem de largura de
14% (4% normal +10 pontos percentuais de segurança). Sem Arial, usa estimativa
conservadora. Medição Pillow trabalha a 4× e quebra por palavras. Na família Arial,
mantém também o piso histórico por caracteres; demais famílias usam a quebra medida.
`needed_height` adiciona margem de largura (5% negrito/2% regular). D010 verifica
altura e a palavra mais larga, na família declarada. A prévia usa a mesma fonte,
desenha em 1280×720 e depois reduz. Não comprova fidelidade de PowerPoint/macOS.
D003 reconhece os estilos por família/fundo/ID do título compilado; D006 mantém
os mínimos e a hierarquia em pontos, sem exigir famílias iguais. D002 não mudou.

| Tipo | Candidatas |
|---|---|
| topicos | cards, rows; grid 2×2 adicional quando há quatro itens |
| numeros | number_columns (valores grandes), number_rows (valor à esquerda) |
| comparacao | comparison_columns (rótulo ao lado do detalhe), comparison_pairs (pares empilhados) |
| imagem | photo40 (cinco colunas, contida), photo50 (meia página sangrada); sem arquivo: rows/cards |
| conclusao | actions_columns (ações numeradas em colunas), actions_rows (ações em linhas) |

Cada candidata é construída e passa pela semântica e pelo verificador de design.
Descartam-se A010/A019/D001/D002/D008/D010 não informativos e qualquer erro semântico.
Caso todas sejam inválidas, a cena permanece inspecionável e a compilação falha com
A010. A030, nível INFORMAÇÃO, guarda variante, classe visual, nota, fatores,
ocupação e todas as candidatas com seus bloqueios. Sem novas chamadas de modelo.

Os fatores puros de `layout_score.py` pertencem a [0,1]:

- Ocupação: união exata de caixas úteis cortadas pela área útil. Não conta fundo,
  título nem créditos. Conta textos ≥16 pt, imagens, cartões e cabeçalhos. A nota é
  `min(1, f/0.45, (1-f)/0.30)`, limitada a [0,1]; platô entre 0,45 e 0,70.
- Equilíbrio: 1 menos a distância entre centro de massa e centro útil, dividida
  pela meia diagonal. Massa = área × peso: imagem 1,2; texto 0,8 a 1,2 conforme
  luminância; forma cheia 0,65; fio 0,08. Caixas são recortadas na área útil.
- Alinhamento: `1 - (nx + ny - 2)/(2n)`, com nx/ny como contagens de bordas
  esquerdas/topos distintos e tolerância de 2 px.
- Regularidade: por grupo de irmãos (tipo/papel), `1/(1+CV(largura)+CV(altura)+CV(gap))`;
  o fator do slide é a média dos grupos. Gap horizontal na mesma linha, vertical
  entre linhas; CV usa desvio populacional. Um único irmão recebe 1.
- Ritmo: 0,1 para variante igual à anterior; 0,55 para classe visual igual;
  1 nos demais casos. Ações em linhas compartilham a classe visual de listas.

Pesos finais: ocupação **0,30**, equilíbrio **0,25**, alinhamento **0,15**,
regularidade **0,15**, ritmo **0,15**. Agregação: média de potência p=−2,
`(Σ peso_i × max(0.01, fator_i)^−2)^−1/2`. O piso é apenas numérico. Um fator
ruim derruba a nota; não se usa soma linear. Desempate mantém a ordem declarada.
Além da nota, nunca se repete a variante imediatamente anterior se existir uma
alternativa válida. Slides com apenas uma composição podem repetir.

Decks de menos de oito slides usam seção como frase de transição, sem numeral
gigante. Com oito ou mais, preserva-se o bloco numerado. O prompt recomenda evitar
seções em decks curtos. Conclusão tem numeração e variantes próprias.

Imagens: busca automática continua em outros provedores se só encontrar baixa
resolução; se existir foto elegível com lado maior ≥1000 px, retira as menores.
Se não houver, mantém fallback e o compilador emite A031, sem bloquear. A seleção
lexical de relevância continua limitada. `photo40` mede/pontua a caixa da imagem
efetivamente contida, mantendo sua proporção. A ordem das candidatas considera
proporção ≥1,5 como horizontal; a nota final decide a largura. Apenas photo50/capa
sangrada usam recorte central. Crédito e atribuição completa permanecem nas notas.

Reprodução: `scripts/auditar_design_r4.py` congela os originais com SHA-256 e gera
PPTX, DSL compilada, IR, diagnóstico, PNG por slide, contato, JSON e CSV por fase.
`--run <pasta> --phase ciclo_N` reusa o corpus congelado; `--compare` gera
comparações lado a lado sem editar as saídas. A linha de base infere variantes
observáveis (cards ou tipo de slide), pois A030 não existia: a diversidade anterior
é uma aproximação, não uma taxonomia retrospectiva perfeita. A031 não existia no
código anterior; zero nesse campo anterior significa diagnóstico indisponível.
Os fontes originais e resultados antigos são preservados. Execução offline, US$ 0.

## Rodada 3: unidades e limites de legibilidade

Canvas 1280?720 em pixels l?gicos, 96 unidades/polegada (13,333?7,5 pol). Fontes na IR s?o pontos tipogr?ficos, passados sem convers?o para fontSize no PptxGenJS; pr?via/medi??o usam pt?96/72 pixels. Corpo m?nimo 16 pt, r?tulo 20 pt, t?tulo 32 pt, subt?tulo de capa 18 pt. Perfil usual 42/24/20 pt, perfil denso 42/20/16 pt restrito ao pr?prio slide; n?o reduz o restante do deck. Cr?ditos/fontes/pagina??o ficam em 12 pt, separados do conte?do. A019 ? erro de m?nimo no compilador Alto; A010 preserva texto/fonte e pede encurtamento quando n?o cabe. D006 avisa corpo conhecido abaixo de 16 pt na DSL detalhada, preservando A como baseline.

A021 avisa ocupa??o <0,30: uni?o exata das caixas ?teis (texto de conte?do ?16 pt, imagem, cart?es/cabe?alhos) recortadas entre o fim do t?tulo e y=636, x=64..1216. Cart?es contam como elementos; o indicador n?o mede tinta e n?o prova equil?brio est?tico. Capa/se??o/cita??o ficam fora desse aviso. A020 detecta prefixo comum de quatro palavras/Jaccard ?0,72 entre descri??es irm?s e eco literal do r?tulo; A022 detecta t?tulo sem conectivos e padr?es nominais conservadores. S?o heur?sticas lexicais com falsos positivos/negativos; reparo usa o or?amento existente. Capa admite origem de imagem opcional, preservada no roundtrip Alto.

## Rodada 7: estilo automático e fotos

`--tema auto` e a opção UI Automático (sugerido) usam a primeira correspondência
na regra local de `auto_theme.choose_theme`. Público infantil/escolar/ensino escolhe
vibrante; intenção acadêmica/TCC/pesquisa/banca escolhe claro; tecnologia/programação/
software/Git escolhe escuro; natureza/ambiente/alimentação/horta/reciclagem escolhe
natural; história/humanidades/leitura/literatura escolhe editorial. Sem correspondência,
claro. Contexto de público e defesa acadêmica tem precedência sobre tema técnico.
A regra opera sobre o pedido, aceita roteiro opcional e não faz chamada de modelo.
O resultado exibe o estilo e permite trocá-lo sem inferência.

Commons usa título, descrição e categorias/extmetadata. A busca simplificada conserva
os termos centrais da consulta original, evitando aceitar outro assunto num fallback
amplo. Pessoas/retratos/palco/conferência são vetados salvo pedido explícito de pessoas.
É filtro lexical, não reconhecimento visual; coincidências e falsos negativos persistem.
O último substantivo concreto da consulta planejada deve estar nos metadados, com
normalização de acentos e plural. PNGs da busca automática e imagens Commons com
descrição menor que 20 caracteres são recusados no modo fotográfico. Essa escolha
conservadora pode perder fotos válidas; arquivos locais PNG continuam aceitos.
`imagem` sem foto aprovada conserva seu tipo e compila em cartões ou destaque de
36–48 pt quando só há legenda/título. Nenhum texto é truncado para esconder erros.
Fontes e limites metodológicos: refs/DOCUMENTOS_EDICAO_R7.md.
