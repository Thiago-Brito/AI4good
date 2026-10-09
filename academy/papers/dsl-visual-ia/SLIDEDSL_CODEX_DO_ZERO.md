# SlideDSL — ESPECIFICAÇÃO EXECUTÁVEL PARA CODEX (PROJETO DO ZERO)

> **Status:** contrato de implementação v1.0, Windows.  
> **Destinatário:** agente de programação Codex.  
> **Comando principal:** implemente o sistema inteiro deste documento, em um **repositório novo e vazio**, sem reaproveitar protótipos anteriores, sem entregar apenas scaffolding, pseudocódigo ou um plano.  
> **Idioma:** documentação, mensagens da CLI, exemplos, interface e DSL em português; nomes técnicos de classes e bibliotecas podem ser em inglês.  
> **Regra de execução:** crie código, testes, exemplos e documentação, rode o que estiver disponível e registre com transparência o que foi realmente executado. **Nunca invente resultados ou alegue que executou testes externos sem credenciais/modelos.**

## 0. O que construir

**Objetivo acadêmico:** projetar, implementar e avaliar uma **linguagem específica de domínio (SlideDSL)** definida por uma **Gramática Livre de Contexto (GLC)** para **criação, edição lógica e validação espacial de apresentações**. Sua sintaxe será um **português controlado** (não português irrestrito). Um modelo de linguagem pequeno rodando localmente deverá traduzir solicitações em linguagem natural em programas SlideDSL; um compilador independente da IA converterá esses programas para slides editáveis de PowerPoint.

**Pergunta de pesquisa:** até que ponto a GLC, a representação intermediária e o verificador determinístico de princípios de design aumentam a validade estrutural e a qualidade espacial de slides gerados por modelos de diferentes capacidades?

**Entregáveis obrigatórios:**

1. Repositório executável em Windows, com ambiente reprodutível.
2. Pesquisa documentada de **Canva (REST/CLI/SDK/MCP), PowerPoint (PptxGenJS e automação nativa) e Google Slides API**: operações suportadas, limitações, autenticação, tipo de edição e evidência/links oficiais.
3. Definição formal da **SlideDSL v1.0**, catálogo de comandos, gramática Lark, exemplos válidos e inválidos, AST tipada e representação intermediária (IR) JSON.
4. Parser, analisador semântico, resolvedor geométrico, verificador de princípios de design e gerador de diagnósticos.
5. Compilador **IR -> PptxGenJS -> `.pptx`**, preservando texto e formas editáveis.
6. CLI em Python para validar, compilar, gerar via SLM e inspecionar relatórios.
7. Integração Ollama com **Qwen3 0.6B e Qwen3 4B**; integração OpenAI com **GPT-4.1 mini e GPT-4.1** somente quando houver chave/conta, sem impedir demais funcionalidades.
8. Benchmark reproduzível com **um mesmo pedido de apresentação de 5 slides** (simples e complexos), 5 repetições por modelo disponível, registros de saídas originais, validação, métricas e relatório.
9. Editor visual mínimo (React Flow), capaz de **abrir, editar, validar e exportar** programas da linguagem via estrutura intermediária, com preview geométrico 2D.
10. Uma apresentação demonstrativa de 5 slides criada inteiramente a partir de um programa `.sld`; documentação para defesa perante o professor.

### Definição do sucesso

O comando `slidedsl compile examples/cinco_slides.sld --out output/apresentacao.pptx` deve criar **cinco slides editáveis**, incluindo um com camadas/oclusão controlada. O comando `slidedsl validate` precisa mostrar diagnósticos precisos. O benchmark deve conseguir testar os modelos disponíveis sem necessidade de alterar o código. O editor visual deve abrir o mesmo documento e manter equivalência semântica após salvar.

---

## 1. Decisões fechadas — não trocar sem justificativa documentada

| Camada | Stack | Papel |
|---|---|---|
| Sistema | Windows 10/11 + PowerShell | ambiente primário |
| Runtime principal | Python 3.12 | CLI, parser, semântica, geometria, IA, benchmark |
| GLC | Lark (gramática em `.lark`, parser LALR) | análise sintática |
| Tipagem de dados | dataclasses ou Pydantic | AST/IR; escolha uma e documente |
| Backend slides | Node.js 24 + `pptxgenjs` | criar `.pptx` editável |
| Editor visual | React + Vite + TypeScript + `@xyflow/react` | nós, portas, relações e inspeção |
| API local | FastAPI (Python) | parser/compilação para editor |
| IA local | Ollama | Qwen3 0.6B e 4B |
| IA remota | API OpenAI, opcional | GPT-4.1 mini e GPT-4.1 |
| Testes | pytest + testes de integração Node | evidência automatizada |
| Dados | JSON, JSONL e CSV | rastreabilidade dos experimentos |
| Formato slide | widescreen 16:9 (1280 × 720 unidades lógicas) | geometria independente da ferramenta |

**Política de escopo:** apenas um compilador completo na v1: **PptxGenJS**. Não bloquear o projeto tentando escrever adaptadores completos para Canva/Google Slides. Entretanto, produzir **matriz de compatibilidade e desenho de adaptadores** para ambos. Se sobrar tempo depois de todos os critérios obrigatórios, criar um protótipo independente de Google Slides (sem tornar credenciais Google requisito).

**Por que não Canva primeiro:** o Canva possui canais distintos (CLI/REST, SDK dentro de apps, conectores MCP) com permissões e limites diferentes; **não assumir que existe um comando genérico** equivalente a `canva run add img x13,4 ...`. Registrar operações apenas após consultar documentação atual. A linguagem será independente desses canais.

