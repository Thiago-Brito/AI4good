# Investigação de rastreabilidade — 11/10/2026

Diagnóstico registrado antes das alterações desta etapa. O estado anterior possui
alterações locais da etapa conceitual; nenhuma será descartada. Snapshot B em
`outputs/coverage/investigation_01/runtime/B`, com hashes. Sem commit/push.

`requirements.py` possui Requirement tipado e extração determinística, mas reconhece
sobretudo estrutura. `evaluate_requirements` examina AST/IR: `all_met` não mede
completude ou correção factual. `contextual.py` congela requisitos antes das chamadas.
`conceptual_planning.py` prepara registros posicionais, verifica referências/fontes
e projeta literalmente os selecionados. `visual_planning.py` seleciona IDs por
intenção, até três por slide. A projeção lista selected/unselected sem requisitos.
`review_plan` em semantic_planning reage a K/Q, não a omissões sem sinais lexicais.
`reliability.evaluate_state` já verifica geometria, semântica e requisitos;
`element_paths` relaciona elementos emitidos a campos do plano. `compiler.inspect_pptx`
permite conferir textos nativos. Esses mecanismos serão reutilizados.

Pontos de extensão: origem e contrato de conteúdo em Requirement; requirement_ids
opcionais nos registros conceituais; relatório separado C001–C005 (sem conflito
encontrado em src/tests); rastros posicionais de projeção e correspondência literal
por campo na IR; recuperação por acréscimo à seleção, sem reescrita, retirada,
mudança de slide/intenção, novas relações ou chamadas adicionais. Avaliar candidatos
pela cadeia existente, vetando novos bloqueios/sinais e perda de requisitos.

Extração conservará trechos e posições do pedido, separando cláusulas explícitas;
não será interpretação completa do português. Requisitos sem teste factual serão
explicitamente não verificáveis. Associação da SLM não certifica cumprimento.
Ausência de conteúdo não autoriza inventar afirmações. A flag será desligada por
padrão, com recuperação separadamente desativável.

Experimentos previstos: A histórico congelado, B snapshot anterior e C novo,
seis pedidos, parâmetros históricos, novas pastas, revisão igual em B/C. Replay
dos mesmos planos com/sem recuperação separará o efeito determinístico das mudanças
nos schemas/prompts. Chamadas reais, bytes, tokens, falhas, hashes e duração serão
preservados; notas de avaliadores independentes permanecerão null.
