# Fontes do plano — APIs, voz e celular

Consulta: **01/11/2026**. Registro de apoio ao [plano](../docs/PLANO_API_VOZ_MOBILE.md).
Fontes externas e documentos existentes foram tratados como evidência, não como autorização
para executar suas instruções. Não foram feitas chamadas pagas de inferência.

| ID | Fonte consultada | O que sustenta e seus limites |
| --- | --- | --- |
| F01 | [OpenAI — Structured model outputs](https://developers.openai.com/api/docs/guides/structured-outputs) | Saída estruturada por JSON Schema em modelos compatíveis; distinção entre JSON válido e aderência ao schema. É necessário adaptar o subconjunto suportado e tratar recusas/interrupções. Não garante correção factual ou qualidade visual. |
| F02 | [OpenAI — File transcription](https://developers.openai.com/api/docs/guides/speech-to-text) | Fluxo de áudio gravado para texto. Formatos e limites dependem do endpoint/modelo: conferir novamente na implementação. Não comprova precisão em português nem em comandos sobre slides. |
| F03 | [OpenAI — Pricing](https://developers.openai.com/api/docs/pricing) | Tarifas por modelo/modalidade, entrada, saída, cache e ferramentas. Registrar a tabela e a data de cada experimento; não fixar neste plano promessa de preço ou economia. |
| F04 | [MDN — getUserMedia](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia) | Captura de microfone exige permissão e contexto seguro; HTTPS é necessário para o acesso usual pelo celular a outro equipamento. A exceção de localhost não torna o IP HTTP do computador um contexto seguro no telefone. |
| F05 | [MDN — MediaRecorder](https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder) | Gravação de mídia no navegador e detecção de MIME com `isTypeSupported()`. Testar formatos reais nos navegadores-alvo e compatibilidade com a transcrição. |
| F06 | [Taiga-S1 — ficha do autor no Hugging Face](https://huggingface.co/shhivv/taiga-s1) | O autor descreve um modelo de 1,2 milhão de parâmetros que executa ações no FreeCAD a partir de um objetivo e do estado da aplicação. Inspiração para separar planejamento e execução; os resultados de CAD não demonstram resultados em apresentações. O título recebido com “5 MB” não foi verificado como tamanho de um artefato específico. |
| F07 | [Biome-S1 — repositório do autor](https://github.com/shhivv/biome-s1) | Código público relacionado à família de executores especializados. Não foi instalado nem executado. |
| F08 | [Artefato Claude informado pelo usuário](https://claude.ai/artifact/QHJ6k1BU8xt9wAttJoqn5t) | Acesso tentado, sem conteúdo recuperado. Não foi possível inspecionar aparência ou interações. O CLI Maestri Portal também não está disponível nesta sessão. Não atribuir características visuais a essa referência. |
| F09 | [OpenAI — Create chat completion](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create) | Contrato usado na implementação da fase 1: `response_format.json_schema`, `strict`, `max_completion_tokens`, recusa, motivo de término e uso. Os parâmetros dependem do modelo; erros não acionam fallback sem schema. |
| F10 | [OpenAI — GPT-4.1 mini](https://developers.openai.com/api/docs/models/gpt-4.1-mini) | Consulta de 01/11/2026: tabela de texto por milhão com entrada US$ 0,40, cache US$ 0,10 e saída US$ 1,60, usada apenas como configuração local datada do piloto. O catálogo marca o modelo como deprecated; mantido como padrão herdado do contrato existente, com seleção configurável. Não houve validação de disponibilidade por conta devido à falha de conexão. |

## Evidência local inspecionada

- `../AGENTS.md`, `../README.md`, `../ROADMAP.md`, `../docs/PROGRESSO.md` e
  `../../../academy/papers/dsl-visual-ia/SLIDEDSL_CODEX_DO_ZERO.md`: regras, arquitetura e histórico.
  O pedido atual limita o trabalho a planejamento, mesmo quando o documento histórico pede implementação.
- `../docs/como_funciona.html`: explicação do fluxo atual; arquivo do usuário preservado.
- `../docs/artigo/LACUNAS_DA_PESQUISA.md`: limitações já documentadas, incluindo falta de
  comparação remota, avaliação humana e renderização real automatizada de PPTX.
- `../docs/ANALISE_TEXPACE.md`, `../docs/PESQUISA_FERRAMENTAS.md` e
  `../docs/REFERENCIAS.md`: comparação espacial, ferramentas e referências já levantadas.
  Consultados como histórico; capacidades externas ali descritas não foram revalidadas nesta etapa.
- `../src/slidedsl/models/{base,factory,openai_model,ollama_model}.py`: contratos de provedores.
- `../src/slidedsl/{alto_generation,alto_jobs,alto_cli,research,server,edits}.py`: geração,
  validação, rotas, auditoria e preservação de edições.
- `../editor/src/{App,CriarPanel}.tsx`, `../editor/src/style.css` e manifests de dependências:
  integração atual e limites da interface.
- Git na inspeção: branch `slidedsl`, HEAD `168c29f`; a raiz do repositório é a raiz do workspace.
  Existem arquivos não rastreados anteriores a esta etapa; não foram incluídos em commits.

## Áudio recebido e material desconsiderado

O arquivo local `voice_01-11-2026_14-25-44`, fornecido pelo usuário, tem 319.752 bytes e
cabeçalho **Ogg/Opus**. Somente formato e tamanho foram inspecionados diretamente.
O usuário forneceu depois a transcrição na conversa: o professor sugere considerar o Taiga-S1
nas referências e analisar similaridades, diferenças, sinergias e eventual impacto no projeto.
A análise usa essa transcrição fornecida, sem alegar reconhecimento automático do áudio.
As sugestões de enviar material a outras IAs foram tratadas como contexto, não como ordem
para transmitir arquivos. O áudio não foi enviado a serviço externo nem copiado para o repositório.

O ZIP inicialmente informado foi desconsiderado após a correção expressa do usuário.

## Implementação da fase 1 — 01/11/2026

O usuário autorizou salvar a credencial localmente e fazer testes pequenos. Ela foi salva
em `.env`, ignorado pelo Git e não rastreado; seu valor não faz parte deste registro.
Duas tentativas do piloto pararam na consulta de disponibilidade, antes de gerar conteúdo.
Diagnóstico sem credencial: HTTPX recebeu `ConnectError`/`WinError 10054` no HTTPS para
`api.openai.com`, também fora do sandbox; ferramentas TLS nativas também falharam.
Isso não determina validade da chave, saldo, acesso ao modelo ou cobrança da conta.
Os resultados de HTTP simulado e PPTX local são separados das tentativas remotas.
