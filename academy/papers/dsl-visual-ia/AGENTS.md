# Instruções permanentes do agente — SlideDSL

Você está construindo **SlideDSL do zero para Windows**. Não reaproveite protótipos, código ou PPTX de trabalhos anteriores.

**Fonte normativa:** leia integralmente `SLIDEDSL_CODEX_DO_ZERO.md` e implemente TODAS as fases e critérios de aceite definidos ali. Se houver conflito entre uma suposição sua e a especificação, siga a especificação ou registre justificativa técnica detalhada.

## Regras de trabalho

1. Não entregue só documentação, pseudocódigo, skeleton ou plano; crie os arquivos reais e execute o sistema quando possível.
2. Comece por parser Lark/GLC, AST, semântica/IR, geometria; depois validador de design, PPTX, IA/benchmark, editor visual e integração final.
3. Mantenha uma camada IR independente de PptxGenJS/Canva/Google Slides.
4. O backend obrigatório é PptxGenJS e gera PowerPoint editável.
5. Não invente testes ou métricas; execute os testes disponíveis e informe bloqueios reais.
6. Não exija credenciais OpenAI, Google ou Canva para que testes, compilação e demo offline funcionem.
7. Registre a cada etapa o que foi implementado em `docs/PROGRESSO.md` e prossiga automaticamente.
8. Implemente todos os casos negativos e positivos definidos e gere apresentação demonstrativa real de cinco slides.
9. Garanta compatibilidade Windows/PowerShell, incluindo caminhos com espaços.
10. No relatório final, liste resultados reais, limitações, comandos de execução e arquivos gerados.

**Comece a trabalhar imediatamente.**
