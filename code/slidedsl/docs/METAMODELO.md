# Metamodelo IR 1.1
`Presentation(title, theme, canvas, slides)` contém `Slide(number, elements,
groups, relations)`. `Element` mantém ID, tipo, geometria absoluta, Z, texto/arquivo,
fonte/cor, papel e origem textual. `Group` contém IDs de membros e rótulo opcional.
`Relation` contém alvo, referência, tipo, margem e localização de origem.

JSON Schema em `src/slidedsl/schemas/ir.schema.json`, gerado pelo Pydantic.
Versão 1.1 identifica as extensões de grupos/relações/papéis; os campos do contrato
1.0 continuam presentes. Não importamos silenciosamente esquemas desconhecidos.
Floats não finitos e campos extras são rejeitados. Verificação semântica da IR na
API acrescenta IDs, escopo, assets e tipos; regras de design acrescentam limites.

Backend recebe somente IR validada. O serializer canônico permite percurso
`.sld → AST → IR → DSL → AST → IR`, com estado geométrico e relações equivalentes.
`semantic_snapshot` é a definição executável de equivalência usada nos testes.