**Importante sobre PptxGenJS:** ele será usado para **gerar apresentações novas a partir da IR**, não para prometer editar diretamente um `.pptx` existente. Os comandos `remover`, `mover`, `redimensionar` e `trazer para frente` alterarão a **cena interna antes de gerar novamente o arquivo**, e não o PPTX já gravado.

---

## 2. Arquitetura obrigatória e contratos entre camadas

```text
Solicitação humana
   │
   ├───────────────► (opcional) Adaptador SLM/LLM
   │                             └── texto SlideDSL
   ▼
Arquivo .sld em português controlado
   │
   ▼
Lark Parser (GLC)
   │  [erro de sintaxe com linha/coluna]
   ▼
AST tipada
   │
   ▼
Análise semântica
   │  [IDs, tipos, escopo, referências, argumentos]
   ▼
IR: Presentation -> Slides -> Elements
   │
   ├── Resolvedor geométrico [coordenadas / relações]
   ├── Validador de design [contraste / proximidade / alinhamento / etc.]
   ├── Serializer JSON versionado
   └── Backend PptxGenJS (Node por subprocesso seguro)
          ▼
     arquivo PPTX editável

Editor React Flow ◄─► API Python ◄─► AST/IR/DSL
Benchmark ───────► todos os modelos ───► mesma cadeia de validação
```

**Regras de separação:**
- **GLC** define a estrutura sintática válida, não julgamento estético nem tamanho dos textos.
- **Análise semântica** detecta IDs duplicados, referência a objeto inexistente, comandos fora de contexto, propriedades incompatíveis e dimensão não positiva.
- **Verificador espacial** calcula coordenadas concretas; sua saída é determinística e testável, sem consultar IA.
- **Validador de design** verifica regras quantitativas e emite `ERRO`, `AVISO` ou `INFORMAÇÃO`, nunca atribui “beleza” absoluta.
- **Backend** apenas converte a IR validada para operações de slide: não faz interpretação de linguagem natural.
- **IA** só produz texto `.sld` e, se solicitado, tenta corrigir os diagnósticos; não executa JavaScript arbitrário.
- **Editor visual** altera os mesmos nós/elementos do domínio; não cria um formato incompatível.

### 2.1 Esquema IR versionado (mínimo)

```json
{
  "schema_version": "1.0",
  "title": "Apresentação exemplo",
  "theme": "claro",
  "canvas": { "width": 1280, "height": 720, "unit": "px_logico" },
  "slides": [
    {
      "number": 1,
      "elements": [
        { "id": "titulo", "type": "text", "text": "Olá", "x": 80, "y": 80,
          "width": 800, "height": 100, "font_size": 46, "color": "#15253B",
          "z": 0, "source_line": 5 }
      ]
    }
  ]
}
```

Preservar **ID**, número do slide, tipo de objeto, origem em linha/coluna, geometria, ordem Z e propriedades. Versão estável e JSON Schema (documentar). IDs são **únicos dentro do slide**, não globalmente. A numeração de slides inicia em **1**.

---

## 3. A linguagem SlideDSL v1.0 (núcleo da pesquisa)

### 3.1 Princípios de modelagem

1. **Português controlado**: comandos legíveis, vocabulário finito, sem ambiguidade sintática. Português natural livre é responsabilidade da IA.
2. **Operações explícitas**: `adicionar`, `remover`, `mover`, `redimensionar`, `mudar cor`, `trazer para frente`, `enviar para tras`, `alinhar`.
3. **Referências por ID**: jamais selecionar “o terceiro retângulo vermelho” na v1.
4. **Geometria declarativa**: posições absolutas ou relações (`abaixo de`, `a direita de`, `canto superior direito`).
5. **Integridade**: todos os comandos afetam um estado de cena determinístico.
6. **Confiabilidade**: qualquer operação impossível retorna diagnóstico, jamais resulta em silêncio.
7. **Portabilidade**: comandos representam intenção; o backend se encarrega da API concreta.

### 3.2 Comandos v1 obrigatórios

| Comando | Sintaxe resumida | Efeito na IR |
|---|---|---|
| Criar apresentação | `apresentacao "..." { ... }` | cria documento |
| Definir tema | `tema claro` / `tema escuro` | inicializa padrões visuais |
| Criar slide | `slide 1 { ... }` | cria página |
| Adicionar retângulo | `adicionar retangulo id caixa em (...) tamanho (...) cor #...` | elemento shape |
| Adicionar elipse | idem | elemento shape |
| Adicionar texto | `adicionar texto id t "..." em (...) tamanho (...) fonte 40 cor #...` | elemento editável |
| Adicionar imagem | `adicionar imagem id foto arquivo "assets/foto.png" em (...) tamanho (...)` | objeto imagem |
| Remover elemento | `remover caixa` | exclui da cena |
| Mover | `mover caixa para (...)` | atualiza coordenadas |
| Redimensionar | `redimensionar caixa para (500, 200)` | atualiza dimensões |
| Mudar cor | `mudar cor de caixa para #FFAA00` | altera fill ou cor de texto |
| Trazer à frente | `trazer caixa para frente` | move elemento para o maior Z |
| Enviar para trás | `enviar caixa para tras` | move elemento para o menor Z |
| Alinhar | `alinhar caixa com titulo pela esquerda` | iguala `x` |

