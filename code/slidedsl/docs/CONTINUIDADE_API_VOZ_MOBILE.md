# Continuidade — APIs, voz e celular

Atualizado em **11/11/2026**. Este é o ponto de entrada para continuar o trabalho.
Última execução: **Rodada 7**, registrada ao final: documentos TXT/MD/PDF/DOCX,
edição de um slide com histórico e estilo automático. Seis PPTX finais, 42 slides.
Evidências: `outputs/testes_reais/20261111-0131_r7/INDICE.md`.
Gasto conhecido US$ 0,31454265; total exato desconhecido; limite com reservas
US$ 0,39645915 no teto autorizado de US$ 0,60. Lote encerrado; não zerar o ledger.
Plano: [PLANO_API_VOZ_MOBILE.md](PLANO_API_VOZ_MOBILE.md).

## Estado atual

- Branch criada primeiro: `feature/slidedsl-api-voz-mobile`, base `168c29f` (`slidedsl`).
- Fase 1 implementada, verificada offline e com piloto remoto real: seleção de OpenAI no fluxo Alto, schema estrito,
  recusa/interrupção explícitas, auditoria de todas as inferências e limites de chamadas/saída.
- Credencial fornecida e salvamento local autorizados pelo usuário. Está em `code/slidedsl/.env`,
  ignorado e não rastreado. **Nunca copiar seu conteúdo para documentação, exemplos ou commits.**
  O servidor carrega o arquivo no startup; ambiente externo tem precedência. Reiniciar o
  servidor após mudar a configuração. Não há chave no JavaScript enviado ao navegador.
- **Piloto remoto concluído.** Causa da falha HTTPS anterior: o Kaspersky intercepta TLS
  (emissor `Kaspersky Anti-Virus Personal Root Certificate`). O Windows confia nessa raiz,
  o `certifi` do HTTPX não. `openai_model.py` agora usa `ssl.create_default_context()`
  (repositório do sistema, verificação ativa). Não desativar verificação TLS.
  Desde a comparação abaixo, `https.py` centraliza o contexto do sistema para
  OpenAI, `research.py` e `media.py`. Busca real concluiu TLS, mas Commons respondeu
  HTTP 403 por política de robôs; Openverse apresentou timeout. Imagens reais
  continuavam sem comprovação funcional naquela rodada. A rodada 2 abaixo comprovou
  busca/download Commons com contato configurado, mantendo TLS ativo.
- Não houve commit, push, publicação ou alteração dos arquivos pessoais preexistentes.

## O que foi implementado e onde

| Área | Arquivos e comportamento |
| --- | --- |
| Adaptador/contrato | `models/base.py`, `openai_model.py`, `ollama_model.py`, `llamacpp_model.py`: capacidades e chamada sem fallback por TypeError; OpenAI envia schema estrito adaptado e valida o domínio localmente. Mantido Chat Completions. |
| Auditoria | `model_usage.py`: uso e custo por tentativa, cache sem duplicação, uso ausente como desconhecido, limite antes da nova chamada, arquivo da chamada pendente antes do HTTP. |
| Integração | `alto_generation.py`, `research.py`, `alto_jobs.py`: pesquisa e extração entram no total; callback atualiza consumo durante a execução; falhas preservam `uso.json` e `relatorio.json`. |
| API/configuração | `server.py`, `local_settings.py`: `/api/providers` sem chamada externa nem chave, OpenAI em `/api/criar`, limites validados, `.env` local apenas com nomes de configuração permitidos, incluindo opções Ollama/Node do exemplo anterior. |
| Interface/CLI | `CriarPanel.tsx`, `UsageSummary.tsx`, `types.ts`, `alto_cli.py`: provedor visível, modelo lembrado por provedor, um candidato por padrão, consumo parcial explícito; CLI `--max-chamadas`. |
| Testes | `tests/test_openai_alto.py` cobre HTTP, falhas, cache, limites, pesquisa e exportação; `editor/tests/openai.spec.ts` cobre envio, preferências e consumo; regressões existentes preservadas. |
| Piloto | `scripts/piloto_openai.py`: um deck de três slides pela API web, até oito inferências, sem pesquisa/imagens; salva evidências em `outputs/api_voz_mobile/piloto_<id>/`. Executa cobrança quando a conexão funcionar; não integra a suíte automática. |

Na fase 1 não havia salvamento/reabertura de projetos, histórico de revisões, chat de edição ou voz.
Na rodada 7 há revisões persistidas dos jobs Alto e desfazer; projeto com IDs estáveis,
reabertura pela UI, chat geral e voz continuam fora desta entrega.
O editor existente continua importando, editando e exportando DSL/PowerPoint.

## Comparação Alto × SLD — 01/11/2026

Executado `docs/PLANO_CODEX_COMPARACAO.md`, com falhas e limites preservados.
Código: helper TLS, autoria da capa condicionada ao pedido, contexto curto dos
slides anteriores, Jaccard determinístico (A017, limiar 0,72) com reparo limitado,
itens curtos no prompt e roteiro com imagem/consulta em inglês. Resolução Alto
restrita a Wikimedia Commons, sem custo de tokens; fallback em tópicos mantido.
A011 de imagem pendente não provoca reescrita inútil. Nenhum limite visual ampliado.

Harness pago: `scripts/comparar_alto_vs_sld.py`; briefs em
`experiments/comparacao/briefs/`; fontes/protocolo em `refs/COMPARACAO_ALTO_SLD.md`.
Modelo gpt-4.1-mini, temperatura 0,2, seed 42 fixos em todas as inferências.
RecordedModel soma todas as rodadas, inclusive reparos de A, tópicos e falhas.
O orçamento bloqueia novas chamadas sem saldo conservador e mantém custos
desconhecidos como desconhecidos, reservando um limite superior auditável.

