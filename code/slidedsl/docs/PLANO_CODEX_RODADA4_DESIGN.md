# Plano para o Codex — rodada 4: sistema de design, variantes com nota e ritmo

Data: 10/11/2026 · Planejador: Claude · Executor: Codex · Branch: `feature/slidedsl-api-voz-mobile`.
Mesmas **Regras** de `docs/PLANO_CODEX_COMPARACAO.md`, com estas diferenças:
- **Rodada 100% offline: nenhuma chamada a API de modelo ou de imagem. Orçamento US$ 0.**
- pytest: `--basetemp outputs\_tmp_r4` (não reutilizar pastas antigas).
- Fontes já registradas em `refs/DESIGN_RODADA4.md`. Leia antes.

## Princípio que não pode ser quebrado

O modelo decide **o que** cada slide comunica (gramática `.slda` inalterada); o compilador
decide **como** fica. Não mude a gramática Alto, o roundtrip `.slda` nem o contrato da IR
além do campo `font_face`, que já existe. O PPTX continua editável (formas e textos nativos).
Nada de coordenadas vindas do modelo, templates de terceiros ou HTML→imagem.

## Diagnóstico do planejador (evidência)

`outputs/api_voz_mobile/visual3_reciclagem_0003/previa.png/previa.png` e `outputs/estilos/*/previa.png`:

1. Estilos `claro/editorial/vibrante/natural/noturno` só mudam a paleta: mesma fonte (Arial fixa
   em `alto_layout.py` Builder), mesmas formas, mesmo layout. Lado a lado são indistinguíveis.
2. Cartões (slides 2 e 5) ocupam a faixa de cima; ~40% inferior da área útil vazio. Dentro do
   cartão, vão grande entre rótulo e descrição (rótulos usam a altura do maior + folga).
3. Monotonia: dois slides "3 cartões" idênticos num deck de 6; mesmos marcadores em toda parte.
4. `secao` num deck de 6 vira bloco "01" gigante com uma frase: parece enchimento.
5. Hierarquia fraca: uma família só; corpo cinza pequeno para o espaço disponível.
6. Foto do Commons de baixa resolução/relevância ocupa sempre meia página.

## Corpus fixo (antes × depois, mesmo conteúdo)

- `outputs/estilos/*.slda` (6 arquivos, mesmo conteúdo, estilos diferentes);
- todo `apresentacao.slda` de seed 42 em `outputs/comparacao_alto_sld/20261101-2227/`;
- `examples/alto/*.slda`.
Copie o corpus para a pasta da rodada antes de compilar; não altere os originais.

## Tarefas

### T1 — Linha de base
Criar `scripts/auditar_design_r4.py` (reutilizável): compila cada deck do corpus com o código
atual, gera prévia PNG por slide e folha de contato por deck, e grava métricas por slide
(T4) em JSON/CSV. Saída: `outputs/design_r4/<AAAAMMDD-HHMM>/antes/`. Rode **antes** de mudar código.

### T2 — Grade e tokens de espaçamento
Módulo novo `src/slidedsl/design_system.py`:
- grade de 12 colunas na área 64..1216 (gutter 24); helpers `col(i, span)`;
- escala de espaço única `[8, 16, 24, 32, 48, 64]`; proibir números mágicos novos nos layouts;
- título ancorado no mesmo y em todos os slides comuns; área útil = fim do título .. `CONTENT_BOTTOM`;
- distribuição vertical: o bloco de conteúdo ocupa **≥ 60% da altura útil** quando houver
  conteúdo suficiente, aumentando espaçamentos ou altura dos cartões (sem aumentar a fonte
  além do máximo do papel); se ainda sobrar, centralizar o bloco opticamente (um pouco acima do centro);
- cartão: padding 32, rótulo → descrição 12 px (corrigir o vão atual), descrição alinhada
  pelo topo entre cartões irmãos.
Migre os layouts de `alto_layout.py` para esses helpers (pelo menos topicos, numeros,
comparacao, etapas, imagem, conclusao, capa).

### T3 — Estilo = sistema de design, não paleta
Trocar as tuplas de `STYLES` por um dataclass `Estilo` com: paletas (comum e destaque),
`fonte_titulo`, `fonte_corpo`, `raio` (0 ou arredondado), `cartao` (`preenchido` | `fio` = linha
superior sem fundo | `bloco` = faixa lateral colorida), `marcador` (`barra` | `numero` | `ponto`),
`alinhamento_titulo`, `motivo_capa`. Só fontes presentes no Office do Windows e do macOS:
Arial, Calibri, Cambria, Georgia, Trebuchet MS, Verdana. Proposta (ajuste se a prévia mostrar problema):
| estilo | título / corpo | cartão | marcador |
|---|---|---|---|
| claro, escuro | Calibri / Calibri | preenchido | barra |
| editorial | Georgia / Calibri | fio | numero |
| vibrante | Trebuchet MS / Calibri | preenchido arredondado sobre `soft` | numero |
| natural | Cambria / Calibri | bloco | ponto |
| noturno | Calibri / Calibri | fio | barra |
Cada par de estilos deve diferir em ≥ 3 atributos além da cor.
- `text_metrics.py`: medir por família (`font_file(family, bold)`), mapear para os `.ttf` de
  `C:/Windows/Fonts` (calibri, calibrib, cambria.ttc, cambriab, georgia, georgiab, trebuc,
  trebucbd, verdana, verdanab) com candidatos macOS/Linux; sem a fonte, cair para Arial com
  fator de segurança e registrar. `needed_height` recebe a família.
