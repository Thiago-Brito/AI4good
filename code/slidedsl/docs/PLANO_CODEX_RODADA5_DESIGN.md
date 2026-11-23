# Plano para o Codex — rodada 5: calibrar a nota e recuperar presença visual

Data: 11/11/2026 · Planejador: Claude · Executor: Codex. Mesmas regras da rodada 4
(`docs/PLANO_CODEX_RODADA4_DESIGN.md`): **offline, US$ 0**, gramática Alto inalterada, sem commit.
pytest: `--basetemp outputs\_tmp_r5`. Corpus: o mesmo de `outputs/design_r4/20261110-234240/corpus/`.
Linha de base desta rodada = `outputs/design_r4/20261110-234240/ciclo_3/` (e também o `antes/` da r4).

## Revisão do planejador sobre a rodada 4

Evidência: `outputs/design_r4/20261110-234240/comparacao/01_editorial.png` e `06_energia_solar_B_img_s42.png`.

Preservar: identidade de cada estilo (Georgia/Cambria/Trebuchet, fio/faixa/soft, marcadores);
transição curta sem "01"; conclusão em colunas numeradas; 16/16 válidos; zero A010/A019/D010;
sem variantes iguais consecutivas.

Regressões que a nota **premiou** (a nota está mal calibrada):
1. **Fotos encolheram.** 10/10 slides de imagem escolheram `photo40`; inversor e lixeiras viraram
   miniaturas. Antes a meia página sangrada era melhor.
2. **Ocupação caiu 0,61 → 0,50** e isso contou como ótimo. Visualmente: metade inferior vazia
   nas listas.
3. **Cartões viraram listas.** Editorial slide 2 trocou 3 cartões por linhas; 26 slides em `rows`.
   O deck parece documento.
4. **Corpo parece menor.** Calibri tem altura-x menor que Arial: 20 pt Calibri ≈ 18 pt Arial.
5. **Alinhamentos centro/direita** (vibrante, escuro, noturno) quebram o eixo: título centralizado
   com fio de destaque e corpo à esquerda.

## Tarefas

1. **Calibrar ocupação.** Platô de nota 1 em 0,55–0,78 (antes 0,45–0,70); queda mais íngreme
   abaixo de 0,45. Imagem conta pela área inteira. Peso de ocupação 35%, equilíbrio 20%.
2. **Fotos.** `photo50` sangrada é a preferida quando a imagem tem lado maior ≥ 1000 px e
   proporção paisagem/quadrada; `photo40` só para retrato estreito ou imagem com A031.
   Foto contida nunca menor que 40% da largura útil nem 50% da altura útil. Teste com assets
   sintéticos de várias proporções.
3. **Cartões de volta.** Para 2–3 itens com rótulo curto e descrição ≤ 110 caracteres, bônus
   para `cards` (ou nota de `rows` limitada); `rows` preferido só com 4+ itens ou descrições longas.
   Ritmo: penalizar a mesma variante em qualquer um dos **3** slides anteriores (não só no
   imediatamente anterior), e bônus de diversidade no deck (nº de variantes distintas).
4. **Tamanho óptico por família.** Escala por família com compensação de altura-x medida
   (razão altura-x da família / Arial, calculada pelos .ttf locais, arredondada a 1 pt).
   Calibri: corpo ≥ 18 pt efetivo, perfil usual 22 pt, rótulo 26 pt. Mínimos continuam valendo
   como piso (nunca abaixo). Documentar a tabela em `docs/REGRAS_DESIGN.md`.
5. **Preencher a altura nas listas.** Em `rows`, distribuir as linhas na altura útil
   (espaçamento entre linhas cresce até 64 px) antes de centralizar; bloco começa no máximo
   48 px abaixo do título se a ocupação ficar < 0,55.
6. **Eixo único.** Slides de conteúdo: título, fio de destaque e corpo no mesmo eixo à esquerda
   em todos os estilos. Centro só em capa, transição e citação, e então fio e subtítulo também
   centralizados. Remover alinhamento à direita do noturno (trocar por outro atributo distintivo:
   ex. faixa vertical fina na margem). Teste: em slide de conteúdo, x do fio == x do título.
7. **Ciclos (até 3)** com `scripts/auditar_design_r4.py` → `outputs/design_r5/<ts>/ciclo_N/`, abrir as
   folhas e escrever `REVISAO.md`. Critérios de parada: (a) nenhuma foto paisagem ≥ 1000 px em
   `photo40`; (b) ocupação média ≥ 0,58; (c) ≤ 35% dos slides de tópicos em `rows`; (d) nenhum
   slide de conteúdo com eixo misto; (e) 16/16 válidos, zero A010/A019/D010.
8. Comparação `outputs/design_r5/<ts>/comparacao/` com três colunas: antes r4 | r4 final | r5.
   pytest + ruff + Node; atualizar `REGRAS_DESIGN.md`, `PROGRESSO.md`, `ROADMAP.md`, continuidade.

## Mensagem final esperada
Arquivos alterados; nova calibragem (pesos, platôs, escala por família); tabela r4-antes × r4 × r5
com os critérios (a)–(e); achados por ciclo; testes; caminhos das folhas finais; o que continua ruim.
