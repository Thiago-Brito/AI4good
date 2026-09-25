# Roteiro de apresentação — Ordered GNN / Cora

Duração sugerida: 8 a 10 minutos. Apresente o artigo e o relatório no Overleaf;
execute o código e a demonstração nesta máquina. O Overleaf compila o relatório,
enquanto a inferência Python roda localmente.

Se você ainda não entendeu classe, nó ou probabilidade, leia primeiro
`ENTENDA_O_CODIGO.md`. A demonstração agora mostra os assuntos por nome e inclui
exemplos prontos. Comece pelo botão “1709 · As duas acertam”; depois use
“1708 · As duas erram”: esperado **Redes neurais**, ambas respondem **Teoria**.

## Antes de começar

Abra o terminal PowerShell na raiz do workspace `ia`. Os comandos abaixo partem
dessa pasta. Deixe abertos:

1. Overleaf: https://www.overleaf.com/project/6a920ba2c3f0c914aa7c7185
2. Demonstração: http://127.0.0.1:8765
3. VS Code na pasta `code/paper-gnn/`.

Se a demonstração não abrir, execute e mantenha este terminal aberto:

```powershell
code/paper-gnn/.venv/Scripts/python.exe code/paper-gnn/demo.py
```

Se já estiver aberta, não é necessário iniciar outro servidor. Para os comandos
seguintes, use uma segunda aba de terminal.

## 1. Mostrar o artigo e a motivação — 1 minuto

Na demonstração, clique em **Artigo que apresenta o método (2023)**. Mostre a primeira página:
**Ordered GNN: Ordering Message Passing to Deal with Heterophily and
Over-smoothing**, Song e colaboradores, ICLR 2023. Mostre também a Tabela 1,
na qual aparece o Cora, e o link do código oficial na primeira página.

Fala sugerida:

> Escolhi um artigo de 2023 que utiliza uma GNN. Ela classifica documentos usando
> seus atributos e suas relações de citação. Minha pergunta foi se acrescentar
> processamento residual e uma combinação de diferentes profundidades melhoraria
> os resultados em um experimento local.

Explique o escopo:

> Executei a arquitetura disponibilizada pelos autores com adaptações documentadas
> para CPU e uma configuração compacta. Não estou afirmando que reproduzi todas
> as tabelas ou o ambiente original do artigo.

## 2. Mostrar o dataset e exemplos reais — 1 minuto

Na página principal, mostre as contagens do Cora: **2.708 documentos, 1.433
atributos, sete classes**. Nó = documento; aresta = relação de citação.

Escolha o documento **1713** e mostre **Veja de onde vêm as informações**, os vizinhos e a seção
expansível **Para conferir a execução**. Ela contém os índices e valores dos
atributos não nulos. São dados efetivamente usados no forward.

No VS Code, abra `outputs/dataset/manifest.json` e `outputs/dataset/split.json`,
relativos a `code/paper-gnn`. Mostre 1.208 nós de treino, 500 de validação e
1.000 de teste, além dos hashes dos arquivos brutos.

> O treinamento é transdutivo: as ligações e os atributos de todos os documentos
> ficam disponíveis, mas só os rótulos dos documentos de treino atualizam os
> pesos. Validação escolhe o checkpoint; teste mede o resultado final.

Os nomes das categorias foram verificados contra `cora.content` usando os
atributos dos 2.708 documentos. Os nomes das palavras não foram reconstruídos.
O sistema não lê o texto integral dos PDFs.

## 3. Mostrar o código da rede e a inferência — 2 minutos

Abra, nesta ordem:

| Arquivo | O que apontar |
| --- | --- |
| `original_model.py` | Classe `GONN` e seu `forward`: projeção de entrada, camadas do grafo, classificador |
| `ordered_layer.py` | `torch.sparse.mm`: agrega vizinhos; gate combina o nó com a mensagem recebida |
| `infer.py` | Carregamento de `model.pt`, `model.eval()` e `torch.inference_mode()` |

> O módulo da rede base veio do código oficial, com a importação da camada
> adaptada. A agregação foi portada e comparada com saídas e gradientes do
> caminho COO da camada oficial. Na inferência, carrego pesos já treinados e
> calculo a previsão sem atualizá-los.

Na demonstração, use os botões de exemplo ou **Pedir uma previsão às duas redes**:

| Nó | Classe real | Base | Modificada | O que demonstra |
| ---: | ---: | ---: | ---: | --- |
| 1709 | Algoritmos genéticos (2) | Algoritmos genéticos | Algoritmos genéticos | Ambas acertam |
| 1713 | Teoria (0) | Aprendizado baseado em casos | Teoria | A modificada corrige um erro |
| 1797 | Aprendizado por reforço (1) | Aprendizado por reforço | Métodos probabilísticos | A modificada também introduz erros |
| 1708 | Redes neurais (3) | Teoria | Teoria | Ambas podem falhar |

