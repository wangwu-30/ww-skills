#!/usr/bin/env python3
"""Validate dynamic advertising parameters and print argv; no Provider I/O.

Exit 0 prints JSON argv. Invalid types, bounds or CLI encoding exit 2 before
execution. See ../libra.md. This released script does not import HPO Server.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping
import json
import math
from pathlib import Path
from typing import Any


_BOOL_OPTIONS = (
    "balance_unequal_traffic", "data_group_style", "multi_compare", "versions_merge"
)
_MAX_SAFE_INTEGER = 2**53 - 1
_MAX_JSON_NODES = 256
_MAX_JSON_BYTES = 16_384
# ECMAScript String.trim(), used by the evidenced official CLI parser.
_CLI_WHITESPACE = "\t\n\v\f\r \u00a0\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a\u2028\u2029\u202f\u205f\u3000\ufeff"


def _transport_text(value: Any, label: str, *, key: bool = False) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{label} must be a non-empty string")
    if "\x00" in value:
        raise ValueError(f"{label} must not contain NUL")
    if value.strip(_CLI_WHITESPACE) != value:
        raise ValueError(f"{label} boundary whitespace cannot be represented by the CLI")
    separator = "=" if key else "@"
    if separator in value:
        raise ValueError(f"{label} containing {separator!r} cannot be represented by the CLI")
    return value


def _number(value: Any, label: str) -> int | float:
    if type(value) not in (int, float):
        raise ValueError(f"{label} must be a number, not a boolean or coerced text")
    if type(value) is int:
        if abs(value) > _MAX_SAFE_INTEGER:
            raise ValueError(f"{label} exceeds the safe JavaScript integer range")
    elif not math.isfinite(value):
        raise ValueError(f"{label} must be finite")
    elif value.is_integer() and abs(value) > _MAX_SAFE_INTEGER:
        raise ValueError(f"{label} exceeds the safe JavaScript integer range")
    return value


def _validate_raw_scope(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError("query_scope must be an object")
    if not set(value) <= {"dimensions", "filters", *_BOOL_OPTIONS}:
        raise ValueError("query_scope contains unsupported fields")
    result: dict[str, Any] = {}
    nodes = 1
    for field, item in value.items():
        nodes += 1
        if field in _BOOL_OPTIONS:
            if type(item) is not bool:
                raise ValueError(f"{field} must be boolean; null is not absence")
            result[field] = item
            continue
        if not isinstance(item, Mapping):
            raise ValueError(f"{field} must be an object; null is not absence")
        container: dict[str, list[Any]] = {}
        for key, values in item.items():
            _transport_text(key, f"{field} key", key=True)
            if type(values) not in (list, tuple) or not values:
                raise ValueError(f"{field}[{key!r}] must be a non-empty array")
            nodes += 1 + len(values)
            if nodes > _MAX_JSON_NODES:
                raise ValueError(f"query_scope exceeds the {_MAX_JSON_NODES}-node limit")
            validate = _number if field == "dimensions" else _transport_text
            container[key] = [validate(v, f"{field}[{key!r}]") for v in values]
        result[field] = container
    if nodes > _MAX_JSON_NODES:
        raise ValueError(f"query_scope exceeds the {_MAX_JSON_NODES}-node limit")
    if set(result.get("dimensions", {})) & set(result.get("filters", {})):
        raise ValueError("a key cannot appear in both dimensions and filters")
    try:
        encoded = json.dumps(result, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")
    except (UnicodeError, TypeError, ValueError) as exc:
        raise ValueError("query_scope must contain valid UTF-8 JSON") from exc
    if len(encoded) > _MAX_JSON_BYTES:
        raise ValueError(f"query_scope exceeds the {_MAX_JSON_BYTES}-byte limit")
    return result


def _positive(value: Any, label: str) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{label} must be a positive integer")
    return _number(value, label)


def build_argv(payload: dict[str, Any]) -> list[str]:
    expected = {"site", "flight_id", "report_id", "config_group_id", "metric_id", "query_scope"}
    if not isinstance(payload, Mapping) or set(payload) != expected:
        raise ValueError("ad-report command payload fields differ")
    site = payload["site"]
    if type(site) is not str or not site or "\x00" in site:
        raise ValueError("site must be non-empty text without NUL")
    scope = _validate_raw_scope(payload["query_scope"])
    argv = [
        "bytedcli", "--json", "--site", site, "libra", "ad-report", "get",
        "--flight-id", str(_positive(payload["flight_id"], "flight_id")),
        "--report-id", str(_positive(payload["report_id"], "report_id")),
        "--group-id", str(_positive(payload["config_group_id"], "config_group_id")),
        "--metric-id", str(_positive(payload["metric_id"], "metric_id")),
    ]
    for key, values in scope.get("dimensions", {}).items():
        argv.extend(["--dimension", key + "=" + "@".join(map(str, values))])
    for key, values in scope.get("filters", {}).items():
        argv.extend(["--filter", key + "=" + "@".join(values)])
    for key in _BOOL_OPTIONS:
        if key in scope:
            argv.extend(["--" + key.replace("_", "-"), str(scope[key]).lower()])
    return argv


def _read_payload(path: Path) -> Any:
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key!r}")
            result[key] = value
        return result

    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request-file", type=Path, required=True,
                        help="JSON object: site, flight_id, report_id, config_group_id, metric_id, query_scope. Example: --request-file request.json")
    args = parser.parse_args()
    try:
        argv = build_argv(_read_payload(args.request_file))
    except (OSError, UnicodeError, TypeError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(argv, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
