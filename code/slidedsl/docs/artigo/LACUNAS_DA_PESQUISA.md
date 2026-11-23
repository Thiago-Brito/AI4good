# Lacunas da pesquisa

Evidências ausentes, limitações experimentais e pontos ainda não demonstrados no SlideDSL, com
sugestões concretas para fortalecer o TCC e a defesa. Complementa a seção 9 de
[ARTIGO_CIENTIFICO_SLIDEDSL.md](ARTIGO_CIENTIFICO_SLIDEDSL.md).

Prioridade: **P1** — necessária para sustentar a tese central na defesa; **P2** — fortalece
significativamente; **P3** — desejável.

---

## 1. Afirmações que o projeto faz ou sugere, mas ainda não demonstrou

| # | Afirmação | Situação atual | Prioridade |
|---|---|---|---|
| 1 | "Com GBNF, o modelo não consegue gerar sintaxe inválida" | Verdadeiro por construção, mas o modo `gramatica` **nunca foi executado com modelo real**. Não se sabe se a GBNF derivada é aceita pela versão instalada do llama-server, qual o custo de latência, nem se a qualidade do conteúdo muda. | **P1** |
| 2 | As correções da "segunda e terceira rodadas de qualidade" (A013–A016, termos centrais, charset, comparação numérica) melhoram o conteúdo | Implementadas **depois** do lote E11 (encerrado às 20:51 de 12/10); só têm testes com modelos simulados. | **P1** |
| 3 | A abordagem assertion–evidence melhora as apresentações geradas | O contrato editorial se inspira em Alley; o efeito não foi medido no SlideDSL. | P2 |
| 4 | O verificador de sustentação reduz distorções | Usa o próprio SLM gerador; não há medida de precisão ou revocação. | P2 |
| 5 | Reparos por SLM ajudam | Sem ganho observado em E3, E9 e E10; no E4, a condição com SLM não fez chamadas. Só há efeito no E2 (S003 localizado). | P2 |
| 6 | Conectores ancorados funcionam no PowerPoint | XML conferido; comportamento ao mover formas no Office não testado. | P3 |
| 7 | "Democratizar a IA" com SLMs locais | Argumento de motivação, sustentado por literatura; o projeto não mediu custo, energia ou acessibilidade frente a alternativas. | P3 |

## 2. Evidências experimentais ausentes

### 2.1 Avaliação humana (P1)

Nenhuma apresentação foi avaliada por pessoas. Existem dois instrumentos prontos e não aplicados:
`docs/AVALIACAO_HUMANA_CONTEXTUAL.md` (nove critérios, escala 1–5) e
`outputs/conceptual/final_08/human_rubric.json`. **Sugestão de protocolo mínimo para o TCC:**

- 3 a 5 avaliadores (colegas ou professores), sem acesso à condição que gerou cada deck;
- 12 a 24 decks: o lote E11 (código antigo) e uma repetição com o código final, mais 2 a 4 decks
  feitos por pessoas como referência;
- critérios do PPTEval (ZHENG et al., 2025) — conteúdo, design, coerência — mais correção factual e
  esforço de correção;
- relatar concordância entre avaliadores (por exemplo, alfa de Krippendorff) e médias com intervalos;
- registrar notas individuais e casos de falha, sem converter ausência de avaliação em zero.

### 2.2 Comparação controlada dos modos de restrição (P1)

Uma ablação `json` × `gramatica` × `direto` com os mesmos pedidos, seeds e modelo (em formato GGUF
para llama.cpp e na etiqueta equivalente do Ollama), medindo: validade sintática na primeira
resposta, número de reparos, tempo, tokens, truncamento (A013) e indicadores de conteúdo. Essa é a
única forma de testar diretamente a contribuição da GLC na **decodificação**, e não só na
**validação**.

### 2.3 Repetições e variância (P1)

Todos os experimentos têm de 1 a 5 repetições. Para o TCC, recomenda-se ao menos 5 seeds por
configuração no experimento principal (E11 repetido), com intervalos de confiança simples para as
proporções (por exemplo, Wilson). Observação importante do E3: seeds iguais **não** reproduziram
respostas iguais no Ollama (1 de 10 pares idênticos); as repetições devem ser tratadas como amostras,
e as comparações entre condições devem compartilhar a mesma resposta inicial sempre que possível
(como no E4).

### 2.4 Outros modelos (P2)

- SLMs de outras famílias e tamanhos (por exemplo, Llama 3.2 3B, Phi, Gemma, Qwen 1.5B/7B).
- Um LLM de referência (o adaptador OpenAI existe; falta credencial), para situar o desempenho do
  SLM. Sem isso, não se pode responder "quanto se perde ao usar um modelo pequeno".

### 2.5 Renderização real (P2)

Nenhum PPTX foi aberto no PowerPoint ou no LibreOffice de forma automatizada (`rendered=false` em
todas as etapas). Sugestão: instalar o LibreOffice e usar `render-optional` (variável
`SLIDEDSL_SOFFICE`) para converter os decks em PDF/PNG e comparar com a prévia Pillow, medindo
overflow real e contraste sobre a imagem renderizada.

### 2.6 Custo e desempenho (P3)

