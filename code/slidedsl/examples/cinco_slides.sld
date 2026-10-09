apresentacao "Princípios de Design de Slides" {
  tema claro
  slide 1 {
    adicionar retangulo id decoracao_faixa em (80, 160) tamanho (1120, 12) cor primaria
    adicionar texto id titulo "Princípios de Design de Slides" em (170, 230) tamanho (940, 100) fonte titulo cor texto
    adicionar texto id subtitulo "Contraste, proximidade e camadas" em (295, 345) tamanho (690, 75) fonte corpo cor texto
    adicionar texto id rodape "SlideDSL • cinco slides gerados de um programa formal" em (230, 585) tamanho (840, 55) fonte rodape cor texto
    alinhar subtitulo com titulo pelo centro horizontal
    alinhar rodape com titulo pelo centro horizontal
  }
  slide 2 {
    adicionar texto id titulo "Contraste orienta a leitura" em (80, 64) tamanho (1120, 95) fonte titulo cor texto
    adicionar retangulo id decoracao_bom em (80, 210) tamanho (500, 190) cor #14233D
    adicionar retangulo id decoracao_fraco em (680, 210) tamanho (500, 190) cor #FFFFFF
    adicionar texto id exemplo_bom "Alto contraste" em (105, 255) tamanho (420, 90) fonte 30 cor #FFFFFF
    adicionar texto id exemplo_fraco "Baixo contraste" em (705, 255) tamanho (420, 90) fonte 30 cor #DDE8F9
    adicionar texto id corpo "A luminância pode ser medida. O exemplo claro é intencionalmente fraco." em (80, 465) tamanho (1100, 130) fonte corpo cor texto
    alinhar decoracao_bom com titulo pela esquerda
    alinhar corpo com titulo pela esquerda
  }
  slide 3 {
    adicionar texto id titulo "Proximidade cria grupos" em (80, 64) tamanho (1120, 95) fonte titulo cor texto
    adicionar retangulo id decoracao_esquerda em (80, 205) tamanho (500, 340) cor secundaria
    adicionar retangulo id decoracao_direita em (680, 205) tamanho (500, 340) cor secundaria
    adicionar texto id grupo_a_titulo "Conteúdo" em (105, 240) tamanho (420, 65) fonte 30 cor texto papel corpo
    adicionar texto id grupo_a_corpo "Ideias relacionadas\nficam próximas." em (105, 330) tamanho (420, 160) fonte corpo cor texto papel corpo
    adicionar texto id grupo_b_titulo "Organização" em (705, 240) tamanho (420, 65) fonte 30 cor texto papel corpo
    adicionar texto id grupo_b_corpo "Grupos distintos\nrecebem espaço." em (705, 330) tamanho (420, 160) fonte corpo cor texto papel corpo
    agrupar [grupo_a_titulo, grupo_a_corpo] como conteudo rotulo "Conteúdo"
    agrupar [grupo_b_titulo, grupo_b_corpo] como organizacao rotulo "Organização"
  }
  slide 4 {
    adicionar texto id titulo "Camadas controlam a visibilidade" em (80, 64) tamanho (1120, 95) fonte titulo cor texto
    adicionar retangulo id decoracao_retangulo em (80, 210) tamanho (480, 250) cor primaria
    adicionar imagem id imagem arquivo "assets/imagem_demo.png" em (430, 300) tamanho (480, 270)
    enviar imagem para tras
    trazer imagem para frente
    adicionar texto id corpo "A imagem passa de trás para frente.\nA ordem final é resolvida na IR." em (945, 280) tamanho (250, 250) fonte 20 cor texto
    adicionar texto id rodape "Objetos editáveis; interseção intencional; ordem Z determinística." em (80, 610) tamanho (1100, 46) fonte rodape cor texto
  }
  slide 5 {
    adicionar texto id titulo "Vantagens e limitações" em (80, 64) tamanho (1120, 95) fonte titulo cor texto
    adicionar retangulo id decoracao_coluna_a em (80, 210) tamanho (510, 330) cor secundaria
    adicionar retangulo id decoracao_coluna_b em (670, 210) tamanho (510, 330) cor #EDEFF3
    adicionar texto id cabecalho_a "Vantagens" em (105, 225) tamanho (455, 70) fonte 28 cor texto papel corpo
    adicionar texto id cabecalho_b "Limitações" em (695, 225) tamanho (455, 70) fonte 28 cor texto papel corpo
    adicionar texto id vantagem_1 "1. Sintaxe verificável" em (105, 315) tamanho (455, 55) fonte 22 cor texto
    adicionar texto id vantagem_2 "2. Geometria determinística" em (105, 385) tamanho (455, 55) fonte 22 cor texto
    adicionar texto id vantagem_3 "3. PowerPoint editável" em (105, 455) tamanho (455, 55) fonte 22 cor texto
    adicionar texto id limitacao_1 "1. Português controlado" em (695, 315) tamanho (455, 55) fonte 22 cor texto
    adicionar texto id limitacao_2 "2. Overflow aproximado" em (695, 385) tamanho (455, 55) fonte 22 cor texto
    adicionar texto id limitacao_3 "3. Avaliação humana" em (695, 455) tamanho (455, 55) fonte 22 cor texto
    adicionar texto id rodape "Validar regras espaciais não garante beleza subjetiva." em (80, 610) tamanho (1120, 46) fonte rodape cor texto
    alinhar decoracao_coluna_a com titulo pela esquerda
    alinhar rodape com titulo pela esquerda
  }
}
