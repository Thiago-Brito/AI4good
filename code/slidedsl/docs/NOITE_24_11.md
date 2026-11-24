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
- ~01:50 — Matriz da bancada (json × gramatica, 48 gerações) em execução em `outputs/teste5_app/`. Parcial: slides
  montados pelo compilador (F001) frequentes nos dois modos, quase sempre por A005 (texto acima do limite).
  Implementado o modo `gramatica_limites` (mesma gramática com os limites A005 do compilador em vez dos limites
  folgados do JSON) para rodar como 3ª condição depois da matriz; 60/60 testes do app.
- Achado do app: em solar_obrigatorio s11 o roteiro não começou com capa/terminou com conclusão e o app abortou.
  O pipeline Python corrige isso (`fix_outline`); o porte do app não. Independe do modo dos slides (roteiro igual
  nos dois); corrigir depois da matriz para não mudar o código no meio do experimento.
- ~02:10 — Matriz json × gramatica concluída (48). gramatica: −21% tokens gerados nos slides (p = 0,008), −11% no
  tempo projetado dos slides (p = 0,08); slides montados pelo compilador 52 → 41 (de 115). Nos dois modos ~40% dos
  slides caem no compilador, quase sempre por A005.
- ~02:20 — 3ª condição `gramatica_limites` (24): slides do compilador 52 → 16 (−69%, p = 0,0002); decks completos
  1 → 10 de 24 (McNemar p = 0,012); tokens gerados nos slides −35%; celular projetado 80,1 → 70,9 min (p = 0,001).
  Custos: 31 de 677 campos cortados no limite (ex.: "…Essa capac"); 2 decks com B4 (bloco sobre o número da página)
  — é o defeito já corrigido no núcleo de 23/11: a cópia do núcleo usada pela bancada é anterior; recompilados
  com o compilador atual, os 2 passam.
- 02:21 — Fix no app: roteiro sem capa/conclusão é corrigido (porte de `fix_outline`) em vez de abortar.
- ~02:25 — 4ª condição `gramatica_limites_reparo`: texto que chega ao limite vira aviso e pede 1 reparo (se persistir,
  o slide é aceito). Testes do app 62/62. Rodando; já com o fix do roteiro (par solar_obrigatorio s11 passa a contar).
- ~03:05 — 4ª condição concluída: o reparo de texto cortado não reduziu cortes (28/673 × 31/677) e custou +22% de
  reparos (resultado negativo). Decisão: app 0.4.0 com `gramatica_limites` ligado por padrão, sem o reparo.
  Testes do app 62/62. Resultados em `docs/RESULTADOS_T5.md`. Próximo: desligar llama-server, build do APK, emulador.
