# Expressividade do planejamento — 11/10/2026

## Diagnóstico anterior à implementação

Base: `22ebec4dac9b76f62a01f94f1c75949314fd2616`. Fontes e evidências
anteriores: [FONTES](../refs/FONTES.md), [diagnóstico](PROXIMAS_MELHORIAS.md)
e [refinamento](REFINAMENTO_VISUAL.md). Esta etapa preserva esses registros.

| Limite rastreado | Consequência | Controle necessário para ampliar |
|---|---|---|
| `INTENT_LAYOUT` e `layout_for_intent` escolhem uma composição por intenção | A segunda chamada não pode escolher uma variante adequada ao conteúdo | Variantes finitas, sem coordenadas livres, compatíveis com a estrutura declarada |
| `constrain_visual_schema` limita diagramas/comparações a 2–3 nós e cards a quatro | Uma quarta camada ou cinco conceitos não são representáveis nesse percurso | Testar capacidade com texto completo e fonte mínima antes de admitir a quantidade |
| `CONTENT_SYSTEM` pede descrições de oito palavras; normalização junta label/detail | Explicação, condição e exemplo não têm lugar estrutural distinto | Separar rótulo, descrição e explicação; conservar uma representação textual canônica |
| Composições nativas impõem `media.maxItems=0` | Capa, conceito, benefícios e conclusão não podem usar mídia na mesma família | Reservar região real para mídia, mantendo seleção autorizada, contain e créditos |
| `composition.py` usa caixas fixas e reduz corpo até 18 pt | Mais texto não significa mais capacidade; pode degradar a leitura | Medir candidatos com corpo ≥22 pt; rejeitar excesso em vez de reduzir ou apagar |
| Refinamento só compara linha/grade para três cards | Pouca adaptação à quantidade, comprimento e espaço restante | Escolher deterministicamente apenas entre candidatos que passam pela cadeia existente |

Os limites de caracteres do decoder não equivalem à capacidade de um layout.
Comparações ainda precisam preservar duas alternativas e stack/services têm
semânticas distintas: variantes não autorizam inventar relações entre serviços.
Requisitos congelados, validação de fontes restritas e restrições espaciais
continuam obrigatórios. Pontuação geométrica não comprova melhoria estética.

## Implementação incremental

1. Contrato opcional com conteúdo estruturado e variantes por intenção.
2. Compilação adaptativa com geometria determinística e validação dos candidatos.
3. Testes de capacidade, mídia, conservação e compatibilidade; comparação local.

## Contrato e integração implementados

O protocolo opcional é `expressive-planning-v1`. `GenerationContext` aceita
`expressive_planning=true`, que também ativa o planejamento visual em duas chamadas.
A CLI oferece `--expressive-planning`; o editor tem a opção **Planejamento
expressivo** nas configurações avançadas. O padrão anterior permanece disponível.
No modo `restricted`, a opção mantém o percurso extrativo anterior: não converte
frases literais em rótulos/explicações. A interface informa essa diferença.

`INTENT_LAYOUT` continua identificando uma família semântica, mas já não determina
sozinho a composição física do percurso opcional. `composition=auto` compara
grade, linha e vertical quando apropriados; uma escolha explícita restringe a
busca. Grades usam duas colunas para até quatro itens e três para cinco/seis,
centralizando a última linha. Diagramas ordenados continuam verticais. Capa,
benefícios e conclusão não recebem setas apenas porque uma resposta antiga
declarou `representation=stack`; a interpretação segue a família do componente.

Cada item tem três campos distintos:

| Campo | Papel | Exibição |
|---|---|---|
| `label` | Nome do componente/conceito | Texto nativo, 24 pt, negrito |
| `detail` | Descrição breve da função | Texto nativo, 22 pt |
| `explanation` | Explicação, exemplo ou condição pertinente | Texto nativo separado, 22 pt; pode ser vazio |

Título principal usa 42 pt, cabeçalho de coluna 26 pt, legenda 18 pt e rodapé
12 pt. O corpo não diminui para fazer caber mais conteúdo. O compilador compara
rótulo lateral com rótulo acima do corpo e mede o conteúdo completo antes de emitir.
`ColumnPlan.content` preserva os campos tipados; `items` mantém uma representação
textual canônica para compatibilidade. Divergência entre eles é rejeitada.
Patches autorizados em `content` recompõem somente essa representação derivada
da coluna afetada; não alteram os outros campos ou slides.

