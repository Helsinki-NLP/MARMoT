#!/usr/bin/env python3
import argparse
import pandas as pd
from viewlib import common,read,emit
p=common(argparse.ArgumentParser(description='Exact matched-case pairwise model difference; A minus B'))
p.add_argument('--a',required=True,help='exact first model name')
p.add_argument('--b',required=True,help='exact second model name')
p.add_argument('--summary',action='store_true',help='one row per metric, direction-macro or case mean')
a=p.parse_args(); df=read(a)
keys=['taskname','testset','testset_src','testset_tgt','metric']
x=df[df.modelname==a.a][keys+['score']].rename(columns={'score':'a_score'})
y=df[df.modelname==a.b][keys+['score']].rename(columns={'score':'b_score'})
out=x.merge(y,on=keys,validate='one_to_one'); out['delta']=out.a_score-out.b_score
if out.empty: raise SystemExit('No matched cases. Verify names and filters; cannot compare disjoint coverage.')
if a.summary:
    if a.aggregation=='direction':
        out=out.groupby(['metric','testset_src','testset_tgt'],as_index=False).delta.mean()
        out=out.groupby('metric',as_index=False).agg(mean_delta=('delta','mean'),n_directions=('delta','size'))
    else: out=out.groupby('metric',as_index=False).agg(mean_delta=('delta','mean'),n_cases=('delta','size'))
else: out=out.sort_values(keys)
emit(out,a.output)
