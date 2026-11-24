# Avaliação cega de qualidade: protocolo (registrado em 24/11/2026, antes das respostas)

Responde à P6 do `docs/PLANO_TCC.md`: além de válidos, os slides são bons?

**Página da avaliação:** https://claude.ai/artifact/PwGfmne7oXP6AZV6qhhYfz (privada; compartilhada só com os avaliadores).

**Preparação:** `scripts/avaliacao_cega_preparar.py` (semente 20261124).
- Os dados ficam em `outputs/avaliacao_cega/`, fora do git.
- O gabarito código → modelo fica só em `gabarito.json`, que não é publicado.

## Material (revisado em 24/11, antes de qualquer resposta: entrou um sistema externo)

15 apresentações de 5 slides: 4 temas (ciclo da água, sono e estudos, Git, energia solar) × 4 condições.
Em todas, a entrada é a mesma: o pedido (nível detalhado), o documento-fonte e 5 slides.

| Condição | O que é | Origem |
|---|---|---|
| celular 0.6B LoRA | app, Qwen3 0.6B destilado | `outputs/teste8_lora` (semente 11) |
| celular 1.7B | app, Qwen3 1.7B | `outputs/teste6_17b_dica` (semente 11) |
| PC 4B | fluxo completo do PC (modo gramática), Qwen3-4B-Instruct-2507 | `scripts/avaliacao_pc_4b.py` |
| externo GPT-4.1-mini | IA comercial escrevendo o PowerPoint direto (python-pptx, prompt do Teste 2), mostrado como sai pelo LibreOffice | `scripts/avaliacao_externo_gpt.py` |

**Regra das sementes (definida antes de gerar a condição PC 4B):**
- usa-se a semente 11;
- se a apresentação for inválida, tentam-se as sementes 12 e 13;
- fica a primeira válida, e as falhas são registradas.

**Resultado da regra:**
- No tema água, o PC 4B falhou nas 3 sementes, sempre por rótulo de comparação acima de 48 caracteres (A005). O fluxo do PC ainda não tem os limites do compilador na gramática, que o app tem.
- Por isso a combinação água × PC 4B fica fora: são 15 apresentações, e a falha entra nos resultados.
- O externo gerou 4/4 na primeira tentativa (cerca de 10 mil tokens, ~US$ 0,01).

**Renderização e visual:**
- As três condições SlideDSL são renderizadas pelo mesmo compilador.
- A externa tem o visual que o modelo escreveu: o modelo padrão do python-pptx, com texto em tópicos.
- Os avaliadores podem reconhecer a externa pelo visual. A página pede que avaliem o conteúdo, e isso é uma limitação registrada.
- Os códigos (A103, A145…) são aleatórios.

## Avaliadores

São 3 colegas voluntários, maiores de 18 anos, sem dado pessoal coletado.
- **Consentimento:** é registrado na própria página, e o avaliador pode parar a qualquer momento.
- **Tarefa:** cada um avalia as 15 apresentações, numa ordem sorteada por avaliador (cerca de 40 minutos).

## Rubrica (por apresentação)

1. **Clareza:** "Dá para entender o assunto só pelos slides?" Escala de 1 a 5.
2. **Erro:** "Você notou alguma afirmação errada ou inventada?" Respostas: não / sim (com o trecho) / não sei.
3. **Repetição:** "Os slides repetem a mesma ideia?" Respostas: não / um pouco / muito.
4. **Utilidade:** "Usaria como ponto de partida para um seminário sobre o tema?" Escala de 1 a 5.
5. **Comentário:** opcional.

O tempo gasto em cada apresentação é registrado.

## Hipóteses (definidas antes das respostas)

- **H1.** O externo (modelo comercial grande) tem utilidade e clareza maiores que as condições do celular. O que se quer medir é a distância, não a vitória.
- **H2.** O 0.6B LoRA não é pior que o 1.7B em clareza e utilidade, mas tem mais afirmações marcadas como erradas. A bancada mostrou menos fatos usados pelo LoRA.
- **H3.** O PC 4B tem clareza e utilidade maiores que o 1.7B do celular, porque é um modelo maior e o fluxo do PC tem verificações de cobertura e sustentação.
- **H4.** O externo tem mais repetição e textos mais longos por slide, porque escreve os tópicos sem os limites do compilador.

## Análise

**Unidade de análise:** a média dos 3 avaliadores por apresentação. São 15 apresentações: 4 temas por condição, 3 no PC 4B, pareadas por tema.

**Concordância entre avaliadores:** alfa de Krippendorff ordinal para clareza e utilidade. Valores abaixo de 0,4 serão relatados como concordância fraca, e as médias serão lidas com cautela.

**Comparação das 4 condições:** teste de Friedman sobre os temas completos (3, porque água × PC 4B ficou fora), para clareza e utilidade. Pares por tema com teste do sinal (H1: externo × LoRA e externo × 1.7B; H2: LoRA × 1.7B; H3: PC 4B × 1.7B). Com 3 ou 4 temas o poder é baixo, então os resultados são relatados como descritivos.

**Erro e repetição:** proporção de "sim" e de "muito" por condição, contada por avaliação (12 por condição; 9 no PC 4B).

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
