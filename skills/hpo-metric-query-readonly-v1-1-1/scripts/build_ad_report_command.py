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

_I18N_TT_SITE = "i18n-tt"


def _positive(value: int, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{label} must be positive")
    return value


def _validated_identity(payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
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
    return site, scope


def _command_prefix(site: str) -> list[str]:
    if site == _I18N_TT_SITE:
        return ["bytedcli", "--no-auto-upgrade"]
    return ["bytedcli"]


def build_argv(payload: dict[str, Any]) -> list[str]:
    site, scope = _validated_identity(payload)
    argv = [
        *_command_prefix(site),
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


def build_summary_argv(payload: dict[str, Any]) -> list[str]:
    # Reuse the detail builder's complete closed-scope validation. Summary mode
    # changes only the Provider selector shape; it does not loosen the Task-owned
    # identity accepted by this Skill.
    build_argv(payload)
    site = payload["site"]
    return [
        *_command_prefix(site),
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
        "--summary-only",
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request-file", type=Path, required=True)
    parser.add_argument("--summary-only", action="store_true")
    args = parser.parse_args()
    payload = json.loads(args.request_file.read_text(encoding="utf-8"))
    builder = build_summary_argv if args.summary_only else build_argv
    print(json.dumps(builder(payload), ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