**Valores e semântica:**
- Cor: formato hexadecimal `#RRGGBB`, sem transparência na v1.
- Posição `(x, y)`: origem `(0,0)` no **canto superior esquerdo**; `x` cresce para direita, `y` para baixo.
- Dimensão `(largura, altura)` em unidades lógicas numéricas; > 0.
- Fonte em **pontos**, 10 a 96 (intervalo validado semanticamente).
- Coordenadas podem ser inteiras ou decimais com ponto (`18.5`); sem vírgula decimal.
- Strings entre aspas duplas com escape padrão (`\"` e `\\`).
- Caminhos de imagens **relativos à raiz do projeto**; apenas PNG/JPG/JPEG locais; não buscar URLs arbitrárias.
- Por padrão, elemento adicionado por último fica por cima; instruções de camada ajustam essa ordem.
- `canto superior direito`: posicionar em `x = 1280 - 64 - largura`, `y = 64`.
- `abaixo de ID com margem M`: `x = x_ref`; `y = y_ref + h_ref + M`.
- `a direita de ID com margem M`: `x = x_ref + w_ref + M`; `y = y_ref`.
- Referência relativa deve apontar para elemento já existente e não removido no **mesmo slide**.
- `alinhar ... pela esquerda` exige ambos existentes no mesmo slide e equivale a `x_dest = x_ref`.
- Na v1 `slide N` deve aparecer em ordem contínua `1..N`; comandos operam no escopo do slide.

### 3.3 Gramática inicial operacional — salvar em `src/slidedsl/grammar/slidedsl.lark`

Esta gramática é um **contrato inicial**; executar o parser e fazer eventuais correções **sintáticas mínimas** necessárias, registrando-as. Não alterar o vocabulário deliberadamente sem atualizar exemplos, testes e documentação.

```lark
start: apresentacao
apresentacao: "apresentacao" STRING "{" tema slide+ "}"
tema: "tema" ("claro" | "escuro")
slide: "slide" INT "{" instrucao+ "}"

?instrucao: adicionar_retangulo
          | adicionar_elipse
          | adicionar_texto
          | adicionar_imagem
          | remover
          | mover
          | redimensionar
          | mudar_cor
          | trazer_frente
          | enviar_tras
          | alinhar

adicionar_retangulo: "adicionar" "retangulo" "id" ID "em" posicao "tamanho" dimensao "cor" COR
adicionar_elipse: "adicionar" "elipse" "id" ID "em" posicao "tamanho" dimensao "cor" COR
adicionar_texto: "adicionar" "texto" "id" ID STRING "em" posicao "tamanho" dimensao "fonte" INT "cor" COR
adicionar_imagem: "adicionar" "imagem" "id" ID "arquivo" STRING "em" posicao "tamanho" dimensao

remover: "remover" ID
mover: "mover" ID "para" posicao
redimensionar: "redimensionar" ID "para" dimensao
mudar_cor: "mudar" "cor" "de" ID "para" COR
trazer_frente: "trazer" ID "para" "frente"
enviar_tras: "enviar" ID "para" "tras"
alinhar: "alinhar" ID "com" ID "pela" "esquerda"

?posicao: ponto
        | "canto" "superior" "direito"   -> canto_superior_direito
        | "abaixo" "de" ID "com" "margem" NUMERO -> abaixo_de
        | "a" "direita" "de" ID "com" "margem" NUMERO -> a_direita_de

ponto: "(" NUMERO "," NUMERO ")"
dimensao: "(" NUMERO "," NUMERO ")"

ID: /[a-zA-Z_][a-zA-Z0-9_]*/
COR: /#[0-9A-Fa-f]{6}/
NUMERO: /-?[0-9]+(\.[0-9]+)?/
%import common.ESCAPED_STRING -> STRING
%import common.INT
%import common.WS
%ignore WS
```

### 3.4 Exemplo v1 válido (deve compilar)

```text
apresentacao "Exemplo da SlideDSL" {
  tema claro
  slide 1 {
    adicionar retangulo id fundo em (0, 0) tamanho (1280, 720) cor #F6F8FC
    adicionar texto id titulo "Introdução à SlideDSL" em (80, 95) tamanho (1040, 100) fonte 52 cor #14233D
    adicionar texto id subtitulo "Uma GLC para apresentações" em abaixo de titulo com margem 24 tamanho (1000, 70) fonte 28 cor #334765
    enviar fundo para tras
  }
  slide 2 {
    adicionar retangulo id cartao em (80, 130) tamanho (520, 300) cor #DDE8F9
    adicionar texto id titulo "Alinhamento" em (80, 50) tamanho (850, 70) fonte 42 cor #14233D
    adicionar texto id explicacao "Objetos relacionados compartilham eixos." em abaixo de titulo com margem 20 tamanho (500, 120) fonte 25 cor #14233D
    alinhar cartao com titulo pela esquerda
  }
}
```

### 3.5 Casos negativos obrigatórios

- `adicionar triangulo ...` -> **sintaxe inválida** (tipo não suportado).
- `remover desconhecido` -> **erro semântico: ID não existe**.
- `adicionar retangulo id a ...; adicionar texto id a ...` -> **ID duplicado no mesmo slide**.
- `tamanho (-50,100)` -> **dimensão inválida**.
- `abaixo de futuro` antes de `futuro` existir -> **referência não resolvida**.
- `slide 1; slide 3` -> **ordem inválida**.
- Imagem sem arquivo existente -> **erro de asset com caminho e linha**.
- Texto muito grande em caixa pequena -> **aviso de possível overflow**, não acusar certeza sem mecanismo de medição real.

### 3.6 Extensões v1.1 após núcleo validado (obrigatórias no projeto completo)

Após concluir a gramática e testes acima, ampliar para:

