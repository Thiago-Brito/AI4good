# Experimento reproduzível

O protocolo histórico A/B/C abaixo permanece intacto. A nova comparação incremental
usa `evaluate-local`, três tags locais, modos direct/json separados, cinco repetições,
seeds 42..46, temperatura 0,1, contexto 8192 e saída 4096 por solicitação de um slide.
Seu contrato e registros são descritos em [SLM_LOCAL_FUNCIONAL.md](SLM_LOCAL_FUNCIONAL.md).
O pedido original complexo permanece em tarefa_cinco_slides.txt; a demonstração
introdutória usa outro pedido explicitamente identificado e não entra nessas taxas.
O JSON é sempre convertido em DSL, reanalisado e compilado pela cadeia existente.
A execução final concluiu 317 respostas físicas e quatro PPTX na validação padrão;
ver [RESULTADOS_INCREMENTAIS.md](RESULTADOS_INCREMENTAIS.md). Os avisos de design e
itens do pedido não atendidos estão separados do sucesso de compilar.
Fontes técnicas registradas em [refs](../refs/FONTES.md); protocolo normativo na
especificação. Pedido literal em `benchmark/prompts/tarefa_cinco_slides.txt`;
prompt único em `prompts/system_dsl.txt`, incluindo GLC e dois exemplos. Nenhuma
personalização por modelo. Configuração: `config/models.yaml`, temperature=0;
Ollama seed=42, OpenAI seed omitida por padrão e registrada como null.

IDs: qwen3:0.6b, qwen3:4b, gpt-4.1-mini e gpt-4.1. Alternativa explícita:
`--models ollama:outro-id` ou `openai:outro-id`, registrada como substituição.
Logs guardam runtime, versão/digest disponível, fingerprint remoto, prompts e hashes.
Chave só no ambiente; nenhum header HTTP ou corpo de erro de conta é registrado.

Cinco repetições por modelo disponível. A/B compartilham os bytes da geração
inicial: A executa GLC/semântica e compila, sem medir avisos; B acrescenta observação
de design, sem correção. Ambos usam backend seguro, que rejeita erros fatais de
geometria. C começa com os mesmos bytes e permite duas respostas adicionais guiadas
por diagnósticos. Cada rodada preserva raw, .sld, parser log, AST, IR, diagnóstico,
PPTX quando válido e métricas. Primeira e última tentativa ficam separadas.

Rubrica automática: 17 itens em `benchmark/rubric.yaml`, com numerador/denominador.
Título/tema, número de slides, caixas da capa, exemplos, grupos, camadas, colunas,
rodapé, margens e integridade. Conteúdo usa proxies lexicais documentados: não
confere verdade factual nem qualidade da explicação. `layer_actions` avalia AST;
`layer_correctness` avalia Z e interseção parcial na IR final. Densidade e overflow
são aproximações, não nota de beleza.

Métricas: parse_success, semantic_success, compile_success, instruction_coverage,
design_errors/warnings e contagem D001..D010, layer_correctness, duration_ms da
geração, compile_ms, repair_rounds e success_after_repair. Falha de transporte não
é texto inválido: é registrada separadamente e não tem taxa inventada. Médias usam
somente respostas recebidas e informam n, inclusive programas inválidos.

Na primeira verificação, os quatro modelos ficaram NAO_EXECUTADO; o relatório
histórico permanece em `outputs/reports_final/`. Depois do pedido de instalação,
Ollama 0.40.1 e os dois Qwen3 foram instalados. O [experimento local real](RESULTADOS_OLLAMA.md)
concluiu cinco repetições por modelo em `outputs/reports_ollama_20261008/`: ambos
com 0/5 programas aceitos inicialmente e após até dois reparos. Não houve falha
de transporte no conjunto final. OpenAI continua pendente de OPENAI_API_KEY.
O mock exercita infraestrutura; seus resultados não são atribuídos a modelos reais.

O adaptador consulta `/api/show`: a tag 0.6b aceita `think=false`, mas a tag 4b
instalada só aceita `think=true`. Essa diferença fica nos metadados e limita a
comparação. Contexto 16384 e saída máxima 8192 são iguais para ambos; motivo de
encerramento e tamanho do campo thinking separado são registrados. O piloto com
parâmetro incompatível foi arquivado fora das taxas; `--resume` reutilizou cinco
repetições completas do 0.6b, preservando hashes e durações. Ver [detalhes](OLLAMA_LOCAL.md).

Para ativar: instalar/iniciar Ollama, `ollama pull qwen3:0.6b` e `ollama pull qwen3:4b`;
para OpenAI, chave com conta/cota e acesso aos IDs solicitados. Então rodar
`slidedsl benchmark --repetitions 5 --out outputs/novo_experimento`.
Usar diretório novo evita sobrescrever logs. Relatórios JSON, JSONL, CSV, ANALISE.md
e RESULTADOS_PENDENTES.md são gerados mesmo quando todos estão ausentes.

Amostra pequena, infraestrutura/tokenizadores distintos e avaliação heurística
limitam conclusões. B mede; não melhora automaticamente a geração. B/C só estima
feedback quando modelos reais respondem. Baseline sem DSL exigiria protocolo próprio.
