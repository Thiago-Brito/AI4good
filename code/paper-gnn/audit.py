"""Independent final checks on saved evidence, without retraining."""
import json
import numpy as np
import torch
from data import ROOT, OUTPUTS, sha256, load_data
from models import make_model


def main():
    torch.set_num_threads(4)
    data, adjacency=load_data()
    folder=OUTPUTS/'main'
    protocol=json.loads((folder/'protocol.json').read_text())
    manifest=json.loads((OUTPUTS/'dataset/manifest.json').read_text())
    assert sha256(OUTPUTS/'dataset/manifest.json')==protocol['dataset_manifest_sha256']
    for relative,digest in manifest['raw_sha256'].items():
        assert sha256(OUTPUTS/'dataset'/relative)==digest
    for name in ['data.py','models.py','ordered_layer.py','original_model.py','train.py']:
        assert sha256(ROOT/name)==protocol['code_sha256'][name]
    results=json.loads((folder/'results.json').read_text())
    checks=[]
    for result in results:
        path=folder/f"{result['kind']}-seed{result['seed']}"
        checkpoint=torch.load(path/'model.pt',weights_only=True)
        assert sha256(path/'model.pt')==result['checkpoint_sha256']
        initial=torch.load(path/'initial.pt',weights_only=True)['state_dict']
        model=make_model(result['kind'],checkpoint['params']).eval()
        model.load_state_dict(checkpoint['state_dict'])
        assert any(not torch.equal(v,initial[k]) for k,v in model.state_dict().items())
        with torch.no_grad(): probabilities=model(data.x,adjacency)['x'].softmax(-1).numpy()
        rows=np.genfromtxt(path/'predictions.csv',delimiter=',',names=True,dtype=None,encoding='utf-8')
        np.testing.assert_array_equal(rows['node_id'],np.arange(data.num_nodes))
        np.testing.assert_array_equal(rows['target'],data.y.numpy())
        np.testing.assert_allclose(probabilities,np.stack([rows[f'p_{i}'] for i in range(7)],axis=1),atol=1e-7)
        test=rows[rows['split']=='test']; assert len(test)==1000
        cm=np.zeros((7,7),dtype=int); np.add.at(cm,(test['target'],test['prediction']),1)
        np.testing.assert_array_equal(cm,result['scores']['test']['confusion'])
        accuracy=np.trace(cm)/cm.sum()
        f1=np.mean(2*np.diag(cm)/np.maximum(cm.sum(0)+cm.sum(1),1))
        np.testing.assert_allclose(accuracy,result['scores']['test']['accuracy'],atol=1e-7)
        np.testing.assert_allclose(f1,result['scores']['test']['macro_f1'],atol=1e-7)
        history=np.genfromtxt(path/'history.csv',delimiter=',',names=True)
        assert np.isfinite(history['gradient_norm']).all() and (history['gradient_norm']>0).all()
        assert result['best_epoch']==int(history['epoch'][history['val_loss'].argmin()])
        checks.append({'kind':result['kind'],'seed':result['seed'],'accuracy_recomputed':accuracy,
                       'macro_f1_recomputed':f1,'checkpoint_inference_matches':True,
                       'code_and_data_hashes_match':True,'parameters_changed_from_initialization':True})
    (OUTPUTS/'audit.json').write_text(json.dumps({'passed':True,'runs':checks},indent=2),encoding='utf-8')
    print(json.dumps({'passed':True,'runs_verified':len(checks)}))


if __name__=='__main__': main()
