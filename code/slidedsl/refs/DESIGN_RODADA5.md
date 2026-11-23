# Evidências locais — rodada 5 (11/11/2026)

Rodada offline, sem consultas de rede ou APIs. Registro anterior à documentação dos resultados.

- Plano: `docs/PLANO_CODEX_RODADA5_DESIGN.md`; fundamentação já registrada em
  `refs/DESIGN_RODADA4.md`. Não se atribui validação estética às métricas.
- Base congelada: `outputs/design_r4/20261110-234240/{antes,ciclo_3,corpus}/`;
  críticas em `RELATORIO.md` e `ciclo_3/REVISAO.md` da mesma pasta.
- Medição própria: Pillow/FreeType, glifo `x` normal a 1000 px, caixa `getbbox`
  com âncora de baseline `ls`. Altura = inferior − superior, incluindo overshoot.
  Razão = altura da família / altura Arial. Compensação em pontos = nominal / razão,
  arredondada a 1 pt; piso efetivo usa teto. Isso aproxima altura-x, não preferência humana.
- Fontes locais: `C:/Windows/Fonts/{arial.ttf,calibri.ttf,cambria.ttc,georgia.ttf,
  trebuc.ttf,verdana.ttf}`. Hashes e razões serão preservados no manifesto da auditoria.
- Código de entrada, hashes e corpus desta rodada: `outputs/design_r5/20261111-001430/`.
  Nenhum conteúdo acadêmico externo novo é alegado.
