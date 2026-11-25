# Plano da noite (25/11/2026): testes e artigo até 12h

O autor dorme. O Claude roda em loop até 12h, testando, melhorando e escrevendo.
**Regra de ouro:** nenhuma mudança pode aumentar o tempo no celular. A medida é `celular_min` da bancada; se o tempo subir mais de 5%, a mudança volta atrás.

## Estado no início (00h30)

- **App 0.7.5** (código no commit `74bd46c`; APK ainda não gerado).
- **Teste no celular com o 0.7.4:** 20,7 min, 1 reparo; ficou melhor. O título cortado já foi corrigido no 0.7.5.
- **Bancada do 0.7.4** (`outputs/teste9_v074_*`): fatos citados 2–3 → 6–8 por deck e menos slides de seção. Mas o 0.6B LoRA teve 12 slides do compilador, tratados no 0.7.5 (citação certa e encurtamento).

## Loop (cada volta ≈ 40–60 min)

1. **Bancada do 0.7.5:** 3 modelos × 24 apresentações, script `bancada_074.sh` com a pasta `teste9_v075_*`. Depois, `scripts/analise_teste9.py` com o par trocado para v075.
2. **Ler os resultados:**
   - completas, slides do compilador, repetição, fatos citados, tempo;
   - abrir 3–4 decks e ler o texto;
   - procurar o próximo defeito mais frequente.
3. **Corrigir só se for barato e medido:**
   - usar `motor_pc.mjs` e `respostas.jsonl` para ver a causa;
   - testes unitários e `npm test` (todos verdes);
   - conferir com os casos rápidos (`agua_rep.sh`, lista de falhas).
   - Se piorar ou ficar mais lento, desfazer.
4. **Registrar:** `docs/RESULTADOS_T9.md` (método, tabela antes/depois, leitura honesta), ROADMAP e commit/push.
5. **Artigo** (`academy/papers/artigo-overleaf/samplepaper.tex`, commit local sem push):
   - resultados do celular (17,8 → 20,7 min com o 0.7.x; antes 48 e 63 min);
   - bancada T9;
   - teste de documento longo (TCC) como limitação;
   - números de testes e paridade atualizados;
   - compilar com `latexmk -pdf` e conferir o PDF.

## Prazos

- **até 06h:** bancada 0.7.5 analisada e `RESULTADOS_T9.md`; no máximo mais 1–2 correções medidas.
- **06h–09h:** artigo atualizado e compilado.
- **09h–10h30:** congelar.
  - gerar o APK final e colocá-lo em `PARA_O_CELULAR`;
  - rodar a verificação completa: pytest, núcleo, app, editor, paridade;
  - criar a tag `artigo-v1`.
- **10h30–12h:** revisão final do texto do artigo e um resumo para o autor (o que mudou, números, o que falta).

## Não fazer

- Mexer na avaliação cega: o protocolo foi registrado antes das respostas, e a página fica como está.
- Rodar dois processos pesados ao mesmo tempo (GPU, build, emulador).
- Push no repositório do artigo, ou mudar a numeração dos testes do plano do TCC.
