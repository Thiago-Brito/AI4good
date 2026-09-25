"""Real, offline inference from trained checkpoints on a Cora node."""
import argparse
import json
import time
import torch
from data import OUTPUTS, load_data, sha256
from models import make_model


class Predictor:
    # Preparação: carrega o Cora e os pesos que já aprenderam durante o treino.
    # Não há otimizador nem atualização de pesos neste arquivo.
    def __init__(self, run='main', seed=42):
        torch.set_num_threads(4)
        self.data, self.adjacency = load_data()
        self.models, self.checkpoints = {}, {}
        for kind in ['original','modified']:
            path = OUTPUTS/run/f'{kind}-seed{seed}'/'model.pt'
            checkpoint = torch.load(path, map_location='cpu', weights_only=True)
            model = make_model(kind, checkpoint['params'])
            model.load_state_dict(checkpoint['state_dict']); model.eval()
            self.models[kind] = model
            self.checkpoints[kind] = {'sha256':sha256(path),'epoch':checkpoint['best_epoch'],'seed':seed}

    def predict(self, node):
        # node é o número de um documento, não o número de uma categoria.
        if not 0 <= node < self.data.num_nodes:
            raise ValueError('node_id deve estar entre 0 e 2707')
        data = self.data
        neighbors = data.edge_index[0,data.edge_index[1]==node].tolist()
        active = data.x[node].nonzero().flatten()
        # target = resposta registrada no dataset, exibida para conferir o acerto.
        # Ela NÃO é passada para model(...): a rede recebe só atributos e grafo.
        result = {'node_id':node,'target':int(data.y[node]),
                  'split':'train' if data.train_mask[node] else 'val' if data.val_mask[node] else 'test',
                  'neighbors':neighbors, 'active_feature_indices':active.tolist(),
                  'active_feature_values':data.x[node,active].tolist(), 'models':{}}
        for kind,model in self.models.items():
            started = time.perf_counter()
            with torch.inference_mode():
                # Calcula pontuações para sete assuntos. softmax transforma essas
                # pontuações em probabilidades; argmax escolhe a maior delas.
                # 93% nesta saída é sobre UM documento, não 93% de acertos no teste.
                out = model(data.x,self.adjacency)
                probabilities = out['x'][node].softmax(-1)
            item = {'predicted_class':int(probabilities.argmax()),'probabilities':probabilities.tolist(),
                    'elapsed_ms':(time.perf_counter()-started)*1000, **self.checkpoints[kind]}
            if 'depth_attention' in out:
                item['depth_attention'] = out['depth_attention'][node].tolist()
            result['models'][kind] = item
        return result


if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('--node',type=int,default=1708)
    p.add_argument('--seed',type=int,default=42); p.add_argument('--run',default='main')
    args=p.parse_args()
    print(json.dumps(Predictor(args.run,args.seed).predict(args.node),indent=2))