- `agrupar [id1, id2, ...] como grupo_id` e `desagrupar grupo_id` na **IR** (não prometer grupo PowerPoint nativo; agrupar no estado e aplicar mover/redimensionar ao conjunto segundo regra documentada).
- `alinhar id1 com id2 pelo centro horizontal`, `pela direita`, `pelo topo`.
- `distribuir horizontalmente [id1, id2, id3] com intervalo 24` (ao menos 3 objetos).
- `definir camada de ID como N` (Z numérico), com normalização determinística.
- Cores e fontes por **tokens de tema** (`cor primaria`, `cor texto`, etc.), mantendo cor literal.
- Blocos de layout `grupo "Comparação" { ... }` se viáveis sem ambiguidade, com teste de parse.
- Atualizar todos os exemplos, IR/JSON Schema, validações e benchmark ao ampliar.

**Proibição:** não afirmar que uma extensão está implementada por constar do README; ela precisa de parser, semântica, compilação e testes.

---

## 4. Princípios de design como regras verificáveis

A fundamentação usa **contraste, repetição, alinhamento e proximidade (CRAP)**, mais hierarquia e uso de espaço em branco. Distinguir verificação automatizada de avaliação estética humana.

| ID | Princípio | Regra automática v1 | Severidade inicial |
|---|---|---|---|
| D001 | Limites/área útil | elemento sai da tela 1280×720 | ERRO |
| D002 | Contraste | texto com fundo conhecido apresenta relação de contraste < 4.5:1 | AVISO |
| D003 | Repetição | mesmo papel de título usa fontes/tamanhos/cores divergentes do tema | AVISO |
| D004 | Alinhamento | elementos com intenção de alinhamento declarada não compartilham eixo, tolerância 2 px | ERRO |
| D005 | Proximidade | integrantes do mesmo grupo ficam muito distantes (> 120 px entre caixas, limite configurável) | AVISO |
| D006 | Hierarquia | título com fonte menor que corpo conhecido do mesmo slide | AVISO |
| D007 | Espaço em branco | densidade de ocupação visível acima de 80% | AVISO |
| D008 | Oclusão | elemento relevante > 20% encoberto por objeto acima | AVISO |
| D009 | Dimensões | largura ou altura <= 0 | ERRO |
| D010 | Texto | estimativa de overflow com métrica aproximada (considerar margem, fonte e linhas) | AVISO |

**Implementação detalhada:**
- Geometria por caixas retangulares com interseção de áreas; inicialmente ignorar máscara irregular de elipse ou imagem.
- Para D008 considerar **Z** e a área de interseção do objeto de baixo com objetos de cima. Não somar sobreposições duas vezes: calcular união ou usar aproximação declarada/testada; não tratar overlap intencional fundo+texto como falha automática — marcar elementos de fundo/decorativos ou reconhecer retângulo cobrindo tela no papel background.
- Para D002 implementar luminância relativa sRGB e relação de contraste WCAG. Quando o fundo real não é conhecido ou contém imagem, retornar `INDETERMINADO`, não `PASSOU`.
- D003 requer papéis (`titulo`, `corpo`, `decoracao`) derivados de uma anotação opcional ou heurística; registrar origem da decisão. Um elemento sem papel não gera falsa violação.
- D004 é exigência de alinhamento explícito ou relação armazenada na IR.
- D007 reportar a **fração aproximada** de cobertura, declarando que não mede qualidade estética.
- Regras configuráveis em `config/design_rules.yaml`; `--strict` converte avisos selecionados em falha de execução, sem mudar a GLC.
- Emitir relatório legível `output/validation.json`, com código, severidade, slide, elemento, coordenada, mensagem e proposta de correção.

**Testes específicos obrigatórios:** contraste preto/branco e texto claro em branco, retângulo totalmente fora do slide, dois objetos com interseção parcial, objeto escondido atrás de retângulo, operação `trazer` corrigindo ordem, grupo visual disperso, alinhamento bem-sucedido e com desvio > 2 px.

---

## 5. Compilação real para PowerPoint editável

1. Ler `.sld`, gerar AST, validar semântica e materializar IR com operações aplicadas na ordem textual.
2. Determinar geometria absoluta de cada elemento e sequência Z definitiva.
3. Gerar JSON intermediário em arquivo temporário dentro de `output/tmp/`.
4. Executar subprocesso Node com script `renderer/render.mjs`, **sem `shell=True`**, passando caminhos como argumentos; sanitizar diretório de saída.
5. Em PptxGenJS configurar widescreen, converter posições de px lógico para polegadas usando **96 unidades por polegada** (`x_in = x/96`) e manter `font_size` em pontos.
6. Para cada slide, adicionar elementos de acordo com ordem Z usando `addText`, `addShape`, `addImage`.
7. Criar arquivo `.pptx` editável; **não** rasterizar slide inteiro como imagem.
8. Inspecionar o ZIP do PPTX em testes: número de slides e tipos de elementos (XML ou `python-pptx` para inspecionar).
9. Se PowerPoint estiver instalado, oferecer `render-preview` via automação COM **opcional**; sem PowerPoint o build deve funcionar e os testes de conteúdo do PPTX devem passar.
10. Não gerar JavaScript diretamente da resposta do modelo: só JSON já validado.

### Contrato de camada

Exemplo: `trazer caixa para frente` reposiciona o objeto no fim da lista de desenho daquele slide (maior Z); `remover caixa` exclui da IR antes de chamar o backend. Registrar esta decisão no `docs/SEMANTICA.md`.

---

## 6. Editor visual (parte essencial para o TCC)

Criar `editor/` com React + Vite + TypeScript + React Flow e `api/` com FastAPI. O editor não deve ser apenas um mockup.

