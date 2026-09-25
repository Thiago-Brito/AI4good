# Ordered GNN (ICLR 2023) — entrega completa

Artigo: **Ordered GNN: Ordering Message Passing to Deal with Heterophily and
Over-smoothing**, Song, Zhou, Wang e Lin, ICLR 2023.

- [Artigo online](https://openreview.net/forum?id=wKPmPBHSnT6)
- [Relatório no Overleaf](https://www.overleaf.com/project/6a920ba2c3f0c914aa7c7185) (acesso conforme as permissões do projeto)
- [PDF original](../../academy/papers/artigo-overleaf/outputs/ordered-gnn/artigo-original-2023.pdf)
- [Relatório técnico local](../../academy/papers/artigo-overleaf/outputs/ordered-gnn/samplepaper.pdf)
- [Código oficial](https://github.com/LUMIA-Group/OrderedGNN), commit
  `80c375896efa5ee2ae6f52b735c70753e3243f4e`, licença MIT preservada.

No GitHub ficam código, instruções e registros textuais. As pastas `outputs/`,
`.venv/` e `vendor/` são locais e não são versionadas. Os links de PDF acima
funcionam no workspace completo; o relatório é mantido em um repositório Overleaf
separado. Em um clone novo, instale o ambiente e gere os checkpoints com
`train.py --name main` antes de abrir a demonstração padrão. Seus links de PDF
também exigem os arquivos do projeto Overleaf nos caminhos documentados.

## Mostrar a entrega

Na raiz do workspace:

```powershell
code/paper-gnn/.venv/Scripts/python.exe code/paper-gnn/demo.py
```

Abrir **http://127.0.0.1:8765**. A página mostra o dataset, os vizinhos e atributos
reais, os resultados agregados e links para os PDFs. Cada clique executa os dois
checkpoints. Exemplos de teste: 1709 (ambos acertam), 1797 (só a base acerta),
1713 (só a modificada acerta), 1708 (ambos erram), na semente 42.

Inferência sem navegador:

```powershell
code/paper-gnn/.venv/Scripts/python.exe code/paper-gnn/infer.py --node 1713
```

O resultado inclui classe, probabilidades, atributos, vizinhos e hash dos pesos.
O terminal mantém os códigos 0 a 6. A tela mostra os nomes dos assuntos,
verificados contra os atributos dos 2.708 documentos no Cora original.
Veja `ENTENDA_O_CODIGO.md` para uma explicação do começo ao fim e
`verify_categories.py` para repetir essa correspondência.

## Resultados realmente executados

Cora completo: 2.708 nós, 1.433 atributos, 7 classes, 10.556 arestas direcionadas.
Split Planetoid `full`: 1.208 treino / 500 validação / 1.000 teste.
Treinamento **transdutivo**: atributos e arestas de todos os nós participam do
forward; apenas rótulos dos nós de treino entram na perda de treinamento.

| Modelo | Parâmetros | Acurácia de teste | F1 macro |
| --- | ---: | ---: | ---: |
| Ordered GNN base, largura 64 | 99.223 | 87,23% ± 0,78 pp | 86,19% ± 0,73 pp |
| Extensão multiescala | 174.344 | 87,10% ± 0,26 pp | 86,00% ± 0,22 pp |

Média e desvio padrão amostral de três sementes (42, 43 e 44), na mesma divisão.
**Não houve ganho médio demonstrado.** A variante adiciona gates independentes,
quatro FFNs residuais e atenção sobre cinco profundidades. Foi treinada do zero.
Os resultados são do protocolo compacto local, não os números publicados.

## Evidências de treinamento

- `outputs/dataset/manifest.json`: contagens e SHA-256 dos oito arquivos brutos.
- `outputs/dataset/Cora/raw/`: dados baixados do distribuidor Planetoid.
- `outputs/dataset/data.pt`: tensores de atributos, rótulos, arestas e máscaras.
- `outputs/dataset/split.json`: índices exatos de cada divisão.
- `outputs/main/protocol.json`: protocolo e hashes de código anteriores ao treino.
- `outputs/main/{original,modified}-seed{42,43,44}/initial.pt`: pesos iniciais.
- `model.pt`: melhor checkpoint por perda de validação; `history.csv`: curva real.
- `metrics.json`: métricas, matriz de confusão, norma das mudanças dos pesos,
  tempo, hash do checkpoint e verificação de recarga/inferência.
- `predictions.csv`: previsões e probabilidades dos 2.708 nós, identificados por split.
- `outputs/main/summary.json`: agregação das três sementes.
- `outputs/demo-inference.json`: resposta real da demonstração para o nó 1713.
- `outputs/serialization-check-incomplete/`: tentativa interrompida por formato de
  metadado do checkpoint. Não entra nos resultados; o problema foi corrigido antes
  de executar integralmente a comparação em `main/`.

Esses registros sustentam a auditoria local; não equivalem a certificação externa.

## Instalar em outra máquina

Python 3.12, CPU. Na pasta `code/paper-gnn`:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install torch==2.14.0 --index-url https://download.pytorch.org/whl/cpu
.venv/Scripts/python.exe -m pip install -r requirements.txt
git clone https://github.com/LUMIA-Group/OrderedGNN.git vendor/OrderedGNN
git -C vendor/OrderedGNN checkout 80c375896efa5ee2ae6f52b735c70753e3243f4e
.venv/Scripts/python.exe -m unittest discover -p test_models.py
.venv/Scripts/python.exe train.py --name reproducao
.venv/Scripts/python.exe infer.py --run reproducao --node 1713
```

O primeiro treino baixa o dataset; depois ele é reutilizado localmente.
`requirements-lock.txt` registra o ambiente completo; as dependências de inspeção
de PDF/navegador são opcionais para treinar e inferir. A execução não sobrescreve
uma pasta de experimentos existente. Para outra execução, usar outro `--name`.

## O que foi adaptado

- `original_model.py`: cópia do módulo oficial, somente import da camada alterado.
- `ordered_layer.py`: substitui infraestrutura antiga de agregação por matriz
  esparsa normalizada. Teste de saídas/gradientes usa o forward original no caminho
  COO. O caminho antigo `SparseTensor` não foi certificado como equivalente.
- Soma cumulativa segue o código oficial, da esquerda para a direita; PDF usa
  notação de direção reversa. A divergência é declarada no relatório.
- Protocolo local: largura 64/grupos 16 em vez de 256/64 do YAML de quatro camadas;
  400 épocas/paciência 70 em vez de 2.000/200; seleção por perda de validação em
  vez de acurácia; Adam com regularização comum para todos os parâmetros.
- Todos os parâmetros, incluindo normalização da entrada, são treinados. O
  agrupamento oficial com duas taxas de regularização omite essa normalização.
- A extensão mistura canais; não se afirma preservar a teoria de ordenação original.

## Organização e revisão

`models.py`: extensão; `train.py`: experimento; `data.py`: dados e manifesto;
`infer.py`: inferência real; `demo.py`/`demo.html`: apresentação no navegador;
`report_assets.py`: gráficos e tabelas derivados. Fontes no `refs/` do relatório.

```powershell
.venv/Scripts/python.exe report_assets.py
.venv/Scripts/python.exe audit.py
```

Na pasta `academy/papers/artigo-overleaf`, compilar duas vezes:

```powershell
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=outputs/ordered-gnn samplepaper.tex
```

A versão anterior Heart Disease foi preservada em
`outputs/ordered-gnn/relatorio-heart-anterior.tex`, relativo ao relatório.
O texto atual descreve a nova entrega. Não foi enviado ao Overleaf remoto.

Revisão final: `outputs/audit.json` verifica os seis modelos, hashes e métricas
recalculadas; `outputs/delivery-inspection.json` registra teste de navegador,
links PDF, inferência e layout móvel. Imagens das páginas e da demonstração estão
em `outputs/ordered-gnn/`, relativo ao relatório. Para repetir a inspeção visual,
instalar `playwright` e `pymupdf`, manter a demonstração ativa e executar
`inspect_delivery.py` (usa o Edge local).
