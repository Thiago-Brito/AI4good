# Próximas melhorias — diagnóstico da SlideDSL

Data: 11/10/2026. Código analisado: `22ebec4dac9b76f62a01f94f1c75949314fd2616`.
Esta etapa utiliza código, planos e relatórios existentes. Não executa Ollama,
pesquisa de imagens, renderização ou novos experimentos e não implementa funcionalidades.
Fontes anteriores estão em [refs/FONTES.md](../refs/FONTES.md).

**Prioridade: melhorar o contrato editorial, ampliar as composições disponíveis
e integrar imagens ao planejamento de cada mensagem.** Os três limites são da
implementação e do percurso de geração. Os resultados disponíveis não isolam
uma incapacidade intrínseca do Qwen3 4B nem permitem quantificar ganho estético.

## Evidências utilizadas e estado atual

| Evidência existente | O que permite concluir |
|---|---|
| [Plano final de arquitetura](../outputs/refinement/delivery_04/plan.json) e [auditoria](../outputs/refinement/delivery_04/audit.json) | Cinco slides válidos, zero diagnósticos D/V, requisitos reconhecidos 2/2 — apenas slides e margens. Conteúdo ainda contém benefícios sem condições ou evidência explícitas. |
| [Relatório do refinamento](../outputs/refinement/delivery_04/refinement.json) | Uma composição candidata nos slides 1, 2, 3 e 5; duas no slide 4, linha e grade de três cards. |
| [Comparação visual](../outputs/refinement/captures_verified/comparison.html) e [documentação](REFINAMENTO_VISUAL.md) | Hierarquia e equilíbrio foram corrigidos, mas isso não comprova profundidade, precisão factual ou qualidade estética com leitores. |
| [Fotografia com fallback](../outputs/planning_visual/photo_delivery_03/report.json) e [fotografia selecionada](../outputs/planning_visual/photo_delivery_04/report.json) | A pesquisa pode terminar em cards; o exemplo seguinte conseguiu uma imagem Moon com créditos. Não há medição de relevância visual ou benefício didático. |
| [Disponibilidade de renderização](../outputs/refinement/rendering/delivery_04/rendering.json) | PowerPoint/LibreOffice indisponíveis naquela execução; `rendered=false`. As capturas são previews geométricos. |

O núcleo já dispõe de planejamento em duas chamadas, schemas restritos,
layouts com imagens, importação local, cache, licenças, refinamento, rollback,
requisitos congelados e conectores nativos verticais. A regressão registrada
na etapa anterior passou com 241 Python, dois Node e onze Playwright;
esses testes não foram executados novamente neste diagnóstico.

## As três limitações principais

| Prioridade | Limitação | Benefício esperado das mudanças |
|---|---|---|
| 1 | Plano editorial pouco expressivo e conteúdo comprimido em rótulo/função | Maior profundidade e precisão; mensagens sustentadas por exemplos, condições e evidências. Afeta todos os temas. |
| 2 | Associação quase fixa entre intenção e composição, com pouca busca de alternativas | Maior variedade funcional e melhor uso do espaço, mantendo consistência e objetos editáveis. |
| 3 | Imagens tratadas em um percurso separado e escolhidas principalmente por palavras do título | Maior pertinência e integração de imagens quando elas ajudam a explicar o assunto. Benefício depende do domínio. |

Essa ordem é uma priorização de engenharia, não uma classificação estatística.
Para arquitetura de software, conteúdo e diagramas têm precedência sobre fotos.
Em temas que dependem de observação visual, a terceira prioridade pode subir.

### 1. O planejamento organiza slides, mas representa pouco do argumento

**Causa no código.** [visual_planning.py](../src/slidedsl/visual_planning.py)
já planeja o deck inteiro: intenção, mensagem, foco, justificativa, alternativas
e estruturas. Porém, não há campos específicos para evidência da mensagem,
exemplo concreto, condição de validade, contraponto ou papel do slide no argumento.
Nos modos não restritos, `constrain_visual_schema` fixa o título com `const`
a partir da primeira chamada, antes de o corpo estar desenvolvido. Uma mensagem fraca pode, assim, orientar
todo o conteúdo seguinte sem uma revisão explícita de sustentação.