**Funcionalidades mínimas, todas obrigatórias:**
- Abrir um arquivo `.sld` via API e mostrar slide atual + lista de slides.
- Exibir um **grafo**: nó apresentação, nós slide, nós de elementos (texto, forma, imagem) e conexões hierárquicas e relacionais (por exemplo, `abaixo de`).
- Portas tipadas: `contém_slide`, `contém_elemento`, `referência_espacial`. Bloquear conexão de tipo incompatível.
- Painel de propriedades para alterar ID, texto, cor, x, y, largura, altura, fonte, Z, tipo de relação.
- **Preview 2D** do slide com retângulos, textos e imagens nas posições da IR; permitir selecionar objetos pelo ID.
- Botão **Validar** chama API, exibe diagnósticos na tela e destaca objeto/slide envolvidos.
- Botão **Exportar DSL** gera código `.sld` a partir do estado visual (serializer determinístico).
- Botão **Gerar PPTX** chama compilador e disponibiliza arquivo local.
- Importar DSL -> visualizar -> exportar DSL -> recompilar deve preservar IR equivalente (ignorar diferenças de whitespace e ordenação de propriedades não semânticas).

**Não incluir** colaboração multiusuário, drag-and-drop avançado em canvas (pode existir, mas não obrigatório), Canva nativo, animação ou editor WYSIWYG completo. O objetivo é uma DSL visual mínima e funcional, compartilhando IR com a DSL textual.

---

## 7. Integração IA e prompting

### 7.1 Adaptadores

Contrato Python:

```python
class TextModel(Protocol):
    def generate(self, system_prompt: str, user_prompt: str, *, temperature: float, seed: int | None) -> str: ...
```

Implementar `OllamaTextModel` (endpoint local configurável) e `OpenAITextModel` (chave via variável de ambiente `OPENAI_API_KEY`), com timeout, tratamento de falhas e logs. **Não colocar chave em repositório, JSONL ou prompt.**

### 7.2 Modelos do benchmark

- **Local fraco:** `qwen3:0.6b`
- **Local mais capaz:** `qwen3:4b`
- **GPT menor:** `gpt-4.1-mini` (quando houver acesso)
- **GPT mais capaz:** `gpt-4.1` (quando houver acesso)

Fixar os IDs acima em `config/models.yaml`, com possibilidade de substituição explícita/registrada se não estiverem disponíveis. Não afirmar que todo modelo remoto está habilitado; a suíte local funciona sem credenciais.

### 7.3 Prompt do gerador de DSL

Criar um único `prompts/system_dsl.txt` versionado contendo:
- contrato: saída **somente** um programa `.sld`, sem Markdown, sem explicações;
- gramática v1 suportada e 2 exemplos curtos válidos;
- coordenadas 1280×720, margens 64, tema escolhido, limite de 5 slides;
- regras de conteúdo e design em linguagem objetiva;
- caminhos válidos das imagens de `assets/`;
- proibição de criar comandos inexistentes.

Para comparar modelos, **não personalizar o prompt por modelo**. Salvar exatamente os bytes do prompt, configurações (temperatura 0 ou mínimo permitido, `seed` se suportado), versão do modelo, runtime e hora de execução. Se um provedor não permitir parâmetro, registrar em vez de simular equivalência.

### 7.4 Reparo controlado

Duas condições experimentais:

- **SEM_REPARO**: uma geração por pedido, validar e reportar os erros.
- **COM_REPARO**: após a primeira geração, permitir no máximo **duas rodadas** adicionais com lista dos erros de parser/semântica; manter as respostas e resultados de cada rodada. Não corrigir no código por heurística escondida.

Não misturar resultados da primeira tentativa com resultados após reparo.

---

## 8. Benchmark reproduzível — exigência do professor

### 8.1 Tarefa principal fixa: uma apresentação de **EXATAMENTE 5 slides**

Arquivo `benchmark/prompts/tarefa_cinco_slides.txt` com o seguinte pedido literal (não adaptar por modelo):

> Crie uma apresentação chamada "Princípios de Design de Slides" com EXATAMENTE cinco slides, em tema claro e proporção 16:9. Slide 1: capa com título e subtítulo centralizados visualmente. Slide 2: explique contraste usando dois exemplos textuais e duas formas coloridas, com alinhamento à esquerda. Slide 3: explique proximidade com dois grupos de informações visualmente separados. Slide 4: explique camadas criando um retângulo e uma imagem local sobrepostos intencionalmente; a imagem deve ficar inicialmente por trás do retângulo e depois ser trazida para frente; o resultado final deve mostrar a imagem parcialmente por cima do retângulo. Slide 5: comparação complexa em duas colunas, com três vantagens, três limitações e um rodapé. Preserve margens, não deixe elementos fora do slide, use IDs únicos e apenas operações da SlideDSL. Utilize `assets/imagem_demo.png` na demonstração de camadas.

**Preparar `assets/imagem_demo.png` no repositório** com imagem geométrica original ou material de licença livre documentada. Sem depender de download online durante testes. Criar um **gabarito estrutural** do mesmo deck em `examples/cinco_slides.sld`, escrito manualmente e validado: ele será a referência do compilador, não resultado de modelo.

### 8.2 Execução do experimento

- No mínimo **5 repetições por modelo disponível** na tarefa fixa; guardar resultado de cada tentativa.
- Toda tentativa recebe exatamente o mesmo pedido e `system_dsl.txt` dentro da mesma condição.
- **Sem edição manual** das saídas do modelo para melhorar pontuação.
- Medir antes de qualquer reparo e depois separadamente, se aplicável.
- Em cada tentativa produzir: raw output, parser log, AST/IR quando válidas, JSON de diagnósticos, `.pptx` se compilar, duração e métricas.
- Ao executar diferentes modelos, se um estiver ausente/desabilitado, registrar `NAO_EXECUTADO`, motivo e passos para ativar; **não fabricar comparativo numérico**.

