# Plano para o Codex — rodada 2: design e imagens

Data: 01/11/2026 · Planejador: Claude · Executor: Codex. Continua `docs/PLANO_CODEX_COMPARACAO.md`
(mesmas **Regras**: sem segredos, sem `verify=False`, sem commit/stash/`git add .`, não sobrescrever
`outputs/`). Orçamento de API desta rodada: **US$ 0,40** (soma conhecida; abortar se passar).

## O que mudou desde a rodada 1

- Causa real do HTTP 403 da Wikimedia: faltava `SLIDEDSL_CONTACT` (User-Agent sem contato).
  Agora está no `.env` local e em `local_settings.KEYS`. Busca de teste retornou 5 fotos CC BY-SA.
  Openverse continua dando timeout: tratar como opcional, com timeout curto, sem travar o fluxo.
- Não use `outputs\_pt` (ficou sem permissão). Para pytest use `--basetemp outputs\_tmp_r2`.

## Diagnóstico de design (revisão do planejador sobre as PNGs da rodada 1)

Evidência: `outputs/comparacao_alto_sld/20261101-2131/*_B*/contato.png`.

1. **Gráfico falso na capa.** As capas de Git e Energia solar mostram um gráfico de barras
   decorativo sem dados. Parece dado real e engana. Proibir gráfico/números decorativos.
   Capa: foto licenciada quando houver; senão, motivo abstrato neutro (formas, faixa de cor) ou só tipografia.
2. **Decks idênticos.** Os três temas seguem a mesma sequência (3 cartões → lista numerada →
   duas colunas/linha do tempo → painel de conclusão). A composição precisa variar conforme o
   conteúdo e evitar repetir a mesma composição em slides vizinhos; não repetir a mesma sequência entre decks
   por padrão.
3. **Composição incompatível com o conteúdo.** Ex.: linha do tempo numerada para itens que não
   são etapas ("Exemplo de planta comum" como passo 1). Só usar linha do tempo/passos para sequência real.
4. **Rótulos que repetem o título ou a coluna.** "Função dos painéis / Função do inversor /
   Importância do inversor"; coluna "Cuidados na avaliação" com item "Cuidados na avaliação".
   Rótulo deve trazer informação nova, curta (2–4 palavras), sem repetir o título nem o cabeçalho.
5. **Hierarquia tipográfica inconsistente.** Descrições do painel de conclusão e das colunas
   ficam muito pequenas (parecem < 14 pt) enquanto rótulos são grandes; tamanhos variam entre
   slides do mesmo deck para o mesmo papel. Definir escala fixa por papel (título, rótulo, corpo),
   com corpo mínimo legível (≥ 14 pt) e reduzir texto antes de reduzir fonte.
6. **Títulos quebrando com palavra órfã** ("…confusão e / perda", "…aproveitar o / sol").
   Títulos de assertiva com até ~45 caracteres ou quebra balanceada; título em caixa de frase
   (não Title Case como "Energia Solar Residencial: Entenda Antes de Avaliar").
7. **Espaço vazio mal distribuído.** Cartões com metade inferior vazia; vão grande entre título
   e painel no slide final. Ajustar altura ao conteúdo ou centralizar o bloco verticalmente.
8. **Repetição semântica não detectada.** Energia solar: slides 2 e 3 explicam o mesmo
   (conversão/inversor). O Jaccard lexical deu 0. O roteiro deve atribuir a cada slide uma
   pergunta distinta e listar no prompt o que já foi coberto (sem chamada extra).
9. **Erro factual de contexto.** "Telhados voltados para o sul recebem mais luz" está errado
   para o Brasil (hemisfério sul: norte). Os prompts devem assumir público brasileiro salvo
   indicação contrária e evitar afirmações dependentes de localização sem dizer o contexto.
10. **Sem imagens.** Agora a busca funciona. Com `images=True`, ter 1–2 slides com foto
    relevante: layout foto em meia página (sangrada) + texto curto, crédito/licença visível
    em fonte pequena. Se a foto encontrada for irrelevante (ex.: mosca numa folha), rejeitar
    por critério local (título/descrição vs. consulta) e cair no fallback.
11. Prévia: o "₂" de CO₂ vira quadrado nas PNGs. Usar fonte com esse glifo na prévia (ou
    registrar que é só da prévia) e conferir que o PPTX guarda o caractere correto.

## Tarefas

1. Ler `alto_layout.py`, `alto_compile.py`, `design_rules.py`, `ir_preview.py`, `alto_generation.py`
   e os chamadores. Corrigir os itens 1–11 no compilador/regras/prompts, priorizando o que é
   determinístico (compilador) sobre o que depende do modelo. Nenhuma chamada extra de
   modelo no caminho feliz. Testes offline para cada regra nova (capa sem gráfico decorativo,
   variação de composição, rótulo ≠ título/cabeçalho, escala tipográfica mínima, título sem órfã,
   foto com crédito, rejeição de foto irrelevante).
2. **Ciclo de iteração (até 3 ciclos):** gerar B+img para os 3 briefs existentes e um 4º brief novo
   (para não ajustar só aos mesmos temas; sugestão: "história da internet para ensino fundamental"),
   gerar PNGs e folhas de contato, **olhar as PNGs** e anotar defeitos visuais em
   `outputs/design_r2/<AAAAMMDD-HHMM>/ciclo_N/REVISAO.md`. Corrigir e repetir. Parar quando não houver defeito dos itens
   1–10 ou ao fim do 3º ciclo. Não editar saídas do modelo à mão.
3. **Comparação final** com o harness `scripts/comparar_alto_vs_sld.py`: A, B e B+img nos 4 briefs,
   pasta nova em `outputs/comparacao_alto_sld/`. Mesmo protocolo e limitações da rodada 1.
   No relatório, comparar com a rodada 1 (custo, tokens, válidos, diagnósticos, imagens incluídas).
4. pytest completo + `ruff check src tests scripts`. Atualizar `docs/CONTINUIDADE_API_VOZ_MOBILE.md`,
   `ROADMAP.md`, `docs/PROGRESSO.md`.

## Mensagem final esperada

Arquivos alterados; o que cada ciclo encontrou e corrigiu; testes; gasto conhecido; tabela A × B × B+img
da rodada 2 vs rodada 1; quantas imagens entraram; caminhos das folhas de contato finais; o que
continua ruim.