O tempo por deck foi registrado (E11: 144–266 s), mas não há medida de GPU/VRAM nem de energia. Um
experimento simples de custo (chamadas, tokens, segundos, memória) por configuração atenderia ao
argumento de eficiência (SCHWARTZ et al., 2020).

## 3. Problemas de validade a declarar na defesa

1. **Pesquisa variável no E11.** As fontes e consultas diferiram entre pedidos, e o SearXNG ficou fora
   do ar em seis casos; não é possível comparar temas nem níveis de detalhe de forma controlada.
2. **Código mudou entre experimentos.** Os experimentos não são comparáveis entre si; cada um tem seu
   *snapshot*.
3. **Pilotos orientaram os ajustes.** Os pedidos de avaliação não são "cegos" em relação ao
   desenvolvimento.
4. **Avaliador = desenvolvedor.** As inspeções qualitativas foram feitas pelo agente de
   desenvolvimento.
5. **Reconhecedor de requisitos com erro conhecido** no E9 (negação "sem rodapé").
6. **Proxies lexicais** (rubrica, cobertura) contam menções, não explicações.

## 4. Lacunas de implementação relevantes para a pesquisa

| Lacuna | Impacto | Sugestão |
|---|---|---|
| Limites de quantidade (2–5 itens etc.) não estão na GLC Alto, só na validação | A GBNF não impede quantidades inválidas na decodificação | Gerar repetições limitadas `{m,n}` na GBNF por tipo (o llama.cpp aceita) |
| `maxLength` corta textos no JSON Schema | Títulos truncados no E11 | Já mitigado (A013 e limites folgados); medir o efeito |
| Verificação de sustentação pelo próprio SLM | Verificador fraco | Usar outro modelo, modelo de NLI ou checagem por especialista |
| Texto alternativo de imagem = ID | Acessibilidade (recomendação da Microsoft) | Usar a legenda ou o título da imagem como `altText` |
| Contraste INDETERMINADO frequente nos layouts Alto | O contraste real não foi medido | Resolver o fundo efetivo (cor do cartão) para formas sobrepostas |
| Paleta Alto com contraste declarado, mas não testado como propriedade | Afirmação do README sem teste dedicado | Teste unitário que verifique todos os pares texto/fundo das paletas |
| Documentação de diagnósticos Alto desatualizada | Divergência doc × código | Atualizar a tabela de `docs/SLIDEDSL_ALTO.md` (A012–A016) |
| Roteiro Alto mostra o texto de no máximo 8 fatos (`facts_block`), mas aceita qualquer ID do dossiê | O modelo pode atribuir fatos que não leu | Mostrar todos os fatos (resumidos) ou restringir o `enum` aos fatos exibidos |
| Reparo Alto regenera o slide inteiro | Um reparo pode alterar campos corretos | Reaproveitar o mecanismo de patches por caminho de `evolution.py` |
| `prompts/system_dsl.txt` desatualizado em relação à GLC | Modo direto histórico ensina uma gramática antiga | Gerar a seção de gramática do prompt a partir do arquivo `.lark` |
| Estudo de cobertura (`coverage-abc-v1`) interrompido | Mecanismo C001–C005 sem avaliação | Concluir o protocolo ou declará-lo fora do escopo do TCC |
| Suíte de testes depende de caminho temporário curto no Windows | 6 falhas com caminho > 260 caracteres | Documentar ou habilitar caminhos longos; o script oficial já usa `outputs/tests/` |
| Dados brutos fora do Git | `outputs/` não é versionado; tabelas do artigo só são verificáveis na máquina do autor | Exportar pacote de dados com hashes (seção 5, item 6) |

## 5. Sugestões para fortalecer o TCC

1. **Delimitar a tese**: "a GLC e o compilador garantem validade estrutural e editabilidade para
   saídas de SLMs locais; a qualidade de conteúdo exige mecanismos adicionais, aqui investigados
   de forma exploratória". Os dados atuais sustentam essa formulação; não sustentam uma afirmação de
   qualidade geral.
2. **Eleger experimentos principais** para a defesa — o E3 (maior amostra controlada: 40 execuções
   com pedidos e seeds pareados, embora apenas 1 de 10 pares C/D tenha tido resposta inicial
   idêntica), o E4 (único desenho em que todas as condições partem exatamente do mesmo plano,
   conferido por hash) e uma nova rodada do E11 com o código final —, tratando os demais como estudos
   de desenvolvimento.
3. **Executar o modo GBNF** pelo menos em um pequeno lote, porque a decodificação restrita por GLC é o
   elo teórico mais citado do trabalho.
4. **Aplicar a avaliação humana mínima** (seção 2.1), mesmo que com poucos avaliadores.
5. **Mostrar os fracassos** na apresentação: o 0/5 do E1, o `before_01` aprovado sem diagnóstico, os
   títulos truncados e o fato distorcido do E11. Eles são a melhor evidência de que validade formal e
   qualidade são coisas diferentes, e de que o projeto mediu isso com honestidade.
6. **Preservar os artefatos**: como `outputs/` não é versionado, exportar um pacote dos dados
   brutos dos experimentos citados (com hashes) para um repositório de dados ou anexo do TCC.
7. **Conferir as referências** na versão publicada (anais e paginação) antes do depósito.