Lote principal: `outputs/comparacao_alto_sld/20261101-2131/`, com CSV, JSON,
`RELATORIO.md`, `auditoria_final.json`, `orcamento.json`, fontes/cru/validações,
seis PPTX (30 slides), 35 PNGs em `<execução>/pngs/` e sete folhas `contato.png`.
Usado Pillow/IR; as prévias não renderizam o PPTX no Office. Sete folhas foram
inspecionadas pelo executor, sem avaliação humana cega.

| Condição | Tokens entrada/saída/cache | USD | Válidos/PPTX | ERRO/AVISO |
| --- | --- | --- | --- | --- |
| A | 19.094 / 8.292 / 2.560 | 0,0201368 | 1/3 | 2/9 |
| B | 24.666 / 5.253 / 1.024 | 0,0179640 | 3/3 | 0/0 |
| B+img | 27.532 / 5.296 / 2.048 | 0,0188720 | 2/3 | 1/0 |

Lote principal: 59 chamadas com uso conhecido, US$ 0,0569728. B reduziu custo
em 10,79%, B+img em 6,28%, mas aumentaram os tokens totais em 9,25% e 19,87%.
Não se demonstrou redução de tokens, qualidade equivalente nem generalização.
Custo por slide válido: A US$ 0,00402736, B US$ 0,00119760, B+img US$ 0,00188720,
incluindo falhas no numerador e somente slides de PPTX válidos no denominador.

Experimento inteiro: 90 chamadas, 72 com uso conhecido e 18 sem uso. Gasto
conhecido US$ 0,0703364; total exato desconhecido; teto conservador incluindo
reservas US$ 0,2325972, abaixo de US$ 1,00. Tentativas e diagnósticos anteriores
estão preservados nos diretórios de 2125/2128/2130 e `diagnostico*`, discriminados
no ledger; a tentativa A copiada na retomada é contabilizada uma vez. Não fazer
novas chamadas para preencher essas lacunas de uso.

Problemas: P001 em A/fotossíntese e A/solar (sem IR/PNGs), oito D010 e um D008
no A/Git exportado, A010 de rótulo longo no B+img/solar (tem prévia, sem PPTX).
Zero imagens incluídas; Commons 403. Glifo CO₂ aparece como quadrado na prévia.
Há retomadas conceituais apesar de Jaccard zero, e o conteúdo não foi validado
factualmente. Amostra de três temas, uma repetição, um modelo, condições com
prompts/reparos diferentes e tentativas prévias de rede limitam as conclusões.
No lote, hashes representam o texto normalizado LF; os arquivos congelados eram
idênticos entre condições, mas A transportava CRLF e B LF. Harness atual grava
bytes sem conversão; `harness_executado.py` preserva a versão usada.

Execução que concluiu o lote: Python via stdin com `runpy.run_path` e
`--carry-budget outputs/comparacao_alto_sld/diagnostico_exec_20261101-213118/orcamento.json`.
Não se identificou a causa das falhas intermitentes da API; nunca se desativou TLS.
Regressão final após auditoria: **421 testes passaram em 91,50 s**, com um aviso
preexistente Starlette/AnyIO; **Ruff limpo** (`ruff check src tests scripts`).
Evidências em `20261101-2131/pytest_final.xml` e `ruff_final.txt`.
Remoção de `outputs/_pt` rejeitada duas vezes pela política do ambiente
(`blocked by policy`), inclusive com caminho literal absoluto já verificado.
A pasta permanece. Branch preservada; nenhum commit/push.

## Rodada 2 de design — 01/11/2026

Executado `docs/PLANO_CODEX_RODADA2_DESIGN.md`, tarefas 1–4, até o limite de
três ciclos. Evidências preservadas em `outputs/design_r2/20261101-2154/` e
lote final em `outputs/comparacao_alto_sld/20261101-2203/RELATORIO.md`.
Fontes/protocolo: `refs/DESIGN_RODADA2.md`. Nenhuma saída do modelo foi editada
à mão. Nenhum commit, push, stash, segredo registrado ou TLS desativado.

Compilador: capa sem barras falsas; composição por densidade com alternância
quando cabe; tópicos sem números, etapas conservadoras; rótulos repetidos ou
contidos no título/cabeçalho suprimidos sem apagar explicações; escala fixa por
deck (42/24/20 pt ou perfil compacto 42/20/16 pt); títulos medidos/balanceados;
listas e cartões com altura pelo conteúdo. D006 cobre corpo conhecido <14 pt.
Fotos em meia página com crédito visível e licença/origem nas notas; recorte
coerente entre renderer e prévia. Segoe UI cobre subscritos na prévia, CO₂
conferido no XML do PPTX em teste real. A018 orienta reparo existente de títulos.
Prompts recebem perguntas distintas/objetivos, conteúdo já coberto e contexto
brasileiro, sem chamada extra no caminho feliz.

Mídia: Commons real comprovado com contato local configurado. Openverse não
integra esse caminho. Filtro usa título/descrição/consulta, licença/resolução,
veta macro incidental e gráfico estatístico não solicitado; ainda é lexical.
`imagens.json` audita candidatos/seleção. Git final caiu no fallback textual.

| Ciclo | Válidos | Imagens no PPTX | USD conhecido do ciclo |
|---|---:|---:|---:|
| 1 | 1/4 | 1 | 0,0320992 |
| 2 | 4/4 | 1 | 0,0261728 |
| 3 | 4/4 | 4 | 0,0300044 |

Quatro folhas de cada ciclo abertas como imagens; defeitos/correções em
`ciclo_N/REVISAO.md`. Ciclo 1: overflow após foto; corrigidos schema de dois
itens e pré-validação da mesma meia página. Ciclo 2: poucas fotos/Title Case/
repetições; ajustados consulta, relevância, rótulos e feedback. Ciclo 3: gráfico
estatístico em Git; veto local antes da comparação final. Parada pelo limite
de três ciclos, com problemas editoriais remanescentes documentados.

Lote final: quatro temas × A/B/B+img, modelo/parâmetros/protocolo preservados,
11 PPTX (55 slides), 60 PNGs e 12 folhas. Todas as folhas abertas pelo executor;
`REVISAO_FINAL.md` detalha cada tema/condição. Pillow/IR não comprova Office.

