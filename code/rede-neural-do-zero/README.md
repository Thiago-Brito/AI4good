# Rede Neural do Zero com Streamlit

Aplicacao didatica que implementa uma rede neural multicamada manualmente com
NumPy. Nao usa TensorFlow, PyTorch, Keras, scikit-learn nem biblioteca pronta
de redes neurais.

## Como executar

### Entrega Heart Disease: MLP baseada em grafo

Requer Python 3.10 ou superior e Streamlit 1.62 ou superior. Na pasta deste projeto:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app_heart.py
```

Clique em **Treinar rede** para baixar a base e acompanhar pesos, gradientes,
perda e acuracia. Tambem e possivel informar o caminho de um `heart.csv` local.
Depois, escolha uma amostra de teste e ative **Animar feed forward**.
Na inferencia, as ativacoes mudam e os pesos permanecem fixos.

Execucao registrada: arquitetura 13-8-4-1, 500 epocas, taxa 0.1 e semente 42:
**86.89% de acuracia de teste**. Das 1025 linhas, restaram 302 apos remover
duplicatas (241 treino / 61 teste). Veja `EXPERIMENTS.md` para os detalhes.
A interface permite outras arquiteturas; seu padrao usa 13-8-4-1, SGD sem L2.

### Ligacoes piscando e apagando

- **Apagar ligacoes inativas**: desenha as linhas progressivamente por camada e
  apaga ao concluir o pulso. Desmarque para manter o restante do grafo ao fundo.
- Azul/vermelho mostra os pesos durante o feed forward; pulsos amarelos voltam
  durante o backpropagation. Isso e uma representacao didatica do fluxo; todas
  as arestas continuam participando do calculo mesmo quando estao apagadas.
- **Segundos por camada** controla o ritmo; o painel tem Pausar e Reiniciar.
  Passe o mouse em uma aresta para consultar peso e ultima alteracao.
- Durante o treino, snapshots recebem pesos atuais. Ao terminar, o replay usa
  snapshots reais de epocas anteriores e uma amostra fixa. Os valores nao sao
  interpolados; a animacao das linhas e independente da velocidade do calculo.
- **Baixar animacao do treinamento** gera um HTML independente, sem internet.
  Na inferencia, somente os pulsos de ida sao mostrados e os pesos ficam fixos.

### Busca de parametros

Ative **Buscar configuracao por validacao** para comparar quatro configuracoes
de SGD/Adam, L2 e arquitetura. Adam e implementado manualmente. A selecao usa
menor entropia cruzada de validacao e paciencia de 60 epocas, limitada pelo
controle de epocas. A regularizacao corresponde a `BCE + L2/2 * soma(w²)`;
as metricas exibidas sao BCE sem a penalidade. Biases nao recebem L2.

Dos 241 exemplos de treino, 192 ajustam os candidatos e 49 validam; a escala
interna usa apenas os 192. Depois a rede e reinicializada e treinada nos 241,
com a configuracao e numero de epocas selecionados. A divisao externa de
241/61 fica identica. As escolhas e os indices internos entram em metrics.json.

Na verificacao com semente 42, a busca escolheu 13-16-8-1, Adam, taxa 0.003,
L2 0.01 e 47 epocas. A perda de teste caiu de 0.3515 para 0.3379, mas a
acuracia caiu de 86.89% para 85.25%. Portanto, a busca e opcional e **nao houve
ganho de acuracia confirmado** nessa tentativa. Veja EXPERIMENTS.md.

```powershell
python heart_mlp.py --tune --epochs 500
```

- `heart_mlp.py`: grafo dirigido aciclico com nos, arestas e listas de adjacencia.
  Os calculos percorrem as arestas; NumPy apenas processa o lote de amostras.
- Feed forward em ordem topologica: soma ponderada mais bias, tanh nas ocultas,
  sigmoid na saida. Backpropagation em ordem reversa, com entropia cruzada binaria
  e descida do gradiente em lote completo. Pesos inicializados por Xavier.
- Divisao estratificada e reproduzivel de 80% treino / 20% teste, arredondando o
  tamanho do teste para cima. Duplicatas exatas sao removidas antes da divisao.
- Padronizacao de cada coluna com media e desvio do treino; teste usa os mesmos
  parametros. Coluna constante usa divisor 1. Os codigos categoricos do CSV sao
  tratados numericamente nesta versao, sem one-hot encoding.
- Teste avaliado ao final, sem participar do gradiente. Limiar de classe: 0.5.
- Streamlit (`st.iframe`) e Canvas fornecem a visualizacao Heart Disease; a frequencia de
  atualizacao e configuravel. A tabela mostra peso, gradiente e ultima alteracao
  de cada aresta; o grafo mostra sinal e magnitude dos pesos e ativacoes nos nos.
- Cada execucao salva historico, metricas, matriz de confusao, previsoes, indices
  da divisao, hash do CSV, parametros de padronizacao e estado do grafo em `outputs/`.
  Os indices referem-se as linhas apos a remocao de duplicatas (base zero).

Execucao sem interface e verificacoes:

```powershell
python heart_mlp.py --epochs 500
python heart_mlp.py --csv outputs/dataset/heart.csv --epochs 500
python -m unittest discover -p test_heart_mlp.py
```

Fontes: [base solicitada](https://www.kaggle.com/datasets/johnsmith88/heart-disease-dataset)
e [API oficial do kagglehub](https://github.com/Kaggle/kagglehub), utilizada para
baixar os arquivos diretamente em `outputs/dataset/`.
O CSV local em outputs/dataset e reutilizado se existir.
Detalhes do [Adam](https://arxiv.org/abs/1412.6980) e da
[API st.iframe](https://docs.streamlit.io/develop/api-reference/text/st.iframe).

### Demonstracoes com dados sinteticos

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Versao com as conexoes se formando:

```powershell
python -m streamlit run app_conexoes.py
```

## O que e exibido

- epoca atual, perda e acuracia;
- ativacoes dentro dos neuronios;
- conexoes positivas e negativas com espessura proporcional ao peso;
- evolucao das metricas;
- fronteira de decisao aprendida pela rede.
