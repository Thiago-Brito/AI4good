"""Execute: python -m streamlit run app_heart.py."""
import time
from pathlib import Path

import numpy as np
import streamlit as st

from heart_graph import graph_html, snapshot
from heart_mlp import FEATURES, GraphMLP, download_dataset, export_run, prepare_data, select_config


def draw(slot, model, frames, training=True, animate=True):
    with slot.container():
        st.iframe(graph_html(model, frames, training, seconds, hide_inactive, animate), height=660)


st.set_page_config(page_title='Heart Disease — MLP em grafo', layout='wide')
st.title('Heart Disease: rede neural em grafo')
st.caption('Conexões acendem na ida das ativações e na volta dos gradientes. Os pesos vêm do treinamento real.')
with st.sidebar:
    local_csv = st.text_input('Caminho de heart.csv (vazio: usar cache ou baixar)')
    automatic = st.checkbox('Buscar configuração por validação', value=False)
    if automatic:
        st.caption('Compara quatro configurações dentro do treino e escolhe pela menor perda de validação.')
    layers = st.slider('Camadas ocultas', 1, 3, 2, disabled=automatic)
    neurons = st.slider('Neurônios na primeira camada oculta', 2, 16, 8, disabled=automatic)
    taper = st.checkbox('Reduzir neurônios nas camadas seguintes', value=True, disabled=automatic)
    epochs = st.slider('Épocas (máximo na busca)', 10, 2000, 500, 10)
    optimizer = st.selectbox('Otimizador', ['sgd', 'adam'], disabled=automatic)
    rate = st.select_slider('Taxa de aprendizado', [.001, .003, .01, .03, .1, .3],
                            value=.1 if optimizer == 'sgd' else .003, disabled=automatic)
    l2 = st.select_slider('Regularização L2', [0., .001, .01, .03], value=0., disabled=automatic)
    seed = st.number_input('Semente', 0, 9999, 42)
    st.subheader('Animação')
    every = st.slider('Atualização visual a cada N épocas', 1, 100, 10)
    seconds = st.slider('Segundos por camada', .15, 1.5, .65, .05)
    hide_inactive = st.checkbox('Apagar ligações inativas', value=True)
    live = st.checkbox('Animar durante o treinamento', value=True)
    start = st.button('Treinar rede', type='primary')

st.write('80% treino / 20% teste, após remover duplicatas. A padronização usa apenas o treino. '
         'A busca opcional reserva parte do treino para validação e depois retreina com os 80% completos.')
