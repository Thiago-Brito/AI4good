# Fila de trabalho da madrugada de 23/11/2026

Autor dormindo e trabalhando hoje (23/11) a partir das 9h; entrega do artigo em 27/11. Claude revisa, Codex executa.
Commit e push **autorizados** pelo autor (23/11 ~01:45): ao fim de cada item revisado, commitar
`code/slidedsl` (sem `.maestri/`, `maestri-mundos/`, `academy/ai4good`) **sem linha de coautor** e dar push
em `feature/slidedsl-api-voz-mobile`; antes, conferir que não entram chaves, GGUF, APK ou `outputs/`.
Atualizar o `README.md` do projeto com o que mudou (app Android, núcleo TS, testes). O Codex continua
sem commitar; quem commita é o Claude após revisar. Push no Overleaf só do artigo revisado. Registrar cada item concluído aqui e no ROADMAP. Não inventar números.

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

1. [x] Dossiês fixos: 12/12 (fatos por pedido: 1 a 22; `solar_obrigatorio` só 1 fato, `agua_obrigatorio` 2 — registrar como limitação). SearXNG e Ollama desligados.
2. [ ] Revisar a rodada 3 do Codex (documento → slides); recompilar com a correção do SHA-256;
   teste de ponta a ponta no emulador: (a) pedido curto sem fontes; (b) documento TXT/DOCX/PDF.
   Desligar o emulador ao terminar (CPU).
3. [x] Artigo LNCS completo (Codex até a seção 2; resto escrito e revisado por Claude): 11 páginas, figura do fluxo, figura com deck gerado pelo Qwen3 4B + tela do app, resumo reescrito, E1–E11 definidos. Compila sem erros. Enviado ao Overleaf (`6ec27c9`). Pendentes em vermelho: Testes 1, 3 e 4.
4. [x] Teste 1 medido por Claude (sem Codex): 127 decks/694 slides; Alto 2,04× texto, JSON 2,15×, 1.1 9,22×, python-pptx 18,45×; p≈1e-22. `docs/RESULTADOS_T1.md`; no artigo.
5. [ ] Teste 3 reduzido via Codex — llama-server (binário oficial do llama.cpp para Windows/CUDA em
   `D:\android\llama`), Qwen3 4B GGUF, modos json × gramatica × direto, 12 pedidos × 2 sementes,
   rodando à noite na RTX 3060; microbenchmark da gramática (ms/token).
6. [ ] Atualizar o artigo com os números medidos (substituir `\pendente`), recompilar e enviar.
7. [ ] Resumos (pedido do autor): `docs/RESUMO_MANHA_23_11.md` **curto, pronto até 07:30** (leitura rápida antes de sair) e `docs/RESUMO_COMPLETO_23_11.md` detalhado para ler depois.

## Registro

- 01:30 — Rodada 3 (documento → slides) concluída pelo Codex: PDF via PdfBox-Android (nativo), DOCX/TXT/MD,
  compartilhar para o app, documento longo em partes; 50/50 testes do app, 43/43 núcleo, 718 pytest (relato
  do Codex). APK 0.3.0 (181 MB) já inclui as correções da gramática estrita e do SHA-256 (conferido no
  código copiado para o build). Teste no emulador aguardando RAM (2,9 GB livres; dossiês em execução).
- 01:50 — Commit `0c1d856` enviado (push ok). Dossiês 12/12. RAM livre 7,6 GB. Disparado Codex T1+T3.
- 02:00 — **Codex atingiu o limite de uso** (artigo parou na seção 2; T1/T3 não começaram). Pela regra do autor, Codex não é mais usado até ele mandar. Claude continua o artigo e os testes diretamente.
- 02:45 — Artigo enviado ao Overleaf (`6ec27c9`). Teste de edição localizada de um slide (Qwen3 4B local) em execução: `scripts/teste_edicao.py`.
- 03:30 — Teste 1 concluído e inserido no artigo (Overleaf). Teste de edição v2 em execução.
