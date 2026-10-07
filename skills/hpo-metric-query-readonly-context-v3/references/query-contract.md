# Analyzer query contract

The current Job's persisted Task context is the sole Task requirement input.
Its observation context supplies the current experiment and baseline/treatments;
the primary Skill's locked output schema owns the result representation.

Use [the shared guide](metric-query/GUIDE.md) for discovery, query semantics and
diagnosis. Keep requirement, resolved identity, actual observation method and
outcome separate. An initially unresolved requirement can resolve at runtime;
a new per-attempt method does not rewrite the frozen Task requirement.

For unresolved clues, trace namespace hints back to their source. Data freshness
or an earlier Agent inference does not bind a query surface; re-examine the
original business path and actual definitions. Preserve exact user identities
and constraints. Distinguish new reads from historical evidence with its age
and scope, and record a changed discovery method in existing analysis fields.
Metadata-only discovery, an incomplete preview and a successful query for a
different requirement do not resolve this requirement's identity or values.

For an exact `libra_ad_report` identity, use
[the existing pure argv builder](metric-query/scripts/build_ad_report_command.py)
with `site`, `flight_id`, `report_id`, `config_group_id`, `metric_id` and the
locked `query_scope`. This candidate supports the tagged
`hpo.libra-ad-report-metric-ref/v3` identity and dynamic query-scope generation.
Its `dimensions` map has non-empty numeric arrays and its `filters` map has
non-empty raw string arrays, with the same four optional boolean options.
A changed business key/value uses the same builder and package; no key allowlist
is maintained. Every present `false` and the supplied value order are retained;
absent options are not synthesized. Read [the transport rules](metric-query/libra.md#dynamic-advertising-scope-and-argv-transport)
before building argv. The builder validates types, bounds and faithful encoding,
prints argv and performs no Provider I/O. A syntactically valid key needs real
metadata and query evidence before it can establish population or observations.

The primary Skill and current Job select the immutable result/input generation;
this candidate does not reinterpret an older identity or expand another query
type. Do not copy new scope semantics into an old frozen Job. Keep site, flight,
report, group, metric and window outside the dynamic maps as structural selectors;
a filter named `flight_id` remains a filter and cannot replace the Job's flight.

For realtime, the closed resolved identity keeps the schema's fixed tags,
`site`, `dashboard_id` and `realtime_group_id`. The selected metric key, its
definition and matching evidence belong in existing method/analysis fields;
do not insert `metric_id` into this closed identity. Flight and comparison
groups come from the Job's observation context. Ordinary metric-group and
Metrics-FE identities likewise retain their existing schema representations.

Describe the attempted request, observation time, sanitized result/error and
remaining uncertainty in the existing analysis fields. Keep execution receipts
in normal Runtime trace. Identity evidence and value availability are separate:
actual indistinguishable candidates are `ambiguous`, failed discovery/query is
`error`, and an accurately located metric whose value query succeeded with a
complete response but no usable values is `missing`. Successful metadata with
zero matches leaves identity unresolved in that searched scope; it is not
ambiguity or a missing observation before a value query. None is
zero, success, a passed guardrail or permission to stop an experiment.