### 8.3 Métricas objetivas

1. `parse_success` — saída é aceita integralmente pela GLC?
2. `semantic_success` — IDs/referências/tipos/comandos corretos?
3. `compile_success` — gerou PPTX com 5 slides editáveis?
4. `instruction_coverage` — quantos requisitos do prompt foram satisfeitos, dentre checklist rubricado?
5. `design_errors` e `design_warnings` — contagens por código D001–D010.
6. `layer_correctness` — imagem do slide 4 está acima do retângulo **na IR final** e tem interseção espacial intencional?
7. `duration_ms` — duração total da geração, separada da compilação.
8. `repair_rounds`, `success_after_repair` — sob condição COM_REPARO.

**Rubrica:** criar `benchmark/rubric.yaml` com 5 slides obrigatórios e itens específicos por slide. Publicar numerador/denominador; não inventar “nota de beleza” automática.

### 8.4 Experimento de ablação (além de comparar modelos)

Para o mesmo modelo, comparar três configurações:

- **A:** geração de comandos da SlideDSL com GLC + semântica, sem aplicar avisos de design.
- **B:** igual A com verificador de design, apenas observação (nenhuma correção).
- **C:** igual B com até 2 reparos guiados pelos diagnósticos.

A comparação A/B isola medição versus correção; **não afirmar que executar apenas o verificador melhora a geração**, pois ele só mede. A comparação B/C estima benefício do feedback. Se houver interesse adicional, registrar baseline sem DSL como outro experimento separado com contrato/output diferente, **sem alegar que o prompt técnico é idêntico**.

### 8.5 Relatório

Gerar `reports/benchmark.csv`, `reports/benchmark.json`, `reports/ANALISE.md` com tabela por modelo e condição, média/taxa por 5 repetições (quando realizadas), amostras de erros e limitações. Incluir `reports/RESULTADOS_PENDENTES.md` se não houver Ollama instalado/chave para OpenAI. Não preencher relatórios com medições fictícias.

---

## 9. Pesquisa documentada de API/SDK/CLI/MCP (obrigatória, mas não bloqueante)

Produzir `docs/PESQUISA_FERRAMENTAS.md` e `docs/MATRIZ_CAPACIDADES.csv`. Investigar a documentação oficial atual no ambiente em que Codex puder acessar web.

### Canais a separar rigorosamente

**Canva:**
- CLI / `canva api`: criar/listar/exportar designs, operações REST disponíveis mediante autenticação e limitações.
- Apps SDK / Design Editing API: inserir/ler/atualizar/remover tipos suportados **dentro de app Canva**; requisitos do ambiente e permissões.
- MCP/AI Connector: ferramentas e capacidades específicas; não confundir com CLI genérico.

**PowerPoint:**
- PptxGenJS: gerar arquivo novo, formas, imagens, textos, dimensões, z-order por sequência de adição; limites de edição de arquivos existentes.
- PowerPoint COM no Windows: dependência de instalação do aplicativo e automação, vantagens e limitações.
- Microsoft Graph/Office.js: avaliar viabilidade, sem assumir API de edição irrestrita.

**Google Slides:**
- Slides API: `presentations.create`, `batchUpdate` para slides/elementos, formas, imagens, texto, transformações, exclusão e controle de ordem; OAuth, cota e disponibilidade offline.

### Matriz obrigatória por operação

Linhas: criar apresentação, adicionar/remover slide, adicionar/remover texto, adicionar/remover forma, inserir imagem, mover, redimensionar, trocar cor, alinhar, agrupar, camadas, exportar PPTX, editar documento existente, execução offline.  
Colunas: PptxGenJS, PowerPoint COM, Canva CLI/REST, Canva Apps SDK, Canva MCP, Google Slides API.

Cada célula: `SIM`, `PARCIAL`, `NÃO` ou `NÃO CONFIRMADO`, **evidência com URL e data**. `SIM` exige referência a função/operação específica. Quando possível realizar smoke test autenticado; caso contrário marcar `NAO_TESTADO` e distinguir **documentado** de **verificado na prática**.

**Referências de partida:**
- https://github.com/lsfcin/spacemantics
- https://github.com/lsfcin/spacemantics/tree/main/dsl
- https://www.canva.dev/docs/apps/design-editing/
- https://www.canva.dev/docs/apps/canva-cli/making-rest-api-requests/
- https://developers.google.com/workspace/slides/api/guides/overview
- https://gitbrent.github.io/PptxGenJS/
- https://docs.ollama.com/

### Referência Texpace / Spacemantics

Ler estrutura `dsl/`, `checker/`, `bench/`, `tests/` do repositório Spacemantics, caso esteja acessível. Produzir `docs/ANALISE_TEXPACE.md` contendo: quais conceitos espaciais seriam úteis para slides (`left of`, `below`, `occludes`, `z-order`), o que será adaptado e o que ficará fora (3D, 4D, tempo). **Não copiar** gramática ou código sem registrar licença, origem e justificativa. Aplicar a ideia de separar uma DSL declarativa, verificador determinístico e benchmark, mantendo trabalho próprio.

---

## 10. Organização do projeto (criar tudo a partir de pasta vazia)

