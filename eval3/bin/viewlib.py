#!/usr/bin/env python3
"""Shared, read-only sacre.tsv loading and filtering. No inference side effects."""
import argparse
import fnmatch
import os
import re
import sys
from pathlib import Path
import pandas as pd

COLS=['modelname','taskname','testset','testset_src','testset_tgt','metric','score']

def common(p):
    p.add_argument('--input',default=os.environ.get('SACRE_TSV','sacre.tsv'))
    p.add_argument('--models',default=os.environ.get('MODELS',''),help='space/comma separated glob patterns; blank means all')
    p.add_argument('--tasks',default=os.environ.get('TASKS',''),help='space/comma separated task globs; blank means all')
    p.add_argument('--testsets',default=os.environ.get('TESTSETS',''))
    p.add_argument('--src',default=os.environ.get('SRC',''))
    p.add_argument('--tgt',default=os.environ.get('TGT',''))
    p.add_argument('--metric',default=os.environ.get('METRIC','BLEU'))
    p.add_argument('--kind',choices=['all','mt','zero','sentmt','docmt'],default=os.environ.get('KIND','all'))
    p.add_argument('--output',default='-',help='TSV file or - for stdout; PNG file for plots')
    p.add_argument('--aggregation',choices=['case','direction'],default='direction',help='case: average test cases; direction: equal weight to language directions')
    return p

def format_table(df, decimals=3):
    """Return an aligned, human-readable table."""
    return df.to_string(
        index=False,
        justify="left",
        float_format=lambda x: f"{x:.{decimals}f}",
    )

def patterns(s):
    return [x for x in re.split(r'[\s,]+',s.strip()) if x]

def apply_patterns(df,col,s):
    pats=patterns(s)
    if pats:
        mask=pd.Series(False,index=df.index)
        for pat in pats: mask |= df[col].astype(str).map(lambda x:fnmatch.fnmatchcase(x,pat))
        df=df[mask]
    return df

def read(a):
    path=Path(a.input)
    if not path.exists(): raise SystemExit(f'Missing score file: {path}')
    df=pd.read_csv(path,sep='\t',dtype=str,on_bad_lines='warn')
    if not set(COLS).issubset(df): raise SystemExit('Expected columns: '+', '.join(COLS))
    df=df[df.metric.isin(['BLEU','chrF2'])].copy()
    df['score']=pd.to_numeric(df.score,errors='coerce')
    df=df.dropna(subset=['score'])
    for col,key in [('modelname','models'),('taskname','tasks'),('testset','testsets'),('testset_src','src'),('testset_tgt','tgt'),('metric','metric')]: df=apply_patterns(df,col,getattr(a,key))
    if a.kind!='all': df=df[df.taskname.str.match('^'+a.kind+r'[0-9]?_')]
    # Never silently average duplicate keys.
    keys=COLS[:-1]
    dups=df.duplicated(keys,keep=False)
    if dups.any(): raise SystemExit(f'Duplicate result keys: {dups.sum()} rows; resolve collisions before analysis')
    if df.empty: raise SystemExit('No results match the selected filters')
    return df

def emit(df, output=None):
    """Print an aligned table or write a machine-readable TSV file."""
    if output is not None and output != "-":
        df.to_csv(
            output,
            sep="\t",
            index=False,
            float_format="%.3f",
        )
        return
    # Format values for terminal display.
    columns = list(df.columns)
    rows = []
    for row in df.itertuples(index=False, name=None):
        rows.append([
            f"{value:.3f}" if isinstance(value, float)
            else str(value)
            for value in row
        ])
    # Determine widths from headers and values.
    widths = [
        max(
            len(str(column)),
            *(len(row[i]) for row in rows),
        )
        for i, column in enumerate(columns)
    ]
    # Right-align numeric columns.
    from pandas.api.types import is_numeric_dtype
    numeric = [
        is_numeric_dtype(df[column]) for column in columns ]
    def format_row(values):
        return "  ".join(
            str(value).rjust(widths[i])
            if numeric[i]
            else str(value).ljust(widths[i])
            for i, value in enumerate(values)
        )
    print(format_row(columns))
    print("  ".join("-" * width for width in widths))
    for row in rows:
        print(format_row(row))

def figure_path(a):
    if a.output=='-': raise SystemExit('Plot views require --output PATH.png')
    Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    return a.output

def direction_means(df):
    return df.groupby(['modelname','taskname','testset_src','testset_tgt'],as_index=False).score.mean()

def macro(df,by,a):
    if a.aggregation=='direction':
        intermediate=df.groupby(list(dict.fromkeys(list(by)+['testset_src','testset_tgt'])),as_index=False).score.mean()
        return intermediate.groupby(list(by),as_index=False).agg(score=('score','mean'),directions=('score','size'))
    return df.groupby(list(by),as_index=False).agg(score=('score','mean'),cases=('score','size'))
