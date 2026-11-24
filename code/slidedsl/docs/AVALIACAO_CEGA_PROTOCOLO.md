# Avaliação cega de qualidade: protocolo (registrado em 24/11/2026, antes das respostas)

Responde à P6 do `docs/PLANO_TCC.md`: além de válidos, os slides são bons?

**Página da avaliação:** https://claude.ai/artifact/PwGfmne7oXP6AZV6qhhYfz (privada; compartilhada só com os avaliadores).

**Preparação:** `scripts/avaliacao_cega_preparar.py` (semente 20261124).
- Os dados ficam em `outputs/avaliacao_cega/`, fora do git.
- O gabarito código → modelo fica só em `gabarito.json`, que não é publicado.

## Material

Foram usadas 12 apresentações de 5 slides: 4 temas (ciclo da água, sono e estudos, Git, energia solar) × 3 modelos. Todas foram geradas na bancada do app, nas mesmas condições:

| Item | Valor |
|---|---|
| Pedido | nível detalhado |
| Documento-fonte | o mesmo para os 3 modelos |
| Semente | 11 |
| Pipeline | `gramatica_limites+frases` |
| Contexto | 4096 |

| Condição | Execução |
|---|---|
| 1.7B | `outputs/teste6_17b_dica` |
| 0.6B | `outputs/teste7_06b_dica` |
| 0.6B LoRA | `outputs/teste8_lora` |

Os slides são renderizados pelo mesmo compilador. Assim, o visual é igual entre as condições e só o conteúdo varia. Os avaliadores veem códigos aleatórios (A103, A145…) e não sabem o modelo.

## Avaliadores

São 3 colegas voluntários, maiores de 18 anos, sem dado pessoal coletado.
- **Consentimento:** é registrado na própria página, e o avaliador pode parar a qualquer momento.
- **Tarefa:** cada um avalia as 12 apresentações, numa ordem sorteada por avaliador (cerca de 30 minutos).

## Rubrica (por apresentação)

1. **Clareza:** "Dá para entender o assunto só pelos slides?" Escala de 1 a 5.
2. **Erro:** "Você notou alguma afirmação errada ou inventada?" Respostas: não / sim (com o trecho) / não sei.
3. **Repetição:** "Os slides repetem a mesma ideia?" Respostas: não / um pouco / muito.
4. **Utilidade:** "Usaria como ponto de partida para um seminário sobre o tema?" Escala de 1 a 5.
5. **Comentário:** opcional.

O tempo gasto em cada apresentação é registrado.

## Hipóteses (definidas antes)

- **H1.** O 0.6B LoRA tem clareza e utilidade maiores que o 0.6B sem treino. Na bancada, o LoRA teve 22/24 apresentações completas contra 8/24, e 13 textos repetidos contra 117.
- **H2.** O 0.6B LoRA não é pior que o 1.7B em clareza e utilidade, mas tem mais afirmações marcadas como erradas. A bancada mostrou menos fatos usados pelo LoRA e conteúdo mais raso.
- **H3.** A repetição percebida segue a ordem 0.6B > 1.7B ≈ 0.6B LoRA, como na contagem automática de textos repetidos.

## Análise

**Unidade de análise:** a média dos 3 avaliadores por apresentação. São 12 apresentações, ou seja, 4 temas pareados por condição.

**Concordância entre avaliadores:** alfa de Krippendorff ordinal para clareza e utilidade. Valores abaixo de 0,4 serão relatados como concordância fraca, e as médias serão lidas com cautela.

**Comparação das 3 condições:** teste de Friedman sobre os 4 temas, para clareza e utilidade. Pares com Wilcoxon (H1: LoRA × 0.6B; H2: LoRA × 1.7B). Com 4 temas o poder é baixo, então os resultados são relatados como descritivos.

**Erro e repetição:** proporção de "sim" e de "muito" por condição, contada por avaliação (36 por condição).

**Ressalvas registradas:**
- São 4 temas e 1 semente, com estudantes como juízes.
- A avaliação mede impressão de qualidade, não aprendizagem.
- O documento-fonte é opcional para o avaliador, então nem todo erro de conteúdo será notado.

**Script:** `scripts/avaliacao_cega_analisar.py <pasta com as respostas exportadas>`.

## Coleta

A página grava uma resposta por avaliador em `respostas/<id>`.
- **Quem lê:** só o dono do artefato. As regras da página impedem que um avaliador veja a resposta de outro (conferido em 24/11).
- **Para gravar:** o avaliador precisa ser convidado por e-mail como Editor.
- **Sem gravar:** a página mostra no fim um código (`SLDA1:…`). O avaliador manda esse código, e o dono o cola no painel de acompanhamento da própria página.
