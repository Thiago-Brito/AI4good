# Plano para o Codex — rodada 6: acabamento + testes reais

Data: 11/11/2026 · Planejador: Claude · Executor: Codex. Regras de `docs/PLANO_CODEX_COMPARACAO.md`
e princípio da rodada 4 (gramática Alto inalterada, PPTX editável, sem commit/push/stash).
pytest: `--basetemp outputs\_tmp_r6`. Corpus offline: o mesmo de
`outputs/design_r5/20261111-001430/corpus/`; linha de base = `.../ciclo_3/`.

**Parte A é offline (US$ 0). Parte B usa a API real, com teto de US$ 0,50 no total.**

## Revisão do planejador sobre a rodada 5

Evidência: `outputs/design_r5/20261111-001430/ciclo_3/{01_editorial,05_vibrante,06_energia_solar_B_img_s42}/contato.png`.
Preservar tudo que a r5 conquistou (critérios (a)–(e) da r5 devem continuar valendo).

Defeitos restantes:
1. **Rótulos de cartões desnivelados.** Editorial slide 5: "Placas por tipo" mais baixo que os
   vizinhos; conclusão: "Repita o mesmo ponto" mais alto. Rótulos devem ser alinhados pelo
   **topo** em todos os cartões irmãos; a descrição começa no mesmo y em todos (abaixo do
   rótulo mais alto + 12 px). Teste: y dos rótulos irmãos idêntico; y das descrições idêntico.
2. **Vão rótulo → descrição ainda grande** e ~30% vazio abaixo dos cartões. A altura do cartão
   abraça o conteúdo + padding; o bloco de cartões é posicionado opticamente (centro − 5% da
   área útil) — não alongar cartões com interior vazio. Se a ocupação ficar baixa, preferir
   aumentar fonte até o perfil máximo do papel antes de criar vazio interno.
3. **Mesma foto, tamanhos diferentes por estilo** (vibrante slide 3: foto das lixeiras pequena;
   editorial: grande). A escolha de variante de imagem não pode depender do estilo. Imagem com
   A031 (baixa resolução) usa `photo50` sangrada mesmo assim se o lado maior ≥ 600 px; abaixo
   disso, layout sem foto ou foto como faixa. Nunca foto contida menor que 45% da largura útil.
4. **Números da conclusão soltos** acima dos cartões ("1 2 3"). Integrar o número ao cartão
   (no topo interno, maior, na cor de destaque, alinhado ao rótulo) ou removê-lo quando o estilo
   já usa marcador numérico.
5. **Transições curtas esparsas.** Usar o motivo do estilo com mais presença (ex.: frase maior,
   até 54 pt, e bloco de cor ocupando ~1/3), sem voltar ao "01" gigante.

## Parte A — tarefas offline

1. Corrigir 1–5 com testes. 2. Até 2 ciclos com `scripts/auditar_design_r4.py` →
`outputs/design_r6/<ts>/ciclo_N/`, abrir folhas, `REVISAO.md`. 3. pytest + ruff + Node verdes
antes da Parte B.

## Parte B — testes reais (geração completa pela API)

Objetivo: o usuário quer **ver decks novos de verdade**, gerados do zero com o código final.

- Provedor `openai`; modelo `gpt-5.4-mini` (padrão do ROADMAP). Se a tarifa desse modelo não
  estiver configurada no `.env` (verifique só a existência da chave de configuração, **nunca**
  imprima valores nem a chave de API), use o modelo com tarifa configurada e registre.
- Imagens: busca Commons/Openverse licenciada (`--imagens`); **sem imagens por IA** (custo).
- 6 decks, cada um num estilo diferente, 6 slides, seed 42:
  | estilo | pedido |
  |---|---|
  | claro | Energia solar residencial para quem pensa em instalar painéis em casa |
  | editorial | Reciclagem no dia a dia para alunos do ensino médio |
  | vibrante | Como funciona a fotossíntese, para alunos do 7º ano |
  | natural | Cuidados básicos com hortas caseiras em apartamento |
  | escuro | Introdução ao Git para estudantes de programação |
  | noturno | Breve história da internet para adolescentes |
- Pesquisa: desligada (padrão com OpenAI), exceto se não custar chamadas extras de modelo.
- Ledger compartilhado: abortar antes de iniciar um deck se o gasto conhecido + estimativa
  passar de US$ 0,50; uso ausente é desconhecido (reservar, nunca zero).
- Falha de um deck: registrar o erro e seguir para o próximo; **não** editar saídas à mão.

**Onde guardar (o usuário vai abrir):** `outputs/testes_reais/<AAAAMMDD-HHMM>/`
- uma subpasta por deck: `NN_<estilo>_<tema>/` com `apresentacao.pptx`, `apresentacao.slda`,
  `contato.png`, PNGs por slide, `diagnosticos.json`, `uso.json` (tokens/custo);
- `INDICE.md` na raiz: tabela deck × estilo × válido × nº fotos × custo × link do PPTX e da
  folha de contato, e **observações honestas** do que ficou bom e ruim em cada deck após abrir
  cada folha;
- `galeria.png`: as 6 folhas de contato numa imagem só, rotuladas por estilo.
Atualizar `outputs/testes_reais/ULTIMO.txt` com o caminho da execução.

## Registros
Atualizar `docs/REGRAS_DESIGN.md`, `docs/PROGRESSO.md`, `ROADMAP.md` (Rodada 6),
`docs/CONTINUIDADE_API_VOZ_MOBILE.md`.

## Mensagem final esperada
Arquivos alterados; correções 1–5 com evidência; testes; tabela dos 6 decks reais (válido,
fotos, chamadas, tokens, custo); gasto total conhecido/desconhecido; caminho da pasta
`outputs/testes_reais/...`, do `INDICE.md` e da `galeria.png`; o que continua ruim.
