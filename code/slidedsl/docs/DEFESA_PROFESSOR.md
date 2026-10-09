# Roteiro de defesa e demonstração

Fontes de implementação e ferramentas foram registradas em [refs/FONTES.md](../refs/FONTES.md).
Evidências executadas e limitações estão em [RESULTADOS.md](RESULTADOS.md).

## Problema e hipótese

Uma instrução de apresentação precisa virar objetos, posições e operações verificáveis.
O problema experimental é medir a variação de estrutura e raciocínio espacial entre
SLMs menores e modelos maiores neste domínio, sob o mesmo pedido de cinco slides.
SlideDSL oferece uma linguagem de português controlado para expressar esses contratos.
A hipótese a avaliar é que diagnósticos explícitos ajudam modelos e pessoas a corrigir
programas de slides. A implementação demonstra a cadeia de compilação e a correção
manual no editor. O experimento local foi executado e não houve ganho de parsing
com reparos na configuração histórica; não demonstra benefício geral nem desempenho humano.
Agora também há geração incremental real com qwen3:4b-instruct, nos modos código
direto e JSON convertido em SlideDSL. A demonstração introdutória já compilou cinco
slides. A comparação do pedido complexo fica em um conjunto separado.
Essa comparação concluiu 30 execuções: quatro PPTX no modo JSON, nenhum no direto;
nenhum deck cumpriu os 17 proxies do pedido complexo. A demonstração introdutória
direta, outra tarefa, passou estritamente sem diagnósticos. Os resultados estão em
[RESULTADOS_INCREMENTAIS.md](RESULTADOS_INCREMENTAIS.md), com prompts e respostas auditados.

## Contribuição implementada

O fluxo é pedido → modelo opcional → DSL → parser LALR → AST → semântica sequencial
→ IR tipada → regras geométricas → editor ou PowerPoint editável. A gramática delimita
comandos e argumentos; textos entre aspas continuam sendo conteúdo livre. Sintaxe
válida não implica referência existente, geometria válida ou qualidade visual.
As camadas finais são ordenadas pela IR. O modelo não fornece JavaScript executável.

A produção inicial é `start: apresentacao`; `apresentacao` contém STRING, tema e
`slide+`; cada slide contém INT e `instrucao+`. Os terminais incluem `adicionar`,
`mover`, ID, COR hexadecimal, NUMERO e STRING com escapes JSON. Por exemplo,
`mover a para (80, 100)` é uma instrução sintaticamente válida; `mover a para ontem`
é rejeitada pelo parser. A primeira ainda exige que `a` exista no slide. O catálogo
completo e exemplos estão em [GRAMATICA.md](GRAMATICA.md) e no arquivo Lark.

O editor exibe apresentação, slides, elementos, grupos e relações. Alterações nas
propriedades e conexões espaciais chegam à mesma IR usada pela CLI. Exportação DSL
e reimportação preservam a cena final e relações; não recuperam operações removidas.
O contraste é calculado quando o fundo é conhecido; casos com imagem ou composição
incerta são declarados indeterminados. Overflow textual é uma estimativa documentada.

## Demonstração de aproximadamente cinco minutos

Para demonstrar geração real, comece com
`powershell -NoProfile -ExecutionPolicy Bypass -File scripts/demo_slm_windows.ps1 -Strict`.
Mostre raw/response.json de cada chamada, presentation.sld, ast.json, ir.json e
diagnostics.json na pasta impressa. O editor abre o resultado do SLM, permite mudar
texto/geometria e gerar novo PPTX. O modelo gerou os elementos e coordenadas; o
JSON não foi renderizado diretamente. Veja [contrato](SLM_LOCAL_FUNCIONAL.md).

O roteiro histórico seguinte demonstra separadamente o gabarito e as falhas originais.

1. Mostre `examples/cinco_slides.sld`, a gramática e `outputs/ast.json` para distinguir
   programa, sintaxe e estrutura. A demo é um gabarito escrito manualmente.
2. Execute `scripts/demo_windows.ps1`. Mostre `outputs/deck.json`, a validação e
   `outputs/delivery.json`: cinco slides, objetos editáveis e roundtrip equivalente.
3. Abra `outputs/apresentacao.pptx`. Percorra capa, contraste, proximidade, camadas
   e comparação. O slide 2 contém baixo contraste intencional, reportado por D002.
4. Execute `slidedsl serve`; em localhost:8000 importe `examples/negativo_fora.sld`.
   Valide, selecione o objeto, altere X de 1300 para 80, valide novamente, exporte DSL
   e gere PPTX. Capturas antes/depois e o teste de navegador documentam esse percurso.
5. Mostre `outputs/reports_ollama_20261008/ANALISE.md` e [RESULTADOS_OLLAMA.md](RESULTADOS_OLLAMA.md).
   Explique A/B com geração inicial pareada e C com no máximo dois reparos. Os dois
   Qwen3 executaram cinco repetições cada: 0/5 programas aceitos inicialmente e
   depois dos reparos. Mostre P001 nos arquivos reais. OpenAI ficou pendente de chave.
   Explique o orçamento de tokens e o thinking obrigatório da tag 4b como limitações.

## Perguntas previsíveis

**Por que uma GLC?** Ela permite reconhecer a estrutura dos comandos e localizar
erros. A semântica verifica ordem, tipos e referências; as regras verificam a cena.

**Como os cinco slides foram avaliados?** Testes automatizados, inspeção ZIP/XML,
rubrica estrutural de 17 itens e inspeção dos previews do editor. Isso confirma
objetos, geometria e requisitos avaliados; não substitui julgamento de conteúdo.

**Qual é o papel da IA?** Produzir DSL pelo mesmo prompt e responder aos diagnósticos.
Os adaptadores e o harness foram testados com transportes simulados e executados
com os dois Qwen3 locais. As respostas reais estão preservadas, incluindo as falhas;
uma resposta recebida não equivale a um programa validado.

**O grupo é um grupo nativo de PowerPoint?** Não: é uma estrutura lógica na IR para
transformações e avaliação. Seus componentes são exportados como objetos editáveis.

**Qual a novidade científica?** Este repositório entrega um sistema verificável.
Novidade e eficácia comparativa exigem revisão específica e experimento. Não há
estudo com usuários nem evidência de que uma regra objetiva assegure beleza.

## Escopo e próximos experimentos

O backend v1 é PptxGenJS para um novo deck; Canva e Google foram pesquisados e têm
desenho de adaptadores, sem autenticação nem implementação de backend nesta versão.
Não há importação de PPTX, fontes medidas pelo PowerPoint ou edição nativa de grupos.
Preview COM precisa de PowerPoint instalado e não foi executado neste ambiente.

As cinco repetições locais e suas amostras inválidas foram analisadas. Próximos passos:
executar os modelos OpenAI quando configurados e testar novos orçamentos/prompts
em experimentos separados, preservando a referência atual. Uma futura
avaliação humana deve definir tarefa, tempo, correções e compreensão antes de recrutar
participantes; o protocolo atual não fornece essas medidas.
Animações, layout automático e uma DSL mais expressiva também são extensões futuras.