### Capacidade, não apenas limites maiores

| Família | Capacidade admitida no decoder | Condição de encaixe |
|---|---|---|
| Conceitos/benefícios | 1–3 itens detalhados **ou** 4–6 concisos | Quatro a seis não recebem explicação adicional; descrições até 40 caracteres |
| Arquitetura/fluxo/sequência | Até cinco nós | Funções curtas, sem parágrafo explicativo no nó; ordem preservada |
| Comparação | Até três por alternativa | Duas colunas; explicações longas não entram neste componente |
| Capa | Até três | Subtítulo e espaço do título contam no orçamento |
| Conclusão | Até quatro | Quatro são concisos; não há ligação sequencial automática |
| Conteúdo com imagem | Até três por coluna | Região real reservada; comparação com mídia exige duas imagens |

Esses máximos não garantem que qualquer combinação de textos caiba. Um título
maior, rodapé, legenda ou palavra longa reduz a capacidade. Há testes que aceitam
cinco camadas/seis conceitos curtos e rejeitam seis explicações longas ou a adição
de rodapé a uma comparação já cheia. O conteúdo é preservado no draft rejeitado.

O schema separa arrays concisos/detalhados por `anyOf`; não apenas aumenta
`maxItems`. O compilador filtra cada candidato com o parser, semântica, design
estrito e V001–V006. Nenhuma composição viável gera L004; relações/decorações
livres ou grupos explícitos são recusados neste percurso, preservando o caminho
anterior para esses planos. Não são rearranjados silenciosamente.

Entre candidatos válidos, requisitos específicos do slide têm precedência na
seleção. O critério geométrico considera área de texto e proporções dos painéis;
preferência compacta participa do desempate. Não é nota de beleza. Requisitos
continuam congelados e avaliados sobre a cena completa; reparos mantêm aceitação,
preservação e rollback existentes. Verificadores de componentes reconhecem a nova
geometria emitida. Um requisito textual integral também pode ser reconstruído a
partir das três caixas do **mesmo nó**, sem unir textos de objetos distintos.

### Medição de texto e mídia

`text_metrics.py` usa Arial regular/negrito local via Pillow quando disponível,
quebra por palavras e margem de largura de 4%. Mantém também o mínimo estimado
pelas regras existentes. Sem as fontes, usa aproximação conservadora, testada
separadamente. Palavras que não cabem inteiras recusam a caixa; não são cortadas.
`composition.json` registra método e hashes das fontes. Geometria é determinística
para conteúdo, opções e ambiente de medição iguais; fontes diferentes podem mudar
a escolha. Não foram copiados arquivos de fonte nem medidos glifos pelo PowerPoint.

As composições nativas de capa, conceitos, benefícios e conclusão agora admitem
um ativo; comparação sem cadeia ordenada admite dois. Diagramas com relações
ordenadas continuam sem esse slot. A imagem usa `contain`, sem corte/distorção,
e créditos continuam nas notas. A seleção, autorização, cache, SSRF, pesquisa
facultativa e compilação sem rede são reutilizados. O modelo deve deixar mídia
vazia quando não houver ativo e a pesquisa estiver desativada. Relevância visual
não é comprovada pelo schema nem pela presença da imagem.

| Módulo | Alteração |
|---|---|
| `visual_planning.py` | Schema por família, decoder expressivo e normalização sem perda |
| `planning.py` | `ContentBlock`, conteúdo tipado, representação canônica e campos opcionais com serialização compatível |
| `expressive_composition.py` | Alternativas, capacidade, hierarquia, slots, seleção e relatório |
| `text_metrics.py` | Medição local e quebra por palavras, com fallback conservador |
| `layouts.py` / `refinement.py` | Integração aditiva; o refiner antigo não desfaz os novos campos |
| `contextual.py` / `cli.py` | Ativação opcional, evidências e preservação de fontes restritas |
| `evolution.py` / `requirements.py` | Reparos dos campos tipados e evidência sobre objetos realmente emitidos |
| `ContextPanel.tsx` | Opção no formulário existente, sem criar outro editor |

