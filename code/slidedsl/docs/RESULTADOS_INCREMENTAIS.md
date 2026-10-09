# Resultados reais da geração incremental local

Fontes registradas em [FONTES.md](../refs/FONTES.md). O projeto existente foi estendido;
GLC, parser, AST, semântica, IR, editor e compilador foram preservados. Nenhum deck
manual foi usado como substituição de uma resposta inválida.

## Critério de conclusão demonstrado

O comando Windows completo foi executado, gerou cinco slides reais por SLM,
exportou PPTX e abriu o editor em produção com a fonte efetivamente produzida:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/demo_slm_windows.ps1 -Mode direct -Strict -Out outputs/demo_local/windows_direct_final
```

Modelo: qwen3:4b-instruct. Pedido: introdução à SlideDSL com IA local, em
[demo_slm_local.txt](../benchmark/prompts/demo_slm_local.txt). Resultado observado:
cinco chamadas, zero reparos, sintaxe e semântica válidas, validação estrita aprovada
e **zero diagnósticos**. Inspeção do PPTX encontrou cinco slides, 16 objetos de texto
e oito formas editáveis. Os textos, IDs, dimensões, coordenadas e formas vieram das
respostas do modelo. A montagem apenas imprimiu os comandos e renumerou os slides.

Evidências da execução:

- [PowerPoint](../outputs/demo_local/windows_direct_final/presentation.pptx)
- [Código SlideDSL](../outputs/demo_local/windows_direct_final/presentation.sld)
- [AST](../outputs/demo_local/windows_direct_final/ast.json), [IR](../outputs/demo_local/windows_direct_final/ir.json) e [diagnósticos](../outputs/demo_local/windows_direct_final/diagnostics.json)
- [Auditoria de proveniência](../outputs/demo_local/windows_direct_final/audit.json)
- [Editor em produção](../outputs/demo_local/windows_direct_final/production_editor.png) e [checagem executada](../outputs/demo_local/windows_direct_final/production_editor_check.json)

A auditoria conferiu message.content contra raw.txt, hashes, prompts enviados, cenas
por rodada selecionada e textos nativos no PPTX. O editor em localhost:8000 carregou
o mesmo arquivo e os cinco slides sem erro JavaScript. O teste de navegador também
editou uma execução direta real em `direct_demonstracao`, revalidou e exportou
`editor_modified.sld` e `editor_modified.pptx`, preservando o original do modelo.

O modo JSON também demonstrou cinco slides reais em `windows_strict`: seis chamadas,
um reparo de D010, validação estrita e PPTX concluídos. Essa execução contém informações
D002 de contraste indeterminado; os previews mostram composições que ainda exigem
revisão visual. Uma execução anterior de JSON passou apenas na validação básica,
com aviso de overflow, e foi preservada. A demonstração direta acima é a entrega
principal sem diagnósticos. Não se afirma que todo pedido ou toda repetição funcionará.

## Avaliação do pedido original complexo

Foram concluídas **30 execuções**, com três modelos, dois modos e cinco repetições
por configuração. Cada apresentação tentou gerar os mesmos cinco slides originais
de capa, contraste, proximidade, camadas e comparação; o pedido literal em
`tarefa_cinco_slides.txt` não foi substituído pelo pedido introdutório da demonstração.

Parâmetros: temperatura 0,1, contexto 8192, máximo 4096 tokens por slide/chamada,
até dois reparos por slide, seeds 42–46 pareadas por repetição, thinking efetivo false,
Ollama 0.40.1, Python 3.12.10 e renderer Node 24.14.0. Prompts são iguais entre
modelos dentro de cada modo; direct/json têm prompts, schema e serialização diferentes.
Esse protocolo usa validação padrão: erros fatais bloqueiam, avisos ficam registrados.

Dados: [evaluation.json](../outputs/evaluation_incremental/evaluation.json),
[CSV](../outputs/evaluation_incremental/evaluation.csv),
[análise auditada](../outputs/evaluation_incremental/ANALISE_AUDITADA.md) e
[auditoria completa](../outputs/evaluation_incremental/audit_analysis.json).

Cada fração abaixo tem denominador cinco apresentações. Inicial/final separa a
primeira resposta por slide das respostas depois dos reparos. Completa API significa
cinco respostas não vazias com done=true e done_reason=stop; não é avaliação factual.

| Modelo | Modo | Completa API inicial/final | Sintaxe inicial/final | Semântica inicial/final | PPTX final | Correções |
|---|---|---|---|---|---:|---:|
| qwen3:4b-instruct | direto | 5/5 → 5/5 | 1/5 → 2/5 | 1/5 → 2/5 | 0/5 | 20 |
| qwen3:4b-instruct | JSON | 5/5 → 5/5 | 5/5 → 5/5 | 0/5 → 5/5 | 2/5 | 11 |
| qwen3:0.6b | direto | 4/5 → 5/5 | 0/5 → 0/5 | 0/5 → 0/5 | 0/5 | 37 |
| qwen3:0.6b | JSON | 5/5 → 5/5 | 5/5 → 5/5 | 0/5 → 0/5 | 0/5 | 50 |
| qwen2.5:3b-instruct | direto | 2/5 → 3/5 | 0/5 → 0/5 | 0/5 → 0/5 | 0/5 | 35 |
| qwen2.5:3b-instruct | JSON | 5/5 → 5/5 | 0/5 → 4/5 | 0/5 → 3/5 | 2/5 | 14 |

Foram **317 respostas físicas reais**, 150 iniciais e 167 reparos, todas auditadas.
Não houve content vazio nem erro de transporte. Houve uma finalização length no
0.6b direto e sete no Qwen2.5 direto; todas as demais finalizaram com stop. Schema
JSON auxiliou a sintaxe, mas não garantiu valores dentro de todos os limites,
IDs únicos, referências existentes, requisitos do pedido ou geometria aprovada.

Erros de design abaixo somam somente as últimas rodadas dos slides cuja semântica
foi alcançada. O denominador potencial é 25 slides por configuração; não alcançado
não é design aprovado. Diagnósticos INFORMAÇÃO ficam no JSON, separados de avisos.

| Modelo | Modo | Slides com design alcançado /25 | Erros finais de design | Avisos finais de design |
|---|---|---:|---:|---:|
| qwen3:4b-instruct | direto | 22 | 14 | 13 |
| qwen3:4b-instruct | JSON | 25 | 5 | 10 |
| qwen3:0.6b | direto | 11 | 0 | 4 |
| qwen3:0.6b | JSON | 5 | 7 | 12 |
| qwen2.5:3b-instruct | direto | 8 | 0 | 18 |
| qwen2.5:3b-instruct | JSON | 22 | 1 | 35 |

## O que falhou e o que os reparos conseguiram fazer

- 4b direto: faltaram colchetes em `agrupar`, causando P001, e caixas do slide 5
  saíram do canvas, causando D001. Houve reparos de sintaxe em parte das rodadas,
  mas nenhuma apresentação complexa completa foi aprovada para PPTX.
- 4b JSON: a primeira geração do slide 4 usou operações back/front sobre `foto`
  sem criar esse ID. S003 apareceu nas linhas 9/10 da DSL convertida; os cinco casos
  foram corrigidos. Três apresentações continuaram com D001 no slide 5.
- 0.6b direto: permaneceu com P001 em slides de grupos/camadas/comparação. JSON
  tornou as 25 saídas sintaticamente analisáveis, mas houve IDs duplicados (S002),
  grupos inválidos (S008) e caixas fora do canvas. Os reparos não produziram PPTX.
- Qwen2.5 direto: cabeçalho inventado `principios_de_design_de_slides` no lugar de
  `apresentacao`, ordem errada de `arquivo` na imagem, repetição/truncamento e P001.
  No JSON, a largura 200 de caixas de texto descumpriu o mínimo 480 do schema,
  gerando J001 antes do parser. Também houve S002, S003 e D001. Parte foi corrigida.

Exemplos verificáveis ficam nos `diagnostics.json`, raw.txt e response.json por
modelo/modo/repetição/slide/rodada em `outputs/evaluation_incremental/runs/`.
Os quatro PPTX compilados foram auditados individualmente: cenas correspondem às
respostas selecionadas e textos são objetos nativos. Todos quatro têm avisos que
reprovam a validação estrita; não foram apresentados como resultados sem problemas.

Compilar também não equivale a cumprir todo o pedido original. A rubrica de 17
proxies registrou 14/17 para os dois PPTX do 4b JSON, 8/17 e 10/17 para Qwen2.5 JSON.
Nenhum atingiu 17/17. A análise auditada lista os itens não atendidos, como relações
de alinhamento, grupos de proximidade e comparação em colunas. Esses proxies não
validam verdade factual nem beleza.

## Engenharia e limites

Passaram 123 testes Python, dois testes Node e quatro Playwright, incluindo uma
apresentação real do SLM aberta, editada, revalidada e exportada novamente. Ruff,
ESLint, Prettier, TypeScript e build Vite passaram. O aviso transitivo AnyIO/Starlette
permanece registrado. O comando único completo e o editor de produção também rodaram.

Corrigida a herança de acesso Windows do PPTX proveniente de TemporaryDirectory;
os arquivos recuperados conservaram hashes e foram lidos pelo usuário normal.
Os conjuntos históricos A/B/C e os pilotos malsucedidos foram preservados.

A demonstração introdutória e a avaliação complexa são tarefas diferentes. Os
pilotos orientaram os prompts/schema antes da avaliação final e não entram nas taxas.
Comparar JSON e código direto mede protocolos com capacidades/limites diferentes;
não isola efeito do tamanho do modelo nem da GLC. Seeds pareadas e apenas cinco
repetições não sustentam uma conclusão estatística geral. Durações incluem cache,
carregamento e chamadas da demonstração/testes durante o experimento; não foram
usadas para alegar superioridade causal de velocidade. Máximo de comprimento de
string no JSON pode produzir frases cortadas; stop não assegura qualidade do texto.
Preview de navegador é geométrico; não houve renderização pelo PowerPoint COM.

Reprodução e contrato completos: [SLM_LOCAL_FUNCIONAL.md](SLM_LOCAL_FUNCIONAL.md).
Diagnóstico das 30 respostas antigas: [DIAGNOSTICO_OLLAMA.md](DIAGNOSTICO_OLLAMA.md).
