#!/usr/bin/env python3
"""Check that an eval plan declares the minimum pre-registered design."""
import json, sys
from pathlib import Path

SPLITS={'dev','val','holdout'}
def validate(x):
    e=[]
    brief=x.get('brief',{})
    for k in ('Goal','Context','Constraints','Done when'):
        if not (isinstance(brief.get(k),str) and brief[k].strip()): e.append(f'brief.{k} is required')
    gate=x.get('gate',{})
    if not (gate.get('quality') and gate.get('efficiency')): e.append('gate.quality and gate.efficiency must be defined upfront')
    models=x.get('models',[])
    if len(models)<2: e.append('at least two evaluated models are required')
    provider_config=json.dumps({'model_execution':x.get('model_execution',{}),'judge':x.get('judge',{})},ensure_ascii=False).lower()
    if any('openrouter' in str(m).lower() for m in models) or 'openrouter' in provider_config: e.append('OpenRouter models/providers are forbidden')
    if int(x.get('repetitions',0))<3: e.append('repetitions must be at least 3')
    judge=x.get('judge',{})
    if not judge.get('model') or str(judge.get('model')).lower() in [str(m).lower() for m in models]: e.append('judge must use a separate model')
    tasks=x.get('tasks',[])
    if not tasks: e.append('tasks must be non-empty')
    for split in SPLITS:
        if not any(t.get('split')==split for t in tasks): e.append(f'at least one task in {split} is required')
    ids=[t.get('id') for t in tasks]
    if len(ids)!=len(set(ids)): e.append('task IDs must be unique')
    for i,t in enumerate(tasks):
        if t.get('split') not in SPLITS: e.append(f'tasks[{i}].split must be dev, val, or holdout')
        if not (t.get('prompt') and t.get('rubric')): e.append(f'tasks[{i}] requires prompt and rubric')
    calibration=judge.get('calibration_cases',[])
    calibrated={c.get('task_id') for c in calibration if c.get('good') and c.get('bad') and c.get('bad_fail_indices')}
    missing_cal={t.get('id') for t in tasks if t.get('id') not in calibrated}
    if missing_cal: e.append('calibrated good/bad examples must exercise every task rubric; missing '+', '.join(sorted(str(i) for i in missing_cal)))
    arms=x.get('arms',[])
    if len(arms)<2 or len(arms)!=len(set(arms)): e.append('at least two distinct arms are required')
    if not x.get('one_change_at_a_time'): e.append('declare the single change under test')
    return e

if __name__=='__main__':
    if len(sys.argv)!=2: raise SystemExit('usage: validate_plan.py plan.json')
    try:
        plan=json.loads(Path(sys.argv[1]).read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f'cannot read valid plan JSON: {exc}')
    if not isinstance(plan,dict): raise SystemExit('plan root must be a JSON object')
    errors=validate(plan)
    print(json.dumps({'valid':not errors,'errors':errors},indent=2))
    raise SystemExit(bool(errors))
