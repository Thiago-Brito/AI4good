# Teste 7 — Qwen3 0.6B sem treino × 1.7B (bancada do app no PC, 24/11/2026)

Pergunta: com gramática e frases (app 0.5.0), o 0.6B, que é ~3× mais rápido, escreve apresentações perto das do
1.7B? Se a diferença for grande, vale a pena destilar o 1.7B ou o 4B no 0.6B (LoRA).

Dados (não versionados): `outputs/teste7_06b/`, `outputs/teste7_06b_dica/`, `outputs/teste6_17b_dica/`
(e `outputs/teste6_frases_v2/` do Teste 6).

## Configuração

A do Teste 6 (`RESULTADOS_T6.md`), condição `gramatica_limites+frases`: 12 pedidos × sementes 11 e 22, 5 slides,
documento do tema, cache esvaziado por geração.
- 1.7B: `Qwen3-1.7B-Q4_K_M.gguf` (1.107 MB), tempo projetado com as velocidades medidas no celular (3,88 / 1,49 tok/s).
- 0.6B: `Qwen3-0.6B.Q4_K_M.gguf` (484 MB). **Não há medição do 0.6B no celular**: as velocidades do 1.7B foram
  escaladas pela razão entre os tamanhos de arquivo (2,29×, ou seja, 8,88 / 3,41 tok/s). É uma estimativa.

## Achado no caminho: a dica de formato era copiada

A dica de uma linha do 0.4.0/0.5.0 usava palavras como marcador (`item "rótulo" "detalhe"`). Os dois modelos
copiavam o marcador como conteúdo: 63 campos em 17 de 24 apresentações no 1.7B, e 161 campos em 24 de 24 no 0.6B.
Correção: a dica passou a usar só `"…"` como marcador e explica o papel de cada texto numa frase à parte. Depois
dela, 0 campos no 1.7B e 3 no 0.6B. As duas bancadas abaixo usam a dica corrigida.

## Resultado (24 gerações por modelo, dica corrigida)

| Medida | 1.7B | 0.6B |
|---|---:|---:|
| Apresentações válidas | 24/24 | 24/24 |
| Verificador estrito | 24/24 | 24/24 |
| Apresentações sem slide do compilador | **13** | 8 |
| Slides montados pelo compilador (de 120) | **12** | 20 |
| Slides de seção (os mais simples) | 12 | 41 |
| Itens por slide de lista | 2,90 | 2,33 |
| Marcadores copiados (campos) | 0 | 3 |
| Tokens gerados por apresentação | 2.526 | 2.423 |
| **Celular (projetado)** | **53,5 min** | **24,4 min (estimado)** |

Lendo as apresentações: o 0.6B repete a mesma frase em vários campos, copia frases do documento como rótulo
(cortadas no limite de 48 caracteres) e enche o roteiro de slides de seção. O 1.7B produz conteúdo variado e
coerente com o pedido.

## Conclusão

- O 0.6B gera **apresentações válidas** em menos da metade do tempo, mas com **conteúdo claramente pior**: mais
  slides do compilador, roteiro raso e repetição.
- Esse é o cenário em que a destilação faz sentido. A gramática já garante a forma; o que falta ao 0.6B é conteúdo,
  e exemplos do 1.7B ou do 4B filtrados pelo compilador ensinam justamente isso. A meta seria aproximar o 0.6B das
  colunas do 1.7B mantendo os ~24 min.
- A estimativa de tempo do 0.6B precisa de uma medição no celular antes de entrar no artigo.

## Outro achado (pré-existente)

Em 1–2 de 24 apresentações de cada condição (inclusive JSON, no Teste 5) aparece "a plataforma/o mercado cresceu
30%". A frase vem do exemplo dentro do prompt de conteúdo (`content_system`), não do documento. Correção sugerida:
um exemplo sem número no prompt, ou recusar número que não esteja nos fatos citados.
