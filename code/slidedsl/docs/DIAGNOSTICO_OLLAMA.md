# Diagnóstico do experimento Ollama anterior

Fontes registradas em [FONTES.md](../refs/FONTES.md). Auditoria executada por
`scripts/diagnose_ollama.py`: [tabela das 30 respostas físicas](../outputs/diagnostico_ollama/DIAGNOSTICO.md)
e [evidências completas](../outputs/diagnostico_ollama/evidence.json).
Todos os 30 replays reproduziram exatamente os diagnósticos originais.

P001 é definido em `src/slidedsl/parser.py`: captura `lark.UnexpectedInput` e
produz ERRO com a primeira linha/coluna rejeitada, contexto e terminais esperados.
Não significa que a semântica ou o design reprovaram; essas fases não foram alcançadas.
Não foi relaxada a GLC nem acrescentada tolerância a comandos incorretos.

- 0.6b: `adicionar_imagem` não é um terminal suportado. O comando correto começa
  com `adicionar imagem`. As 15 respostas atingiram o limite de 8192 tokens.
- 4b: omissão da palavra `arquivo` na imagem, variantes incorretas do comando
  `trazer ID para frente`, duas respostas com content vazio e EOF em comando
  incompleto. Onze respostas terminaram por length e quatro por stop.
- A resposta 4b rep_01/A/round_0 falha na linha 21, coluna 29: o parser espera
  ARQUIVO antes de `"assets/imagem_demo.png"`. Esse erro precede o final truncado.

O adaptador anterior retorna apenas `message.content` textual sem remover trechos,
Markdown ou thinking. A tag 4b instalada declarou thinking obrigatório; o orçamento
foi compartilhado com esse trabalho. Os metadados preservam thinking_output_chars,
eval_count, done_reason e num_predict. Os corpos HTTP completos antigos não foram
salvos; não é possível reconstruir os textos de thinking a partir de suas contagens.
Os dados não provam que thinking causou cada resposta vazia. Length comprova o
limite de geração, mas não explica sozinho erros sintáticos anteriores ao EOF.

Há uma inconsistência de representação no relatório antigo: metrics registra null
para design não alcançado, enquanto attempt pode mostrar zero. Esses zeros não
significam design aprovado. A avaliação incremental conserva null quando não há
uma apresentação completa analisada e guarda diagnósticos por slide alcançado.

As respostas iniciais de A/B/C eram pareadas. A auditoria percorre C/round_0..2,
uma vez por chamada física, evitando contar como independentes as cópias de A/B.
O JSON de evidências lista cada modelo/repetição/rodada, causa da primeira falha,
linha ofensiva, contexto, tail, hash e controles; erros posteriores ao primeiro
erro sintático podem existir e não são enumerados por um parser que interrompe ali.
