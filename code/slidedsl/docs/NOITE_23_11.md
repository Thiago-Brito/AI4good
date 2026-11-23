# Fila de trabalho da madrugada de 23/11/2026

Autor dormindo e trabalhando hoje (23/11) a partir das 9h; entrega do artigo em 27/11. Claude revisa, Codex executa.
Regras de sempre: nada de commit/push no repositório do projeto; push no Overleaf só do artigo revisado
(autorizado). Registrar cada item concluído aqui e no ROADMAP. Não inventar números.

## Regra de memória (pedido do autor: não travar o PC)

- Antes de qualquer tarefa pesada (build, emulador, llama-server, teste com modelo, novo Codex):
  `powershell -File scripts\memoria_livre.ps1 -MinGB 3`. Se sair 1, **não iniciar**: esperar a tarefa
  atual terminar e reagendar.
- **Uma tarefa pesada por vez.** Emulador nunca junto com build ou llama-server. Desligar o emulador e
  o SearXNG/Docker quando não estiverem em uso; `ollama stop <modelo>` depois de usar.
- Gradle limitado em `D:\android\gradle\gradle.properties` (sem daemon, 1,5 GB, 2 workers).

## Regra do Codex (pedido do autor, 23/11 ~01:35)

- O autor precisa do Codex para o trabalho dele **hoje, 23/11, às 9h**.
- **Não iniciar nenhum Codex novo depois das 07:30.** Às **08:30**, encerrar qualquer Codex ainda rodando
  (registrar o que ficou incompleto).
- Se o Codex acusar fim de cota/limite/contexto, parar de usá-lo na hora.
- Depois disso, **não usar o Codex de novo até o autor mandar**. O que faltar, fazer diretamente (sem
  Codex) ou deixar anotado para ele.

## Fila (em ordem)

Prioridade por causa da janela do Codex (até 07:30): assim que o Codex do artigo terminar, disparar o
Codex dos Testes 1 e 3 (`docs/PLANO_CODEX_TCC_T1_T3.md`). O teste no emulador (item 2) é feito sem
Codex, só quando não houver llama-server/build rodando e a RAM livre for ≥ 4 GB.

1. [ ] Dossiês fixos (`scripts/build_dossiers.py`, SearXNG + Qwen3 4B) — em execução.
2. [ ] Revisar a rodada 3 do Codex (documento → slides); recompilar com a correção do SHA-256;
   teste de ponta a ponta no emulador: (a) pedido curto sem fontes; (b) documento TXT/DOCX/PDF.
   Desligar o emulador ao terminar (CPU).
3. [ ] Revisar o artigo LNCS do Codex; compilar; enviar ao Overleaf (`academy/papers/artigo-overleaf`).
4. [ ] Teste 1 (custo do formato) via Codex — `scripts/format_cost.py`, tokenizador do Qwen3.
5. [ ] Teste 3 reduzido via Codex — llama-server (binário oficial do llama.cpp para Windows/CUDA em
   `D:\android\llama`), Qwen3 4B GGUF, modos json × gramatica × direto, 12 pedidos × 2 sementes,
   rodando à noite na RTX 3060; microbenchmark da gramática (ms/token).
6. [ ] Atualizar o artigo com os números medidos (substituir `\pendente`), recompilar e enviar.
7. [ ] Resumo para o autor ler de manhã: `docs/RESUMO_MANHA_23_11.md`.

## Registro

- 01:30 — Rodada 3 (documento → slides) concluída pelo Codex: PDF via PdfBox-Android (nativo), DOCX/TXT/MD,
  compartilhar para o app, documento longo em partes; 50/50 testes do app, 43/43 núcleo, 718 pytest (relato
  do Codex). APK 0.3.0 (181 MB) já inclui as correções da gramática estrita e do SHA-256 (conferido no
  código copiado para o build). Teste no emulador aguardando RAM (2,9 GB livres; dossiês em execução).