Gramática Lark, AST/IR 1.1, parser, backend PptxGenJS e editor permanecem usados.
Os conectores ancorados existentes são reutilizados; não há novo tipo na DSL.

## Comparação real com o mesmo modelo local

Pedido idêntico: `benchmark/prompts/arquitetura_software.txt`, cinco slides.
Antes: [before_01](../outputs/expressiveness/before_01/report.json).
Resposta nova aceita: [after_05](../outputs/expressiveness/after_05/report.json).
Qwen3 4B local, digest `0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`,
seed 42, temperatura 0,1, contexto 8192, máximo 4096 por chamada, thinking desligado.
Nenhum modelo online e nenhuma pesquisa de imagens nesta comparação.

| Execução | Chamadas reais | Tokens de saída | Resultado observado |
|---|---:|---:|---|
| `before_01` | 2 | 1.449 | PPTX estrito, contrato anterior |
| `after_01` | 2 | 1.970 | Rejeitado: conteúdo excessivo/mídia ausente; também expôs erro na validação isolada de slides acima de 1 |
| `after_02` | 2 | 1.765 | Rejeitado: quatro cards com explicações não cabiam |
| `after_03` | 1 | 423 | Interrompido após outline: decoder antigo de conclusão assumia item string; corrigido e testado |
| `after_04` | 2 | 1.723 | Schema rejeitou descrição acima do limite; interação pattern/maxLength do decoder registrada |
| `after_05` | 2 | 1.731 | PPTX estrito, cinco explicações adicionais preservadas em objetos nativos |

São **11 chamadas, 9.061 tokens de saída e 13.082 de entrada**, incluindo falhas
e a execução parcial. Todas as respostas HTTP terminaram com `stop`; isso não
significa aprovação do programa. A auditoria verifica bytes brutos contra HTTP,
schema enviado, parâmetros e hashes dos snapshots anteriores às chamadas.
Essas tentativas são desenvolvimento exploratório, não uma taxa de sucesso de
benchmark previamente definido. Não se descartaram ou reescreveram as falhas.

O regex de frase concluída permanece na validação posterior: nesta versão do
Ollama sua combinação com `maxLength` não restringiu confiavelmente a amostragem.
O decoder recebe limites de tamanho; a saída bruta ainda passa pelo schema, e
a estrutura normalizada passa por suas restrições antes do compilador.

### Conteúdo fixo e entrega recompilada

[comparison_06/comparison.json](../outputs/expressiveness/comparison_06/comparison.json)
separa duas avaliações: nova geração (conteúdo diferente) e recompilação do plano
anterior com todas as frases originais preservadas. Textos sem rótulo recebem
apenas o rótulo explícito “Síntese”; não há resumo nem alteração da afirmação.
O plano `after_05` também foi recompilado integralmente após a correção da medição,
sem nova chamada ao modelo. Snapshots e hashes da compilação estão separados.

Entrega atual: [PPTX](../outputs/expressiveness/comparison_06/generated_after/presentation.pptx)
e [plano](../outputs/expressiveness/comparison_06/generated_after/plan.json).
Tem **39 textos nativos, quatro conexões ancoradas, cinco explicações**,
corpo mínimo 22 pt, zero diagnósticos D/V e critérios reconhecidos **2/2**.
Esses dois critérios são apenas quantidade e margens. `faithful=true` neste caso
não prova cobertura editorial, veracidade ou adequação dos diagramas.

As composições atuais foram capa em grid, componentes verticais, comparação
vertical, benefícios em linha e conclusão vertical. A auditoria confere cada
campo tipado contra texto emitido e cada texto emitido contra o XML nativo do PPTX.

Cinco pares de capturas por comparação:

- [Mesmo conteúdo, antes/depois](../outputs/expressiveness/captures_fixed_02/comparison.html).
- [Gerações locais antes/depois, com recompilação final](../outputs/expressiveness/captures_model_02/comparison.html).

