# Madrugada de 24/11/2026 — gramática Alto no app

Pedido do autor (dormindo): usar a gramática da SlideDSL Alto na escrita dos slides do app (hoje JSON Schema),
testar no emulador e deixar um resumo. Claude conduz sozinho; commits sem coautor na branch
`feature/slidedsl-api-voz-mobile`, sem `outputs/`, APK ou GGUF. Regras de memória de NOITE_23_11 valem
(uma tarefa pesada por vez; `scripts/memoria_livre.ps1` antes de build/emulador/llama-server).

## Plano

1. App: gramática GBNF por tipo de slide gerada do mesmo schema JSON (mesmos campos e limites; só muda a
   sintaxe) + leitor do bloco Alto que devolve o mesmo objeto do JSON; modo `json | gramatica` escolhível.
2. Paridade do leitor TS com o parser Python nos slides do corpus.
3. Bancada no PC: o pipeline do próprio app (TS) contra llama-server com o Qwen3 1.7B do celular,
   12 pedidos × 2 sementes × 2 modos; tempo no celular projetado pelas velocidades medidas no moto g8
   (prompt 3,9 tok/s; geração 1,5 tok/s).
4. APK novo e teste no emulador (Qwen3 0.6B) no modo gramática.
5. Resumo da manhã.

## Registro
(horários do relógio do PC; "~" = aproximado)
- 01:33 — Qwen3 1.7B Q4_K_M baixado em D:\android\models; SHA-256 igual ao do app (b139949c…).
- ~01:37 — App: `src/pipeline/altoText.ts` (gramática GBNF por tipo derivada do schema JSON; leitor do bloco Alto →
  mesmo objeto do JSON), `Recorder.grammar`, `generate({slideMode})`, llama.rn com `grammar`, chave na tela Modelo,
  `slide_mode` nos dados exportados. Paridade do leitor com o parser Python: 393/393 slides do corpus
  (`scripts/export_alto_parity.py` → `mobile/app/test/fixtures/alto_slides.json`). Testes do app 59/59; typecheck ok.
- ~01:40 — Bancada `mobile/app/bench/app_bench.mjs`: pipeline do app contra llama-server imitando o llama.rn.
  Achado: o servidor reaproveitava o prompt da geração anterior (cache de slot e `--cache-ram`), favorecendo o
  segundo modo; corrigido com `--cache-ram 0`, `--slot-save-path` e erase antes de cada geração.
- ~01:42 — Validação da projeção: JSON em agua_detalhado projetou 66,1 min no celular (real: 63,0 min, +5%).
- ~01:44 — Decisão de projeto no piloto (antes da matriz): dica de formato do modo gramática reduzida a uma linha
  (o exemplo completo somava ~120 tokens de prompt por slide; a gramática já impõe as palavras-chave).
  Pilotos isolados variam muito por causa dos reparos A005; decisão pela matriz completa.
