#!/usr/bin/env python3
import argparse
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from viewlib import common,read,macro,figure_path
p=common(argparse.ArgumentParser(description='Source x target BLEU heatmap; select a model for clear interpretation'))
p.add_argument('--title',default='MARMoT score heatmap')
a=p.parse_args(); df=read(a)
if df.modelname.nunique()>1: raise SystemExit('Heatmap requires exactly one model: use --models MODEL')
if df.metric.nunique()>1: raise SystemExit('Heatmap requires exactly one metric')
t=macro(df,['testset_src','testset_tgt'],a).pivot(index='testset_src',columns='testset_tgt',values='score')
fig,ax=plt.subplots(figsize=(max(7,len(t.columns)*.48+2),max(5,len(t.index)*.34+2)))
img=ax.imshow(t.values,aspect='auto',cmap='viridis'); ax.set_xticks(range(len(t.columns)),t.columns,rotation=90);ax.set_yticks(range(len(t.index)),t.index)
ax.set_xlabel('Target');ax.set_ylabel('Source');ax.set_title(a.title+'\n'+df.modelname.iloc[0]);fig.colorbar(img,ax=ax,label=df.metric.iloc[0]);fig.tight_layout();fig.savefig(figure_path(a),dpi=170);plt.close(fig)
