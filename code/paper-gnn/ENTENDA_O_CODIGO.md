# Comece aqui: o que este programa realmente faz?

Ele tenta responder: **qual é o assunto deste documento científico?**
Existem sete respostas possíveis, como Teoria, Redes neurais e Algoritmos genéticos.
Chamamos cada resposta possível de **classe**, ou simplesmente **categoria**.

## Um exemplo real, do começo ao fim

Na demonstração, escolha **1708 — As duas erram**.

1. `1708` é a posição de um documento dentro do Cora, nosso conjunto de dados.
   Não é um assunto, uma nota ou uma quantidade de acertos.
2. O programa busca os indicadores de palavras desse documento e suas ligações
   com outros documentos. Ele não abre um PDF nem recebe o texto completo.
3. As redes calculam sete probabilidades: uma para cada assunto.
4. Ambas escolhem **Teoria**, que tem a maior probabilidade em suas saídas.
5. Consultamos o dataset para conferir: a categoria registrada é **Redes neurais**.
6. A tela mostra **Errou este documento**. Ter alta probabilidade não garantiu acerto.

O código usa números internos. As correspondências verificadas são:

| Código | Assunto | Explicação curta |
| ---: | --- | --- |
| 0 | Teoria | Fundamentos matemáticos do aprendizado de máquina |
| 1 | Aprendizado por reforço | Aprender ações com recompensas |
| 2 | Algoritmos genéticos | Buscar soluções com mecanismos inspirados na evolução |
| 3 | Redes neurais | Aprender com unidades conectadas |
| 4 | Métodos probabilísticos | Representar dados e incerteza por probabilidades |
| 5 | Aprendizado baseado em casos | Aproveitar exemplos ou casos anteriores |
| 6 | Aprendizado de regras | Aprender condições e regras de decisão |

**Como sabemos esses nomes?** Comparamos os 1.433 indicadores de palavras de
cada documento com `cora.content`, da distribuição original do Cora. Os 2.708
documentos tiveram correspondência de categoria sem ambiguidade.
`verify_categories.py` repete a verificação; o resultado está em
`outputs/dataset/class-label-verification.json`. Não adivinhamos a ordem dos códigos.

## E as citações?

Exemplo fictício, apenas para explicar: um artigo B menciona um artigo A em suas
referências bibliográficas. Dizemos que **B cita A**. Isso cria uma ligação.
No programa, documentos são nós e citações fornecem as arestas do grafo.
A representação utilizada permite trocar informações nos dois sentidos.
Uma ligação não garante que os documentos tenham o mesmo assunto.

## Onde acontece cada parte no código?

| Pergunta | Arquivo / trecho | Leitura em português |
| --- | --- | --- |
| De onde vêm os exemplos? | `data.py`, `load_data()` | Carrega documentos, atributos, categorias e ligações |
| Como a rede do artigo é organizada? | `original_model.py`, `GONN.forward()` | Transforma atributos, passa pelas camadas e produz sete pontuações |
| Onde entra a vizinhança? | `ordered_layer.py`, `torch.sparse.mm(adjacency, x)` | Calcula a média das informações dos documentos ligados |
| O que o gate faz? | `ordered_layer.py`, `x * expanded + m * (1 - expanded)` | Combina informação própria com informação dos vizinhos |
| Como ela aprende? | `train.py`, `loss.backward()` e `optimizer.step()` | Calcula como mudar os pesos e aplica a mudança |
| Como guardamos o aprendizado? | `train.py`, `torch.save(...)` | Salva os pesos em um checkpoint |
| Como ela responde depois? | `infer.py`, `Predictor.predict()` | Carrega os pesos e calcula a resposta sem retreinar |
| Como decide o assunto? | `infer.py`, `softmax()` e `argmax()` | Calcula probabilidades e escolhe a maior |
| Onde a tela fica mais legível? | `demo.html`, `CATEGORIES` e `renderModel()` | Traduz códigos e explica acerto ou erro |

O módulo oficial fica preservado para compará-lo com o código dos autores.
Este guia explica os arquivos sem alterar a matemática já treinada.

## Leia a inferência como uma receita

```python
# Exemplo didático das operações que já existem em infer.py:
saida = model(data.x, adjacency)       # Atributos + ligações; não recebe respostas.
pontuacoes = saida['x'][1708]          # Sete números para o documento escolhido.
probabilidades = pontuacoes.softmax(-1)
categoria_escolhida = probabilidades.argmax()
categoria_esperada = data.y[1708]      # Só para conferir a resposta, depois.
acertou = categoria_escolhida == categoria_esperada
```

Esse trecho é explicativo: `model`, `data` e `adjacency` precisam ser carregados
como em `Predictor`. Para executar de verdade, na raiz do workspace:

```powershell
code/paper-gnn/.venv/Scripts/python.exe code/paper-gnn/infer.py --node 1708
```

## Dois números diferentes: probabilidade e acurácia

- **Probabilidade individual:** a rede atribui, por exemplo, 93% a Teoria para
  um documento. Ela ainda pode estar errada. Não é uma garantia de correção.
- **Acurácia no conjunto:** contamos as respostas certas entre os 1.000 documentos
  de teste. A média entre três treinamentos da base foi 87,23%.

## O que mudou na segunda rede?

A base usa quatro rodadas de troca de informações e classifica a partir da última.
Em `models.py`, a variante adiciona controles separados por rodada, blocos que
transformam e somam informação (residuais) e uma combinação aprendida das cinco
representações: entrada + quatro rodadas. Os pesos de ambas foram aprendidos
separadamente, do zero. A variante não melhorou a acurácia média.

## O que mostrar para uma pessoa que nunca estudou IA?

1. Abra a demonstração e leia a pergunta do título.
2. Escolha “1709 — As duas acertam”: esperado e previsto são Algoritmos genéticos.
3. Escolha “1708 — As duas erram”: esperado é Redes neurais; ambas dizem Teoria.
4. Mostre que barras altas também aparecem em respostas erradas.
5. Só depois mostre a média de acertos dos 1.000 documentos e o código acima.