if start:
    try:
        with st.spinner('Carregando Heart Disease...'):
            data = prepare_data(Path(local_csv) if local_csv else download_dataset(), int(seed))
        hidden = [max(2, neurons // (2 ** i)) if taper else neurons for i in range(layers)]
        config = {'sizes': [13, *hidden, 1], 'optimizer': optimizer, 'rate': rate,
                  'l2': l2, 'epochs': epochs, 'seed': int(seed)}
        if automatic:
            selection_status = st.empty()
            def selection_progress(number, total, epoch):
                selection_status.write(f'Validação: configuração {number}/{total}, época {epoch}…')
            selected, audit = select_config(data['raw_train'], data['y_train'], int(seed), epochs, selection_progress)
            config.update(selected)
            config['selection'] = audit
            selection_status.success('Configuração escolhida; iniciando treino final com os 80%.')
    except Exception as error:
        st.error(f'Não foi possível preparar o treinamento: {error}')
        st.stop()
    model = GraphMLP(config['sizes'], int(seed))
    st.write(f"{data['original_count']} linhas originais; {data['duplicates_removed']} duplicatas removidas; "
             f"{len(data['x_train'])} treino / {len(data['x_test'])} teste.")
    st.write(f"Arquitetura {' → '.join(map(str, config['sizes']))} · {config['optimizer'].upper()} · "
             f"taxa {config['rate']} · L2 {config['l2']} · {config['epochs']} épocas")
    status, graph, chart, weights = st.empty(), st.empty(), st.empty(), st.empty()
    progress = st.progress(0)
    history, frames = [], [snapshot(model, data['x_train'][0], 0)]
    # Limita o replay a aproximadamente 100 snapshots para evitar HTML excessivo.
    capture_every = max(every, int(np.ceil(config['epochs'] / 100)))
    for epoch in range(1, config['epochs'] + 1):
        model.train_step(data['x_train'], data['y_train'], config['rate'], config['optimizer'], config['l2'])
        history.append({'epoch': epoch, **model.metrics(data['x_train'], data['y_train'])})
        if epoch % capture_every == 0 or epoch == config['epochs']:
            frames.append(snapshot(model, data['x_train'][0], epoch))
        if epoch == 1 or epoch % every == 0 or epoch == config['epochs']:
            status.write(f"Época {epoch}/{config['epochs']} — perda treino {history[-1]['loss']:.4f} — "
                         f"acurácia treino {history[-1]['accuracy']:.1%}")
            if live:
                draw(graph, model, [snapshot(model, data['x_train'][0], epoch)])
                time.sleep(.15)
            chart.line_chart({'Perda treino': [h['loss'] for h in history],
                              'Acurácia treino': [h['accuracy'] for h in history]})
            weights.dataframe([{'Origem': e.source, 'Destino': e.target, 'Peso': e.weight,
                                'Gradiente': e.grad, 'Alteração': e.change} for e in model.edges], height=200)
            progress.progress(epoch / config['epochs'])
    directory, report = export_run(model, data, history, config)
    st.session_state['heart_run'] = (model, data, history, directory, report)
    st.session_state['heart_frames'] = frames
    graph.empty()

if 'heart_run' in st.session_state:
    model, data, history, directory, report = st.session_state['heart_run']
    st.subheader('Rever as conexões aprendendo')
    st.caption('Replay dos pesos gravados durante o treino, com uma amostra fixa. '
               'O movimento dos pulsos é ilustrativo; apagar uma linha não remove sua conexão da rede.')
    frames = st.session_state.get('heart_frames') or [snapshot(model, data['x_train'][0], len(history))]
    draw(st.empty(), model, frames)
    if report['config'].get('selection'):
        with st.expander('Comparação na validação interna'):
            st.dataframe(report['config']['selection']['candidates'])
            st.caption('A época e os parâmetros foram escolhidos pela perda de validação. '
                       'Isso não garante aumento da acurácia no teste.')
    st.subheader('Avaliação no conjunto de teste')
    c1, c2 = st.columns(2)
    c1.metric('Acurácia teste', f"{report['test']['accuracy']:.1%}")
    c2.metric('Perda teste', f"{report['test']['loss']:.4f}")
    st.caption('Matriz de confusão: linhas = classe real 0/1; colunas = classe prevista 0/1.')
    st.dataframe(np.array(report['confusion_true_rows_predicted_columns']))
    st.caption(f'Artefatos desta execução: {directory}')
    st.download_button('Baixar métricas e histórico', (directory / 'metrics.json').read_bytes(), 'metrics.json')
    st.download_button('Baixar animação do treinamento', graph_html(model, frames, True, seconds, hide_inactive),
                       'treinamento.html', mime='text/html')
    st.subheader('Inferência: acompanhar uma amostra por camada')
    index = st.slider('Amostra de teste', 0, len(data['x_test']) - 1, 0)
    st.dataframe([dict(zip(FEATURES, data['raw_test'][index]))])
    animate_inference = st.toggle('Animar feed forward', value=True)
    draw(st.empty(), model, [snapshot(model, data['x_test'][index], len(history))],
         training=False, animate=animate_inference)
    probability = float(model.predict(data['x_test'][index:index + 1])[0, 0])
    st.write(f'Saída sigmoid: {probability:.4f} | Classe prevista: {int(probability >= .5)} | '
             f"Classe real: {int(data['y_test'][index, 0])}")
    st.caption('Na inferência os pesos ficam fixos; as ativações avançam pelas camadas. '
               'Os controles de treinamento são aplicados ao clicar em Treinar rede.')
else:
    st.info('Clique em Treinar rede para iniciar. O padrão usa a arquitetura 13 → 8 → 4 → 1.')
