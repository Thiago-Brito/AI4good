# Registro do seminário 3: slides gerados (local e API) e revisão

Data: 18/11/2026. Entrada comum: o roteiro `../sem3_slidedsl.md` e o mesmo pedido de 6 slides.
Revisão feita pelo Claude no papel do estudante, seguindo os itens de verificação do sem3.
Os números do competidor e do teste pequeno vêm dos arquivos citados; nada foi estimado.

## Linha do tempo

| Passo | O que aconteceu | Evidência |
| --- | --- | --- |
| 1 | Compilador passa a desenhar SVG (etapas, ciclo, grafico); conferidor automático; 12 pedidos com gabarito | commit 8051c11 |
| 2 | Teste pequeno com a primeira chave da API: HTTP 401 (chave recusada) | `teste_pequeno/` |
| 3 | Teste pequeno com Qwen3 4B local: A 0/3, B 2/3. Conferidor aprovava ciclo ilegível (corrigido); modelo escreveu `ciclo` (virou bloco) | `teste_pequeno/resultado_local.json` |
| 4 | Deck v1 gerado com o modelo local: sem competidor, inventou "o teste envolve estudantes reais" nas notas | `code/slidedsl/outputs/sem3/gerado_v1/` (fora do git) |
| 5 | Chave nova da API. Teste pequeno com gpt-4.1-mini: A 0/3 (US$ 0,0051), B 3/3 (US$ 0,0007) | `teste_pequeno/resultado_api.json` |
| 6 | Deck v1 com a API: sem competidor, conclusão "confirmar que o SlideDSL melhora" (só pode dar sim) | `code/slidedsl/outputs/sem3/gerado_api_v1/` (fora do git) |
| 7 | Roteiro atualizado com o teste pela API; v2 gerado nos dois modos a partir dele; revisão de cada um | `api/`, `local/` |

## Geração v2: custo e o que veio errado

| | Local (qwen3:4b-instruct) | API (gpt-4.1-mini) |
| --- | --- | --- |
| Tempo / chamadas | 200,4 s / 32 | 171,6 s / 43 |
| Tokens entrada / saída | 62.725 / 12.199 | 66.768 / 11.258 |
| Custo | sem cobrança por token | US$ 0,0378 |
| Slide do competidor | faltou | faltou |
| Capa | sem sentido ("Comparações visíveis...") | boa |
| Regras passou/caiu/inconclusivo | faltou inconclusivo | só passou |
| Afirmação de resultado antes do teste | "replicável e escalável para mais estudantes" | "O SlideDSL aumenta..." (2×), "vai provar em 25/11" |
| Calendário até 02/12 | sem datas | sem datas |
| Teste pequeno | bom (local, API e erros) | bom (0/3, 2/3, 3/3) |

Nas duas rodadas (v1 e v2), nenhum dos dois modelos fez o slide do competidor, embora a seção esteja no roteiro.

## O que a revisão mudou, slide a slide

**API** (`api/revisao.diff`, 116 linhas trocadas):
1. Capa: título mantido; subtítulo trocado ("Mostrar que o SlideDSL gera diagramas claros" afirmava o resultado).
2. Competidor: slide criado (faltava), com os números de 01/11.
3. Objetivo e regras: virou passou / caiu / inconclusivo; a frase "o SlideDSL aumenta" passou para as notas como "quero mostrar".
4. Comparação: estrutura mantida ("Desenho direto do SVG", "Conteúdo na DSL"); "Diagramas mais corretos" (afirmação) virou "Medida".
5. Resultados em números: virou slide de imagem com as barras de A e B do teste pela API; os números 0/3, 2/3 e 3/3 ficaram nos itens.
6. "O que quebrou": foi para as notas do slide 5, para caber o competidor nos 6 slides.
7. Conclusão: virou linha do tempo com 18/11, 24/11, 25/11, 27/11 e 02/12; saiu "vai provar".

**Local** (`local/revisao.diff`, 115 linhas trocadas):
1. Capa: reescrita.
2. Competidor: slide criado (faltava).
3. "O que quero mostrar": título mantido; itens viraram as três regras.
4. "Regras de avaliação" (sem inconclusivo): removido, juntado ao 3.
5. Comparação: título mantido; rótulos repetidos ("IA sozinha" / "IA sozinha") viraram "Quem escreve" / "Quem desenha".
6. Teste 18/11: mantido quase inteiro; o terceiro item virou "O que mudou".
7. Conclusão: virou linha do tempo; saiu "escalável para mais estudantes".

As duas versões revisadas passaram na validação estrita na primeira tentativa e compilaram para 6 slides editáveis.

## Leitura honesta

- A API custou US$ 0,038 e foi 29 s mais rápida; o local não cobra, mas ocupa a GPU.
- O volume de revisão foi parecido (cerca de 115 linhas nos dois). A diferença foi o tipo de erro:
  o local errou mais na forma (capa vazia, rótulos repetidos); a API errou mais no tom,
  afirmando o resultado antes do teste.
- Os dois pularam o competidor e o calendário: o SlideDSL ainda não cobre bem pedidos de plano
  de teste. Isso é observação de um deck, não medida.

## Arquivos

- `api/`: `gerado.slda`, `gerado_previa.png`, `revisado.slda`, `revisado_previa.png`, `sem3_api.pptx`, `revisao.diff`, `piloto_barras_api.png`.
- `local/`: os mesmos arquivos, sem a imagem.
- `teste_pequeno/`: `resultado_local.json`, `resultado_api.json`, `piloto_ciclo_local.png`.
