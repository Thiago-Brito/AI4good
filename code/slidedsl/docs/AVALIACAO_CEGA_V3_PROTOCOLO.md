# Avaliação cega v3: assuntos novos (registrado em 27/11/2026, antes das respostas)

**Por que uma v3.** As avaliações v1 e v2 usam os 4 temas do banco de pedidos padrão: água, sono, Git e energia solar. O sistema foi ajustado ao longo do projeto com pedidos desses mesmos temas. A v3 usa 4 assuntos que nunca entraram em bancada, para ver se o resultado se mantém fora do material usado para ajustar o sistema. Ela também compara o app congelado para o artigo com a versão nova da leitura de documento (`docs/CELULAR_DOCUMENTO_26NOV.md`). A v1 e a v2 continuam como estão.

**Página da avaliação v3:** https://claude.ai/artifact/C8CMKn74XorFr4qvZkWd3D (privada; publicada em 27/11/2026, antes de qualquer resposta). Mesmas regras de acesso da v2: compartilhar como Editor, e cada avaliador lê e grava só a própria resposta.

**Preparação:**
- `scripts/avaliacao_cega_v3_documentos.py`: documentos e pedidos.
- `scripts/bancada_v3.sh`: celular, nas duas versões.
- `scripts/avaliacao_pc_4b.py --documentos outputs/avaliacao_cega_v3/documentos --pedidos outputs/avaliacao_cega_v3/pedidos.json --saida outputs/avaliacao_cega_v3/pc4b`: PC 4B.
- `scripts/avaliacao_externo_gpt.py --documento …`: externo, via `outputs/avaliacao_cega_v3/rodar_externo.sh`.
- `scripts/avaliacao_cega_v3_preparar.py`: sorteio dos códigos `C###`, com semente 20261127.
- Dados em `outputs/avaliacao_cega_v3/`, fora do git. O gabarito (código → condição) fica só em `gabarito.json` e nunca é publicado.

## Material

24 apresentações de 5 slides: 4 assuntos × 6 condições. Em todas as condições entram o mesmo pedido, o mesmo documento e a semente 11.

| Assunto | Documento (trechos literais da Wikipédia em português, CC BY-SA 4.0) | Pedido (público) |
|---|---|---|
| Vacinas | "Vacina": introdução e Eficácia | alunos do ensino médio |
| Reciclagem | "Reciclagem": introdução, Conceito, Benefícios, Cores dos cestos | moradores de condomínio |
| Polinização | "Polinização": introdução e Polinização biótica | ensino fundamental |
| Sistema Solar | "Sistema Solar": introdução e Sol | ensino fundamental |

Os quatro documentos têm de 4,6 a 5,5 mil caracteres. Os pedidos completos estão em `outputs/avaliacao_cega_v3/pedidos.json`.

| Condição | Código |
|---|---|
| celular 0.6B LoRA, app 0.7.7 (congelado, `artigo-v2`) | `mobile/app` na tag `artigo-v2` |
| celular 0.6B LoRA, app novo | branch `exp/celular-documento`: leitura inteira, leitura literal, detalhe literal |
| celular 1.7B, app 0.7.7 | idem, tag |
| celular 1.7B, app novo | idem, branch |
| PC 4B (referência) | fluxo completo do PC, branch `exp/celular-documento` |
| externo GPT-4.1-mini (referência comercial) | o modelo escreve o python-pptx direto |

As condições SlideDSL são renderizadas pelo mesmo compilador, que é igual ao do `artigo-v2`. A condição externa mantém o visual do python-pptx e pode ser reconhecida; a página pede que se avalie o conteúdo.

**Regra de falha (igual à v2):** se uma combinação não gerar apresentação válida, ela fica fora e é registrada no gabarito, sem trocar de semente. A exceção é o PC 4B, que segue a regra da v1: até 3 sementes (11, 12 e 13).

## Avaliadores, tarefa e rubrica

Iguais à v2:
- 3 colegas voluntários, maiores de 18 anos, sem dado pessoal, com consentimento na página.
- Cada avaliador vê as apresentações numa ordem sorteada só para ele.
- Rubrica: clareza (1–5), erro (não / sim com trecho / não sei), repetição (não / um pouco / muito) e utilidade (1–5), mais comentário opcional.
- O tempo por apresentação é registrado.

## Hipóteses (definidas antes das respostas)

- **N1.** Em cada modelo do celular, a versão nova tem **menos** apresentações marcadas com afirmação errada que a 0.7.7. Na bancada, a leitura e o detalhe literais tiraram as trocas de sujeito e de número.
- **N2.** Em cada modelo do celular, a versão nova tem utilidade maior ou igual à da 0.7.7. A bancada mostrou mais seções e números do documento.
- **N3.** A versão nova não repete mais que a 0.7.7. O detalhe literal usa um fato diferente por item.
- **N4.** O PC 4B e o externo ficam acima das condições do celular em utilidade, como na v2.
- **N5.** A ordem das condições em utilidade é parecida com a da v2 nas condições comuns: 0.7.7 do celular, PC 4B e externo. Se mudar, os assuntos do banco padrão favoreciam o sistema.

## Análise

Igual à v2 (`scripts/avaliacao_cega_analisar.py`):
- os pares nova × 0.7.7 são feitos pelo mesmo avaliador e pelo mesmo assunto;
- a utilidade é comparada com Wilcoxon pareado;
- "afirmação errada" é comparada com McNemar exato;
- a concordância entre avaliadores é medida.

Com 3 avaliadores e 4 assuntos, os números mostram a direção, não uma taxa.

## Registro da preparação (27/11, antes das respostas)

As 24 combinações geraram apresentação válida na primeira semente, e nenhuma ficou de fora.
- **Celular:** os 16 decks foram compilados sem erro. Projeção de tempo no aparelho: 0.6B LoRA com cerca de 22 min no app novo, contra 23 a 27 min no 0.7.7; 1.7B com 53 a 60 min no app novo, contra cerca de 64 min no 0.7.7.
- **PC 4B:** de 36 a 51 chamadas e de 110 a 152 s por apresentação.
- **Externo:** gerou na primeira tentativa nos 4 assuntos.

**Observação feita antes das respostas, sem mudar o material:** o deck do 0.6B LoRA no app novo sobre vacinas diz que "a vacinação garante que 99% dos casos de gripe sejam tratados com eficiência". Esse número não está no documento. Passou porque, num slide de comparação, número sem fato é só aviso (A012), e esse item não teve frase do documento parecida para trocar. A rubrica de "afirmação errada" deve pegar esse tipo de erro. O material foi mantido como gerado.
