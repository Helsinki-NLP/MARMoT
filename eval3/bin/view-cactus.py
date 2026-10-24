#!/usr/bin/env python3
import argparse
import numpy as np
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from viewlib import common,read,figure_path
p=common(argparse.ArgumentParser(description='Quality-coverage curves on exact common evaluation keys'))
p.add_argument('--threshold-max',type=float,default=None)
a=p.parse_args();df=read(a)
if df.metric.nunique()!=1: raise SystemExit('Select one metric')
keys=['taskname','testset','testset_src','testset_tgt','metric']
wide=df.pivot(index=keys,columns='modelname',values='score').dropna()
if wide.shape[1]<2: raise SystemExit('Select at least two models with common cases')
if wide.empty: raise SystemExit('No common evaluation cases across selected models')
upper=a.threshold_max if a.threshold_max is not None else float(np.ceil(wide.max().max()/5)*5)
xs=np.linspace(0,upper,151)
fig,ax=plt.subplots(figsize=(9,5.5))
for name in wide.columns: ax.plot(xs,[(wide[name]>=x).mean()*100 for x in xs],label=name,lw=1.7)
ax.set(xlabel='Minimum '+df.metric.iloc[0],ylabel='Common cases reaching threshold (%)',title=f'Quality coverage: {len(wide)} exactly matched cases');ax.grid(alpha=.2);ax.legend(fontsize=7,loc='upper right');fig.tight_layout();fig.savefig(figure_path(a),dpi=180);plt.close(fig)