| Condição | Entrada/saída/cache | USD | Válidos | ERRO/AVISO | Imagens |
|---|---:|---:|---:|---:|---:|
| A | 39.163/11.134/3.712 | 0,0323660 | 4/4 | 0/28 | 1 |
| B | 46.821/7.170/5.760 | 0,0284724 | 3/4 | 1/2 | 0 |
| B+img | 49.179/7.404/6.272 | 0,0296364 | 4/4 | 0/6 | 3 |

A contém uma imagem geométrica demonstrativa inadequada ao exemplo de planta;
B+img contém três fotos Commons com crédito/licença. B/Internet falhou por
A010 no detalhe de uma comparação. Avisos finais Alto são A018 de título;
A tem 26 D010 e dois D002. Repetição semântica, rótulos genéricos, Title Case,
omissões e afirmações factuais não verificadas persistem.

Nos três temas compartilhados com a rodada 1: A/B/B+img agora 3/3 válidos;
custos 0,0248248/0,0201216/0,0215332 USD. Na rodada 1 eram 1/3, 3/3 e 2/3,
com 0,0201368/0,0179640/0,0188720 USD. Lote final de quatro temas reduz custo
total de B/B+img frente a A em 12,03%/8,43%; B tem maior custo por slide válido
por causa da falha. Não se demonstrou economia de tokens nem qualidade equivalente.

Rodada inteira: **207 chamadas**, 203 com uso conhecido e quatro desconhecidas;
**US$ 0,1787512 conhecidos**, total exato desconhecido, teto conservador
**US$ 0,20175**, abaixo do orçamento US$ 0,40. Lote final US$ 0,0904748;
ciclos US$ 0,0882764. Tentativas diretas iniciais falharam no transporte;
retomada via stdin/runpy funcionou. Não se atribuiu causa sem evidência.

Verificação final: **438 testes passaram** em 86,16 s (um aviso Starlette/AnyIO
preexistente), Ruff limpo, dois testes Node passaram. Hashes do código executado,
briefs idênticos entre condições e ledger conferidos em `auditoria_final_r2.json`.
Remoção de `outputs/_tmp_r2` rejeitada pela política automática apesar da verificação
do caminho; pasta preservada. Limite de três ciclos atingido; novas despesas
dependem de nova solicitação. Próxima fase funcional continua sendo projetos
persistidos, separada das pendências de qualidade editorial.

## Rodada 3 de design — 01/11/2026

Plano: [PLANO_CODEX_RODADA3_DESIGN.md](PLANO_CODEX_RODADA3_DESIGN.md). Executor (Codex) concluiu
os três ciclos (`outputs/design_r3/20261101-2216/`) e o lote final com 3 seeds
(`outputs/comparacao_alto_sld/20261101-2227/`), mas parou por limite de uso da conta antes
da tarefa 4; o registro e a verificação foram feitos pelo planejador. 452 testes Python
passaram; Ruff limpo. Gasto conhecido do lote: US$ 0,3704, sem chamadas de uso desconhecido.

| Condição (4 temas × 3 seeds) | Válidos | Tokens entrada+saída | USD | USD/slide válido | ERRO/AVISO |
| --- | ---: | ---: | ---: | ---: | ---: |
| A — IA escreve `.sld` | 11/12 | 137.876 | 0,0947 | 0,00172 | 1/91 |
| B — Alto + compilador | 12/12 | 168.054 | 0,0860 | 0,00143 | 0/8 |
| B+img | 10/12 | 179.984 | 0,0927 | 0,00185 | 2/21 |

Leitura: B custa ~9% menos no total e ~17% menos por slide válido, com muito menos avisos de
layout, mas **consome ~22% mais tokens** (uma chamada por slide repete instruções/schema).
Não alegar economia de tokens com este fluxo. Validade de A oscilou entre rodadas (1/3, 4/4,
11/12) sem mudança no seu caminho: amostra pequena. Revisão visual do planejador: corpo
legível (≥ 16 pt), fotos licenciadas com crédito na capa e em slides internos, caixa de frase,
ocupação melhor. Pendências vistas nas PNGs: rótulo vazio e rótulos em minúsculas copiados
dos tópicos (Internet s42, slide 2); título factual errado ("folhas capturam água"); entradas/saídas
repetidas entre slides 2 e 4 (fotossíntese); faixa cinza decorativa sem função na capa sem foto;
cartões de conclusão com texto centralizado e vazio acima. As PNGs são prévias Pillow/IR.

Próximo experimento recomendado: condição **B-lote** (conteúdo de todos os slides em uma
chamada estruturada, compilador igual) para atacar o custo de entrada repetida.
Pasta `outputs/_pt`, `_tmp_r2` e `_tmp_r3` criadas pelo sandbox do Codex não podem ser
removidas pelos agentes; apagar manualmente.

## Rodada 4 (planejador implementou) — 01/11/2026

Feito sem o Codex. Mudanças:
- Removidas do prompt regras específicas dos temas do experimento (telhado/hemisfério,
  Git) e a lista fixa de nomes próprios do `sentence_case`; substituídas por regras gerais
  (contexto para afirmações dependentes de lugar; nome próprio só com evidência no pedido).
- `alto_quality.structural_topic`: "Conclusão", "Exemplos concretos" etc. não viram tópicos.
- `editorial.visible_labels`: rótulos de um grupo são suprimidos juntos (antes, um item
  ficava sem rótulo). Comparação exige duas alternativas do mesmo tipo e usa a mesma
  composição nas duas colunas. Cartões abraçam o conteúdo, texto alinhado ao topo e na
  mesma linha entre cartões. Capa sem foto: barra lateral, sem forma decorativa solta.
- **B-lote** (`generate_alto(batch=True)`, `batch_content`): roteiro + uma chamada
  estruturada para todos os slides; mesmas validações; reparo individual só do slide
  reprovado; falha do lote cai para slide a slide; limite de chamadas nunca é contornado.
  `title_budget` informa a contagem quando a mensagem do roteiro excede o título.
