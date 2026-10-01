# Ordered GNN — entrega da disciplina

- [x] Selecionar artigo ICLR 2023 e verificar código oficial e Cora.
- [x] Registrar fontes e preservar commit oficial e licença.
- [x] Executar rede base com adaptação documentada para CPU.
- [x] Implementar variante arquitetural substancial e verificar matemática.
- [x] Treinar ambas sob protocolo comum e registrar evidências: seis treinos.
- [x] Recarregar checkpoints e demonstrar inferência com dados reais.
- [x] Gerar gráficos, exemplos qualitativos e comparação quantitativa.
- [x] Escrever e revisar relatório técnico, compilar PDF e preparar demonstração.

Resultado: base 87,23% ± 0,78 pp; modificada 87,10% ± 0,26 pp. Sem ganho médio.
Quatro testes, auditoria independente dos seis checkpoints e teste de navegador
passaram. PDF de nove páginas e demonstração local com inferência real.
O protocolo compacto e as diferenças do ambiente publicado estão documentados.
Ablações, outros splits e reprodução integral das tabelas são trabalhos futuros.

## Apresentação e Overleaf

- [x] Criar APRESENTACAO.md com roteiro, falas, exemplos e comandos de auditoria.
- [x] Confirmar demonstração local acessível em http://127.0.0.1:8765.
- [x] Enviar relatório e dependências ao Overleaf: commit d27877d aceito no remoto.
- [x] Reexecutar auditoria dos seis checkpoints: passou.

## Clareza da demonstração

- [x] Verificar os sete nomes de categoria nos dados originais: 2.708 correspondências.
- [x] Mostrar assuntos, resposta esperada e explicação de acerto/erro na interface.
- [x] Adicionar quatro exemplos clicáveis, glossário e explicação das probabilidades.
- [x] Organizar JavaScript em funções legíveis e comentar a inferência em português.
- [x] Criar ENTENDA_O_CODIGO.md e atualizar o roteiro com exemplos concretos.
- [x] Testar os quatro exemplos e layout móvel no Edge; nenhuma falha JavaScript.
- [x] Auditar novamente os seis checkpoints e recompilar o relatório explicativo.
- [x] Detalhar a comparação de arquiteturas na tela: exemplo de rodadas, caminhos
  de decisão, três alterações com localização no código e significado dos parâmetros.

## Versionamento no GitHub

## Slides para apresentação

- [x] Gerar PowerPoint editável e PDF compacto de cinco páginas, com roteiro de fala.
- [x] Incluir artigo de 2023, Cora, código, modificações e resultados reais.
- [x] Capturar a aplicação em execução e incluir o exemplo 1713 nos slides.
- [x] Verificar cinco páginas no PDF e ausência de transbordamento no HTML.
- Arquivos: `outputs/apresentacao-ordered-gnn/` na raiz do workspace.
- Importação no Canva pendente: integração ainda não conectada.

## Registro do Git flow

- Feature: `feature/ordered-gnn-cora`, criada a partir de `develop`.
- Base sincronizada com o trabalho anterior já integrado em `origin/main`.
- Validação anterior ao commit: quatro testes passaram e seis checkpoints auditados.
- Destino da feature concluída: `develop`; publicação de release é uma etapa separada.
- Código e documentação versionados; dados gerados, pesos, vendor e ambiente local ignorados.