```text
slidedsl/
├── README.md
├── AGENTS.md
├── pyproject.toml
├── .env.example
├── .gitignore
├── package.json                   # se necessário na raiz; caso contrário documentar npm em renderer/
├── config/
│   ├── design_rules.yaml
│   ├── models.yaml
│   └── themes.yaml
├── src/slidedsl/
│   ├── __init__.py
│   ├── cli.py
│   ├── grammar/slidedsl.lark
│   ├── parser.py
│   ├── ast_nodes.py
│   ├── semantic.py
│   ├── ir.py
│   ├── serializer.py
│   ├── geometry.py
│   ├── design_rules.py
│   ├── diagnostics.py
│   ├── compiler.py
│   ├── models/base.py
│   ├── models/ollama_model.py
│   └── models/openai_model.py
├── renderer/
│   ├── package.json
│   └── render.mjs
├── api/
│   └── main.py
├── editor/
│   ├── package.json
│   └── src/ ...
├── assets/
│   └── imagem_demo.png
├── examples/
│   ├── cinco_slides.sld
│   ├── operacoes.sld
│   ├── negativo_id_duplicado.sld
│   └── negativo_oclusao.sld
├── prompts/
│   └── system_dsl.txt
├── benchmark/
│   ├── run.py
│   ├── rubric.yaml
│   └── prompts/tarefa_cinco_slides.txt
├── tests/
│   ├── test_grammar.py
│   ├── test_semantic.py
│   ├── test_geometry.py
│   ├── test_design.py
│   ├── test_ir_roundtrip.py
│   ├── test_compile_pptx.py
│   ├── test_cli.py
│   └── test_benchmark_mock.py
├── docs/
│   ├── GRAMATICA.md
│   ├── SEMANTICA.md
│   ├── METAMODELO.md
│   ├── REGRAS_DESIGN.md
│   ├── PESQUISA_FERRAMENTAS.md
│   ├── MATRIZ_CAPACIDADES.csv
│   ├── ANALISE_TEXPACE.md
│   ├── EXPERIMENTO.md
│   └── DEFESA_PROFESSOR.md
├── reports/
└── output/                        # artefatos gerados; ignorar em git se grandes
```

O nome do pacote CLI será `slidedsl`, instalado de forma editável via `pip install -e .`.

---

## 11. Interface de linha de comando — contratos exatos

Implementar estes comandos; usar `argparse` ou `typer`, com `--help`, códigos de saída consistentes e mensagens amigáveis.

```powershell
slidedsl validate examples/cinco_slides.sld
slidedsl validate examples/cinco_slides.sld --strict --json output/validation.json
slidedsl ast examples/cinco_slides.sld --out output/ast.json
slidedsl ir examples/cinco_slides.sld --out output/deck.json
slidedsl compile examples/cinco_slides.sld --out output/deck.pptx
slidedsl generate --provider ollama --model qwen3:4b --prompt-file benchmark/prompts/tarefa_cinco_slides.txt --out output/llm_deck.sld
slidedsl benchmark --models qwen3:0.6b,qwen3:4b --repetitions 5 --out reports/
slidedsl serve --host 127.0.0.1 --port 8000
```

**Saídas:** `validate` falha código 1 se erro sintático/semântico; `compile` falha antes de criar arquivo se validação básica falhar; `generate` salva a saída crua do modelo além do `.sld`, não faz overwrite silencioso; `benchmark` gera relatórios de estado mesmo com modelos ausentes.

---

## 12. Preparação e execução no Windows

Requisitos: Python 3.12, Node.js 24/npm, Git. Ollama apenas para rodar os modelos locais. PowerPoint não é obrigatório para geração `.pptx`.

```powershell
# a partir da raiz do repositório
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"

cd renderer
npm install
cd ..

pytest -q
slidedsl validate examples/cinco_slides.sld
slidedsl compile examples/cinco_slides.sld --out output/deck.pptx

# opcional, quando houver Ollama local
ollama pull qwen3:0.6b
ollama pull qwen3:4b
slidedsl benchmark --models qwen3:0.6b,qwen3:4b --repetitions 5 --out reports/

# editor visual (terminal separado)
cd editor
npm install
npm run dev
```

Se política do PowerShell bloquear ativação, documentar execução usando `.venv\Scripts\python.exe` sem mudar política global. Fornecer scripts `scripts/setup_windows.ps1`, `scripts/test_windows.ps1`, `scripts/demo_windows.ps1`, tratando caminhos com espaços.

---

## 13. Etapas de construção — ordem obrigatória e aceite

### FASE 0 — Bootstrap e pesquisa (não é entrega isolada)
- Criar repositório novo, estrutura, ambiente, `.gitignore`, dependências com versões fixadas, `README` inicial.
- Investigar APIs e Texpace; preencher matriz com evidências oficiais.
- **Aceite:** projeto instala em Windows e docs distinguem capacidades verificadas e não verificadas.

### FASE 1 — GLC/AST
- Implementar gramática Lark, AST, printer, erros com localização.
- Criar testes para **todos os comandos** e negativos descritos.
- **Aceite:** parser aceita exemplos válidos e rejeita inválidos; `slidedsl ast` funciona.

### FASE 2 — Semântica/IR/geometria
- Resolver IDs, tipos, referência relativa, ações e ordem Z; gerar IR versionada e JSON Schema.
- Escrever documentação de cada regra matemática e seus testes.
- **Aceite:** remover/mover/redimensionar/alinhar/camadas alteram a IR exatamente como especificado; determinismo no roundtrip.

### FASE 3 — Princípios de design
- Implementar D001–D010, configuração, mensagens diagnósticas, tolerâncias e testes positivos/negativos.
- **Aceite:** detector distingue oclusão verdadeira de fundo decorativo; diagnósticos com evidência geométrica e linha quando houver.

