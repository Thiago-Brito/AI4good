apresentacao "Catálogo de operações" {
  tema escuro
  slide 1 {
    adicionar retangulo id a em (80, 100) tamanho (200, 100) cor primaria
    adicionar elipse id b em a direita de a com margem 24 tamanho (100, 100) cor destaque
    adicionar texto id titulo "Operações da SlideDSL" em (80, 300) tamanho (1000, 100) fonte titulo cor texto
    adicionar imagem id foto arquivo "assets/imagem_demo.png" em canto superior direito tamanho (200, 120)
    adicionar retangulo id temporario em (0, 0) tamanho (20, 20) cor primaria
    remover temporario
    mover a para (100, 100)
    redimensionar b para (120, 100)
    mudar cor de a para secundaria
    trazer a para frente
    enviar b para tras
    alinhar titulo com a pela esquerda
    agrupar [a, b] como g
    mover g para (80, 100)
    redimensionar g para (400, 120)
    desagrupar g
    distribuir horizontalmente [a, b, foto] com intervalo 24
    definir camada de titulo como 5
    alinhar titulo com a pela esquerda
  }
}
