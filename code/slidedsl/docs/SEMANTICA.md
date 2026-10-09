# Semântica operacional e geometria
Pydantic foi escolhido para AST/IR: validação de tipos na API e JSON Schema gerado
da mesma definição. A semântica percorre comandos na ordem textual em cada slide.
IDs são locais e não podem colidir com grupos. Referência futura, removida ou de
outro slide falha. Depois de remover, o ID pode ser reutilizado.

Canvas 1280×720, origem superior esquerda. `abaixo`: x=x_ref, y=y_ref+h_ref+m;
`direita`: x=x_ref+w_ref+m, y=y_ref; canto superior direito: x=1280−64−w, y=64.
Referências a grupo usam a caixa união dos membros. Não são restrições reativas:
alterações posteriores não recalculam automaticamente comandos já executados.

Alinhar esquerda iguala x; direita iguala x+w; centro horizontal iguala x+w/2;
topo iguala y. Intenção fica na IR para D004. Grupo é uma coleção de IDs, sem
objeto gráfico adicional. Mover grupo aplica mesma translação a todos; redimensionar
escala posições e dimensões em torno do canto superior esquerdo da caixa união.
Não escala o tamanho da fonte. Grupos sobrepostos/aninhados são rejeitados.
Distribuição usa a ordem explícita da lista e conserva y, começando no x do primeiro.

Z é normalizado após cada operação por ordenação estável: 0..n−1. Adicionar vai
ao topo, trazer vai após o maior Z, enviar antes do menor. Camada numérica ordena
com os valores atuais; empate conserva a ordem de criação/estado. Backend usa
exatamente essa sequência. Remover exclui elemento, referências e grupos que
ficarem com menos de dois membros. O PPTX é regenerado da cena final.

IR → DSL adiciona a geometria absoluta, grupos e relações, depois restaura posições
absolutas. Assim mantém relações declaradas e inclusive um desvio posterior que
D004 precisa diagnosticar. Ignoram-se apenas proveniência de linha/coluna e origem
heurística versus anotação na comparação semântica. Papéis e cores são preservados.
Não se preserva o histórico de operações excluídas: conserva-se o estado final.

Imagens são relativas à raiz, PNG/JPG/JPEG com assinatura válida e caminho resolvido
dentro da raiz; rejeitam URL, caminho absoluto, travessia e escape via symlink.
Dimensões devem ser positivas; fontes 10..96 pt. Código de modelo nunca vira JS.
