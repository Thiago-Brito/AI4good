# Roadmap

## Entrega Heart Disease

- [x] Implementar MLP sobre grafo explicito, com feed forward e backpropagation.
- [x] Integrar download pelo kagglehub e leitura de CSV local.
- [x] Dividir treino/teste 80/20, remover duplicatas e padronizar pelo treino.
- [x] Visualizar treinamento e inferencia por camada com Streamlit/Matplotlib.
- [x] Exportar pesos, biases, historico, previsoes e metricas em outputs/.
- [x] Verificar gradientes por diferencas finitas, aprendizado XOR e isolamento da divisao.
- [x] Registrar execucao completa com a base real: 86,89% no teste, semente 42, 500 epocas.

## Animacao e tentativa de melhorar a acuracia

- [x] Animar ligacoes surgindo, piscando e apagando por camada, com retorno dos gradientes.
- [x] Adicionar pausa, reinicio, velocidade, consulta de pesos e download do replay em HTML.
- [x] Implementar Adam e L2 manualmente e busca opcional por validacao interna.
- [x] Verificar Adam, separacao da validacao e fluxo da interface com dados reais.
- [x] Registrar resultado: perda menor, acuracia 85,25%; sem ganho confirmado sobre 86,89%.

## Relatorio tecnico

- [x] Gerar figuras e metricas adicionais com report_assets.py usando os modelos e previsoes registrados.
- [x] Atualizar o relatorio LNCS no projeto artigo-overleaf com metodologia, harness, arquitetura e resultados.
