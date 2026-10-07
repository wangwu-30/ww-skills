# Shared metric discovery and query knowledge

This guide supplies query knowledge to creation and analysis entry points.
Each entry owns its inputs, output schema, confirmation and interaction.
Use the installed bytedcli Skill, Provider references and current CLI help to
choose official read-only discovery, query and diagnosis. Examples are useful
entry points, not a whitelist, required sequence, call count or retry budget.

## Start from the meaning and available clues

Preserve the user's original metric meaning, source URL, reference experiment,
business path/name, site/region and explicit scope. A URL can identify a report,
template, dashboard or service without containing a complete metric identity.
Inspect the corresponding object and its contents; do not reduce discovery to
searching dashboard titles. A title miss, absent numeric ID or unattempted lookup
does not prove the metric is absent or ambiguous. A successful metadata search
with zero candidates establishes only that no match was found in its actual
searched scope; keep identity unresolved rather than calling it ambiguous or
reporting missing values before a value query.

Use relevant app/experiment metadata, template categories, report definitions,
dashboard groups and metrics, descriptions, formulas and filter definitions to
narrow candidates. Keep the metadata path that connects the original clue to
the selected metric. Similar names, translated titles and a bare ID are not
sufficient matches. Two real definitions that remain indistinguishable are an
ambiguity; explain the difference and follow the calling entry's interaction.

Keep five questions separate: what the metric means (formula, unit, attribution
and population); how its data is produced (freshness, coverage and backfill);
where it is displayed; which official query/computation can read it; and what
the result supports (values, completeness, comparisons and statistics).
Realtime, near-realtime and offline business labels describe data freshness,
not necessarily a query namespace. An advertising report can be near-realtime
without belonging to the user realtime-dashboard API. Follow the original
business path and definitions rather than choosing a surface from freshness.

## Establish the meaning of numbers

When a user's rule depends on an absolute value, inspect the selected metric's
definition and data-field lineage for currency, units and raw-versus-display
scale. Use existing knowledge only when it applies to that exact definition and
scope. Another metric's USD field, a GMV name or the magnitude of returned values
does not establish those facts. A formula without an explicit multiplier does
not prove its input or returned value has no conversion.

Keep unavailable business facts separate from an unresolved query identity or
missing observations. Creation returns a material business gap to its calling
entry for a specific user clarification before confirmation; a general risk
acceptance does not answer it. Clear business meaning with an unresolved ID
still follows that entry's existing natural-language path. Analysis retains the
gap and its evidence under its result contract. The current Analyzer may ask a
nonblocking question only for facts the user alone knows; it continues monitoring
and uses the answer as interpretation material. It cannot invent a conversion,
rewrite the frozen requirement or substitute an exact confirmed query identity.
An existing open question is not repeated. Tool failures, omitted query dates
and facts discoverable from the installed knowledge are diagnosis work, not
questions to the user.

When a metric is defined only for treatments, creation records
`applicable_groups: treatment_only` on that objective/guardrail requirement,
explains why the control has no definition and shows that scope for confirmation.
Otherwise the absent/`all` case covers every group. A failed control query alone
does not justify changing applicability during analysis. Query and report only
the frozen applicable groups, always using the current Trial's version IDs.

## Know which object you located

| Query surface | Object hierarchy | Observation anchors |
|---|---|---|
| Libra metric-group | template/bundle → category → metric-group → metric | site, current flight, group, metric, comparison groups |
| Libra ad-report | folder/tab → report → config-group → metric | site, current flight, report, config-group, metric, scope |
| Libra realtime | dashboard → realtime-group → metric | site, current flight, dashboard, realtime-group, selected metric, comparison groups |
| Metrics-FE/Bosun | service/page → canonical metric/expression → returned tag groups | site, region, metric/expression, tags, aggregation and window |

A template is a discovery directory, not a fourth Libra value namespace.
Dashboard ID, realtime-group ID, ordinary metric-group ID and ad-report
config-group ID are distinct. Metric IDs and dimension/value IDs must remain in
their actual namespace. One metric-group can appear in multiple categories;
category contents may show only a subset. Finding a group does not establish
that its target metric exists or has values.

Shared observation anchors describe queries, not new wire fields. The calling
entry's output schema determines where each fact is recorded. Do not extend a
closed identity object to hold all columns in this table.

## Separate identity from values

Metadata can establish an identity even when a new experiment has no data yet.
Creation can retain clear business meaning with unresolved identity and original
clues under its existing preview/confirmation rules. Analysis attempts resolution against the current
experiment and records the result without rewriting Task requirements.

An unresolved namespace hint can be an earlier Agent inference. Check its
source and re-examine contradictory definitions instead of repeating that
route indefinitely. Keep the original requirement and explicit constraints;
record a changed discovery method in the attempt. An exact user-specified
query identity cannot be substituted this way. Reused historical evidence
keeps its age and searched scope; identify what was actually read this time.

