# Planos para o último mês do TCC

Prazo considerado: **cerca de 4 semanas, de 13/10 a 13/11/2026**. Este documento apresenta três
caminhos possíveis para decidir com o orientador. A avaliação que motiva os planos está em
[AVALIACAO_DO_TCC.md](AVALIACAO_DO_TCC.md).

> **Regra para qualquer plano:** congelar o código no início da semana 2. Depois disso, só correções
> de erro. Mudar o código durante os experimentos foi o principal motivo de os experimentos atuais
> não serem comparáveis entre si.

---

## Visão geral

| | Plano A — Forma | Plano B — Democratização (recomendado) | Plano C — Qualidade do conteúdo |
|---|---|---|---|
| Tese | A GLC garante forma e editabilidade em SLMs locais | SLM local + GLC chega perto de um LLM pago, com custo e hardware acessíveis | Melhorar o conteúdo gerado |
| Liga com a motivação? | Parcialmente | **Sim, diretamente** | Pouco |
| Novos experimentos | GBNF × JSON; repetição do lote multitemas | A + comparação com LLM grande + hardware + modelos menores | Novos verificadores e avaliação |
| Precisa de algo externo? | Não | Chave de API paga (pouco uso) e acesso a uma máquina comum | Não |
| Risco de não terminar | Baixo | Médio | **Alto** |
| Ganho para a defesa | Médio | **Alto** | Incerto |

**Recomendação:** seguir o **Plano B**, tendo o **Plano A** como versão mínima de segurança. O A é
um subconjunto do B: se o cronograma apertar, cortam-se as partes extras do B e sobra o A completo.
O Plano C não é recomendado para um mês, porque exige mexer muito no código e o resultado é incerto.

---

## Plano A — Forma (mínimo seguro)

**Tese:** a gramática e o compilador garantem validade estrutural e editabilidade para saídas de SLMs
locais; o conteúdo exige outros mecanismos.

**Experimentos:**
1. **GBNF × JSON × direto** com o Qwen3 4B, nos mesmos pedidos e seeds. Testa diretamente a geração
   restrita pela gramática, que nunca rodou com modelo real.
2. **Repetir o lote multitemas (12 pedidos) com o código final**, com 3 seeds, para medir o efeito
   das correções feitas depois do lote (títulos truncados, sustentação, citações, cobertura).
3. **Avaliação humana mínima:** 3 a 5 pessoas, 12 a 24 decks, usando o formulário já pronto
   (`docs/AVALIACAO_HUMANA_CONTEXTUAL.md`).

**Entregáveis:** artigo atualizado, tabelas novas, slides da defesa.

## Plano B — Democratização (recomendado)

Tudo do Plano A, mais:

4. **Comparação com um LLM grande pago** (por exemplo, GPT ou Claude), nos mesmos 12 pedidos, com o
   mesmo fluxo SlideDSL. Mede quanto se perde ao usar o modelo pequeno.
5. **Teste de hardware:** rodar uma amostra numa máquina comum (só CPU ou notebook sem GPU dedicada),
   medindo tempo por deck e memória.
6. **Modelos menores:** repetir uma amostra com modelos de ≈1B e 1,5B parâmetros.
7. **Custo por deck:** local (tempo e energia estimada) × API (tokens multiplicados pelo preço oficial
   do provedor na data do experimento).

**Pergunta que o Plano B responde:** um SLM local guiado por uma GLC gera apresentações válidas e
editáveis com qualidade próxima à de um LLM pago, a custo e requisitos de hardware acessíveis?

## Plano C — Qualidade do conteúdo (não recomendado agora)

Atacar os problemas de conteúdo: verificador de sustentação independente (outro modelo), controle de
cobertura dos tópicos pedidos, correção do roteiro (hoje ele mostra ao modelo o texto de apenas 8
fatos). É o problema mais interessante cientificamente, mas exige desenvolvimento novo e não cabe com
segurança em um mês junto com a escrita. Fica como trabalho futuro.

---

## Cronograma sugerido (Plano B)

| Semana | Datas | Tarefas | Corte se atrasar |
|---|---|---|---|
| 1 | 13–19/10 | Decidir o plano com o orientador. Definir os 12 pedidos e o protocolo (seeds, parâmetros, métricas). Preparar o llama.cpp com o modelo em GGUF e fazer um teste curto do modo GBNF. Conseguir a chave de API e a máquina comum. **Congelar o código no fim da semana.** | — |
| 2 | 20–26/10 | Rodar os experimentos: GBNF × JSON × direto (Qwen3 4B, 3 seeds); LLM grande; modelos menores; teste em CPU. Salvar tudo em pastas novas de `outputs/`. | Cortar modelos menores |
| 3 | 27/10–02/11 | Avaliação humana (avaliadores sem saber qual configuração gerou cada deck). Montar tabelas e gráficos. | Reduzir para 3 avaliadores e 12 decks |
| 4 | 03–13/11 | Atualizar o artigo (introdução, metodologia, resultados, conclusão). Fazer os slides da defesa. Revisão do orientador. | — |

**Estimativa de tempo de máquina** (aproximada, com base no lote multitemas, que levou de 144 a 266 s
por deck numa RTX 3060):

- GBNF × JSON × direto: 12 pedidos × 3 seeds × 3 modos ≈ 108 decks ≈ 5 a 8 horas;
- modelos menores: tendem a ser mais rápidos que o 4B;
- em CPU, o tempo por deck deve ser bem maior; medir com uma amostra pequena (2 a 3 pedidos);
- LLM pago: tempo de rede; custo a calcular pelos tokens registrados.

Os experimentos podem rodar à noite. O gargalo real é a semana 3 (pessoas) e a semana 4 (escrita).

## Riscos e como lidar

| Risco | Plano de contingência |
|---|---|
| O modo GBNF falha no llama.cpp (versão, gramática não aceita) | Registrar a falha como resultado e seguir com JSON × direto |
| Sem chave de API ou orçamento | Fazer o Plano A completo; citar a comparação com LLM como trabalho futuro |
| Poucos avaliadores disponíveis | 3 avaliadores e 12 decks já permitem uma análise descritiva |
| SearXNG ou Docker instável (aconteceu no lote anterior) | Gerar e salvar os dossiês antes e reutilizá-los em todas as configurações (`--dossie`) — isso também deixa a comparação mais justa |
| Falta de espaço em disco (aconteceu no lote anterior) | Conferir o espaço livre antes de cada lote |

## Perguntas para decidir com o orientador

1. Qual plano seguimos: A, B ou um meio-termo?
2. A motivação deve ser reformulada de "indisponibilidade da IA" para "dependência de fornecedores"?
3. É aceitável usar uma API paga (com custo baixo) como referência de comparação?
4. Quantos avaliadores e quais critérios são suficientes para a avaliação humana?
5. Precisa de teste estatístico, ou basta análise descritiva com as limitações declaradas?
6. Os onze experimentos atuais entram todos no texto, ou só E1, E3 e E11, com os demais como
   "evolução do sistema"?
7. Formato final: o artigo em Markdown serve como base, ou é preciso passar para o modelo da
   instituição (ABNT/LaTeX/Word)?
8. Qual a data exata de entrega e de defesa?