- 458 testes Python; Ruff limpo.

Lote `outputs/comparacao_alto_sld/20261101-2307_r4/` (4 temas × 3 seeds; US$ 0,3035):

| Condição | Válidos | Tokens entrada+saída | Chamadas/execução | USD | USD/slide válido | ERRO/AVISO |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A — IA escreve `.sld` | 11/12 | 141.151 | 3,0 | 0,0957 | 0,00174 | 1/89 |
| B — Alto, slide a slide | 12/12 | 146.033 | 8,2 | 0,0746 | 0,00124 | 0/5 |
| B+img | 10/12 | 164.368 | 8,8 | 0,0806 | 0,00161 | 2/10 |
| **B-lote** | 11/12 | **83.866** | 4,4 | **0,0526** | **0,00096** | 1/4 |

B-lote usou **41% menos tokens** e custou **45% menos** que A, com menos avisos de layout.
Primeira evidência, nesta amostra (4 temas, 3 seeds, um modelo, sem pesquisa), de economia
de tokens pela representação Alto + compilação. Não generalizar; falta avaliação humana cega.

Pendências observadas nas PNGs/diagnósticos:
- Falhas de B, B+img e B-lote são A010 (texto estoura por poucos px) detectado só na
  compilação final, sem reparo. Próximo passo: pré-validar layout do slide na geração ou
  recompor automaticamente antes de falhar.
- Sem a regra específica, voltou "telhados voltados para o sul no Brasil" (B+img s42):
  afirmação dependente de lugar exige fato com fonte; prompt genérico não basta.
- Rótulos ainda genéricos às vezes ("Função das folhas", "Importância do ambiente") e
  rótulos que repetem o título quando os irmãos são distintos.

## Rodada 5: modelo, imagens por IA e identidade visual — 02/11/2026

Pedido do usuário: qualidade ainda básica, pesquisa ligada sem querer, imagens não saíam.
- Interface: pesquisa desligada por padrão com OpenAI; opção "Gerar em lote" (padrão);
  "Fonte das imagens" (só livres · livres + IA quando faltar · só IA) e "Qualidade da
  imagem por IA" (econômica `gpt-image-2` baixa ~US$ 0,005; média `gpt-image-1-mini`
  ~US$ 0,015), com preço na tela; consumo mostra imagens e total. CLI: `--lote`,
  `--imagens-fonte`, `--imagens-ia-qualidade`.
- `ai_images.py`: Images API, 1536×1024 JPEG, prompt sem texto/logotipos; custo pelo
  `usage` da resposta (tarifa de 01/11/2026) ou tabela oficial por imagem; crédito
  "Imagem gerada por IA · modelo"; máximo 3 por deck. `RecordedModel.record_image` soma ao total
  (`uso_imagens.jsonl`, `image_cost_usd`). Preços conferidos em developers.openai.com
  (pricing e guia de geração de imagens).
- Busca Commons: consultas simplificadas quando vazia (só amplas no modo "livres");
  retratos/biografias rejeitados salvo busca por pessoas; crédito usa a 1ª linha do autor.
- Visual: capa e conclusão em paleta invertida (fundo escuro, papel `background`; D003
  aceita a cor do título sobre fundo próprio com contraste conferido); maiúscula inicial;
  coluna de rótulo da comparação comporta a palavra mais longa; slide de imagem que não
  cabe após reparos é recomposto em tópicos; A010 informa a proporção de palavras a cortar.
- Modelo: `gpt-5.4-mini` aceita temperatura, seed e schema estrito; sem tokens de raciocínio
  por padrão. Tarifa US$ 0,75/0,075/4,50 por 1M. Definido como padrão no `.env` local.
- Evidências (`outputs/api_voz_mobile/visual2_*`, `visual3_reciclagem_*`): mesmo pedido
  monolito × microsserviços, lote, livres+IA — 4.1-mini 7 chamadas US$ 0,0076; 5.4-mini
  4 chamadas US$ 0,0118 + 1 imagem IA US$ 0,0051 = US$ 0,0169. Conteúdo do 5.4-mini
  visivelmente mais concreto (revisão do planejador, sem avaliação cega).
- 467 testes (um teste de PDF com limite de tempo oscilou sob carga e passou isolado); Ruff,
  TypeScript, ESLint e build conferidos.

## Estilos visuais e ajustes da tela — 02/11/2026

- Tela: caixas de seleção alinhadas ao texto (a regra global `input {width:100%}` as
  esticava); o antigo padrão `gpt-4.1-mini` guardado no navegador cede ao padrão do servidor.
- Estilos (`tema` do `.slda`): `claro`, `escuro`, `editorial`, `vibrante`, `natural`, `noturno`.
  `alto_layout.STYLES` define paleta comum, paleta de abertura/fechamento e tema-base da IR;
  cor própria entra como retângulo de fundo (`role=background`). Renderizador e IR seguem
  com claro/escuro. Todos compilam sem ERRO/AVISO (teste parametrizado).
- Galeria: `outputs/estilos/<estilo>/previa.png` e `<estilo>.pptx` (mesmo conteúdo).
- Fontes da pesquisa: [refs/ESTILOS_VISUAIS_FONTES.md](../refs/ESTILOS_VISUAIS_FONTES.md).
  Modelos de terceiros não adotados (motor não abre `.pptx`; licenças variam).
- 473 testes; Ruff, TypeScript, ESLint e build conferidos.

## Como executar

Da pasta `code/slidedsl`:

```powershell
.\.venv\Scripts\slidedsl.exe serve
```

Abrir `http://127.0.0.1:8000`, escolher **OpenAI · API paga** e conferir o modelo.
O `.env` já foi criado localmente; em outra instalação usar `.env.example` como referência.
O modelo herdado é `gpt-4.1-mini`; a documentação atual o marca como deprecated. O nome
é configurável por `SLIDEDSL_OPENAI_MODEL` ou na interface. Não presumir acesso a outro
modelo sem consultar a documentação e a conta; esta etapa não fez migração de modelo.

