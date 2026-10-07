#!/usr/bin/env python3
"""Project one closed ad-report query identity to argv without executing it."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


_BOOL_FLAGS = (
    "balance_unequal_traffic",
    "data_group_style",
    "multi_compare",
    "versions_merge",
)


def _positive(value: int, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{label} must be positive")
    return value


def build_argv(payload: dict[str, Any]) -> list[str]:
    expected = {
        "site",
        "flight_id",
        "report_id",
        "config_group_id",
        "metric_id",
        "query_scope",
    }
    if set(payload) != expected:
        raise ValueError("ad-report command payload fields differ")
    site = payload["site"]
    if not isinstance(site, str) or not site:
        raise ValueError("site must be non-empty")
    scope = payload["query_scope"]
    if not isinstance(scope, dict):
        raise ValueError("query_scope must be an object")
    allowed = {"dimensions", "filters", *_BOOL_FLAGS}
    if not set(scope) <= allowed or any(value is None for value in scope.values()):
        raise ValueError("query_scope contains unsupported or null fields")
    argv = [
        "bytedcli",
        "--json",
        "--site",
        site,
        "libra",
        "ad-report",
        "get",
        "--flight-id",
        str(_positive(payload["flight_id"], "flight_id")),
        "--report-id",
        str(_positive(payload["report_id"], "report_id")),
        "--group-id",
        str(_positive(payload["config_group_id"], "config_group_id")),
        "--metric-id",
        str(_positive(payload["metric_id"], "metric_id")),
    ]
    dimensions = scope.get("dimensions")
    if dimensions is not None:
        if not isinstance(dimensions, dict) or set(dimensions) != {"abtest_bingo"}:
            raise ValueError("unsupported ad-report dimensions")
        values = dimensions["abtest_bingo"]
        if not isinstance(values, list) or not values or any(
            isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            for value in values
        ):
            raise ValueError("abtest_bingo values must be numeric")
        argv.extend(["--dimension", "abtest_bingo=" + "@".join(map(str, values))])
    filters = scope.get("filters")
    if filters is not None:
        if not isinstance(filters, dict) or set(filters) != {"external_action_en"}:
            raise ValueError("unsupported ad-report filters")
        values = filters["external_action_en"]
        if not isinstance(values, list) or not values or any(
            not isinstance(value, str) or not value for value in values
        ):
            raise ValueError("external_action_en values must be strings")
        argv.extend(["--filter", "external_action_en=" + "@".join(values)])
    for key in _BOOL_FLAGS:
        if key not in scope:
            continue
        value = scope[key]
        if not isinstance(value, bool):
            raise ValueError(f"{key} must be boolean")
        argv.extend(["--" + key.replace("_", "-"), str(value).lower()])
    return argv


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request-file", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.request_file.read_text(encoding="utf-8"))
    print(json.dumps(build_argv(payload), ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