The current Analyzer's adopted resolution memory can identify the most recent
successful or failed attempt for a requirement outside the recent full report
window. Prefer a successful method while substituting current Trial/group/window
values; rediscover when the evidence changes or the method failed, explaining
why. A previous reading is historical evidence and not a fresh observation.
Coverage counters distinguish reduced memory from complete query facts; an
omitted item does not prove that a requirement was never checked. Only the
calling Analyzer's output contract determines which due requirements it checks
now, when it next runs and whether current observed evidence supports an advisory.

- `observed`: the located metric has usable observations for the required scope.
- `missing`: the metric is accurately located and its value query succeeded
  with a complete response, but contains no usable values; retain the request
  and any known reason, such as no values for the selected groups/window.
- `ambiguous`: actual candidates or interpretations cannot be distinguished by
  the available evidence; retain those candidates and the unresolved difference.
- `error`: discovery/query failed, including timeout, permissions, malformed
  response or unrecovered truncation; retain the actual failure.

A timeout is not evidence of multiple metrics or empty data. Old evidence keeps
its age and limits; an old error is not today's identity or availability fact.
A legitimate numeric zero is a value, not automatically missing. Distinguish
zero traffic, null values, absent rows and incomplete comparisons. Do not fill
missing values with zero or infer a verdict from them.

## Keep the actual scope

Preserve every explicit population/filter, direction, unit, baseline, window,
aggregation and statistical method. Optional unspecified constraints stay
unspecified; material business gaps follow the clarification distinction above.
Choose suitable methods within the remaining freedom and record the actual choice.
CLI defaults and reference examples do not become user requirements.
For a newly confirmed Libra identity, freeze the exact native bytedcli
subcommand, argument vector and any needed result-row selection rule inside
`native_query`. HPO treats that object as bounded opaque JSON; it does not parse
or normalize its command fields. Use placeholders for every value supplied by
the current Trial, each group's binding/configuration, or the requested window.
Examples are `{{trial.flight_id}}`, `{{group.version_id}}`,
`{{group.version_name}}`, `{{group.config.lsa_ltv_opt_traffic_exptag}}`,
`{{window.start_date}}`, `{{window.end_date}}`, `{{window.start}}` and
`{{window.end}}`. Resolve placeholders per group from the current Trial and
its frozen bindings, never from a reference flight. A known fixed business
filter such as `abtest_bingo=1` remains the string filter `1`; do not replace it
with a version ID. Consult the installed bytedcli Skill and latest command
help for flags and accepted forms, then record the complete executed command in
`query_method`. See [native Libra identities](libra.md#native-query-identities).

Changing a native argument or business key/value is part of the frozen query
bytes, not a request to add an HPO field. Do not treat the former typed
advertising scope or its `build_ad_report_command.py` argv builder as the new
identity contract. The helper may remain available for its existing callers.

Use the authorized site and existing identity/network configuration. Keep
site, Provider data region and time zone distinct. Resolve current experiment
version IDs from official metadata; names and reference experiment IDs do not
supply current groups. Record which group is the baseline and which direction
a relative difference compares. Do not reinterpret a filter value as a version
ID just because both are numeric.

Reference values may help understand an identity under a matched scope, but
cannot replace current Trial measurements. Cross-surface comparison needs
matching meaning, flight, groups, window and filters; similar values alone do
not establish identity or authorize changing an exact frozen query type.
Data freshness does not establish a query namespace, monitoring schedule or
statistical maturity. Query knowledge does not set workflow cadence, thresholds,
success rules or experiment lifecycle actions.

## Inspect completeness and filter execution

A successful HTTP/CLI envelope is not proof of a complete usable observation.
Check nested Provider status, parsing, truncation indicators, target metric and
the rows selected by the frozen `native_query` rule. Group queries may return
many metrics and comparisons; a single-metric flag or a short window may not
reduce the response. The selected row and comparison keys must be grounded in
the returned schema/metadata, not a “first row” shortcut.

Keep large responses in local files under the calling entry's existing handling
rules. Read their shape, status and only relevant metadata/values into context.
Redirection preserves what the tool emitted; it cannot recover data already
truncated by a wrapper. `--jq` is a local output projection, not a server filter.
Use supported pagination, a scoped query or a supported body-file/trace route
when appropriate, then verify completeness before extracting observations.
See [Libra response handling](libra.md#large-realtime-responses).

Preserve raw filter keys and values and verify that the intended population
actually reached execution. Labels can differ from backend keys. Inspect the
Provider's executed conditions/SQL when available; a request flag or HTTP 200
alone does not prove application. Unverified filtering cannot support a scoped
requirement. A changed value is not required when the metric already embeds the
filter, and zero values do not prove the filter was ignored.

Use sanitized requests/errors and existing evidence paths. Do not print full
raw result bodies, auth status payloads, cookies, tokens or auth headers into
analysis. A readonly query guide neither grants writes nor changes identity,
Runtime permissions, Task confirmation or Provider control authority.

Read the relevant surface details:

- [Libra discovery, values and diagnosis](libra.md)
- [Metrics-FE / Bosun](metrics-fe.md)