Esses exemplos usam os checkpoints da semente 42. Mostre as probabilidades,
não apenas o rótulo previsto. Cada clique executa um novo forward do grafo.

Se preferir demonstrar diretamente no terminal:

```powershell
code/paper-gnn/.venv/Scripts/python.exe code/paper-gnn/infer.py --node 1713
```

## 4. Comprovar o treinamento — 1 a 2 minutos

Abra a pasta `outputs/main/original-seed42/` no VS Code e mostre:

- `initial.pt`: pesos antes do treino; `model.pt`: checkpoint escolhido;
- `history.csv`: perdas e acurácias registradas por época;
- `metrics.json`: época selecionada e `parameter_l2_changes`, que registra
  quanto os parâmetros mudaram; hash do checkpoint e checagem de inferência;
- `predictions.csv`: previsões por nó e identificação do split.

Depois mostre as seis pastas: base e modificada, sementes 42, 43 e 44.

Execute a auditoria, que verifica os dados e checkpoints reais:

```powershell
code/paper-gnn/.venv/Scripts/python.exe code/paper-gnn/audit.py
```

Saída esperada: `passed: true`, `runs_verified: 6`. O script confere hashes,
recarrega os modelos e recalcula previsões, matriz de confusão, acurácia e F1.

> Não apresento somente uma imagem de treinamento. Entrego os dados, o protocolo,
> os pesos iniciais e finais, o histórico e um verificador executável.

Se pedirem um novo treinamento ao vivo, use um nome novo de experimento:

```powershell
code/paper-gnn/.venv/Scripts/python.exe code/paper-gnn/train.py --name apresentacao-ao-vivo --seeds 42
```

Esse comando treina os dois modelos do zero para a semente 42. O nome precisa
ser inédito: a proteção contra sobrescrita é intencional. O resultado ao vivo
não substitui a comparação principal de três sementes. Pode levar mais tempo
conforme a carga da máquina; não é necessário repetir durante toda apresentação.

## 5. Mostrar a mudança de arquitetura e o retreinamento — 1 minuto

Abra `models.py` e a classe `MultiScaleOrderedGNN`. Aponte:

1. `global_gating=False`: gates independentes por camada;
2. `feedforward` e `residual_norm`: quatro novos blocos residuais;
3. `depth_score` e `torch.stack(states, dim=1)`: combinação aprendida de cinco
   profundidades, substituindo a classificação apenas da última representação.

Mostre o diagrama das arquiteturas no relatório e a pasta
`outputs/main/modified-seed42/`, que contém seus próprios pesos e histórico.

> Alterei o caminho de processamento, não somente a taxa de aprendizagem.
> A rede passou de 99.223 para 174.344 parâmetros e foi treinada do zero.
> As três alterações foram avaliadas juntas; não isolei o efeito de cada uma.

## 6. Apresentar o relatório e a conclusão — 1 a 2 minutos

No Overleaf, abra `samplepaper.tex` e o PDF compilado. Mostre:

- motivação e artigo escolhido;
- dataset, protocolo e adaptações;
- diagrama das arquiteturas;
- tabela dos seis treinamentos e curvas;
- matrizes de confusão e quatro exemplos qualitativos;
- revisão assistida por IA, evidências e limitações.

| Modelo | Acurácia média | F1 macro médio |
| --- | ---: | ---: |
| Base | 87,23% ± 0,78 pp | 86,19% ± 0,73 pp |
| Modificada | 87,10% ± 0,26 pp | 86,00% ± 0,22 pp |

> A hipótese de melhora média não foi confirmada. A variante funcionou e foi
> retreinada, mas teve custo maior e acurácia média ligeiramente menor. A diferença
> é descritiva: não fiz um teste de significância. Os resultados se limitam ao
> Cora, uma divisão e três sementes.

Sobre a IA:

> O desenvolvimento e a revisão foram assistidos por IA. Conferi fontes e
> resultados com testes, hashes e execução real. Não uso “sem alucinações” como
> garantia absoluta: cada resultado apresentado tem evidência verificável.

## Respostas rápidas

- **“Base” significa o quê?** Dataset é a base de dados Cora; modelo base é a
  Ordered GNN usada como referência. São coisas diferentes.
- **É uma MLP?** Há camadas lineares dentro da arquitetura, mas o modelo é uma
  GNN porque usa as relações entre documentos para agregar informações.
- **Você está treinando ao clicar?** Não. O clique executa inferência com pesos fixos.
- **Melhorou?** Não na média das três sementes. Não escondemos o resultado negativo.
- **O relatório e o artigo são iguais?** Não. O artigo é dos pesquisadores de 2023;
  o relatório descreve a reprodução local e a modificação deste projeto.
- **O teste ficou totalmente invisível?** Não: atributos e arestas são conhecidos;
  os rótulos de teste não participam das atualizações dos pesos.
