# Metrics-FE / Bosun read-only queries

Metrics-FE belongs to Byteplot/Bosun and has a separate namespace from Libra.
Start from the supplied service/page URL, canonical metric/expression, site,
region and explicit query constraints. The installed bytedcli APM Skill and
current help own supported syntax. This knowledge does not establish Libra
metric IDs, create-body metrics, a reference control-plane site or a target
experiment's creation site/regions.

## Source clues, URL and query scope

Plot URLs can contain a fragment with window, region and an expression between
semicolons, for example:

```text
https://<metrics-fe-host>/web/plot/metrics#now-1h,now,,,,,,,<region>,false,,;<expression>;0
```

Extract the actual expression, percent-decode URL-escaped bytes when necessary
and retain the original URL as provenance. Do not rewrite metric, aggregator,
tag keys or tag values. A `now-1h,now` source window can map to `--duration 1h`;
an explicit absolute window needs the appropriate supported time parameters.
A copied example does not specify a previously unspecified Task window.

These existing source examples are clues, not a complete site registry or
identity proof:

| Source host | Query site | Byteplot region example |
|---|---|---|
| `metrics-fe-ttp-us.tiktok-row.org` | `us-ttp` | `US-TTP` |
| `metrics-fe-i18n.tiktok-row.org` | `i18n-tt` | `Singapore-Central` |
| `metrics-fe.byted.org` | `cn` | use the actual plot region |

Check the source's actual selection and current bytedcli support. Site selects
the backend; `--region` does not switch sites. A region fragment alone does not
prove a page/backend region switch. Byteplot region is distinct from another
Metrics OpenAPI's `_region`. Preserve the caller's authorized network/profile;
a failed request does not authorize switching endpoints or credentials.

```bash
bytedcli --site <site> --json apm bosun query '<expression>' \
  --duration <lookback> --region <byteplot-region>
```

Pass the expression as one literal argv value, never interpolate it as shell
code. Raw OpenTSDB/ByteTSD expressions can include `p90:`, `p99:`, `pct90:`,
`store:` and `literal_or(...)` when supported by the current capability. Current
help also advertises full `q(...)` and multi-line Argos alert templates (direct
text or `@file`). Older recipes claiming all multi-line forms are unsupported
must not override that capability. Do not invent other statement forms or
substitute the separate `apm argos bosun query` VMP/PromQL interface.

Consult help for `--duration`, `--downsample`, `--region`, `--all-regions`,
`--end-time`, `--start-time` and `--at`. Downsample changes the sampling detail;
`--all-regions` stays within the selected site and must match the requested
scope. `--end-time` is a Unix-second UTC evaluation anchor: durations in `q(...)`
are relative to it, so retain that anchor for reproducibility. Range/explicit
point evaluation differs from a raw expression's lookback. CLI defaults are
query behavior to record, not new Task constraints. A broader window changes
cost and detail; choose it only within the user's allowed scope.

If identity is incomplete, source documentation and available instrumentation
code can connect the user meaning to an emitted metric, aggregator, tag keys
and config-derived values. Preserve exact source coordinates and the mapping;
a service name or config key alone is not a metric definition. Official
read-only metadata methods, where applicable to that source, include:

```bash
bytedcli --site <site> --json apm metric search --prefix '<metric-prefix>'
bytedcli --site <site> --json apm metric field-list --metric '<metric-name>'
bytedcli --site <site> --json apm metric tagk-list --metric '<metric-name>'
bytedcli --site <site> --json apm metric tagv-list --metric '<metric-name>' --tags '<tag-key>'
```

These discover native metric fields/tags; their availability does not make a
Bosun `store:` expression interchangeable with native `apm metric query` or a
Libra query. If the source lacks supported metadata, preserve the actual gap
and exact supplied expression instead of inventing another endpoint.

## Current experiment tags and group coverage

The metric name identifies service instrumentation, not a Libra experiment.
Use exact group tag values from the current observation context and frozen
version configuration, with an expression or instrumentation mapping that
proves the tag key. At execution, a confirmed group-specific value can be
expressed as `{{group.config.lsa_ltv_opt_traffic_exptag}}`; resolve it from
that current group's frozen candidate config for each group. Preserve the
original Metrics-FE URL exactly as provenance while separately recording its
resolved expression and query window. A config key such as
`lsa_ltv_opt_traffic_exptag` can supply a value but does not prove that the
emitted tag key is `abtest_tag`.

For an actual `abtest_tag` key, multiple exact values use
`literal_or(<control-tag>|<treatment-tag>)`, with `|` rather than commas.
When each group is queried separately, substitute that group's own tag rather
than reusing a reference experiment's value. Preserve case/underscores and all required groups. A missing control tag remains
missing; do not fabricate it or borrow a reference tag as current identity.
For reference discovery, reference tags can explain the source but remain
reference observations. Concrete service names such as
`ad.reranker.tiktok.lsa_longterm_value.disturb_coef`, or historical tag values,
are candidate source examples only: never use them as a default or frozen Task
value without matching evidence.

Check returned `Group` tags against requested groups. If the user rule applies
to any individual group, assess each series separately; averaging across groups
can hide a breach. Keep percentiles and mean reads distinct instead of treating
their numerical agreement as identity proof.

## Response shape, completeness and local statistics

A common successful series response has `data.Type = "series"` and
`data.Results[]`, each with a `Group` object and `Values` keyed by Unix seconds:

```json
{"status":"success","data":{"Type":"series","Results":[{"Group":{"abtest_tag":"<exact-tag>"},"Values":{"1785842730":0.0961,"1785843030":0.5351}}]}}
```

This is a shape example, not an execution receipt or fallback result. Inspect
the actual type, groups, numeric timestamps, values and scope. Empty `Results`,
an empty series, null/missing points, a legitimate zero, unsupported shape and
query failure are different outcomes. None silently proves a healthy guardrail.
Large responses use the shared guide's local file/completeness handling; keep
original captured bytes and the actual request/window separate from derived
statistics under the calling entry's existing evidence handling.

Per-series local statistics may include count, min, max, sample arithmetic
mean, total and earliest/latest sample time. Sort timestamps numerically and
record UTC and relevant local time zone. The two example points have count 2,
mean 0.3156 and total 0.6312. Arithmetic mean is unweighted: averaging minute
p90 values does not give the population p90, and summing samples is not an event
count or an integral. Do not fill absent buckets.

Preserve the complete series, including the latest potentially partial bucket.
If the allowed analysis method excludes an identified incomplete bucket,
record its time, reason and both full/included statistics. Do not discard an
anomalous last point to pass a threshold. The package includes the pure local
[statistics helper](scripts/metrics_fe_summarize.py). It reads an already
captured successful series response from a file or stdin, uses only the Python
standard library, performs no service/CLI calls and writes no files:

```bash
python3 scripts/metrics_fe_summarize.py --help
python3 scripts/metrics_fe_summarize.py result.json
python3 scripts/metrics_fe_summarize.py < result.json
```

Run from this guide's installed directory, or resolve the script relative to
that installation. Piping input alone does not retain an original receipt;
capture it first when the calling entry needs provenance. The helper keeps all
buckets, reports each series independently and does not supply statistical
policy. Exit 0 means local processing finished (including no data), 1 means
invalid/error input, and 2 means CLI usage error. Successful local parsing is
not Provider/query success or business acceptance. Report uncertain outcomes through the existing result;
statistics and this guide do not grant experiment lifecycle authority.
