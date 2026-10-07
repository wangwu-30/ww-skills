#!/usr/bin/env python3
"""Summarize a captured bytedcli Byteplot/Bosun series response, without I/O to a service.

Adapted from zhongken/agentic_hpo_online@dd326f8a8955d196f824d772d4184b9b718ed300,
graphs/hpo_agent_graph/agent/skills/metrics-fe-skill/summarize.py.
The statistics are unchanged; this packaged entry adds help and input validation.
See ../metrics-fe.md for provenance and interpretation limits.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone


def summarize_series(values: dict[str, float]) -> dict:
    ts_pairs = sorted((int(ts), float(v)) for ts, v in values.items())
    if not ts_pairs:
        return {"count": 0}
    nums = [v for _, v in ts_pairs]
    total = sum(nums)
    return {
        "count": len(nums),
        "min": min(nums),
        "max": max(nums),
        "avg": total / len(nums),
        "total": total,
        "first_ts": ts_pairs[0][0],
        "last_ts": ts_pairs[-1][0],
    }


def fmt_ts(ts: int) -> str:
    utc = datetime.fromtimestamp(ts, tz=timezone.utc)
    local = utc.astimezone()
    return f"{local.strftime('%Y-%m-%d %H:%M:%S %Z')} (utc={utc.strftime('%H:%M:%S')})"


def render(payload: object) -> str:
    if not isinstance(payload, dict) or payload.get("status") != "success":
        raise ValueError("expected a successful bytedcli JSON response; inspect the raw receipt")
    data = payload.get("data")
    if not isinstance(data, dict) or data.get("Type") != "series":
        raise ValueError("expected data.Type=series")
    results = data.get("Results")
    if not isinstance(results, list):
        raise ValueError("expected data.Results as a list")
    if not results:
        return "no series"

    lines = []
    for i, series in enumerate(results):
        if not isinstance(series, dict):
            raise ValueError(f"series {i}: expected an object")
        group = series.get("Group", {})
        values = series.get("Values")
        if not isinstance(group, dict) or not isinstance(values, dict):
            raise ValueError(f"series {i}: expected Group and Values objects")
        for ts, value in values.items():
            if not ts.isascii() or not ts.isdecimal():
                raise ValueError(f"series {i}: expected Unix-second timestamp keys")
            if isinstance(value, bool) or not isinstance(value, (int, float, str)):
                raise ValueError(f"series {i}: expected finite numeric samples")
            if not math.isfinite(float(value)):
                raise ValueError(f"series {i}: expected finite numeric samples")
        stats = summarize_series(values)
        group_str = ", ".join(f"{k}={v}" for k, v in group.items()) or "(no group)"
        lines.append(f"[{i}] {group_str}")
        if stats["count"] == 0:
            lines.append("    no data points")
            continue
        if not math.isfinite(stats["total"]):
            raise ValueError(f"series {i}: summary overflow")
        lines.extend([
            f"    count : {stats['count']}",
            f"    min   : {stats['min']:.6g}",
            f"    max   : {stats['max']:.6g}",
            f"    avg   : {stats['avg']:.6g}",
            f"    total : {stats['total']:.6g}",
            f"    first : {fmt_ts(stats['first_ts'])}",
            f"    last  : {fmt_ts(stats['last_ts'])}",
        ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Summarize a local bytedcli Bosun series JSON; never contacts a service.",
        epilog=("Examples: %(prog)s result.json; %(prog)s < result.json. "
                "Exit codes: 0 processed (including no data), 1 invalid/error input, "
                "2 usage error. Statistics do not authorize a business action."),
    )
    parser.add_argument("file", nargs="?", help="captured JSON file; omit or use - for stdin")
    args = parser.parse_args()
    try:
        if args.file is None or args.file == "-":
            payload = json.load(sys.stdin)
        else:
            with open(args.file, encoding="utf-8") as stream:
                payload = json.load(stream)
        summary = render(payload)
    except (OSError, UnicodeError, ValueError, TypeError, OverflowError) as exc:
        print(f"invalid metrics-fe input: {exc}", file=sys.stderr)
        return 1
    print(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
