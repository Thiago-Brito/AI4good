# Gramática e catálogo
A GLC está em `src/slidedsl/grammar/slidedsl.lark`, processada por Lark LALR.
`start → apresentacao`; apresentação contém tema e um ou mais slides; slide contém
uma ou mais instruções. Terminais: palavras reservadas, ID, COR, números, STRING,
chaves, colchetes, parênteses e vírgulas. Branco é ignorado; comentários e ponto e
vírgula não fazem parte da sintaxe. Strings usam escapes JSON. Português livre não
é aceito pela GLC: é traduzido pelo adaptador de modelo.

Correção mínima v1: `TEMA` preserva claro/escuro na árvore (literais anônimos eram
descartados). O vocabulário original permanece. Exemplos: `examples/minimo.sld`,
`examples/operacoes.sld`, `examples/cinco_slides.sld`; testes em `test_grammar.py`.

Catálogo v1: apresentação/tema/slide; adicionar retângulo, elipse, texto, imagem;
remover, mover, redimensionar, mudar cor, trazer/enviar, alinhar pela esquerda.
Posições: ponto absoluto, canto superior direito, abaixo de, a direita de.

Extensões 1.1 testadas após o núcleo: `agrupar [a,b] como g`, `desagrupar g`,
`alinhar a com b pela direita|pelo centro horizontal|pelo topo`,
`distribuir horizontalmente [a,b,c] com intervalo 24`, `definir camada de a como -2`,
`cor primaria|texto|fundo|secundaria|destaque`, `fonte titulo|corpo|rodape` e
`grupo "Comparação" { ... }` (ao menos dois elementos novos, sem grupos aninhados).

Anotações opcionais 1.1: `papel titulo|corpo|decoracao|background|nenhum`,
`familia "Arial"` no texto e `rotulo "Comparação"` após agrupar. Preservam papéis,
fonte e rótulos no roundtrip visual. `papel nenhum` desativa inferência pelo ID.
Tokens de tema são valores finitos definidos em `config/themes.yaml`.
AST Pydantic é tipada, sem campos extras, com linha e coluna por comando.
