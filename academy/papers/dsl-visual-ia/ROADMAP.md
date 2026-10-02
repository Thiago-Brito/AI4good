# Roadmap — DSL visual para orquestração de IA

## Imagens dos guias no GitHub — 01/10/2026

- [x] Identificar que a regra global de `outputs/` excluía as imagens incorporadas aos Markdown.
- [x] Criar exceções restritas para o mapa da área e os PNGs de figuras e tabelas dos três estudos detalhados.
- [x] Atualizar a documentação sobre quais artefatos acompanham os guias no Git.
- [x] Incluir as imagens junto aos guias para versionamento; conferir a existência e a inclusão permitida das 51 imagens referenciadas.
- [ ] Estudante conferir a renderização no GitHub após o envio da branch `dsl-visual`.

## Adaptação do guia ao domínio de slides — 01/10/2026

- [x] Registrar e preservar em `estudos/01-fundamentos/refs/` o texto e a imagem fornecidos pelo estudante antes da adaptação.
- [x] Adaptar `GUIA-INICIAL.md` para análise e melhoria de slides, com conceitos, metamodelo, tipos e contratos dos blocos.
- [x] Incorporar a imagem do fluxo e explicar decisão, estado, correção, revalidação e saída com pendências ao atingir o limite.
- [x] Detalhar desenvolvimento incremental e preservar vídeos, trilha de estudo e navegação para os artigos.
- [ ] Validar com o orientador o recorte proposto e o público da linguagem.
- [ ] Definir formato de entrada, critérios de análise com referências, gravidade dos problemas e alterações suportadas.
- [ ] Especificar portas, estado e regras de execução; implementar e avaliar as etapas incrementalmente.

O guia descreve uma proposta, não funcionalidades implementadas nem qualidade de correção já demonstrada. O domínio proposto passa a ser slides; as pendências históricas sobre delimitação devem ser lidas à luz desse recorte.

## Apresentação das palavras-chave — 30/09/2026

- [x] Confirmar o foco com o estudante: descrever palavras-chave do tema, incluindo a organização dos blocos na tela.
- [x] Registrar fontes e limites em `estudos/01-fundamentos/refs/FONTES-APRESENTACAO.md` antes da redação.
- [x] Criar 12 slides sobre DSL, linguagem visual, orquestração de IA, nós/portas/conexões e organização espacial.
- [x] Gerar PowerPoint editável, apresentação HTML, PDF e roteiro de fala em `estudos/01-fundamentos/outputs/apresentacao/`.
- [x] Conferir as 12 páginas do PDF, notas dos 12 slides e limites dos elementos; revisar visualmente a composição exportada.
- [ ] Estudante revisar a terminologia e ensaiar a explicação do fluxo.
- [ ] Validar os termos candidatos nas bases de pesquisa; as traduções em inglês não constituem validação bibliométrica.

Gerador local: `tools/create_dsl_slides.py`, a partir da raiz do workspace. Usa `python-pptx` instalado localmente em `outputs/slide-deps`; PDF exportado do HTML com Chrome headless.

Índice de navegação: [README.md](README.md). Os arquivos das etapas introdutória e de curadoria abaixo foram reorganizados em `estudos/01-fundamentos/`; seus caminhos antigos neste histórico devem ser lidos a partir dessa subpasta.

## Etapa introdutória — 27/09/2026

- [x] Registrar fontes conceituais e materiais em `refs/FONTES.md` antes da redação.
- [x] Preparar `GUIA-INICIAL.md` com exemplos, glossário, vídeos e exercícios.
- [x] Incluir mapa didático da área como imagem em `outputs/diagrama-area.svg`.
- [ ] Estudante assistir aos vídeos e preencher os exercícios.
- [ ] Confirmar compreensão explicando o fluxo sem consultar o guia.
- [ ] Refinar público, domínio e pergunta de pesquisa com o orientador.

## Continuidade da solicitação mais ampla

- [ ] Validar palavras-chave em bases de literatura revisada por pares; registrar consultas e contagens.
- [ ] Levantar veículos relevantes, incluindo BRACIS, com fontes oficiais e contexto/período de Qualis; registrar explicitamente classificações não encontradas.
- [x] Propor três artigos relacionados para o núcleo inicial: ChainForge, InstructPipe e Oakes et al.; seleção final a confirmar após leitura.
- [ ] Ler cada artigo integralmente e explicar suas figuras e tabelas com página, métricas, exemplos e limitações.
- [ ] Registrar termos e fluxos difíceis, pesquisar suas fontes e documentar o que esclareceu cada dúvida.
- [ ] Só então definir alvos A/B/C, verificar deadlines oficiais e comparar com os prazos da disciplina.

Este diretório registra o novo tema em separado, pois os projetos acadêmicos existentes tratam de outros assuntos. Não há escolha final de veículo, template, experimento ou estudo com participantes nesta etapa.

## Curadoria de artigos — 27/09/2026

