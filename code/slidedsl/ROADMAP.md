# Roadmap — SlideDSL

## Evolução visual/contextual — 11/10/2026
- [x] Base limpa: 9b6a8edf80ce4b76c54c13bcbb7fc0e768aab847; hash confirmado em origin/dsl-visual, sem commit vazio.
- [x] Imagens de APIs oficiais, segurança, cache e seis layouts editáveis; Openverse/NASA consultados, Commons real indisponível (403).
- [x] Personalização opcional, referências locais e rastreabilidade; restrito extrativo validado com SLM real.
- [x] Validação V004–V006, renderização opcional e preservação conservadora de edições com conflitos.
- [x] Experimento novo: 20 avaliações estruturais, 17 chamadas reais; cinco planos compartilhados, auditoria e documentação.
- [x] Regressão: 209 Python, dois Node e onze Playwright; lint/formatação/build; upload de imagem própria offline.
- [x] Revisão final para commit/push na branch dsl-visual; confirmação no relatório de entrega.
- [ ] Renderização COM/LibreOffice real, avaliação humana, maior amostra, GPU, conectores ancorados e sincronização completa plano/IR.

## Núcleo e fases históricas

- [x] Fase 0: ambiente e pesquisa oficial
- [x] Fase 1: GLC, AST e printer
- [x] Fase 2: semântica, IR, geometria e extensões 1.1
- [x] Fase 3: regras D001–D010
- [x] Fase 4: PowerPoint editável de cinco slides
- [x] Fase 5: adaptadores e geração
- [x] Fase 6: benchmark, ablação e relatório real
- [x] Fase 7: editor visual e teste UI
- [x] Fase 8: integração, documentação e defesa
- [x] Instalar Ollama 0.40.1 e baixar qwen3:0.6b/qwen3:4b na máquina
- [x] Completar experimento local: cinco repetições por Qwen3, A/B/C e até dois reparos; ambos 0/5 parse inicial/final
- [ ] Experimento remoto: aguarda credencial/acesso OpenAI
- [x] Diagnosticar e reproduzir P001 nas 30 respostas físicas originais
- [x] Implementar geração incremental direta/JSON restrito, parser/semântica existentes e até dois reparos explícitos
- [x] Validar uma demonstração SLM real de cinco slides, PPTX editável e editor
- [x] Comparar três modelos, dois modos e cinco repetições por configuração: 317 respostas auditadas, quatro PPTX no pedido complexo; demonstrações estritas separadas
- [x] Explicar no README o fluxo do projeto e a GLC, com exemplo executável validado e compilado

## Evolução SLM — 10/10/2026
- [x] Analisar arquitetura/evidências e verificar base: 123 testes Python passaram; Ollama 0.40.2 disponível.
- [x] Implementar plano sem coordenadas, IDs determinísticos, três layouts e validação pela cadeia original; 24 testes de etapa passaram, incluindo PPTX reais.
- [x] Implementar estratégias A/B sem reparos e C/D com planejamento; D aplica patches em campos diagnosticados, com limite de dois reparos.
- [x] Integrar geração, modelos locais e progresso à interface existente; fluxo real de geração/edição/exportação verificado no navegador.
- [x] Executar comparação A/B/C/D: 40 execuções, 122 respostas auditadas; PPTX estrito A 0/10, B 0/10, C 10/10, D 9/10. Nenhum pedido complexo atingiu 17/17.
- [x] Verificar regressão (141 Python, 2 Node, 7 Playwright), demonstração real e editor de produção; documentar em EVOLUCAO_SLM.md.
- [ ] Ampliar pedidos/seeds e isolar reparos a partir do mesmo plano inicial; corrigir omissões de requisitos (formas/camadas) e avaliar conteúdo com pessoas.

## Confiabilidade — 11/10/2026
- [x] Commit e push prévios: c53bb4498a6aba2812e22014bd1cf66954abfd13, origin/dsl-visual.
- [x] Requisitos tipados por slide, verificação AST/IR independente e diagnósticos R001.
- [x] D com adições determinísticas autorizadas, patches locais, limite configurável, progresso, rejeição de regressões e estados antes/depois.
- [x] Cards, sequência e fluxo; layouts anteriores preservados, geometria compacta sem cortar textos.
- [x] V001–V003 e fases separadas; investigar renderização real (PowerPoint COM indisponível).
- [x] Ablação com oito planos compartilhados, quatro pedidos e 32 avaliações: 8 respostas reais, 30 PPTX auditados; complexo 17/17 nas duas repetições após reparo.
- [x] Interface de requisitos/correções/revalidação; fluxo real com Ollama e exportação.
- [x] Documentar arquitetura, evidências e limites em docs/EVOLUCAO_CONFIABILIDADE.md.
- [ ] Ampliar amostra e avaliação humana; resolver overflow persistente, interpretação de pedidos e reparo depois de edição manual.
