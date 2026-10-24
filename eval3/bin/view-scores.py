#!/usr/bin/env python3
import argparse
from viewlib import common,read,emit,macro
p=common(argparse.ArgumentParser(description='Score table: selected raw cases or aggregated means'))
p.add_argument('--group-by',default='modelname,metric',help='comma-separated columns, or raw')
p.add_argument('--sort', default='score',help='Comma-separated sort columns')
#p.add_argument('--sort',default='score',help='score or a group-by column')
a=p.parse_args(); df=read(a)
if a.group_by=='raw': out=df.sort_values(['modelname','taskname','testset','metric'])
else:
    by=[x.strip() for x in a.group_by.split(',') if x.strip()]
    valid={'modelname','taskname','testset','testset_src','testset_tgt','metric'}
    if not set(by)<=valid: p.error('Invalid group-by; choose from '+','.join(sorted(valid)))
    out=macro(df,by,a)
    sort_cols = [s.strip() for s in a.sort.split(',')]
    invalid = set(sort_cols) - set(out.columns)
    if invalid:
        p.error(f"Invalid sort columns: {', '.join(sorted(invalid))}")
    out = out.sort_values(
        sort_cols,
        ascending=[col != 'score' for col in sort_cols],
        kind='stable',)
emit(out,a.output)