Para repetir apenas o piloto autorizado, quando a rede funcionar:

```powershell
.\.venv\Scripts\python.exe scripts/piloto_openai.py
```

Tarifas opcionais: `SLIDEDSL_OPENAI_PRICING` contém um mapa JSON por modelo, com `input`,
`cached_input`, `output` em USD por milhão e `date` ISO. O `.env` local tem tarifa datada
do modelo do piloto, conferida em fonte oficial. Sem tarifa ou uso confiável, o custo
total fica indisponível; limites de chamadas não garantem um teto exato em dólares.

## Verificações e evidências

- **Piloto remoto** `outputs/api_voz_mobile/piloto_5ab371e27016/` (job
  `5d620a2be1194525b62221b672260f70`, arquivos em `outputs/criar/<job>/`): modelo retornado
  `gpt-4.1-mini-2025-04-14`; 5 chamadas, todas com uso conhecido (roteiro, slides 1–3 e um
  reparo no slide 3); 3.514 tokens de entrada, 877 de saída, 0 em cache; **US$ 0,0028088**
  pela tarifa datada; ~10,6 s de inferência; PPTX exportado (HTTP 200). Qualidade observada:
  conteúdo genérico, slides 2 e 3 repetem ideias (metas, revisão) e a capa inventa um autor
  ("Equipe de Educação em Tecnologia"). Sem pesquisa, `qualidade.json` fica vazio.
- Regressão Python final: **403 passaram**, em 95 s (inclui teste do contexto TLS).
  No sandbox, usar `-p no:cacheprovider --basetemp outputs\_pt` (o temp padrão é negado e
  caminhos longos estouram 260 caracteres); apagar `outputs\_pt` depois.
- Regressão Python anterior: 402 passaram, em 92,3 s. Um aviso de depreciação de
  Starlette/AnyIO já aparece na infraestrutura de testes; não houve falha de teste.
- Regressão de navegador final: **13 passaram, cinco optativos omitidos**, em 15,2 s;
  API local em porta separada, build servido em produção. Inclui compilação de PPTX real.
- Renderer: **dois testes Node passaram**. TypeScript, ESLint, Ruff e build Vite conferidos.
- Evidências da regressão Python: `outputs/api_voz_mobile/tests/python-final.xml`.
  Relatório UI: `outputs/api_voz_mobile/tests/ui-final/results.json`.
- Pilotos `outputs/api_voz_mobile/piloto_1f821beb1246/` e `piloto_b1f93bb611bd/`:
  falharam antes da inferência; os IDs dos jobs estão nos manifests e em `outputs/criar/`.
  Não há PPTX nem custo remoto observado nessas tentativas. Não tratar uso `null` como zero.
- Problemas intermediários: um teste UI contava também botões dos elementos; seletor
  corrigido para slides. O esbuild não resolveu caminhos no sandbox; build fora do sandbox
  passou. A primeira execução UI precisou encerrar seu próprio servidor de teste na porta
  8765; a execução final na porta 8766 terminou normalmente.
- Verificado: `.env` ignorado e não rastreado; nenhuma ocorrência da credencial nos arquivos
  versionados ou nas pastas de código, testes, scripts, documentação e referências.

## Decisões e contratos

- Completar o adaptador Chat Completions existente nesta fase, evitando uma migração de
  endpoint junto da mudança de contabilização. Responses API continua possível depois.
- Geração estruturada deve falhar explicitamente quando o modelo/adaptador não aceitar
  schema; não repetir silenciosamente o pedido sem restrição após `TypeError`.
- Registrar todas as chamadas do fluxo, incluindo pesquisa, verificação e falhas, com
  uso ausente marcado como desconhecido. Gravar imediatamente para preservar interrupções.
- Projeto persistido futuro: conteúdo Alto + IDs estáveis + ajustes explícitos + revisão;
  IR será derivada. Não converter arbitrariamente a cena editada de volta para Alto.
- Primeiro piloto pago: um deck pequeno, um candidato, reparos limitados. Valor em dólares
  só pode ser calculado com tarifa identificada por modelo, data e moeda; sem tarifa, custo desconhecido.

## Próximo ponto de retomada

1. Ler este registro, o plano e o `git diff`; permanecer na branch existente.
2. ~~Piloto pequeno~~ e comparação de três temas concluídos (ver evidências).
   Autoria, repetição lexical e TLS implementados; busca/download Wikimedia
   comprovados na rodada 2. Restam casos A010 e avaliação de conteúdo/estética.
   Novas despesas de API dependem de outra solicitação; este lote terminou.
3. **Próxima implementação: fase 2, projetos persistidos com revisões.** Fechar schema e
   política de IDs; representar Alto e ajustes manuais sem perda. Definir estado da seleção,
   salvamento/reabertura, detecção de revisão antiga e restauração antes de editar por IA.
4. Fase 3: pedidos textuais locais com patch, revisão-base e preservação dos outros slides.
5. Fase 4: navegação móvel, captura/transcrição revisável e demonstração HTTPS. Publicação,
   autenticação e retenção continuam pendentes; o servidor permanece local.

### Comandos de verificação

