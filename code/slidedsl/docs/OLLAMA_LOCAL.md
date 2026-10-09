# Ollama instalado e modelos locais

Fontes oficiais registradas previamente em [refs/FONTES.md](../refs/FONTES.md).
Ollama 0.40.1 foi instalado por winget na conta Windows, com hash do instalador
verificado. O executável fica em `%LOCALAPPDATA%/Programs/Ollama/ollama.exe`, e
os pesos ficam em `%USERPROFILE%/.ollama/models`, fora do projeto e do OneDrive.
A API local respondeu em `http://127.0.0.1:11434`.

Instalados: `qwen3:0.6b` (522 MB) e `qwen3:4b` (2,5 GB). Os digests completos,
quantização, capacidades e parâmetros dos modelos foram salvos em
`outputs/ollama/models.json` e `outputs/ollama/show_*.json`. Logs de instalação e
download ficam no mesmo diretório. Nenhum login remoto foi necessário.

Hardware consultado: aproximadamente 16 GiB de RAM, NVIDIA RTX 3060 com 12 GiB
de VRAM, driver 591.44. `outputs/ollama/gpu.csv` registra a GPU/driver;
`running_models.json` registra o contexto e a alocação de VRAM observados durante
o benchmark. O estado de GPU é uma captura, não uma medida contínua de utilização.

## Reproduzir

```powershell
winget install --id Ollama.Ollama --version 0.40.1 --exact --source winget --accept-package-agreements --accept-source-agreements --silent --disable-interactivity
$ollamaExe = Join-Path $env:LOCALAPPDATA 'Programs/Ollama/ollama.exe'
& $ollamaExe pull qwen3:0.6b
& $ollamaExe pull qwen3:4b
& $ollamaExe list
```

Após a instalação, o aplicativo mantém a API local em segundo plano. Caso ela não
esteja disponível, execute `& $ollamaExe serve` em outro terminal. A partir da raiz
de `code/slidedsl`, use um diretório de saída novo a cada experimento:

```powershell
.\.venv\Scripts\slidedsl.exe benchmark --models qwen3:0.6b,qwen3:4b --repetitions 5 --out outputs/novo_experimento_ollama
```

O relatório desta execução fica em `outputs/reports_ollama_20261008/` e conserva
raw, DSL, diagnósticos e métricas por rodada. O benchmark anterior, no qual faltava
Ollama, continua preservado em `outputs/reports_final/`.

## Configuração do experimento

Mesmo pedido literal, mesma gramática e mesmos dois exemplos para os dois modelos.
Antes da primeira execução com respostas reais, foi corrigida a codificação dos
acentos no prompt técnico. Seu novo hash fica no relatório; o pedido literal não
foi alterado. Não há comparação de métricas com o prompt anterior, que não recebeu
respostas de modelos reais.

O adaptador consulta `/api/show` e prefere `think=false`. A tag 0.6b instalada
declara `values=[false,true]`; a tag 4b declara `values=[true]`, portanto recebe
`think=true`. Essa limitação fica nos metadados, com valor solicitado e efetivo.
Ambos recebem temperatura 0, seed 42, `num_ctx=16384` e `num_predict=8192`.
Contexto explícito acomoda gramática, programa
anterior e diagnósticos no reparo; evita depender do padrão de 4096 observado no
servidor desta máquina. Timeout por chamada: 300 segundos. Esses parâmetros são
registrados nos metadados de cada resposta. Quinze testes de modelos/benchmark/CLI
passaram após os ajustes de contrato HTTP e retomada, assim como Ruff check/format.

## Retomada e controle de validade

O primeiro piloto enviou `think=false` à tag 4b antes de detectar sua limitação.
Essas tentativas estão em `discarded_unsupported_thinking/` dentro do relatório e
ficam fora das taxas finais. A resposta incorreta não foi editada ou recortada.
O adaptador passou a usar o parâmetro suportado; a resposta final da API é
`message.content`, enquanto `message.thinking` é um campo separado. O número de
caracteres do campo separado é registrado nos metadados.

As cinco repetições completas do 0.6b foram preservadas e reutilizadas por
`benchmark --resume`. A retomada exige os mesmos bytes dos prompts, configuração,
rubrica, identidade da tentativa, hash da resposta, digest do modelo e parâmetros
registrados. Uma repetição incompleta não é sobrescrita; precisa ser preservada fora
de `attempts/` antes de reexecutá-la. O relatório conta repetições reutilizadas,
e conserva suas durações originais. A etapa 4b é executada novamente com controle
suportado e o mesmo pedido; prompts não são personalizados por modelo.

A comparação envolve regimes efetivos distintos de thinking, além dos tamanhos dos
modelos. Não isola causalmente o número de parâmetros. O limite de 8192 tokens inclui
a geração do provedor; `done_reason=length` identifica saída limitada pelo orçamento.

Cinco repetições com seed/temperatura fixos podem repetir respostas idênticas;
isso não equivale a cinco amostras independentes. A/B usam a mesma primeira resposta,
e C permite até dois reparos. Não se corrigem os arquivos gerados manualmente.
