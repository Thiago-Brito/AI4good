# Plano da noite (25/11/2026): código e testes prontos até 12h — CONCLUÍDO às 05h40 (tag artigo-v1; resumo em docs/RESUMO_NOITE_25NOV.md)

O autor dorme. O Claude roda em loop até 12h, testando e melhorando o código.
**Atualização (00h40):** até 12h o autor precisa só do **código** pronto e testado; o artigo fica para depois, e não se mexe nele esta noite.
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
5. **Artigo:** fica para depois. Só deixar os números prontos em `RESULTADOS_T9.md` e no `ROADMAP.md` para quando for escrever.

## Prazos

- **até 06h:** bancada do 0.7.5 analisada, `RESULTADOS_T9.md` escrito e 1–2 correções medidas (com bancada de novo, se mudar o pipeline).
- **06h–09h:** mais voltas de teste e correção, se houver defeito barato. Também testes de ponta a ponta que ainda faltam:
  - fluxo do PC com o motor do celular e a API;
  - edição;
  - limpeza de PDF no fluxo do PC (`documents.py`), se for simples e com paridade.
- **09h–10h30:** congelar o código.
  - gerar o APK final e colocá-lo em `PARA_O_CELULAR`;
  - rodar a verificação completa: pytest, núcleo, app, editor, paridade e prompts em sincronia;
  - criar a tag `artigo-v1`.
- **10h30–12h:** resumo para o autor: o que mudou, os números e o que falta.

## Não fazer

- Mexer na avaliação cega: o protocolo foi registrado antes das respostas, e a página fica como está.
- Rodar dois processos pesados ao mesmo tempo (GPU, build, emulador).
- Mexer no artigo esta noite, ou mudar a numeração dos testes do plano do TCC.
