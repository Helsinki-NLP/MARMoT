#!/usr/bin/env python3
import argparse
import numpy as np
import pandas as pd
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from viewlib import common,read,figure_path
p=common(argparse.ArgumentParser(description='Classical MDS of models on exact common cases'))
p.add_argument('--center',action='store_true',help='subtract per-model mean to emphasize response profiles')
p.add_argument('--coordinates',default='',help='optional coordinates TSV')
a=p.parse_args();df=read(a)
if df.metric.nunique()!=1: raise SystemExit('Select one metric')
keys=['taskname','testset','testset_src','testset_tgt','metric']
wide=df.pivot(index=keys,columns='modelname',values='score').dropna()
if len(wide.columns)<3 or len(wide)<2: raise SystemExit('Need >=3 models and >=2 exactly common cases')
X=wide.to_numpy().T
if a.center:X=X-X.mean(axis=1,keepdims=True)
D2=((X[:,None,:]-X[None,:,:])**2).mean(axis=2)
n=len(X);J=np.eye(n)-np.ones((n,n))/n;B=-.5*J@D2@J
vals,vecs=np.linalg.eigh(B);order=np.argsort(vals)[::-1];vals=vals[order];vecs=vecs[:,order]
xy=vecs[:,:2]*np.sqrt(np.maximum(vals[:2],0))
out=pd.DataFrame({'modelname':wide.columns,'x':xy[:,0],'y':xy[:,1]})
if a.coordinates:out.to_csv(a.coordinates,sep='\t',index=False)
fig,ax=plt.subplots(figsize=(10,7));ax.scatter(xy[:,0],xy[:,1],s=45)
for _,r in out.iterrows():ax.annotate(r.modelname,(r.x,r.y),fontsize=7,xytext=(4,3),textcoords='offset points')
ax.set(xlabel='Classical MDS 1',ylabel='Classical MDS 2',title=f'Model BLEU-profile distance: {len(wide)} common cases');ax.grid(alpha=.2);fig.tight_layout();fig.savefig(figure_path(a),dpi=180);plt.close(fig)