A primeira inspeção revelou cortes de “Manutenção”/“Escalabilidade” e quebra do
corpo no preview, apesar da estimativa de caracteres passar. A medição por palavras
e fontes corrigiu o problema; as novas capturas têm **zero overflow no DOM e zero
erro JavaScript**, com fonte exibida idêntica ao arquivo. As capturas antigas
foram preservadas. São previews geométricos, não renderização Office.
As fontes DSL da recompilação final `comparison_06` foram conferidas byte a byte
contra os casos capturados em `comparison_05`; são idênticas. O snapshot final
inclui a capacidade de um único conceito, sem inventar um segundo nó, e remove
definições tipadas não utilizadas do schema histórico. Não altera respostas reais.

Fixture offline de mídia: [audit.json](../outputs/expressiveness/media_offline_01/audit.json).
Cinco famílias, seis imagens nativas usando Moon e Apollo 11 já em cache,
créditos nas notas, zero D/V, zero chamadas ao modelo/rede. Demonstra integração,
não mede benefício didático nem relevância de escolhas automáticas.
`render-optional` novamente retornou `engine=geometric`, `rendered=false`;
[evidência](../outputs/expressiveness/rendering_01/rendering.json).

## Testes e utilização

**271 testes Python passaram**, incluindo 30 novos casos de capacidade,
variantes distintas, conservação, fontes restritas, mídia, patches, requisitos,
numeração de slides, palavras longas e fallback de fontes.
Dois testes Node passaram. Playwright: **oito passaram, quatro optativos foram
omitidos**, sem habilitar novas gerações reais nas suítes históricas. O transporte
da nova opção no formulário foi testado com resposta simulada, separado das
chamadas reais da CLI. Ruff, ESLint, Prettier, TypeScript e build passaram.
Permanece o aviso transitivo AnyIO/Starlette.

Evidências: [Python](../outputs/tests/expressive-final.xml),
[Playwright](../outputs/expressiveness/ui-tests-final/results.json).

```powershell
.\.venv\Scripts\slidedsl.exe generate-contextual --expressive-planning --strategy C --repair-max 0 --model qwen3:4b-instruct --prompt-file benchmark/prompts/arquitetura_software.txt --out outputs/expressiveness/nova_geracao
.\.venv\Scripts\python.exe scripts/compare_expressive_planning.py outputs/expressiveness/before_01 outputs/expressiveness/after_05 --out outputs/expressiveness/nova_comparacao
```

A API aceita `context: {expressive_planning: true}`. D continua disponível para
reparos locais. Para reproduzir compilação exatamente, considere também os hashes
das fontes; em outra máquina o fallback pode recusar uma composição anteriormente
aceita. Use pastas novas, sem sobrescrever snapshots ou resultados.

## Limitações observadas

Mais expressividade não corrigiu automaticamente a qualidade conceitual. A nova
geração colocou “Camadas” como nó junto de Interface/Negócio/Dados; a comparação
usou Estrutura/Aplicação e Serviços/Independência em vez de somente entidades reais.
Há repetição título/corpo na conclusão e a recomendação mudanças rápidas versus
sistemas estáveis ainda é simplificada. A alegação de que mudanças numa camada
não afetam as demais precisa de condições. Os textos originais foram preservados,
sem correção manual apresentada como resultado do Qwen3.

O schema não distingue um componente real de uma categoria abstrata pelo nome.
Não mede verdade factual, sustentação da mensagem ou relevância visual. Faltam
avaliação humana e renderização real. Não se afirma melhora estética com base
no score, na quantidade de objetos ou na exportação. A medição local reduz cortes
observados no preview, mas não garante identidade do layout no PowerPoint.

O título continua condicionado à mensagem inicial; não houve nova revisão
editorial automática. Há alternativas finitas e apenas cadeias verticais
conectadas; não há paginação automática, grafo arbitrário ou interpretação completa
de estilo. Explicações extensas podem ser rejeitadas. Próxima etapa recomendada:
declarar papel semântico dos nós e relações, verificar sustentação/cobertura e
avaliar com leitores antes de aumentar novamente a capacidade.

Branch, HEAD e alterações anteriores foram preservados; sem commit/push nesta
etapa. Artefatos ficam em `outputs/`. O diagnóstico anterior não foi reescrito.
