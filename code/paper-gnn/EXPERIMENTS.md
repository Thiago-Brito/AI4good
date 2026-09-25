# Experimento principal — 2026-09-25

Pergunta: gates independentes, FFNs residuais e fusão de profundidades melhoram
a classificação do Cora em relação à arquitetura Ordered GNN base?

Protocolo fixado em `outputs/main/protocol.json` antes dos seis treinos.
Dados Planetoid Cora/full: 1208/500/1000 nós de treino/validação/teste.
Arquiteturas com 64 canais e quatro camadas, três sementes pareadas, Adam 0.001,
weight decay 5e-6, limite 400 épocas, paciência 70, seleção pela perda de validação.
Teste avaliado após a escolha do checkpoint; sem seleção de hiperparâmetros pelo teste.

| Modelo | Semente | Época escolhida | Épocas executadas | Acurácia teste |
| --- | ---: | ---: | ---: | ---: |
| Base | 42 | 67 | 137 | 86,60% |
| Modificada | 42 | 44 | 114 | 87,30% |
| Base | 43 | 64 | 134 | 88,10% |
| Modificada | 43 | 44 | 114 | 87,20% |
| Base | 44 | 67 | 137 | 87,00% |
| Modificada | 44 | 44 | 114 | 86,80% |

Conclusão: diferença média -0,13 pp para a variante. Não demonstrou ganho médio.
Os 75,71% de parâmetros adicionais não se justificaram por melhora de acurácia
neste protocolo. Não extrapolar para outros splits ou concluir significância.

Verificações: quatro testes passaram; seis checkpoints recarregados com logits
idênticos e pesos preservados na inferência. Gráficos e tabelas derivam dos CSV/JSON.
A inferência HTTP do nó 1713 confirmou real=0, base=5 e modificada=0.

Não é reprodução integral do protocolo publicado. Ver diferenças no README e
relatório, incluindo largura, orçamento, regularização, critério de seleção e
adaptação das dependências antigas. Os três componentes da extensão não foram
avaliados isoladamente por ablação.
