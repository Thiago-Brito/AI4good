import time

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st


st.set_page_config(page_title="Conexões Neurais ao Vivo", page_icon="⚡", layout="wide")


def criar_luas(quantidade, ruido, semente):
    rng = np.random.default_rng(semente)
    metade = quantidade // 2
    angulo = rng.uniform(0, np.pi, metade)
    primeira = np.c_[np.cos(angulo), np.sin(angulo)]
    segunda = np.c_[1 - np.cos(angulo), 0.45 - np.sin(angulo)]
    entradas = np.vstack((primeira, segunda))
    alvos = np.vstack((np.zeros((metade, 1)), np.ones((metade, 1))))
    entradas += rng.normal(0, ruido, entradas.shape)
    ordem = rng.permutation(len(entradas))
    return entradas[ordem], alvos[ordem]


class RedeNeural:
    def __init__(self, tamanhos, semente):
        rng = np.random.default_rng(semente)
        self.pesos = []
        self.biases = []
        for entrada, saida in zip(tamanhos[:-1], tamanhos[1:]):
            limite = np.sqrt(6 / (entrada + saida))
            self.pesos.append(rng.uniform(-limite, limite, (entrada, saida)))
            self.biases.append(np.zeros((1, saida)))

    def propagar(self, entrada):
        ativacoes = [entrada]
        atual = entrada
        for pesos, bias in zip(self.pesos[:-1], self.biases[:-1]):
            atual = np.tanh(atual @ pesos + bias)
            ativacoes.append(atual)
        z = np.clip(atual @ self.pesos[-1] + self.biases[-1], -500, 500)
        ativacoes.append(1 / (1 + np.exp(-z)))
        return ativacoes

    def treinar(self, entradas, alvos, taxa):
        ativacoes = self.propagar(entradas)
        previsoes = ativacoes[-1]
        delta = (previsoes - alvos) / len(entradas)
        gradientes_p = [None] * len(self.pesos)
        gradientes_b = [None] * len(self.biases)

        for camada in reversed(range(len(self.pesos))):
            gradientes_p[camada] = ativacoes[camada].T @ delta
            gradientes_b[camada] = delta.sum(axis=0, keepdims=True)
            if camada > 0:
                delta = (delta @ self.pesos[camada].T) * (1 - ativacoes[camada] ** 2)

        for camada in range(len(self.pesos)):
            self.pesos[camada] -= taxa * gradientes_p[camada]
            self.biases[camada] -= taxa * gradientes_b[camada]

        perda = -np.mean(
            alvos * np.log(previsoes + 1e-9)
            + (1 - alvos) * np.log(1 - previsoes + 1e-9)
        )
        acuracia = np.mean((previsoes >= 0.5) == alvos)
        return float(perda), float(acuracia)


