"""Generate figures/tables only from completed experimental artifacts."""
import csv
import json
from pathlib import Path
import numpy as np
import torch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from data import ROOT, OUTPUTS, load_data
from infer import Predictor

DEST = ROOT.parents[1]/'academy/papers/artigo-overleaf/outputs/ordered-gnn'
COLORS = ['#1764ab','#07877c']
NAMES = ['Base','Modificada']


def main():
    DEST.mkdir(parents=True,exist_ok=True)
    results=json.loads((OUTPUTS/'main/results.json').read_text())
    summary=json.loads((OUTPUTS/'main/summary.json').read_text())
    assert len(results)==6
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':140})
    fig,axes=plt.subplots(1,2,figsize=(11,3.5),constrained_layout=True)
    for color,kind,label in zip(COLORS,['original','modified'],NAMES):
        history=np.genfromtxt(OUTPUTS/f'main/{kind}-seed42/history.csv',delimiter=',',names=True)
        axes[0].plot(history['epoch'],history['train_loss'],color=color,label=label+' treino')
        axes[0].plot(history['epoch'],history['val_loss'],color=color,linestyle='--',label=label+' validação')
        axes[1].plot(history['epoch'],history['val_accuracy']*100,color=color,label=label)
    axes[0].set(xlabel='Época',ylabel='Entropia cruzada'); axes[0].legend(fontsize=8)
    axes[1].set(xlabel='Época',ylabel='Acurácia de validação (%)'); axes[1].legend()
    fig.savefig(DEST/'curvas.png'); plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(10,4),constrained_layout=True)
    for ax,kind,label in zip(axes,['original','modified'],NAMES):
        run=next(r for r in results if r['kind']==kind and r['seed']==42)
        cm=np.array(run['scores']['test']['confusion'])
        ax.imshow(cm,cmap='Blues',vmin=0,vmax=300)
        for i in range(7):
            for j in range(7): ax.text(j,i,str(cm[i,j]),ha='center',va='center',fontsize=8,color='white' if cm[i,j]>150 else 'black')
        ax.set(title=label+' · semente 42',xlabel='Classe prevista',ylabel='Classe real',xticks=range(7),yticks=range(7))
    fig.savefig(DEST/'confusao.png'); plt.close(fig)
    data,_=load_data()
    fig,axes=plt.subplots(1,2,figsize=(11,3.5),constrained_layout=True)
    left=np.zeros(7)
    for split,color in [('train','#1764ab'),('val','#48afa5'),('test','#efb354')]:
        counts=torch.bincount(data.y[getattr(data,split+'_mask')],minlength=7).numpy()
        axes[0].bar(range(7),counts,bottom=left,label=split,color=color); left+=counts
    axes[0].set(xlabel='Identificador da classe',ylabel='Nós'); axes[0].legend()
    ids=data.test_mask.nonzero().flatten()[:20]
    # Display exact nonzero feature coordinates; no invented word meanings.
    selected=data.x[ids].numpy()
    row,col=np.nonzero(selected)
    axes[1].scatter(col,row,s=3,color='#1764ab')
    axes[1].set(xlabel='Índice do atributo (bag-of-words)',ylabel='Primeiros 20 nós do teste',xlim=(0,1433))
    fig.savefig(DEST/'dataset.png'); plt.close(fig)
    fig,ax=plt.subplots(figsize=(11,5)); ax.set(xlim=(0,11),ylim=(0,5)); ax.axis('off')
    def box(x,y,w,text,color):
        ax.add_patch(FancyBboxPatch((x,y),w,.65,boxstyle='round,pad=.08',facecolor=color,edgecolor='none'))
        ax.text(x+w/2,y+.325,text,ha='center',va='center',color='white',fontsize=9)
    box(.2,3.8,2,'Cora\n2.708 × 1.433','#19304b')
    box(3,3.8,2.3,'MLP de entrada\n1.433 → 64 → 64','#19304b')
    ax.annotate('',xy=(2.9,4.1),xytext=(2.3,4.1),arrowprops={'arrowstyle':'->'})
    box(.2,2.1,4.6,'BASE: 4 camadas Ordered GNN\ngate compartilhado · média dos vizinhos',COLORS[0])
    box(6.2,2.1,4.3,'Última representação → Linear → 7 classes',COLORS[0])
    box(.2,.3,4.6,'MODIFICADA: 4 gates independentes\n+ 4 blocos feed-forward residuais',COLORS[1])
    box(6.2,.3,4.3,'Atenção sobre h0, h1, h2, h3, h4\n→ Linear → 7 classes',COLORS[1])
    for y in [2.4,.6]: ax.annotate('',xy=(6.1,y),xytext=(4.9,y),arrowprops={'arrowstyle':'->'})
    ax.text(7.9,4.1,'Mesmos dados e protocolo\nTreinos independentes',ha='center',va='center')
    fig.tight_layout(); fig.savefig(DEST/'arquiteturas.png'); plt.close(fig)
    rows=[]
    for r in results:
        t=r['scores']['test']
        rows.append(f"{'Base' if r['kind']=='original' else 'Modificada'} & {r['seed']} & {r['best_epoch']} & {100*t['accuracy']:.2f} & {100*t['macro_f1']:.2f} & {t['loss']:.4f} \\")
    # Two literal backslashes per LaTeX row.
    (DEST/'runs.tex').write_text('\\newcommand{\\ResultRows}{%\n'+'\n'.join(row+'\\' for row in rows)+'\n}\n',encoding='utf-8')
    macros=[]
    for kind,prefix in [('original','Base'),('modified','Mod')]:
        for metric,name in [('accuracy','Acc'),('macro_f1','Fone')]:
            v=summary[kind][metric]
            macros += [f'\\newcommand{{\\{prefix}{name}}}{{{100*v["mean"]:.2f}}}',f'\\newcommand{{\\{prefix}{name}Std}}{{{100*v["std_sample"]:.2f}}}']
        r=next(r for r in results if r['kind']==kind and r['seed']==42)
        macros.append(f'\\newcommand{{\\{prefix}Params}}{{{r["parameter_count"]}}}')
    (DEST/'numbers.tex').write_text('\n'.join(macros)+'\n',encoding='utf-8')
    pred={k:np.genfromtxt(OUTPUTS/f'main/{k}-seed42/predictions.csv',delimiter=',',names=True) for k in ['original','modified']}
    # Select lowest test node ID in each category, never cherry-pick confidence.
    test=data.test_mask.numpy(); truth=data.y.numpy()
    bc=pred['original']['prediction']==truth; mc=pred['modified']['prediction']==truth
    groups={'ambas acertam':test&bc&mc,'somente base acerta':test&bc&~mc,'somente modificada acerta':test&~bc&mc,'ambas erram':test&~bc&~mc}
    predictor=Predictor(); examples=[]
    for label,mask in groups.items():
        ids=np.flatnonzero(mask)
        if len(ids): examples.append({'category':label,'category_count':len(ids),**predictor.predict(int(ids[0]))})
    (DEST/'qualitative.json').write_text(json.dumps(examples,indent=2),encoding='utf-8')
    fig,axes=plt.subplots(1,len(examples),figsize=(12,3.3),constrained_layout=True)
    for ax,example in zip(axes,examples):
        for color,kind,offset in zip(COLORS,['original','modified'],[-.18,.18]):
            ax.bar(np.arange(7)+offset,example['models'][kind]['probabilities'],width=.36,color=color,label=kind)
        ax.set(title=f"Nó {example['node_id']} · real {example['target']}\n{example['category']}",xlabel='Classe',ylim=(0,1),xticks=range(7))
    axes[0].set_ylabel('Probabilidade'); axes[-1].legend(fontsize=7)
    fig.savefig(DEST/'qualitativo.png'); plt.close(fig)
    details={'runs':[{k:r[k] for k in ['kind','seed','best_epoch','epochs_run','parameter_count','training_seconds','full_graph_inference_ms_median']} for r in results],
             'paired_accuracy_difference_pp':[100*(next(r for r in results if r['kind']=='modified' and r['seed']==s)['scores']['test']['accuracy']-next(r for r in results if r['kind']=='original' and r['seed']==s)['scores']['test']['accuracy']) for s in [42,43,44]],
             'qualitative_category_counts':{k:int(v.sum()) for k,v in groups.items()}}
    (DEST/'details.json').write_text(json.dumps(details,indent=2),encoding='utf-8')
    print(json.dumps(details,indent=2))


if __name__=='__main__': main()
