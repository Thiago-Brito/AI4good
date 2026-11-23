# Avaliação do TCC e proposta de enquadramento

Documento para a conversa com o orientador. Resume o estado atual do SlideDSL (13/10/2026), os
pontos fortes e fracos e uma proposta de reformulação da motivação. Os detalhes técnicos estão em
[../artigo/ARTIGO_CIENTIFICO_SLIDEDSL.md](../artigo/ARTIGO_CIENTIFICO_SLIDEDSL.md) e as lacunas em
[../artigo/LACUNAS_DA_PESQUISA.md](../artigo/LACUNAS_DA_PESQUISA.md).

---

## 1. A ideia original

> As IAs de ponta estão cada vez mais caras e concentradas. É preciso democratizá-las. Para isso,
> o trabalho usa modelos de linguagem pequenos (SLMs), executados localmente, junto com uma gramática
> livre de contexto (GLC), para criar apresentações de slides.

## 2. O que o projeto já demonstra

| Resultado | Evidência |
|---|---|
| A GLC e o compilador impedem que saídas inválidas virem slides e geram diagnósticos localizados | Todos os experimentos (E1–E11) |
| Tirar a geometria do modelo foi a decisão de maior efeito | E3: exportação estrita de **0/10 → 10/10** com o mesmo Qwen3 4B |
| O fluxo completo (pesquisa + SlideDSL Alto) funciona de ponta a ponta com um modelo de 4B | E11: **12/12** decks de seis slides em quatro temas |
| O PPTX gerado é editável (objetos nativos, não imagens) | Inspeção do XML dos PPTX |
| Engenharia sólida | 388 testes Python, editor visual, auditoria com hashes |

## 3. Pontos fortes

- **Ideia central clara:** "o modelo propõe, o compilador decide".
- **Contribuição original:** duas GLCs em camadas (SlideDSL Alto para a intenção, SlideDSL 1.1 para a
  geometria).
- **Um resultado forte e fácil de mostrar** (0/10 → 10/10).
- **Honestidade:** os fracassos estão documentados e preservados (0/5 na geração direta, reparos sem
  ganho, títulos truncados, fatos usados com outro sentido).

## 4. Pontos fracos

1. **Evidência pequena:** de 1 a 5 repetições por configuração, praticamente um só modelo (Qwen3 4B) e
   nenhum teste estatístico. Hoje é um estudo exploratório.
2. **Nenhuma avaliação humana.** O trabalho mostra que os slides são *válidos*, não que são *bons*.
3. **A geração restrita pela gramática (GBNF/llama.cpp) nunca rodou com modelo real.** Todos os
   experimentos usaram JSON Schema no Ollama. É o elo teórico mais citado do trabalho.
4. **Escopo espalhado:** onze experimentos com protocolos diferentes; parece mais um diário de
   desenvolvimento do que uma pergunta fechada.
5. **Conteúdo ainda fraco:** títulos cortados, fatos descontextualizados, tópicos do pedido omitidos.
6. **A motivação (democratização) não é medida.** Não há medida de custo, de hardware mínimo nem
   comparação com um modelo grande.

## 5. O problema da motivação atual

A pergunta "quando a IA não vai mais estar disponível para todos?" é especulativa e fácil de atacar:
o próprio AI Index 2025 (citado no projeto) mostra o custo de inferência caindo mais de 280 vezes em
cerca de 18 meses.

**Proposta:** trocar "indisponibilidade" por **dependência**, que é sustentável com fatos:

> O acesso à IA de ponta depende de poucas empresas, de APIs pagas, de conexão e das políticas
> desses fornecedores. Este trabalho investiga se modelos pequenos, abertos e locais, combinados com
> uma linguagem formal, conseguem realizar uma tarefa útil — gerar apresentações editáveis — sem essa
> dependência.

Argumentos que já têm fonte no projeto (`docs/REFERENCIAS.md`):

- custo de treino concentrado em poucas empresas (AI Index 2024; Strubell et al., 2019);
- pesos abertos permitem execução local e auditoria (Kapoor et al., 2024);
- eficiência como critério de avaliação (Schwartz et al., 2020, "Green AI");
- privacidade (nada sai da máquina) e custo zero por uso.

## 6. O que falta para ligar a motivação aos resultados

Hoje os experimentos provam: **a GLC controla a forma do que o SLM gera.**
Eles **não** provam: **que isso democratiza alguma coisa.**

Para fechar essa ponte, faltam quatro medidas:

| # | Medida | Pergunta que responde |
|---|---|---|
| 1 | Comparar SLM + GLC com um LLM grande pago, nos mesmos pedidos | Quanto se perde ao usar um modelo pequeno local? |
| 2 | Rodar numa máquina comum (só CPU ou notebook) e medir tempo e memória | Funciona em computador acessível? |
| 3 | Estimar custo por deck: local × API paga | Qual a economia real? |
| 4 | Testar modelos menores (≈1B, 1,5B) além do 4B | Até onde dá para reduzir o modelo? |

## 7. Proposta de título e pergunta de pesquisa

**Título (sugestão):**
*Linguagens formais como compensação para modelos de linguagem pequenos: geração local de
apresentações editáveis com SlideDSL*

**Pergunta de pesquisa (sugestão):**
Um modelo de linguagem pequeno, executado localmente e guiado por uma gramática livre de contexto,
consegue gerar apresentações válidas e editáveis com qualidade próxima à de um modelo grande pago, com
custo e requisitos de hardware acessíveis?

**Como as peças se encaixam:**

| Peça | Papel na tese |
|---|---|
| SLM local | meio de democratizar: barato, offline, aberto |
| Fraquezas do SLM | erra sintaxe, geometria e conteúdo (E1: 0/5 válidos) |
| GLC + compilador | compensa as fraquezas de forma e geometria (E3: 0/10 → 10/10) |
| O que falta medir | se o resultado é bom o bastante, e a que custo e em qual hardware |

## 8. Avaliação geral

O trabalho já passa como está: a engenharia está bem acima da média de um TCC, e a documentação é
honesta. Hoje, porém, ele é mais forte como engenharia do que como pesquisa. Com a avaliação humana,
o teste do modo GBNF e a comparação com um modelo grande, a motivação de democratização deixa de ser
só um argumento e passa a ser um resultado medido.