def desenhar_rede(rede, amostra, progresso_ligacoes, epoca):
    ativacoes = rede.propagar(amostra.reshape(1, -1))
    tamanhos = [a.shape[1] for a in ativacoes]
    maior = max(tamanhos)
    posicoes = []
    for camada, tamanho in enumerate(tamanhos):
        ys = np.arange(tamanho) - (tamanho - 1) / 2
        posicoes.append([(camada * 2.5, y) for y in ys])

    todas_ligacoes = []
    for camada, matriz in enumerate(rede.pesos):
        for origem in range(matriz.shape[0]):
            for destino in range(matriz.shape[1]):
                todas_ligacoes.append((camada, origem, destino, float(matriz[origem, destino])))

    # A ordem fixa faz as linhas nascerem uma a uma, sem piscarem entre épocas.
    total_exato = progresso_ligacoes * len(todas_ligacoes)
    completas = int(total_exato)
    fracao_da_proxima = total_exato - completas
    escala = max(max(abs(item[3]) for item in todas_ligacoes), 1e-9)

    fig, ax = plt.subplots(figsize=(12, max(6, maior * 0.55 + 2)))
    for indice, (camada, origem, destino, peso) in enumerate(todas_ligacoes):
        if indice > completas or (indice == completas and fracao_da_proxima == 0):
            continue
        fracao = 1.0 if indice < completas else fracao_da_proxima
        x1, y1 = posicoes[camada][origem]
        x2, y2 = posicoes[camada + 1][destino]
        # A ponta da ligação caminha da origem até o neurônio de destino.
        ponta_x = x1 + (x2 - x1) * fracao
        ponta_y = y1 + (y2 - y1) * fracao
        cor = "#228be6" if peso >= 0 else "#fa5252"
        largura = 0.5 + 4 * abs(peso) / escala
        ax.plot([x1, ponta_x], [y1, ponta_y], color=cor, linewidth=largura, alpha=0.65, zorder=1)
        if fracao < 1:
            ax.scatter(ponta_x, ponta_y, s=45, color="#ffd43b", zorder=5)

    nomes = ["Entrada", *[f"Oculta {n + 1}" for n in range(len(tamanhos) - 2)], "Saída"]
    for camada, valores in enumerate(ativacoes):
        for no, ((x, y), valor) in enumerate(zip(posicoes[camada], valores.ravel())):
            cor = (float(valor) + 1) / 2 if 0 < camada < len(tamanhos) - 1 else float(valor)
            ax.scatter(x, y, s=1150, c=[[np.clip(cor, 0, 1)]], cmap="YlGn", vmin=0, vmax=1,
                       edgecolors="#202938", linewidths=2, zorder=3)
            texto = f"x{no + 1}\n{valor:+.2f}" if camada == 0 else f"{valor:+.2f}"
            ax.text(x, y, texto, ha="center", va="center", fontsize=9, zorder=4)
        ax.text(posicoes[camada][0][0], maior / 2 + 0.7, nomes[camada], ha="center", fontweight="bold")

    percentual = min(progresso_ligacoes, 1.0)
    ax.set_title(
        f"Época {epoca} — {min(completas, len(todas_ligacoes))}/{len(todas_ligacoes)} ligações formadas "
        f"({percentual:.0%})"
    )
    ax.text(0.01, 0.02, "🔵 peso positivo   🔴 peso negativo   🟡 ligação sendo formada",
            transform=ax.transAxes, fontsize=10)
    ax.set_xlim(-1, (len(tamanhos) - 1) * 2.5 + 1)
    ax.set_ylim(-maior / 2 - 1, maior / 2 + 1.4)
    ax.axis("off")
    fig.tight_layout()
    return fig


st.title("⚡ Conexões neurais se formando ao vivo")
st.write("Esta é uma aplicação separada. O arquivo original `app.py` não foi alterado.")

with st.sidebar:
    st.header("Configuração")
    pontos = st.slider("Pontos de treinamento", 100, 800, 400, 50)
    ruido = st.slider("Ruído", 0.00, 0.35, 0.12, 0.01)
    camadas = st.slider("Camadas ocultas", 1, 3, 2)
    neuronios = st.slider("Neurônios por camada", 2, 16, 8)
    epocas = st.slider("Épocas", 50, 1000, 300, 10)
    taxa = st.select_slider("Taxa de aprendizado", [0.01, 0.03, 0.1, 0.3], value=0.1)
    formar_ate = st.slider("Formar todas as ligações até a época", 10, epocas, min(150, epocas), 10)
    atualizar = st.slider("Atualizar a cada época(s)", 1, 20, 2)
    velocidade = st.slider("Pausa da animação", 0.00, 0.30, 0.05, 0.01)
    iniciar = st.button("▶ Formar e treinar a rede", type="primary", use_container_width=True)

if not iniciar:
    st.info("Clique em **Formar e treinar a rede** para começar a animação.")
else:
    x, y = criar_luas(pontos, ruido, 42)
    rede = RedeNeural([2, *([neuronios] * camadas), 1], 42)
    painel = st.empty()
    metricas = st.empty()
    barra = st.progress(0)

    for epoca in range(1, epocas + 1):
        perda, acuracia = rede.treinar(x, y, taxa)
        if epoca == 1 or epoca % atualizar == 0 or epoca == epocas:
            progresso = min(epoca / formar_ate, 1.0)
            figura = desenhar_rede(rede, x[epoca % len(x)], progresso, epoca)
            painel.pyplot(figura, clear_figure=True)
            plt.close(figura)
            with metricas.container():
                c1, c2, c3 = st.columns(3)
                c1.metric("Época", f"{epoca}/{epocas}")
                c2.metric("Perda", f"{perda:.5f}")
                c3.metric("Acurácia", f"{acuracia:.1%}")
            barra.progress(epoca / epocas)
            if velocidade:
                time.sleep(velocidade)

    st.success("Todas as conexões foram formadas e o treinamento terminou.")

