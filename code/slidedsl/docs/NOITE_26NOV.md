# Registro da noite de 26/11/2026

Plano: `docs/PLANO_NOITE_26NOV.md`. Branch: `exp/noite-26nov`.

| hora | tarefa | resultado | API acumulada |
|---|---|---|---|
| 00:30 | início | branch criado; T1 (A/B sem documento) rodando: lado "antes" pronto (12/12), "depois" em execução | US$ 0,00 (as 4 gerações de 25/11 com GPT-5.4-mini ficaram antes do orçamento da noite) |
| 00:45 | T2 | `scripts/avaliar_documento.py` + `benchmark/documento_diferencial.json`. Notas das execuções de 25/11 (GPT-5.4-mini): antes das correções 6/7 seções e 3/9 números; v2_corrigido 7/7, 1/9, com "custa mais caro"; v6 7/7, 5/9, sem invertidas; escrita à mão 7/7, 8/9 | US$ 0,00 |
| 01:20 | T1 | 12 pedidos, s11, gramática, 4B. Antes (f12b102) × depois (f64d822): compilam 10/12 × 9/12 (1 discordante, solar_tema por A005; McNemar p = 1,0); reparos 11,67 × 11,67; tokens saída 7.144 × 7.124; tempo 113,6 × 107,9 s. Sem sinal de piora; 6 fatos por slide mantido. Obs.: o 'valido' do runner deu 0/12 no lado antes porque a cópia antiga não tem node_modules do renderer; a validade foi refeita compilando o .slda com o compilador de cada lado. | US$ 0,00 |
| 00:47 | T4 (medição) e T3 (preparo) | T4 commitado (041c9dc, pytest 764/764); 12 pedidos com a gramática limitada rodando em segundo plano (outputs/regressao_pc_ab/t4). Preparado scripts/bancada_documento.py (todos os motores no mesmo documento, com avaliação) e scripts/rodar_t3_lado.sh. GPT-5.4-mini custa ~US$ 0,10 por execução (uso.json): o orçamento dá ~9 execuções. | US$ 0,00 |
