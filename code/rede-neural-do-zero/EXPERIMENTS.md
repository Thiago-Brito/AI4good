# Experimentos
> Registro dos testes feitos com o codigo.

## Experimento 2026-09-11 - verificacao da arquitetura 13-8-5-1

- Objetivo: verificar a sugestao de que 8-5 neuronios e 60 epocas generalizavam melhor.
- Configuracao: 13-8-5-1, tanh/sigmoid, SGD em lote completo, taxa 0.1,
  sem L2, 60 epocas, semente 42, mesma divisao externa dos demais experimentos.
- Resultado: treino completo com BCE 0.4503733922 e acuracia 0.8174273859;
  teste com BCE 0.4538945279 e acuracia 0.7868852459 (48/61).
- Interpretacao: a sugestao nao foi confirmada e nao deve ser apresentada como
  melhor arquitetura. A configuracao base 13-8-4-1/500 manteve 53/61 no teste.
- Grade auxiliar em validacao interna: 13-8-1, 13-8-4-1, 13-8-5-1 e
  13-16-8-1, com 60, 100, 300 e 500 epocas, SGD e taxa 0.1. Treinos mais
  longos elevaram o ajuste, mas a BCE de validacao das redes de duas camadas
  piorou depois de seus melhores pontos, compativel com sobreajuste.
- Limite: nenhuma configuracao registrada chegou a 100% no treino; essa frase
  nao foi incorporada ao relatorio.

## Experimento 2026-09-11 - Adam, L2 e selecao interna

- Objetivo: tentar melhorar a generalizacao mantendo o mesmo teste externo.
- Mesmos CSV, hash, deduplicacao, divisao 241/61 e semente 42 do experimento abaixo.
- Selecao: divisao estratificada dentro dos 241 (192 ajuste / 49 validacao),
  escala ajustada apenas nos 192, minimo da BCE de validacao, paciencia 60,
  maximo de 500 epocas por candidato. Nenhum dado de teste entra na selecao.
- Candidatos (arquitetura, otimizador, taxa, L2, melhor epoca, BCE validacao):
  - 13-8-4-1, SGD, 0.1, 0, 215, 0.3849982133.
  - 13-8-4-1, Adam, 0.01, 0.001, 76, 0.3948134407.
  - 13-8-4-1, Adam, 0.003, 0.01, 234, 0.3786514930.
  - 13-16-8-1, Adam, 0.003, 0.01, 47, 0.3547679398 (selecionado).
- Treino final: reinicializacao com semente 42; 47 epocas nos 241 exemplos,
  usando media/desvio desses 241; configuracao escolhida antes de avaliar teste.
- Teste: BCE 0.3379420534, acuracia 0.8524590164 (52/61),
  matriz de confusao `[[22, 6], [3, 30]]`.
- Interpretacao: perda menor que a execucao original, mas um acerto a menos.
  Nao houve melhora de acuracia confirmada; a busca continua opcional.
  Resultado de uma divisao pequena, sem estimativa de variabilidade entre sementes.
- Artefatos: `outputs/heart-20260911-204939-879247/`, incluindo parametros,
  indices internos de validacao, metricas dos candidatos e previsoes finais.
- Verificacao: cinco testes unitarios passaram, incluindo atualizacoes Adam
  em tres passos e isolamento da escala interna. AppTest passou em treino
  manual e busca, com replay e alternancia da inferencia usando o CSV real.
- Animacao: Canvas no navegador, pesos reais em snapshots, pulsos ilustrativos
  de ida e volta. Ocultar arestas na tela nao altera a topologia nem os calculos.
  JavaScript validado com node --check e renderizacao conferida no Edge headless;
  demonstracao local e captura em `outputs/animation-preview.html` e `.png`.

## Experimento 2026-09-11 - Heart Disease com grafo explicito

- Objetivo: executar feed forward e backpropagation percorrendo nos e arestas,
  treinar com 80% dos dados e realizar inferencia nos 20% reservados.
- Configuracao: Python 3.12, kagglehub 1.0.2, arquitetura 13-8-4-1, tanh/sigmoid,
  Xavier, gradiente em lote completo, taxa 0.1, 500 epocas, semente 42.
- Dados: johnsmith88/heart-disease-dataset, download da versao 2 pelo kagglehub.
  CSV com 1025 linhas; 723 duplicatas exatas removidas; 302 linhas unicas.
  Divisao estratificada: 241 treino e 61 teste. Padronizacao ajustada no treino.
- SHA-256 do CSV: `ddb2996b2f4db2e00aad13f4518200179ff69f79093838e3c21ffa672ebec0f1`.
- Metricas de teste: acuracia 0.8688524590 (53/61), entropia cruzada 0.3514938613.
  Matriz de confusao (linhas reais, colunas previstas): `[[23, 5], [3, 30]]`.
- Interpretacao: resultado de uma unica divisao; nao estima variacao entre sementes.
  O teste nao participou das atualizacoes dos parametros. Remover duplicatas evita
  que copias exatas sejam compartilhadas entre treino e teste.
- Arquivos gerados: `outputs/heart-20260911-204447-117664/`: `metrics.json`,
  `model.json` e `predictions.csv`. CSV original em `outputs/dataset/heart.csv`.
- Verificacao: 3 testes automatizados passaram (todos os gradientes por diferencas
  finitas; aprendizado de XOR e inferencia sem alterar pesos; deduplicacao,
  reproducibilidade e padronizacao apenas pelo treino).
- Interface: Streamlit AppTest verificou abertura, treino de 10 epocas, exportacao,
  persistencia da rede entre interacoes e animacao da inferencia sem excecoes,
  usando fixture sintetica apenas para verificar o fluxo da interface.

Use uma entrada por experimento.

## Template

### Experimento YYYY-MM-DD - titulo curto

- Objetivo:
- Configuracao:
- Dados:
- Metricas:
- Resultado:
- Interpretacao:
- Arquivos gerados:
