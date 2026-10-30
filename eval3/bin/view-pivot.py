#!/usr/bin/env python3
import argparse
from viewlib import common,read,emit,macro
p=common(argparse.ArgumentParser(description='SQL-style pivot table: rows x columns, values mean score'))
p.add_argument('--rows',default='testset_src',help='comma-separated row keys')
p.add_argument('--columns',default='testset_tgt',help='single column key')
a=p.parse_args(); df=read(a)
rows=[x.strip() for x in a.rows.split(',') if x.strip()]; cols=a.columns.strip()
valid={'modelname','taskname','testset','testset_src','testset_tgt','metric'}
if not set(rows+[cols])<=valid: p.error('Invalid row/column fields')
by=list(dict.fromkeys(rows+[cols])); tab=macro(df,by,a)
out=tab.pivot_table(index=rows,columns=cols,values='score',aggfunc='first').reset_index()
out.columns=[str(x) for x in out.columns]
emit(out,a.output)
