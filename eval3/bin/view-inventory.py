#!/usr/bin/env python3
import argparse
from viewlib import common,read,emit
p=common(argparse.ArgumentParser(description='Inventory: models, task types, testsets and score counts'))
a=p.parse_args();df=read(a)
df=df.assign(kind=df.taskname.str.extract(r'^([^_]+)_')[0])
df['direction']=df.testset_src+'>'+df.testset_tgt
out=df.groupby(['modelname','kind','testset','metric'],as_index=False).agg(n_cases=('score','size'),n_tasks=('taskname','nunique'),n_directions=('direction','nunique'))
emit(out.sort_values(['modelname','kind','testset','metric']),a.output)