O prompt `CONTENT_SYSTEM` recomenda rótulos de 1–3 palavras e descrições de até
oito palavras. Essa recomendação não é um limite de palavras aplicado pelo schema:
o decoder permite até 80 caracteres no rótulo e 180 na descrição. Ainda assim,
o contrato privilegia função curta por entidade; os componentes impõem de dois
a três nós, ou até quatro cards, conforme o layout. A normalização concatena
`label` e `detail` em uma string. A representação perde a distinção estrutural
entre tese, exemplo, evidência e ressalva.

**Efeito observado.** O plano de arquitetura declara “Facilita atualizações sem
interromper o sistema” e “Reduz riscos de falhas em componentes isolados”, sem
indicar condições ou fontes para essas vantagens. A conclusão já abandonou a
regra simples/complexo, mas privilegia dados/escala e deixa equipe e implantação
menos desenvolvidos. O refinamento remove redundâncias exatas; não aprofunda
nem verifica essas afirmações. A aprovação 2/2 mede quantidade e margens.

Isso não parece ser truncamento nesse caso: a geração `real_02` terminou com
`stop`, usando 1.538 tokens de saída no total das duas chamadas, sob limite de
4.096 por chamada. Aumentar apenas o orçamento não corrige o contrato editorial.

**Mudança de maior benefício.** Acrescentar ao plano campos opcionais e tipados
para mensagem, sustentação, exemplo e condição/trade-off; definir quais deles
são necessários conforme objetivo e público. Conferir cobertura do pedido e
compatibilidade título/conteúdo antes de congelar a composição. Permitir revisão
localizada da mensagem quando o corpo não a sustentar, com registro e preservação
dos critérios existentes. Não exigir uma terceira chamada para todo deck.

Profundidade não exige mais parágrafos no canvas: exemplos e relações podem ser
visuais; detalhes complementares podem ir para notas, se esse suporte for ampliado.
Em geração com documentos, recuperar trechos por necessidade do slide, dentro do
orçamento existente, em vez de depender somente da consulta global.
[documents.py](../src/slidedsl/documents.py) hoje recupera lexicalmente até oito
fragmentos/6.000 caracteres. `source_audit`, em
[contextual.py](../src/slidedsl/contextual.py), verifica vínculos e literalidade
no modo restrito; não demonstra implicação semântica ou verdade factual.
Essas garantias devem ser mantidas, sem apresentar uma nova checagem lexical
como prova de conteúdo correto.

**Módulos a alterar futuramente.** `visual_planning.py` e `planning.py` para o
contrato; `contextual.py` para orquestração e fontes; `requirements.py` para
cobertura declarada; `documents.py` para recuperação por necessidade;
`reliability.py` para correção localizada dos novos campos. `composition.py` e
`renderer/render.mjs` só precisam mudar se novos campos forem efetivamente exibidos
ou enviados às notas. Reutilizar validadores e reparos, sem criar outro compilador.

**Como verificar.** Aplicar uma rubrica previamente declarada aos planos existentes:
mensagem sustentada, exemplo pertinente, condições das vantagens, critérios de
comparação e conclusão contextual. Separar cobertura mensurável de julgamento
factual humano. Usar somente trechos selecionados para chamadas futuras de reparo,
quando justificadas, em vez de regenerar o deck inteiro.

### 2. A variedade nominal de layouts excede a variedade efetiva de composições

**Causa no código.** `INTENT_LAYOUT` associa cada intenção a uma composição
principal; `layout_for_intent` acrescenta uma exceção para conceito com stack/services.
Não há escolha entre várias composições adequadas à mesma mensagem, salvo override
explícito. Existem oito composições nativas e seis layouts com imagens, mas a
intenção `image` do percurso automático escolhe `text_image`.

