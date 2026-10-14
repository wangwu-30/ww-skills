#!/usr/bin/env python3
"""Aggregate eval run records against their pre-registered plan."""
import argparse
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

def group_key(row):
    return row['arm'], row['model'], row['split']


def planned_counts(plan):
    """Accept the generic eval plan or an existing per-run planned.json list."""
    if isinstance(plan, list):
        return Counter(group_key(row) for row in plan)
    repetitions = plan['repetitions']
    if not isinstance(repetitions, int) or repetitions < 1:
        raise ValueError('plan repetitions must be a positive integer')
    splits = Counter(task['split'] for task in plan['tasks'])
    return Counter({(arm, model, split): count * repetitions
                    for arm in plan['arms'] for model in plan['models']
                    for split, count in splits.items()})


def aggregate(rows, plan):
    counts = planned_counts(plan)
    groups = defaultdict(list)
    for row in rows:
        key = group_key(row)
        if key not in counts:
            raise ValueError(f'recorded group is absent from plan: {key}')
        groups[key].append(row)
    output = []
    for key, planned in sorted(counts.items()):
        recorded = groups[key]
        if len(recorded) > planned:
            raise ValueError(f'recorded count exceeds plan for {key}: {len(recorded)} > {planned}')
        item = {'arm': key[0], 'model': key[1], 'split': key[2],
                'planned': planned, 'recorded': len(recorded),
                'n_missing': planned - len(recorded),
                'failures': [r.get('run_id') for r in recorded
                             if r.get('status') not in ('ok', 'passed', 'success')],
                'metrics': {}}
        for name in ('quality', 'wall_seconds', 'input_tokens', 'output_tokens',
                     'cached_input_tokens', 'tool_calls', 'steps'):
            values = [r.get(name) for r in recorded if isinstance(r.get(name), (int, float))]
            item['metrics'][name] = {
                'mean_all_recorded': statistics.fmean(values) if values else None,
                'n_available': len(values), 'n_missing': planned - len(values)}
        output.append(item)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('runs', type=Path, help='JSONL; one run record per line')
    parser.add_argument('--plan', type=Path, required=True,
                        help='pre-registered eval plan JSON or existing per-run planned.json')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.runs.read_text().splitlines() if line.strip()]
    result = aggregate(rows, json.loads(args.plan.read_text()))
    text = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.out:
        args.out.write_text(text)
    print(text, end='')


if __name__ == '__main__':
    main()
