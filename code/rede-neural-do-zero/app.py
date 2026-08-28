import time

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st


st.set_page_config(page_title="Rede Neural do Zero", page_icon="🧠", layout="wide")


def make_dataset(kind: str, samples: int, noise: float, seed: int):
    """Gera problemas binarios 2D sem depender do scikit-learn."""
    rng = np.random.default_rng(seed)
    half = samples // 2

    if kind == "Luas":
        angle = rng.uniform(0, np.pi, half)
        first = np.c_[np.cos(angle), np.sin(angle)]
        second = np.c_[1 - np.cos(angle), 0.45 - np.sin(angle)]
        x = np.vstack((first, second))
        y = np.vstack((np.zeros((half, 1)), np.ones((half, 1))))
    elif kind == "Círculos":
        angle = rng.uniform(0, 2 * np.pi, half)
        inner = np.c_[0.55 * np.cos(angle), 0.55 * np.sin(angle)]
        angle = rng.uniform(0, 2 * np.pi, half)
        outer = np.c_[1.25 * np.cos(angle), 1.25 * np.sin(angle)]
        x = np.vstack((inner, outer))
        y = np.vstack((np.zeros((half, 1)), np.ones((half, 1))))
    else:  # XOR
        x = rng.uniform(-1, 1, (samples, 2))
        y = ((x[:, 0] * x[:, 1]) > 0).astype(float).reshape(-1, 1)

    x = x + rng.normal(0, noise, x.shape)
    order = rng.permutation(len(x))
    return x[order], y[order]


class NeuralNetwork:
    """MLP binaria implementada somente com algebra matricial NumPy."""

    def __init__(self, input_size, hidden_sizes, seed=42):
        rng = np.random.default_rng(seed)
        sizes = [input_size, *hidden_sizes, 1]
        self.weights = []
        self.biases = []
        for fan_in, fan_out in zip(sizes[:-1], sizes[1:]):
            # Inicializacao de Xavier, apropriada para tanh.
            limit = np.sqrt(6 / (fan_in + fan_out))
            self.weights.append(rng.uniform(-limit, limit, (fan_in, fan_out)))
            self.biases.append(np.zeros((1, fan_out)))

    @staticmethod
    def sigmoid(z):
        z = np.clip(z, -500, 500)
        return 1 / (1 + np.exp(-z))

    def forward(self, x):
        activations = [x]
        current = x
        for weight, bias in zip(self.weights[:-1], self.biases[:-1]):
            current = np.tanh(current @ weight + bias)
            activations.append(current)
        current = self.sigmoid(current @ self.weights[-1] + self.biases[-1])
        activations.append(current)
        return activations

    def train_step(self, x, y, learning_rate):
        activations = self.forward(x)
        prediction = activations[-1]

        # Com sigmoid + entropia cruzada, dL/dz = predicao - alvo.
        delta = (prediction - y) / len(x)
        weight_grads = [None] * len(self.weights)
        bias_grads = [None] * len(self.biases)

        for layer in reversed(range(len(self.weights))):
            weight_grads[layer] = activations[layer].T @ delta
            bias_grads[layer] = np.sum(delta, axis=0, keepdims=True)
            if layer > 0:
                delta = (delta @ self.weights[layer].T) * (1 - activations[layer] ** 2)

        for layer in range(len(self.weights)):
            self.weights[layer] -= learning_rate * weight_grads[layer]
            self.biases[layer] -= learning_rate * bias_grads[layer]

        epsilon = 1e-9
        loss = -np.mean(y * np.log(prediction + epsilon) + (1 - y) * np.log(1 - prediction + epsilon))
        accuracy = np.mean((prediction >= 0.5) == y)
        return float(loss), float(accuracy)

    def predict(self, x):
        return self.forward(x)[-1]