- [x] Pesquisar e selecionar sete artigos próximos ou complementares ao tema.
- [x] Registrar metadados, DOI, fontes primárias e limites em `refs/BUSCA-ARTIGOS.md` antes da redação.
- [x] Criar `ARTIGOS-PARA-LER.md` com ordem de leitura, acesso aos textos, justificativa dos veículos, orientações sobre figuras/tabelas e limites de cada trabalho.
- [x] Diferenciar artigos completos, Extended Abstracts e versões de preprint.
- [x] Ler o corpo e os apêndices dos três trabalhos do núcleo e produzir guias/fichamentos detalhados: Oakes et al., ChainForge e InstructPipe. A curadoria dos demais trabalhos permanece seletiva.
- [ ] Verificar classificações Qualis com fonte e período e aprofundar a busca nos anais de BRACIS.

## Organização e estudo do PDF — 27/09/2026

- [x] Separar os materiais anteriores em `estudos/01-fundamentos/`, preservando suas referências e diagrama.
- [x] Criar `estudos/02-workflows-ml/` para o artigo fornecido, com guia, fontes e outputs separados.
- [x] Copiar o PDF de Downloads para `estudos/02-workflows-ml/refs/3638243.pdf`; verificar identidade SHA-256 e preservar o original.
- [x] Ler o corpo da versão publicada de 50 páginas e inspecionar visualmente as 12 figuras e 7 tabelas.
- [x] Registrar fontes auxiliares e esclarecer ontologias, padrões de workflow, agrupamento, avaliação no Orange e métricas de experiência do usuário.
- [x] Criar `estudos/02-workflows-ml/GUIA-DETALHADO.md` com as oito seções do artigo, imagens comentadas, interpretação dos números, limites e relação com a DSL visual.
- [x] Registrar inconsistências editoriais observadas e distinguir resultados, propostas dos autores e exemplos didáticos.
- [x] Atualizar a navegação e verificar links locais.
- [ ] Estudante realizar os exercícios e explicar a Figura 4 com um exemplo próprio.
- [ ] Delimitar público, domínio e transformação principal que a DSL pretende apoiar.
- [x] Concluir o aprofundamento dos três artigos do núcleo. Oakes et al., ChainForge e InstructPipe têm guias detalhados concluídos.

## Estudo detalhado do ChainForge — 01/10/2026

- [x] Criar `estudos/03-chainforge/`, mantendo guia, fontes e artefatos separados.
- [x] Preservar o original em Downloads e copiar `3613904.3642016.pdf` para `refs/`; verificar identidade SHA-256.
- [x] Ler as seções 1–9 e os apêndices A e B da versão de 18 páginas fornecida pelo estudante.
- [x] Inspecionar visualmente as 7 figuras e 3 tabelas; gerar recortes com legendas e manifesto de página/coordenadas.
- [x] Registrar fontes antes da redação, incluindo apoio sobre boxplots e documentação oficial.
- [x] Produzir `GUIA-DETALHADO.md` com glossário, exemplo percorrido, combinações, metadados, avaliação, leitura crítica e exercícios.
- [x] Relacionar achados sobre mover/conectar nós e inspecionar resultados ao foco do estudante em organização espacial, distinguindo evidência e propostas de pesquisa.
- [x] Registrar limites dos números e inconsistência P15/P9 no apêndice, sem atribuir causalidade de layout ou significância estatística não demonstrada.
- [x] Atualizar navegação e conferir links locais, recortes e integridade do PDF.
- [ ] Estudante explicar as Figuras 1, 3 e 4 e realizar os exercícios do guia.
- [ ] Delimitar uma tarefa de compreensão de workflows e consultar literatura específica de layout/agrupamento antes de afirmar novidade.
- [x] Aprofundar InstructPipe; guia concluído em `estudos/04-instructpipe/GUIA-DETALHADO.md`.

## Estudo detalhado do InstructPipe — 01/10/2026

- [x] Criar `estudos/04-instructpipe/` com guia, referências e outputs separados.
- [x] Preservar o PDF de Downloads e copiar a publicação de 22 páginas para `refs/3706598.3713905.pdf`, conferindo SHA-256.
- [x] Ler as seções 1–9 e apêndices A–D; inspecionar visualmente as 15 figuras, 4 tabelas e o Algoritmo 1.
- [x] Registrar fontes antes da redação e criar recortes com legendas e manifesto de página/coordenadas.
- [x] Produzir guia com glossário, arquitetura, pseudocódigo, layout, avaliações, limites, exercícios e fichamento.
- [x] Explicitar o rumo solicitado: transformar intenção em fluxo visual que o usuário consiga compreender, corrigir e completar.
- [x] Distinguir geração estrutural, organização espacial, parâmetros, tempo e demanda mental; separar propostas de pesquisa dos resultados dos autores.
- [x] Registrar inconsistências e limites de interpretação, atualizar navegação e verificar links e integridade dos artefatos.
- [ ] Estudante explicar as Figuras 1, 4 e 11 e distinguir Tabelas 1–2 da Figura 8.
- [ ] Escolher uma mudança visual e uma tarefa de compreensão/correção; discutir o recorte com o orientador.
- [ ] Verificar novidade em literatura específica antes de adotar a pergunta candidata como contribuição.
