# Plano da noite de 26/11/2026: fluxo com documento, todos os modelos

**Pedido do autor:** testar com todos os modelos e ir melhorando até chegar ao melhor, em loop, num branch separado, sem afetar o código congelado.

**Branch:** `exp/noite-26nov`. O código do artigo está congelado em `artigo-v2` / `congelado/artigo-v2` e não muda. O branch `feature/slidedsl-api-voz-mobile` também não recebe nada esta noite.

## Regras (valem em toda volta do loop)

- Antes de tarefa pesada: `powershell -NoProfile -File scripts/memoria_livre.ps1 -MinGB 3`. Se não houver memória, esperar a próxima volta.
- Uma tarefa pesada por vez (GPU ou llama-server). Não iniciar outra se houver uma em segundo plano.
- Não fechar programas do usuário; o daemon Gradle da extensão Java do VS Code fica intocado.
- Não mexer no artigo (`academy/papers/artigo-overleaf`) nem no app do celular (`mobile/app`) nesta noite.
- Commits só neste branch, sem coautor; push permitido neste branch. Nunca commitar `outputs/`, `.env`, chaves, GGUF ou APK.
- **OpenAI (GPT-5.4-mini): orçamento total da noite de US$ 1,00.** Somar `custo.json` de cada execução em `docs/NOITE_26NOV.md`; parar de usar a API ao chegar perto do limite.
- Toda mudança de código: `pytest` completo (`--basetemp D:/pyt/<nome> -p no:cacheprovider`) verde antes do commit.
- Mudança que piora uma métrica em outro caso é revertida ou restrita ao caso em que ajuda.
- **Fim: 08:30 de 26/11.** Depois disso, só escrever `docs/RESUMO_NOITE_26NOV.md`, fazer o commit final e apagar o cron.

## O que é "melhor"

Para o fluxo com documento, numa apresentação gerada a partir de `outputs/diferencial_professor/diferencial_v2.md` (8 slides, o pedido de `outputs/criar/b8ae5384784247b285307924df7dfa00/pedido.txt`):
1. válida (compila);
2. cobre as 7 seções do documento;
3. traz os números-chave: 1 de 24, 13 de 24, 19 de 24, 1.380, 1.344, 0,98, 63, 18 a 21, 23;
4. sem afirmação invertida (ex.: "a garantia custa mais caro");
5. menos tempo e chamadas, a qualidade igual.

Para a geração sem documento (12 pedidos do Teste 3, semente 11, modo gramática, Qwen3 4B): validade, reparos, tokens e tempo não podem piorar.

## Fila de tarefas (fazer em ordem; marcar aqui ao concluir)

- [ ] **T1. A/B sem documento** (`scripts/regressao_pc_ab.sh`, rodando desde 26/11 ~00h; antes = commit f12b102 em `D:/wt_antes`). Comparar `outputs/regressao_pc_ab/antes` × `depois`. Se 6 fatos por slide piorar validade, reparos ou tempo (>10%), aplicar 6 só quando houver documento.
- [ ] **T2. Script de avaliação automática** `scripts/avaliar_documento.py`: lê o `.slda` de uma execução e mede os itens 1–4 acima (seções pelas palavras dos títulos, números presentes no texto visível, lista de frases suspeitas de inversão).
- [ ] **T3. Bancada de modelos com o documento** (`diferencial_v2.md`), uma execução por modelo, registrada em `docs/NOITE_26NOV.md`:
  - motor do celular no PC (`scripts/e2e_motor_celular.py --modelo ...`): `qwen3-0.6b-lora`, `qwen3-0.6b`, `qwen3-1.7b`, `qwen3-4b-instruct`, `qwen3-4b-instruct-lora`;
  - fluxo completo do PC: `--provider llamacpp` (Qwen3 4B local) e `--provider openai --model gpt-5.4-mini`.
- [ ] **T4. Limites do compilador na gramática do PC.** O fluxo do PC com o 4B local falha por rótulo acima de 48 caracteres (A005), porque a gramática do PC não tem os limites, e a do app tem (`mobile/app/src/pipeline/altoText.ts`, `withCompilerLimits`). Portar a ideia para `src/slidedsl` (modo gramática), medir com T1 (12 pedidos) e T3 (documento).
- [ ] **T5. O que T3 mostrar** como pior defeito restante (ex.: slide de resultados sem todos os números; título que contradiz os fatos). Uma correção por volta, sempre medida antes e depois.
- [ ] **T6. Repetir T3 com a melhor configuração** e escolher a recomendação por modelo.
- [ ] **T7. Resumo** em `docs/RESUMO_NOITE_26NOV.md`: o que mudou, números antes e depois, o que não funcionou, o que recomendo levar para o branch principal.

## Registro

Cada volta acrescenta uma linha em `docs/NOITE_26NOV.md` (hora, tarefa, resultado, custo da API acumulado).