def decision_figure(model, x, y, epoch):
    padding = 0.45
    x_min, x_max = x[:, 0].min() - padding, x[:, 0].max() + padding
    y_min, y_max = x[:, 1].min() - padding, x[:, 1].max() + padding
    xx, yy = np.meshgrid(np.linspace(x_min, x_max, 150), np.linspace(y_min, y_max, 150))
    grid = np.c_[xx.ravel(), yy.ravel()]
    probability = model.predict(grid).reshape(xx.shape)

    fig, ax = plt.subplots(figsize=(7, 5))
    contour = ax.contourf(xx, yy, probability, levels=np.linspace(0, 1, 21), cmap="RdBu", alpha=0.72)
    ax.contour(xx, yy, probability, levels=[0.5], colors="white", linewidths=2)
    ax.scatter(x[:, 0], x[:, 1], c=y.ravel(), cmap="bwr", edgecolors="white", linewidths=0.5, s=28)
    ax.set_title(f"Fronteira de decisão — época {epoch}")
    ax.set_xlabel("Característica 1")
    ax.set_ylabel("Característica 2")
    fig.colorbar(contour, ax=ax, label="Probabilidade da classe azul")
    fig.tight_layout()
    return fig


def history_figure(losses, accuracies):
    fig, loss_axis = plt.subplots(figsize=(7, 4))
    epochs = np.arange(1, len(losses) + 1)
    loss_axis.plot(epochs, losses, color="#ff6b6b", label="Perda")
    loss_axis.set_xlabel("Época")
    loss_axis.set_ylabel("Perda", color="#ff6b6b")
    loss_axis.tick_params(axis="y", labelcolor="#ff6b6b")
    accuracy_axis = loss_axis.twinx()
    accuracy_axis.plot(epochs, accuracies, color="#4dabf7", label="Acurácia")
    accuracy_axis.set_ylabel("Acurácia", color="#4dabf7")
    accuracy_axis.tick_params(axis="y", labelcolor="#4dabf7")
    accuracy_axis.set_ylim(0, 1.02)
    loss_axis.grid(alpha=0.2)
    fig.tight_layout()
    return fig


def network_figure(model, sample, epoch):
    """Desenha neuronios, ativacoes e pesos atuais da rede."""
    activations = model.forward(sample.reshape(1, -1))
    layer_sizes = [values.shape[1] for values in activations]
    layer_names = ["Entrada", *[f"Oculta {i + 1}" for i in range(len(layer_sizes) - 2)], "Saída"]
    max_nodes = max(layer_sizes)
    fig_width = max(8, 2.4 * len(layer_sizes))
    fig, ax = plt.subplots(figsize=(fig_width, max(5, 0.48 * max_nodes + 2)))
    positions = []

    for layer, size in enumerate(layer_sizes):
        x_position = layer * 2.3
        y_positions = np.arange(size) - (size - 1) / 2
        positions.append([(x_position, y) for y in y_positions])

    # As ligacoes sao desenhadas primeiro para ficarem atras dos neuronios.
    all_weights = np.concatenate([weight.ravel() for weight in model.weights])
    weight_scale = max(float(np.max(np.abs(all_weights))), 1e-9)
    for layer, weight_matrix in enumerate(model.weights):
        for source in range(weight_matrix.shape[0]):
            for target in range(weight_matrix.shape[1]):
                weight = float(weight_matrix[source, target])
                color = "#228be6" if weight >= 0 else "#fa5252"
                width = 0.3 + 3.2 * abs(weight) / weight_scale
                alpha = 0.18 + 0.72 * abs(weight) / weight_scale
                x1, y1 = positions[layer][source]
                x2, y2 = positions[layer + 1][target]
                ax.plot([x1, x2], [y1, y2], color=color, linewidth=width, alpha=alpha, zorder=1)

    for layer, (layer_positions, values) in enumerate(zip(positions, activations)):
        values = values.ravel()
        for node, ((x_position, y_position), value) in enumerate(zip(layer_positions, values)):
            # tanh pode ser negativa; convertemos para 0..1 apenas para a cor.
            color_value = (float(value) + 1) / 2 if 0 < layer < len(layer_sizes) - 1 else float(value)
            color_value = float(np.clip(color_value, 0, 1))
            ax.scatter(
                x_position,
                y_position,
                s=1050,
                c=[[color_value]],
                cmap="YlGn",
                vmin=0,
                vmax=1,
                edgecolors="#1f2937",
                linewidths=1.5,
                zorder=3,
            )
            label = f"x{node + 1}\n{value:+.2f}" if layer == 0 else f"{value:+.2f}"
            ax.text(x_position, y_position, label, ha="center", va="center", fontsize=8, zorder=4)
        ax.text(layer_positions[0][0], max_nodes / 2 + 0.6, layer_names[layer], ha="center", fontweight="bold")

    output = float(activations[-1][0, 0])
    predicted_class = int(output >= 0.5)
    ax.set_title(
        f"Rede funcionando — época {epoch} | saída = {output:.3f} | classe prevista = {predicted_class}",
        fontsize=12,
    )
    ax.text(
        0.01,
        0.01,
        "Azul: peso positivo   •   Vermelho: peso negativo   •   Espessura: força da conexão\n"
        "Verde mais forte: neurônio mais ativado",
        transform=ax.transAxes,
        fontsize=9,
        va="bottom",
    )
    ax.set_xlim(-1, (len(layer_sizes) - 1) * 2.3 + 1)
    ax.set_ylim(-max_nodes / 2 - 1, max_nodes / 2 + 1.2)
    ax.axis("off")
    fig.tight_layout()
    return fig


