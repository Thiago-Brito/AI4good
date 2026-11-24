# Teste 4 — celular físico (medido em 24/11/2026)

Dados: `outputs/teste4/celular_agua_1/` (`SlideDSL-teste-1795493866226.json`, exportado pelo app, e
`SlideDSL-1795493652953.pptx`). Documento: `outputs/teste4/documentos/agua.txt`, gerado por
`scripts/documentos_teste4.py` a partir dos dossiês fixos (mesmos fatos dos testes no computador).

## Configuração

- Aparelho: Motorola moto g(8) power lite, 3,96 GB de RAM, Android 10; sem carregador (battery_state 1);
  modo de economia desligado. Abaixo do mínimo que o próprio app indica para o modelo (6 GB).
- App 0.2.0 (APK de 23/11, antes da correção de layout de 23/11), perfil celular: até 6 leituras do documento,
  roteiro, uma chamada por slide, no máximo 1 reparo por slide.
- Modelo: Qwen3 1.7B Q4_K_M (llama.rn), contexto 4096, só CPU (GPU desligada), temperatura 0,2.
- Pedido: "Apresente o ciclo da água para alunos do ensino fundamental, …" + `agua.txt` (3.114 caracteres,
  9 trechos), 5 slides.

## Resultado (medido, n = 1)

| Medida | Valor |
|---|---:|
| Status | sucesso; 5 slides; 0 reparos; 0 slides montados pelo compilador (F001) |
| Verificador único (`pptx_checks.py`) | válido e estrito (nenhum estouro de texto) |
| Tempo total | **63,0 min** |
| Chamadas | 12 (6 leituras do documento, 1 roteiro, 5 slides) |
| Tokens entrada / saída | 12.154 / 3.784 |
| Processamento do prompt | mediana **3,9 tokens/s** (3,3–4,6) |
| Geração | mediana **1,5 tokens/s** (1,3–2,1) |
| Divisão do tempo | geração 68%, prompt 32% |
| Por etapa | leitura do documento 29,2 min (46%); roteiro 8,4 min (13%); slides 25,3 min (40%) |
| Bateria | 95% → 77% (18 pontos em 63 min) |

- O cache de prefixo do llama.cpp funcionou: nas leituras 2–6 e nos slides 2–5 só 101–255 tokens novos foram
  processados por chamada (o resto do prompt foi reaproveitado); roteiro e slide 1 processaram o prompt inteiro
  (1.132 e 1.470 tokens, 4,4 e 6,0 min só de leitura).
- A leitura do documento gerou mais texto (2.021 tokens) que os cinco slides (1.376).
- Temperatura: não disponível (Expo Battery não expõe); o autor relatou que o aparelho não esquentou muito.

## Conteúdo (inspeção do PPTX contra `agua.txt`)

- Forma: texto dentro das caixas, tipografia e layout do compilador.
- Repetição: os slides 2, 3 e 4 repetem evaporação, condensação e precipitação.
- IDs de fatos visíveis no texto ("Fonte F2").
- Afirmações ausentes do documento: "água potável", "manhã de inverno", "agricultura", "granizo"; duas estão
  erradas — a chuva "se torna água potável" ao cair no solo, e a evaporação explicada por "água quente exposta ao
  ar frio, como em uma manhã de inverno".

## Interpretação

- O fluxo completo funciona num celular de entrada com 4 GB, sem rede, e entrega um arquivo que passa no
  verificador; mas 63 min por apresentação não é uso interativo. O gargalo é a geração (1,5 tokens/s): reduzir
  tokens gerados importa mais que reduzir o prompt.
- Melhorias com efeito previsível (não medidas): ler documento curto em uma chamada e limitar a saída das
  leituras (46% do tempo); escrever o deck em uma chamada (no Teste 2, ~5× mais rápido no computador).
- A garantia do compilador é de forma, não de conteúdo: o documento reduziu, mas não eliminou, afirmações sem
  fonte.