### FASE 4 — Backend PowerPoint
- Criar renderer PptxGenJS consumindo somente IR validada.
- Criar deck gabarito de 5 slides e conferir contagem/editabilidade por inspeção do PPTX.
- **Aceite:** deck real `.pptx`, cinco slides e elementos editáveis; slideshow 4 respeita camada final.

### FASE 5 — IA local/remota
- Adapters, prompts, logs e reparo controlado; smoke test com provedor mock para não exigir rede.
- **Aceite:** `generate` funciona com mock; Ollama funciona se estiver instalado; remotos pulados claramente quando não configurados.

### FASE 6 — Benchmark
- Harness, 5 repetições, experimento ablação, logs e relatório reproduzível.
- **Aceite:** suite mock mede contagens corretamente; suite real produz métricas só quando modelo respondeu; ausência de modelos não vira resultado falso.

### FASE 7 — Editor visual real
- React Flow + API FastAPI, import/export, grafo, tipos de portas, propriedades, preview 2D, validação, PPTX.
- **Aceite:** importar -> editar -> exportar -> compilar reproduz cena equivalente; demonstrar correção de objeto fora do slide no editor.

### FASE 8 — Integração e pacote para professor
- Executar suite completa, corrigir falhas e regressões; produzir `docs/DEFESA_PROFESSOR.md`.
- **Aceite:** README com reprodução passo a passo, saída real, comparação dos modelos executados, limites e próximas extensões. Nada de placeholders como `TODO: implementar parser`.

### Verificação ao final de cada fase

Em `docs/PROGRESSO.md`, registrar data, arquivos alterados, comandos realmente executados, sucesso/falha, limitações e próximo passo. O Codex deve continuar automaticamente à próxima fase — não parar para pedir confirmação após cada etapa, exceto ação externa que exija autenticação/compra.

---

## 14. Testes mínimos antes de declarar “feito”

- 10+ casos sintáticos (válidos/invalidos).
- 10+ casos semânticos (IDs, escopo, referência, dimensão).
- 8+ casos de relações geométricas e Z.
- 10+ casos para regras D001–D010 (ao menos 1 por regra, mais casos de borda para camadas).
- 1 teste de ponta a ponta compilando o `.sld` de 5 slides em `.pptx`.
- 1 teste de inspeção do ZIP do `.pptx` verificando exatamente cinco arquivos XML de slide e existência de objetos de texto/imagem/forma.
- 1 teste de benchmark usando mock com sucessos/erros controlados e métricas previsíveis.
- 1 roundtrip `.sld -> AST -> IR -> DSL -> AST -> IR` sem mudança semântica relevante.
- 1 teste de UI para importação, edição de propriedade, validação e exportação, automatizado conforme stack escolhida.

**Quality gates:** `pytest -q`, `npm test` (quando configurado), `npm run build` do editor, lint/format, execução do demo. Não basta afirmar que os testes existem; rodar e registrar resultados. Se instalação do ambiente impedir alguma etapa, reportar bloqueio em vez de marcar sucesso.

---

## 15. Documentação acadêmica e avaliação para apresentação

Criar `docs/DEFESA_PROFESSOR.md` com:
1. Problema: SLMs variam em capacidade de estrutura e raciocínio espacial.
2. Contribuição: linguagem formal de comandos + AST/IR + verificador espacial de design + tradução para software de slides.
3. Descrição da GLC (terminais, não terminais, produções, tokens, exemplos aceitos/rejeitados).
4. Diferença clara entre **sintaxe da GLC**, **análise semântica** e **regras de design**.
5. Demonstração: programa `.sld`, árvore/IR, mudança de ordem de camadas, PPTX final.
6. Experimento com mesmos prompts, 5 slides, modelos menores/maiores, sucesso e erros.
7. Ameaças à validade: mesmo prompt não significa mesmo tokenizador/infra; qualidade estética não é inteiramente capturada pelas regras; amostra pequena e modelo específico.
8. Limitações e próximos passos: integração Canva/Google Slides, richer DSL, avaliação humana, animações, layout automático.

**Não prometer** que a GLC resolve ambiguidades do português natural; ela define um subconjunto controlado. **Não prometer** que um slide aprovado por regras matemáticas é subjetivamente “bonito”.

---

## 16. Instrução operacional final ao Codex

> **EXECUTE, NÃO APENAS PLANEJE.** Inicie em um diretório novo, ignore integralmente qualquer `slidedsl_windows_demo`, `deck.pptx` ou arquivos protótipos anteriores. Implemente todas as fases deste documento até ter uma solução executável, com GLC, AST/IR, geometria, princípios de design, PPTX editável, editor visual, integração de modelos e benchmark reproduzível. Não use mocks como substitutos finais: mock é somente para testes sem credenciais. Faça commits ou checkpoints lógicos após cada fase. Teste o que puder automaticamente no ambiente; se APIs remotas/Ollama não estiverem disponíveis, deixe a integração pronta, indique o motivo do não teste e prossiga com todas as demais fases. Ao terminar, apresente: árvore dos arquivos criados, comandos de instalação/execução, resultados reais dos testes, caminho do PPTX real, estado de cada modelo no benchmark, decisões de escopo e limitações. Não encerre respondendo apenas com um documento, tarefas pendentes ou pseudocódigo.

**Prioridade de engenharia:** compilação determinística e GLC funcional > design checker > benchmark > editor visual completo. Essa é uma **ordem de execução**, não permissão para omitir o editor visual ou demais entregáveis.
