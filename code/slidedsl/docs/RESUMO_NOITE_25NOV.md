# Resumo da noite (25/11/2026): código pronto

**Estado:** código congelado na tag **`artigo-v1`** (commit `cd09024`, app **0.7.6**). Verificação completa verde:

| suíte | resultado |
|---|---|
| Python (pytest) | 755/755 |
| app (node) | 97/97 |
| núcleo TS | 44/44 |
| editor (Playwright) | 15 ok + 5 pulados (precisam de Ollama/OpenAI) |
| paridade PC/celular | 861/861 decks |
| contratos mobile (prompts) | em sincronia |

**APK para o celular:** `D:\slidedsl-mobile\PARA_O_CELULAR\1-SlideDSL-0.7.6.apk`, também no zip `SlideDSL-para-o-celular.zip`; o LEIA-ME está atualizado.

## O que mudou desde o teste do TCC

**No app (0.7.3 → 0.7.6; detalhes em `docs/RESULTADOS_T9.md`):**
- **Roteiro:** vê todos os fatos; antes via só 3.
- **Repetição:** cada slide recebe fatos diferentes e vê os itens já escritos nos outros slides.
- **Gramática:** só caracteres latinos; não sai mais "滑".
- **Números:**
  - número inventado em slide de números/gráfico vira tópicos com os fatos;
  - número certo com a citação errada é citado corretamente.
- **Textos que não cabem:**
  - texto cortado no limite termina na última pausa da frase, o que resolve o título "e volta ao";
  - slide que não cabe tem os detalhes encurtados, em vez de virar slide do compilador.
- **Itens duplicados:** saem do slide.
- **PDF:** junta a hifenização, tira os cabeçalhos das páginas, segue as seções e para nas referências.

**No PC:**
- o PDF tem a mesma limpeza;
- o motor do celular entrega o PDF por página ao código do app;
- o teste de ponta a ponta pela API passou (criar → refazer → mover → desfazer).

## Números (bancada T9, 24 apresentações por modelo, contra T7/T8)

- **Fatos do documento usados por apresentação:** 2,3–2,9 → **5,3–7,7**.
- **Apresentações completas:**
  - 0.6B: 8 → 16;
  - 1.7B: 13 → 17;
  - LoRA: 22 → 20 (agora os números inventados são recusados).
- **Slides de seção vazios:** de 41 para 14 no 0.6B e para 0 no LoRA e no 1.7B.
- **Pares de slides parecidos no LoRA:** 12 → 6.
- **Custo:** cerca de 10% a mais de tempo (LoRA 20,6 → 22,9 min projetados). No seu celular: 17,8 min (0.7.2) e 20,7 min (0.7.4).
- **Tentativa descartada:** encurtar os pedidos para recuperar o tempo (0.7.6 experimental) não reduziu o tempo e aumentou os reparos.

## Emulador (APK 0.7.5)

- 0.6B base: 5 slides em 19,0 min.
- LoRA importado: 5 slides em 20,5 min.
- A tela nova de edição funcionou nos dois.

## O que continua limitado (para o artigo)

- O 0.6B ainda escreve frases erradas ("a água condensa em vapor com temperatura alta"). O compilador confere forma, números e citação, não a verdade de cada frase.
- Documento longo e técnico (o PDF do TCC) fica fora do alcance dos modelos que cabem no celular. O 4B e o GPT-4.1-mini pelo SlideDSL se saem bem (`docs/TESTE_TCC_DOCUMENTO_LONGO.md`).
- A avaliação cega usa decks da versão anterior a estas correções (protocolo registrado antes).

## O que falta (fora do código)

- Mandar a avaliação cega aos 3 colegas e, quando voltarem, rodar `scripts/avaliacao_cega_analisar.py`.
- Se quiser, testar o 0.7.6 no celular para confirmar o tempo.
- Escrever o artigo com os números do T9 e do celular. Os números estão em `RESULTADOS_T9.md` e `ROADMAP.md`.