st.title("🧠 Rede Neural do Zero")
st.caption("Treinamento visual em tempo real, sem TensorFlow, PyTorch, Keras ou scikit-learn.")

with st.sidebar:
    st.header("Configuração")
    dataset_name = st.selectbox("Conjunto de dados", ["Luas", "Círculos", "XOR"])
    samples = st.slider("Quantidade de pontos", 100, 1000, 400, 50)
    noise = st.slider("Ruído", 0.00, 0.40, 0.12, 0.01)
    hidden_layers = st.slider("Camadas ocultas", 1, 3, 2)
    neurons = st.slider("Neurônios por camada", 2, 32, 8)
    learning_rate = st.select_slider("Taxa de aprendizado", [0.001, 0.003, 0.01, 0.03, 0.1, 0.3], value=0.1)
    epochs = st.slider("Épocas", 10, 1000, 300, 10)
    update_every = st.slider("Atualizar animação a cada", 1, 50, 10)
    delay = st.slider("Pausa visual (segundos)", 0.00, 0.20, 0.02, 0.01)
    seed = st.number_input("Semente aleatória", 0, 9999, 42)
    start = st.button("▶ Iniciar treinamento", type="primary", use_container_width=True)

st.info("A rede usa **tanh** nas camadas ocultas, **sigmoid** na saída e aprende por **backpropagation** com descida do gradiente.")

if not start:
    st.write("Ajuste os parâmetros na barra lateral e clique em **Iniciar treinamento**.")
else:
    x, y = make_dataset(dataset_name, samples, noise, int(seed))
    network = NeuralNetwork(2, [neurons] * hidden_layers, int(seed))
    losses, accuracies = [], []

    metrics = st.empty()
    progress = st.progress(0, text="Preparando treinamento...")
    st.subheader("Neurônios funcionando ao vivo")
    st.caption("A cada atualização, um ponto do conjunto atravessa a rede. Os valores dentro dos círculos são as ativações atuais.")
    network_slot = st.empty()
    st.subheader("Resultado do aprendizado")
    left, right = st.columns(2)
    boundary_slot = left.empty()
    history_slot = right.empty()

    for epoch in range(1, epochs + 1):
        loss, accuracy = network.train_step(x, y, learning_rate)
        losses.append(loss)
        accuracies.append(accuracy)

        if epoch == 1 or epoch % update_every == 0 or epoch == epochs:
            with metrics.container():
                c1, c2, c3 = st.columns(3)
                c1.metric("Época", f"{epoch}/{epochs}")
                c2.metric("Perda", f"{loss:.5f}")
                c3.metric("Acurácia", f"{accuracy:.1%}")
            progress.progress(epoch / epochs, text=f"Treinando... {epoch}/{epochs}")

            sample_index = (epoch // update_every) % len(x)
            live_network_fig = network_figure(network, x[sample_index], epoch)
            network_slot.pyplot(live_network_fig, clear_figure=True)
            plt.close(live_network_fig)

            boundary_fig = decision_figure(network, x, y, epoch)
            boundary_slot.pyplot(boundary_fig, clear_figure=True)
            plt.close(boundary_fig)
            history_fig = history_figure(losses, accuracies)
            history_slot.pyplot(history_fig, clear_figure=True)
            plt.close(history_fig)
            if delay:
                time.sleep(delay)

    progress.progress(1.0, text="Treinamento concluído!")
    st.success(f"Concluído: perda final {losses[-1]:.5f} e acurácia {accuracies[-1]:.1%}.")