[composition.py](../src/slidedsl/composition.py) e
[layouts.py](../src/slidedsl/layouts.py) usam regiões e cardinalidades finitas.
[refinement.py](../src/slidedsl/refinement.py) compara linha/grade somente para
três itens em `benefit_cards` ou `concept_map`; os demais casos elegíveis têm um
candidato. Seu objetivo considera centro dos painéis e variação de áreas.
A fração ocupada é registrada, mas não mede leitura, ritmo entre slides ou
adequação semântica. Com mídia, grupos, decorações ou relações espaciais explícitas,
o refinamento não reorganiza a cena.

Os conectores já existem. [connections.py](../src/slidedsl/connections.py)
suporta cadeias verticais explícitas entre retângulos alinhados. A limitação atual
é de expressividade: stack/services/cards não descrevem, por si, ramificações,
dependências nomeadas ou interações entre serviços. Não basta acrescentar setas
para obter um diagrama semanticamente mais completo.

**Efeito observado.** O caso final é equilibrado e tem cinco seções diferentes,
mas utiliza reiteradamente painéis de mesma família visual. Só o slide de
benefícios teve duas alternativas avaliadas. A correção de “Pagamentos” exigiu
inspeção de captura: uma composição intermediária passou pela estimativa de texto
apesar de cortar o rótulo. Esse problema foi corrigido; demonstra o limite do
método de medição, não um corte persistente na entrega atual.

**Mudança de maior benefício.** Separar intenção comunicativa de variante de
composição. Oferecer poucas alternativas úteis por família, como comparação por
critérios versus comparação de estruturas, diagrama central versus distribuição
lateral e texto com imagem em diferentes proporções. Condicionar a seleção à
estrutura do conteúdo, quantidade de texto, presença de mídia e preferências.
Avaliar também sequência do deck, evitando repetir uma composição quando uma
alternativa semanticamente adequada estiver disponível; não alternar layouts
aleatoriamente nem fixar um roteiro universal.

Começar com os mesmos objetos texto/retângulo/imagem/seta. Para diagramas mais
complexos, declarar nós e relações lógicas no plano antes de ampliar a ancoragem.
Preservar a ordem e as restrições espaciais obrigatórias, IDs estáveis, validação
e rollback. A inclusão de uma variante não deve exigir reescrever a gramática.

**Módulos a alterar futuramente.** `visual_planning.py` e `planning.py` para
variantes e relações declaradas; `composition.py`, `layouts.py` e `refinement.py`
para gerar/selecionar composições; `connections.py` apenas ao ampliar conexões
explicitamente planejadas. `visual_validation.py` e `preview.py` apoiam a avaliação.

**Como verificar.** Recompilar os mesmos planos gravados em variantes, offline,
comparando os cinco slides com conteúdo e requisitos iguais. Conferir legibilidade,
hierarquia e distribuição com inspeção das capturas; renderizar o PPTX real quando
houver engine disponível. Pontuação geométrica permanece um filtro, não nota
estética. Validar a diversidade pelo propósito das composições, sem contar formas.

### 3. A imagem não é planejada junto dos componentes e da mensagem

**Causa no código.** Nas composições de `COMPOSED_LAYOUTS`,
`constrain_visual_schema` impõe `media.maxItems=0`; o compilador também rejeita
mídia adicional nessas composições. Assim, capa, comparação ou cards do caminho
mais comum não podem simplesmente receber uma imagem explicativa. Os layouts com
imagens existem, inclusive comparação e cartões, mas não são alternativas
automaticamente oferecidas para essas intenções.

Há pesquisa automática, importação própria, escolha manual e cache. A pesquisa
depende de um slot com consulta e de autorização. `research=off` é o padrão;
com documentos, consultas derivadas exigem `share_queries`. Essas são decisões
de controle e privacidade, não defeitos a remover.

[media.py](../src/slidedsl/media.py) pontua interseção de palavras da consulta
com o título do candidato. A seleção automática exige correspondência lexical
integral, resolução mínima e licença elegível; a ordenação inclui resolução.
Isso não mede o que está representado na imagem, sua contribuição à mensagem
ou sua adequação ao slot. Em `contextual.py`, ausência de ativo pode transformar
o layout em `concept_map`/`comparison_visual`, preservando conteúdo e avisando.

