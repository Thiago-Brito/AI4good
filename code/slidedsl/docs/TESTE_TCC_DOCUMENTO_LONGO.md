# Teste com documento longo: o próprio TCC como fonte (25/11/2026)

Pergunta: se o usuário mandar um documento grande e técnico ao app (o PDF do artigo do TCC), sai uma apresentação útil?

## Montagem

- **Documento:** `academy/papers/artigo-overleaf/samplepaper.pdf`, com 23 páginas e 47.310 caracteres (cerca de 15 vezes o `agua.txt` da bancada).
- **Texto:** extraído com pypdfium2 e separado por página (`# Página N`). Isso imita o módulo de PDF do Android, que agrupa os trechos por página. O PDF tem hifenização e cabeçalhos de página, e o texto foi usado como saiu.
- **Modelos locais:** 0.6B LoRA, 1.7B e 4B Instruct-2507, todos Q4_K_M.
  - Rodaram o `generate()` do app via `bench/motor_pc.mjs`, no modo `gramatica_limites+frases`, com contexto de 4096 e semente 11.
  - O llama-server rodou na GPU do PC; o tempo no celular é outro.
- **Externo:** GPT-4.1-mini escrevendo python-pptx, com `scripts/avaliacao_externo_gpt.py --documento`.
  - Ele recebe o documento **inteiro** (12,5 mil tokens). O app lê no máximo 6 trechos de 900 caracteres.
- **Saídas:** `outputs/teste_tcc/`, fora do git. Os decks são `TCC-*.pptx` e as imagens estão em `png/` e `png8/`.

## Rodada 1: 0.6B LoRA, 5 slides

| Pedido | Resultado |
|---|---|
| vazio (genérico) | Capa e ideia central corretas, mas o conteúdo é raso e repetitivo. Um lado da comparação é **inventado** ("modelo grande em nuvem, linguagem universal"). O slide 4 virou divisória vazia (F001 com 1 fato só). Não há nada de resultados. |
| "Apresente o problema, a metodologia e os resultados do TCC" | **Sem sentido.** "O TCC evita que ntativas sejam consideradas como autoria…" vem de uma palavra quebrada pela hifenização do PDF. "100 linhas" aparece inventado em todos os slides, e o gráfico é "100 vs. 100". Foram 19 avisos A007/A012. A busca por palavras-chave pegou trechos de tabelas e notas. |

## Rodada 2: pedido de banca, 8 slides, 4 modelos

Pedido: *"Apresente este TCC para a banca: o problema (…), a proposta do SlideDSL (…), a versão no celular, os principais resultados dos testes e as limitações do trabalho."*

| | 0.6B LoRA | 1.7B | 4B | GPT-4.1-mini |
|---|---|---|---|---|
| deck válido | sim | sim | sim | sim (1ª tentativa) |
| slides do compilador | 0 | 2 (divisórias vazias) | 0 | — |
| fatos extraídos / **usados no deck** | 24 / **1** | 26 / **2** | 32 / **3** | documento inteiro |
| cobre resultados? | não | não ("Resultados" é uma divisória vazia) | não (gráfico de notas **inventadas** 4/4/4/5) | sim (0/10 → 10/10, 12/12, 63 min, 7%) |
| cobre limitações? | não | não | não | sim |
| número inventado | "90%" | — | notas 1–5, "geram dependên" | nenhum notado |
| outros defeitos | 6 dos 8 slides repetem "o modelo escreve apenas a intenção" | rótulos cortados no limite ("SlideD", "aexec"), conclusão com 2 itens iguais | caractere chinês ("cada 滑"), rótulos cortados | visual do modelo padrão, só texto em tópicos |
| tempo (PC) | 12,9 s | 35,8 s | 62 s | 18,9 s, cerca de US$ 0,01 |

## Rodada 3: GPT-4.1-mini pelo SlideDSL (fluxo completo do PC)

`slidedsl criar ... --provider openai --model gpt-4.1-mini --slides 8 --documento samplepaper.pdf --fontes documentos --buscador nenhum`, com o mesmo pedido.
- **Execução:** o PDF foi lido pelo próprio PC, e o roteiro viu os 24 fatos. Foram 58 chamadas (com as correções do verificador de sustentação), 166,6 s e US$ 0,044.
- **Resultado:** deck válido, que cobre os 5 assuntos do pedido: problema, proposta, divisão modelo/compilador, celular, resultados (10/10 e 7%, ambos corretos) e limitações. Os números vêm de fatos citados, e não houve invenção notada.
- **Comparado ao GPT direto:** tem o mesmo conteúdo com o visual do compilador, mas custa 4 vezes mais e leva 9 vezes mais tempo, por causa das chamadas de verificação.
- **Defeitos:**
  - título cortado no limite ("Problema: gerar apresentações com IA depende");
  - nos slides 3 e 5, a 2ª linha do título encosta nos cartões;
  - itens do slide 2 repetem a mesma ideia.

## Diagnóstico

1. **O roteiro do app só vê os 3 primeiros fatos.** Esta é a causa principal.
   - Em `generate.ts`, `factsBlock()` corta em `slice(0, 3)`. O roteiro do PC (`alto_generation.facts_block(all_facts=True)`) recebe até 32.
   - No TCC, os fatos F1–F3 vêm todos do resumo (página 1), então os 3 modelos falam só da ideia central. Os fatos de resultados extraídos (F6 0/10→10/10, F13 12/12, F15 "nove vezes menor", F25 telefone de 3,96 GB) nunca chegam ao planejamento.
   - É uma divergência entre PC e celular que a paridade (que compara o compilador) não cobre.
   - Também afeta as bancadas T6–T8, cujos documentos são curtos (6 fatos, dos quais o roteiro via 3).
2. **Escolha de trechos.** A leitura genérica por páginas pega as referências (p. 23) e tabelas. A busca por palavras-chave do pedido específico pegou tabelas e notas.
3. **Texto do PDF sujo:** hifenização ("ntativas") e cabeçalhos de página repetidos.
4. **O modelo inventa para preencher tipos numéricos.** Com o roteiro pedindo `numeros` ou `grafico` sem fato numérico, o 0.6B e o 4B inventaram valores. O verificador avisou (A007/A012), mas aviso não bloqueia.
5. **Capa (falso alarme):** na prévia do VS Code (extensão `pptx-preview`), o título de 2–3 linhas aparecia por cima do subtítulo. No PowerPoint para a web, o mesmo arquivo fica correto (conferido pelo autor em 25/11/2026). A extensão aplica o espaçamento de linha de outro jeito, então essa prévia não serve para conferir layout. Conferir no PowerPoint ou no LibreOffice.

## Leitura para o artigo

- Com documento curto (bancada), o app chega perto do externo em validade. Com documento longo e técnico, o gargalo não é o tamanho do modelo: até o 4B falhou.
- O gargalo é o que o pipeline deixa o modelo ver: 3 fatos no roteiro e 6 trechos. O GPT-4.1-mini, lendo o documento inteiro, cobriu os 5 assuntos do pedido com números corretos.
- Este caso entra como limitação. As correções (itens 1–3 e 5) são candidatas a trabalho futuro ou a uma versão do app antes do congelamento, com nova bancada.