Da raiz de `code/slidedsl`:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --junitxml=outputs/api_voz_mobile/tests/python-final.xml
.\.venv\Scripts\python.exe -m ruff check src tests scripts/piloto_openai.py
.\outputs\runtime\node.exe --test renderer/render.test.mjs
```

Da pasta `editor`:

```powershell
..\outputs\runtime\node.exe node_modules/typescript/bin/tsc --noEmit
..\outputs\runtime\node.exe node_modules/eslint/bin/eslint.js .
..\outputs\runtime\node.exe node_modules/vite/bin/vite.js build
$env:SLIDEDSL_API_PORT = '8766'
$env:SLIDEDSL_TEST_BUILT_EDITOR = '1'
$env:SLIDEDSL_UI_RESULTS_ROOT = '../outputs/api_voz_mobile/tests/ui-final'
..\outputs\runtime\node.exe node_modules/@playwright/test/cli.js test
```

O Node portátil em `outputs/runtime/` já estava presente; não foi instalado nesta etapa.
Se faltar em outra máquina, usar Node 24 compatível. Não encerrar servidores de outras
sessões para liberar porta: escolher outra porta de teste.

## Cuidados com o workspace

### Rodada 4 de design — concluída em 11/11/2026

Executado `PLANO_CODEX_RODADA4_DESIGN.md`, com fontes previamente registradas em
`refs/DESIGN_RODADA4.md`, sem rede/APIs de modelo ou imagem. Custo US$ 0.
Não houve commit, push ou stash. Alterações anteriores do workspace preservadas.

Implementação: `design_system.py` (12 colunas/tokens/Estilo), `layout_score.py`
(cinco fatores e média de potência −2), migração de `alto_layout.py`, medição e
prévia por família, validação D003/D010/semântica, aviso A031 e filtro de resolução.
Prompt evita seção curta; seção de deck <8 vira transição. A030 registra todas
as candidatas. A031 não vai ao feedback de reparo de texto, pois o modelo de
texto não consegue corrigir resolução; continua no diagnóstico do compilador.
Gramática Alto, roundtrip e contrato IR não foram alterados.

Evidências: `outputs/design_r4/20261110-234240/`. Corpus congelado e hashes em
`corpus/` e `corpus.json`, linha de base em `antes/`, ciclos 1..3 com revisões,
PPTX/IR/DSL/PNGs/contato por deck. Foram abertas as 48 folhas dos ciclos.
Último ciclo: **16/16 PPTX e 89 slides**, sem A010/A019/D010; oito A031.
Comparações `comparacao/*.png` e `comparacao/TABELA.md`: nota 0,7966→0,8353,
ocupação 0,6079→0,4966, variantes/deck 4,625→4,875, repetição imediata 3→0.
As variantes anteriores são inferidas, pois A030 não existia; A031 não estava
disponível antes. Prévia é IR/Pillow, não medição de aparência do Office.

Testes finais: **591 passaram em 87,47 s**, Ruff limpo, **2 Node** passaram.
JUnit `pytest_aprovacao.xml`, logs `pytest_aprovacao.txt`, `ruff_aprovacao.txt`,
`node_final.txt`. Há um aviso preexistente de depreciação Starlette/AnyIO.
Editor não foi editado nesta rodada; build/lint condicionais não se aplicam.
Auditoria de ZIP/XML confirmou 652 textos editáveis, 298 formas e 19 imagens
nos 89 slides, sem divergência de família/tamanho entre IR e PPTX. Os hashes das
fontes originais e suas cópias coincidem. Python 3.12.10, Node v24.14.0.
`outputs/_tmp_r4` foi preservada: a revisão automática rejeitou sua remoção
recursiva com o motivo `blocked by policy`. Não tentar contornar a política.

Reproduzir em nova pasta, sem sobrescrever esta rodada:

```powershell
.\.venv\Scripts\python.exe scripts/auditar_design_r4.py
.\.venv\Scripts\python.exe scripts/auditar_design_r4.py --run outputs/design_r4/<novo-ts> --phase ciclo_1
.\.venv\Scripts\python.exe scripts/auditar_design_r4.py --run outputs/design_r4/<novo-ts> --phase ciclo_1 --compare
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp outputs\_tmp_r4
.\.venv\Scripts\python.exe -m ruff check src tests scripts
.\outputs\runtime\node.exe --test renderer/render.test.mjs
```

Pendências visuais: listas predominam (26 rows), todas as dez imagens escolheram
photo40, fotos contidas podem ficar pequenas e um grafo continua irrelevante;
corpo denso segue em 16 pt. Rótulos de alturas diferentes podem ter topos
desnivelados; seções curtas ainda parecem esparsas. Há decks com nota menor que
antes. Encerramento pelo limite de três ciclos, sem alegar validação estética.

O repositório abrange todo o workspace. Antes desta implementação já existiam alterações
em `ROADMAP.md` e `docs/PROGRESSO.md` e arquivos não rastreados em `.maestri/`,
`code/maestri-mundos/`, `docs/artigo/`, `docs/orientacao/`, `docs/como_funciona.html`,
no plano e em suas fontes. Preservar esses arquivos; nunca usar `git add .` ou limpar
o workspace para preparar um commit.

## Rodada 5 de design — concluída em 11/11/2026

Executado integralmente `PLANO_CODEX_RODADA5_DESIGN.md`, offline, US$ 0, sem APIs
de modelo/imagem e sem commit/push/stash. Preservadas as alterações anteriores.
Não mudar gramática Alto, roundtrip ou contrato IR para reproduzir esta rodada.

Evidências: `outputs/design_r5/20261111-001430/`: corpus r4 copiado e hashes,
código de entrada selecionado, ciclos 1..3 com PPTX/IR/DSL/PNGs e revisões,
comparações **r4-antes | r4-final | r5** em `comparacao/*.png`, tabela e relatório.
As 48 folhas dos ciclos foram abertas. Encerrado com todos os critérios (a)–(e):
16/16 PPTX e 89 slides; ocupação 0,6294; tópicos em rows 7/30 (23,3%); nenhuma
foto grande paisagem/quadrada em photo40; nenhum eixo misto; zero A010/A019/D010.
Repetições imediatas 0, variantes/deck 4,9375, oito A031. Conclusões em colunas
numeradas 14/15; microsserviços fica em linhas por falta de espaço nas colunas.

Calibragem em `layout_score.py`: ocupação 35%, equilíbrio 20%, demais 15%; platô
0,55–0,78, quadrática abaixo de 0,45, média de potência −2; memória de três slides,
bônus de diversidade e preferência explícita por cartões curtos e ações em colunas.
Fotos grandes paisagem/quadradas só oferecem photo50; photo40 usa viewport de
cinco colunas, mínimo 50% da altura útil (a foto visível pode ser menor pelo contain).
Título/fio/corpo de conteúdo no eixo esquerdo; noturno tem fio vertical na margem.
Linhas usam gaps 8..64, começam no máximo 48 px após a área do título.

Fontes: altura-x dos TTF locais relativa à Arial, arredondamento a 1 pt e pisos.
Calibri usual título/rótulo/corpo 46/26/22; compacto 46/22/20, corpo ≥18 pt efetivos.
Referência óptica do rótulo 23,5 pt, ajustada para obter 26 Calibri sem abandonar a
medição por família. Tabela completa e fórmulas em `docs/REGRAS_DESIGN.md`;
fontes/metodologia em `refs/DESIGN_RODADA5.md`, hashes no manifesto das métricas.
Comparações densas ganharam fallback `comparison_text`; cronologias podem unir
rótulo — detalhe numa frase. Conteúdo permanece inteiro e editável, hierarquia é menor.

614 pytest passaram em 90,59 s (`pytest_aprovacao.xml`), Ruff limpo, dois Node.
Há um aviso preexistente Starlette/AnyIO. Editor e renderer não foram editados
nesta rodada; build/lint do editor não se aplicam. Auditoria ZIP/XML: 629 textos,
332 formas, 19 imagens, 89 slides; nenhuma divergência de texto/família/tamanho.
Python 3.12.10, Node v24.14.0. Temporários de pytest preservados, sem limpeza.

Reprodução em pasta nova (copiar corpus e corpus.json da r4 antes):

```powershell
.\.venv\Scripts\python.exe scripts/auditar_design_r4.py --run outputs/design_r5/<novo-ts> --phase ciclo_1
.\.venv\Scripts\python.exe scripts/comparar_design_r5.py --run outputs/design_r5/<novo-ts> --phase ciclo_1
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp outputs\_tmp_r5
.\.venv\Scripts\python.exe -m ruff check src tests scripts
.\outputs\runtime\node.exe --test renderer/render.test.mjs
```

Continuam ruins: fotos pequenas (photo40 em seis slides), grafo de hyperlinks
irrelevante, rótulos de topos diferentes, transições e certas conclusões esparsas.
O catálogo congelado fala em "imagem contida", mas escolhe sangrada. Notas são
heurísticas; ocupar o viewport não comprova presença visual. Prévia IR/Pillow não
valida aparência no Office. Não fazer nova inferência para corrigir conteúdo
sem autorização de outra rodada; nenhum conteúdo do corpus foi reescrito.


## Rodada 6 — Parte A concluída; Parte B bloqueada por autenticação (11/11/2026)

Plano: `docs/PLANO_CODEX_RODADA6_DESIGN.md`; fontes: `refs/DESIGN_RODADA6.md`.
Código: `alto_layout.py`, `design_system.py`; testes r3/r4/r5 atualizados e
`test_design_r6.py`, `test_reais_r6.py` adicionados. Harness pago:
`scripts/testes_reais_r6.py`; comparação offline: `scripts/comparar_design_r6.py`.

Parte A offline, US$ 0: dois ciclos, 32 folhas abertas. Critérios (a)–(e)
preservados: 16/16 PPTX, 89 slides, ocupação 0,6294→0,6664, tópicos em rows
7/30→4/30, zero A010/A019/D010/eixo misto/repetição imediata. Dez fotos internas
em photo50; oito A031 mantidos. Quinze conclusões em colunas com número interno.
Rótulos/descrições compartilham topos; cartões têm altura natural + padding32;
centro útil −5%, limitado pelo topo. Fontes começam no maior perfil válido.
Fotos ≥600 px têm variante única independente de estilo; <600 px usam texto,
inclusive capa. Transições curtas: 48–54 pt, bloco de um terço e motivo da família.

Evidências: `outputs/design_r6/20261111-004533/RELATORIO.md`, `comparacao/`,
`ciclo_1/REVISAO.md`, `ciclo_2/REVISAO.md`. Corpus idêntico por SHA-256 à r5;
gramática Alto, IR e roundtrip preservados. Refinamento de capa <600 px não
altera o corpus inspecionado: IR finais reconstruídas e comparadas, sem diferença.
Auditoria PPTX: 629 textos, 345 formas, 19 imagens, 89 slides; zero divergência
de fonte/texto. **640 pytest passaram em 156,28 s**, Ruff limpo e dois Node.
Um aviso Starlette/AnyIO preexistente; editor/renderer não alterados nesta rodada.
Temporários preservados; nenhum commit, push ou stash.

Parte B: modelo **gpt-5.4-mini**, tarifa configurada (somente presença verificada;
nenhum valor do .env exibido), seis pedidos/estilos, seis slides/seed42,
imagens livres habilitadas, pesquisa desligada, sem imagens por IA.
**6/6 tentativas recusadas com HTTP 401 antes do roteiro. Nenhum deck novo foi
gerado:** sem PPTX/SLDA/PNG de slide. Os seis contato.png e a galeria são painéis
de falha explicitamente identificados; não são folhas de decks reais.
Nenhuma busca de fotos foi alcançada. Credencial local carregada; sem chave
herdada. Não se modificou .env nem se imprimiram seu conteúdo ou a chave.

Pasta: `outputs/testes_reais/20261111-0050/`, com `INDICE.md`, `galeria.png`,
`resultados.json`, `orcamento.json`, diagnóstico e uso por tentativa.
ULTIMO.txt aponta para essa execução. Seis painéis e galeria abertos.
Gasto conhecido **US$ 0,00000000**; seis usos/custos desconhecidos; total exato
**desconhecido**; reserva conservadora **US$ 0,09354600**, dentro de US$ 0,50.
Não declarar custo total zero. Não houve retries pagos após as seis falhas.

Foi solicitada atualização local da credencial, sem enviá-la no chat.
Após corrigir a credencial, retomar da raiz em nova pasta automática:

```powershell
.\.venv\Scripts\python.exe scripts/testes_reais_r6.py --carry-budget outputs/testes_reais/20261111-0050/orcamento.json
```

O ledger conserva as seis reservas no MESMO teto total de US$ 0,50; preflight
por deck e reserva antes de cada chamada. Não iniciar outro lote com orçamento
zerado. Retomada dentro do teto já autorizado exige credencial válida, sem nova
autorização de gasto. **Parte B permanece pendente, não concluída.**

Limitações: nota geométrica caiu 0,8023→0,7048, apesar dos critérios explícitos;
vazios externos, recorte/nitidez das fotos e grafo irrelevante do corpus antigo
persistem. Sem validação Office, avaliação humana cega ou pesquisa factual.
Conteúdo gerado não foi editado à mão para esconder falhas.

## Rodada 7 — concluída em 11/11/2026

Plano: docs/PLANO_CODEX_RODADA7_DOCUMENTOS_EDICAO.md. Fontes previamente registradas em
refs/DOCUMENTOS_EDICAO_R7.md. Alterações anteriores preservadas; sem commit, push, stash,
imagens por IA, exposição de chave ou conteúdo do .env. TLS permaneceu verificado.

- T1: TXT/MD/PDF textual e DOCX sem dependência nova, até oito arquivos, 2 MiB por arquivo
  e 5 MiB para DOCX; macros/cifra recusadas. Dossiê local com trecho literal verificado,
  fontes documento:nome#trecho-N, prioridade documental e internet opt-in; CLI/API/UI.
- T2: refazer_slide troca somente o bloco selecionado; valida gramática/check_slide,
  no máximo um reparo. Ajustes sem modelo de estilo/foto/ordem/exclusão, histórico em
  outputs/criar/<id>/versoes e desfazer persistido; consumo inclui falhas e versões desfeitas.
- T3: Commons com categorias/extmetadata, consulta central preservada nos fallbacks,
  veto de retratos/eventos/diagramas e fallback de imagem sem foto em cartões/destaque.
  Revisão conservadora rejeita PNGs da busca fotográfica e metadados sem descrição
  suficiente. Buscas adicionais de foto sem inferência obtiveram varanda e roteador.
- T4: estilo auto determinístico, padrão na UI/CLI; público infantil e contexto acadêmico
  precedem tema técnico. Regra e limites em docs/REGRAS_DESIGN.md; troca sem modelo.
- T5: 678 pytest passaram em 112,72 s (um aviso Starlette/AnyIO preexistente), Ruff limpo,
  dois Node, npm build e lint passaram. Build usou --configLoader native por restrição
  do esbuild no sandbox. Playwright final: 15 passaram em 17,1 s, cinco testes locais
  opcionais pulados; inclui upload real e edição com modelo simulado. A primeira suíte
  exigiu encerrar sua própria árvore de servidor na porta 8777; a final usou servidor
  separado na porta 8778 e encerrou os testes normalmente. Logs em outputs/rodada7/.
- T6: seis PPTX finais, 42 slides, duas fotos Commons. Folhas finais, galeria e comparação
  antes/depois abertas. Original de documento/DOCX desta execução falhou em A005/A010;
  os slides 1/6 e 5 foram refeitos em pastas novas, sem editar o texto manualmente.
  Slide 3 refeito em uma chamada por US$ 0,00516750; outros sete blocos idênticos em bytes.

Evidência principal: outputs/testes_reais/20261111-0131_r7/INDICE.md, galeria.png,
03_refeito_revisado/antes_depois_slide3.png e preservacao.json. Antes em antes.slda e
antes.pptx; depois em apresentacao.slda e apresentacao.pptx na mesma pasta de edição.
ULTIMO.txt aponta para essa execução. ARQUIVOS_ALTERADOS.md e manifesto_sha256.json
relacionam arquivos e artefatos. Auditoria do deck do projeto encontrou zero números
visíveis ausentes dos fatos e conferiu os nomes técnicos; não prova toda paráfrase.

| Caso final | Válido | Fatos documentais usados | Fotos | Chamadas | USD |
|---|---|---:|---:|---:|---:|
| Artigo + README | sim | 19 | 0 | 37 | 0,06522735 |
| DOCX do artigo | sim | 19 | 0 | 34 | 0,06548055 |
| Refazer slide 3 | sim | 20 | 0 | 1 | 0,00516750 |
| Git | sim | 0 | 0 | 8 | 0,01478985 |
| Horta | sim | 0 | 1 | 7 | 0,01352625 |
| Internet | sim | 0 | 1 | 10 | 0,01797705 |

A tabela soma geração e reparos por caso; refazer é apenas o custo adicional de edição.
Casos finais US$ 0,18216855; tentativas anteriores US$ 0,13237410. Rodada inteira:
176 tentativas, 171 com uso conhecido; US$ 0,31454265 conhecidos. Cinco falhas iniciais
no transporte têm uso/custo desconhecidos, reserva US$ 0,08191650. Total exato desconhecido;
limite com reservas US$ 0,39645915 <= teto US$ 0,60. Nenhuma chamada de imagem por IA.
Ledgers anteriores preservados e acumulados, nunca reiniciados. Não houve HTTP 401 nesta
rodada. Retomada via stdin/runpy funcionou; causa das falhas de transporte não foi comprovada.
Lote encerrado: não fazer novas inferências para melhorar a amostra sem outra solicitação.

Continuam ruins: filtros lexicais perdem fotos úteis; a foto do roteador tem recorte apertado
com marca em destaque, e a varanda contém plantas ornamentais. Há comparações de aspectos
não equivalentes, repetição e generalizações (por exemplo, modelos menores e conexão sempre
ativa). O RAG inicial recuperava comandos CLI demais; priorizar trechos narrativos melhorou
o assunto, mas oito passagens não cobrem todo o artigo. Verificação por modelo tem falsos
positivos e custa chamadas. Validade formal não implica sustentação semântica nem beleza.
Prévias IR/Pillow, sem validação Office ou avaliação humana cega. Git/horta/internet não
usaram pesquisa factual. Projeto com IDs estáveis, reabertura pela UI, voz e celular
continuam como etapas futuras do plano maior; o histórico desta rodada é específico dos jobs Alto.