- `ir_preview.py`: desenhar com a mesma família medida.
- Adaptar D003/D006 e `semantic.py` para aceitar a família do estilo (sem relaxar contraste
  D002 nem mínimos de tamanho). Teste: nenhum texto excede a caixa (A010/D010) no corpus em
  nenhum estilo.

### T4 — Variantes por slide escolhidas por nota estética (núcleo da rodada)
Para `topicos`, `numeros`, `comparacao`, `imagem` e `conclusao`, o compilador gera de 2 a 5
variantes candidatas (ex.: cartões, linhas rótulo|detalhe, grade 2×2 para 4 itens, primeiro item
em destaque + demais, foto 40% ou 50% conforme a proporção da imagem, número grande + explicação).
Descartar candidatas com erro (A010, A019, D001, D002, D008, D010). Pontuar as restantes
com funções puras em `src/slidedsl/layout_score.py`, cada uma em [0,1]:
- **ocupação**: união das caixas úteis / área útil; 1 na faixa 0,45–0,70, caindo fora dela;
- **equilíbrio**: distância entre o centro de peso visual (peso = área; texto escuro/forma
  cheia/imagem pesam mais que fio) e o centro da área útil, normalizada;
- **alinhamento**: menos bordas esquerdas/topos distintos (tolerância 2 px) = melhor;
- **regularidade**: desvio de tamanhos e espaçamentos entre irmãos;
- **ritmo**: penalidade se a variante (ou o tipo visual) for igual à do slide anterior.
Agregação não linear: média de potência com expoente negativo (ex.: p = −2) com pesos
documentados, para que um fator ruim derrube a nota. Desempate determinístico pela ordem
das variantes. Registrar variante escolhida e notas como diagnóstico INFO (novo código A030)
e no JSON da auditoria. Testes unitários de cada métrica com caixas sintéticas e um teste
de que a escolha é determinística. Documentar em `docs/REGRAS_DESIGN.md` como heurística,
sem alegar validação estética (as patentes também não têm validação psicofísica).

### T5 — Ritmo do deck
- Nunca a mesma variante em dois slides seguidos quando existir alternativa válida.
- `secao` em deck com menos de 8 slides: em vez do bloco numerado gigante, layout de "frase
  de transição" (título grande + subtítulo, motivo discreto do estilo). Bloco numerado só em
  decks com 8 slides ou mais. Em `alto_generation.py`, orientar o modelo a evitar `secao` em
  decks curtos (só o prompt; sem chamada extra).
- `conclusao` deve ter visual próprio (ex.: ações numeradas em destaque), diferente de `topicos`.

### T6 — Imagens
- Na seleção automática (`media.py`), rejeitar fotos com lado maior < 1000 px quando houver
  alternativa; teste offline.
- No compilador, aviso A031 para imagem local com lado maior < 1000 px (sem bloquear).
- Proporção decide a largura da coluna da foto (T4); recorte central só na meia página sangrada.

### T7 — Ciclos e comparação
Até 3 ciclos: recompilar o corpus → `outputs/design_r4/<ts>/ciclo_N/` → **abrir as folhas de
contato** e escrever `REVISAO.md` (o que melhorou, o que piorou, próxima correção). Parar
quando os defeitos 1–5 estiverem resolvidos no corpus ou após o 3º ciclo. Por fim, gerar
`outputs/design_r4/<ts>/comparacao/` com folhas antes|depois lado a lado por deck e tabela:
nota média, ocupação média e faixa, nº de variantes distintas por deck, slides seguidos com
a mesma variante, contagem de A010/A019/A031. Sem editar saídas à mão.

### T8 — Qualidade e registros
pytest completo (`--basetemp outputs\_tmp_r4`), `ruff check src tests scripts`, testes Node do
renderer; se tocar em `editor/src`, `npm run build` e lint. Atualizar `docs/REGRAS_DESIGN.md`,
`docs/PROGRESSO.md`, `ROADMAP.md` (seção "Rodada 4 de design") e
`docs/CONTINUIDADE_API_VOZ_MOBILE.md`. Sem commit/push.

## Mensagem final esperada

Arquivos alterados; atributos de cada estilo; variantes por tipo e pesos da nota; tabela
antes × depois; achados por ciclo; testes com números; caminhos das folhas de contato
finais (antes|depois); o que continua ruim.