**Efeito observado.** O exemplo `photo_delivery_03` caiu em cards; o posterior
`photo_delivery_04` selecionou Moon e exportou a imagem com créditos. O mecanismo
funciona, mas o êxito de download/exportação não comprova escolha profissional.
A ausência de fotografias na arquitetura não é, isoladamente, falha: diagramas
podem comunicar melhor esse assunto. A lacuna é a impossibilidade de decidir e
integrar mídia por função dentro de várias composições.

**Mudança de maior benefício.** Planejar a função do ativo — evidência visual,
exemplo, comparação ou contexto — junto da mensagem, com descrição do que deve
ser visível e alternativa nativa se não houver material adequado. Permitir slots
opcionais nas variantes apropriadas. Reutilizar primeiro ativos próprios e cache;
depois melhorar consultas e avaliação de candidatos com metadados, proporção do
slot e revisão humana entre poucas opções. Qualquer ranking semântico futuro
precisa ser avaliado separadamente; não é garantia de relevância.

Manter HTTPS/SSRF, limites de arquivos, direitos, créditos, pesquisa autorizada
e compilação sem rede. Não inserir fotos para preencher espaço, baixar ativos
NASA sem revisão ou substituir uma imagem ausente por material irrelevante.

**Módulos a alterar futuramente.** `visual_planning.py` e `planning.py` para
papel/slots; `contextual.py` para seleção e fallback; `media.py` para consultas
e ranking; `layouts.py` e `refinement.py` para equilíbrio texto/imagem nas novas
variantes. `ContextPanel.tsx` pode reaproveitar a seleção existente para apresentar
os candidatos vinculados ao slot, sem criar outro formulário de geração.

**Como verificar.** Usar imagens já em cache e planos de fotografia existentes,
incluindo o fallback, sem pesquisa ou Ollama no primeiro ciclo. Comparar relevância
para a mensagem, legibilidade, proporção, créditos e preservação do conteúdo.
Aprovação visual deve ser humana; correspondência de palavras é só evidência auxiliar.

## Ordem de implementação recomendada

| Etapa | Entrega proposta | Dependência e controle de custo |
|---|---|---|
| 0 | Congelar casos e rubrica de conteúdo/composição/imagem usando os artefatos atuais | Preparação offline; manter snapshots e separar resultados históricos. Preparar renderização real quando disponível. |
| 1 | Enriquecer o contrato editorial e verificar cobertura/sustentação da mensagem | Maior benefício esperado. Projetar campos semânticos de conteúdo e mídia antes de alterar layouts; começar com fixtures e planos gravados. |
| 2 | Introduzir variantes por intenção e equilíbrio conjunto de conteúdo/mídia | Depende do contrato; escolher variantes com compilação determinística e requisitos preservados. Reusar layouts com imagens já disponíveis. |
| 3 | Melhorar planejamento do ativo e seleção de imagens por propósito | Usa os slots da etapa 2; começar por catálogo/cache e escolha assistida. Pesquisa e modelos auxiliares apenas quando houver benefício demonstrável. |
| 4 | Executar uma pequena avaliação pareada previamente definida | Só após verificações offline. Separar clareza/fidelidade/estética de validade estrutural e medir chamadas/tokens reais. |

Não começar por troca de modelo, aumento indiscriminado de tokens, novos provedores
ou mais decoração. O código atual já tem os mecanismos básicos; a prioridade é
usar melhor o conteúdo e as representações disponíveis. A falta de renderização
real e avaliação com leitores é uma limitação transversal da evidência: deve
acompanhar as três melhorias, sem ser confundida com uma quarta funcionalidade
de geração ou com prova de que o Qwen3 é o responsável pelo resultado.

Nesta etapa, ficam preservados código, gramática, compilador, editor, resultados,
branch e HEAD. As únicas alterações são este diagnóstico e seu registro mínimo
em roadmap/progresso; não há commit ou push.
