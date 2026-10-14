#!/usr/bin/env python3
"""Aggregate eval run records without dropping failures or missing metrics."""
import argparse, json, statistics
from collections import defaultdict
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument('runs', type=Path, help='JSONL; one run record per line')
    p.add_argument('--planned', type=int, required=True, help='planned count per arm/model/split group')
    p.add_argument('--out', type=Path)
    a=p.parse_args()
    rows=[json.loads(x) for x in a.runs.read_text().splitlines() if x.strip()]
    groups=defaultdict(list)
    for r in rows: groups[(r.get('arm'),r.get('model'),r.get('split'))].append(r)
    output=[]
    for key, rs in sorted(groups.items()):
        item={'arm':key[0],'model':key[1],'split':key[2], 'planned':a.planned,'recorded':len(rs),
              'failures':[r.get('run_id') for r in rs if r.get('status') not in ('ok','passed')],
              'metrics':{}}
        for name in ('quality','wall_seconds','input_tokens','output_tokens','cached_input_tokens','tool_calls','steps'):
            vals=[r.get(name) for r in rs if isinstance(r.get(name),(int,float))]
            item['metrics'][name]={'mean_all_recorded':statistics.fmean(vals) if vals else None,
                                   'n_available':len(vals),'n_missing':a.planned-len(vals)}
        output.append(item)
    s=json.dumps(output,ensure_ascii=False,indent=2)+'\n'
    if a.out: a.out.write_text(s)
    print(s,end='')
if __name__=='__main__': main()
