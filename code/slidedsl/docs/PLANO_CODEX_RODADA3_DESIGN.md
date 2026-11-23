# Plano para o Codex — rodada 3: legibilidade, ocupação e texto

Data: 01/11/2026 · Planejador: Claude · Executor: Codex. Mesmas **Regras** de
`docs/PLANO_CODEX_COMPARACAO.md`. Orçamento de API desta rodada: **US$ 0,60** (soma conhecida).
pytest: `--basetemp outputs\_tmp_r3` (não reutilizar `_pt`/`_tmp_r2`).

## Revisão do planejador sobre a rodada 2

Evidência: `outputs/comparacao_alto_sld/20261101-2203/{git,energia_solar}_B_img/contato.png`.

O que melhorou e deve ser preservado: sem gráfico falso; "norte (hemisfério sul)"; foto com
crédito no slide do inversor; títulos mais curtos; variedade maior de composições.

Defeitos a corrigir, em ordem de prioridade:

1. **Regressão de legibilidade (crítico).** O corpo de texto encolheu (Git slides 2, 3 e 5
   parecem ~11–12 pt num slide 13,33 in). Era para crescer. Regra dura no compilador:
   corpo ≥ 16 pt, rótulo ≥ 20 pt, título ≥ 32 pt (ajuste os números ao sistema de unidades real
   e documente). **Nunca reduzir fonte abaixo do mínimo para caber**: se não couber, mudar
   composição, dividir em menos itens, ou pedir ao modelo texto mais curto no reparo já existente.
   Teste: nenhum texto de corpo na IR final abaixo do mínimo, em todos os decks do experimento.
2. **Ocupação/equilíbrio vertical.** Conteúdo ocupa faixa estreita e deixa metade do slide
   vazia (Git slide 3: dois itens soltos; slide 2: cartões numa faixa; Energia slide 2: vão
   entre título e cartões). Regra: o bloco de conteúdo distribui a altura disponível
   (centralizar verticalmente ou expandir espaçamento/fonte até o máximo do papel); com
   2 itens, usar composição de 2 colunas grandes ou destaque, não lista com vão.
   Métrica local: fração da área útil ocupada por texto/elementos; avisar abaixo de um limiar.
3. **Rótulos telegráficos.** "Problema cópias manuais", "Cuidados avaliação imóvel":
   rótulo curto não pode cortar preposições/artigos. Pedir rótulos de 2–5 palavras em
   português natural; validação local simples (ex.: rótulo que é o título sem preposições → aviso).
4. **Repetição dentro do slide.** Três cartões começando com "Salvar cópias manuais…".
   Cada descrição deve trazer um fato diferente e não repetir o rótulo nem o início das irmãs.
   Checagem local de prefixo/sobreposição entre irmãos; usar o reparo existente.
5. **Repetição entre slides** (Energia 4 e 5 tratam de avaliação/sombreamento). No roteiro,
   cada slide recebe uma pergunta única; o slide de conclusão deve sintetizar/agir, não
   repetir itens anteriores.
6. **Capa.** Ainda Title Case ("Energia Solar Residencial Descomplicada") e círculo azul genérico.
   Normalizar para caixa de frase preservando siglas/nomes próprios. Com `images=True`,
   preferir a melhor foto relevante na capa (meia página, com crédito); sem foto, motivo
   abstrato discreto. Subtítulo da capa legível (≥ 18 pt).
7. **Imagens.** 3 fotos em 4 decks. Meta: ≥ 1 foto relevante por deck quando houver no Commons
   (Git pode não ter; aceitar fallback). Reutilizar o resultado da busca da capa se servir.

## Tarefas

1. Corrigir 1–7 com testes offline, priorizando o compilador determinístico. Sem chamada extra
   de modelo no caminho feliz.
2. **Ciclos (até 3):** B+img nos 4 briefs → PNGs → olhar → `outputs/design_r3/<AAAAMMDD-HHMM>/ciclo_N/REVISAO.md`.
   Parar quando 1–6 estiverem resolvidos ou após o 3º ciclo. Sem edição manual de saídas.
3. **Comparação final com repetições:** A, B e B+img nos 4 briefs, **3 repetições** cada
   (seeds 42, 43, 44), pasta nova. Reportar média e faixa (mín–máx) de custo, tokens, taxa de
   válidos e custo por slide válido; destacar que a rodada 1 (n=1) teve validade instável para A
   (1/3 vs 4/4 na rodada 2 sem mudança no caminho de A).
4. pytest + ruff + testes Node; atualizar `CONTINUIDADE_API_VOZ_MOBILE.md`, `ROADMAP.md`, `PROGRESSO.md`.

## Mensagem final esperada

Arquivos alterados; achados/correções por ciclo; tamanhos mínimos adotados; testes; gasto conhecido;
tabela final (média e faixa) A × B × B+img; fotos incluídas por deck; caminhos das folhas
de contato finais; o que continua ruim.
