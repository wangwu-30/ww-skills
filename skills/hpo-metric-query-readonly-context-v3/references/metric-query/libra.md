# Libra discovery, values and diagnosis

Use the authorized site and existing caller identity/network configuration.
Consult the installed bytedcli Libra Skill and current help for exact syntax.
These examples show alternative useful reads; select them from the supplied
clues and preserve the calling entry's frozen identity and scope.

## Ordinary metric-group and template discovery

```bash
bytedcli --json --site <site> libra experiment get --flight-id <flight_id>
bytedcli --json --site <site> libra experiment report --flight-id <flight_id>
bytedcli --json --site <site> libra metric-group template get --url <template_url>
bytedcli --json --site <site> libra metric-group template get --id <template_id> --app-id <app_id> --type conclusion
bytedcli --json --site <site> libra metric-group get --id <ordinary_metric_group_id>
```

Experiment metadata supplies actual versions, app, region and group/template
clues. Templates can use `normal` or `conclusion` structures; inspect their
actual category/group/metric contents instead of treating a wrong JSON path as
an empty directory. `experiment report` can provide `metric_meta` even when
another metadata route fails. Preserve the actual error of the failed route.
`metric-group get` here refers to ordinary report groups, not realtime groups.

```bash
bytedcli --json --site <site> libra experiment report   --flight-id <flight_id> --metric-group <metric_group_id>   --start <YYYY-MM-DD> --end <YYYY-MM-DD> --merge-type total
bytedcli --json --site <site> libra experiment report   --flight-id <flight_id> --metric-group <metric_group_id> --list-dimensions
```

Check definitions in `metric_meta.metrics` and group-local dimension/value
metadata before interpreting `report.merge_data`. Dimension selection uses
`<dimension_id>:<value_id[,value_id...]>`; the same semantic dimension can have
different IDs in different groups. Cross dimensions, trends and an explicit
baseline change output shape or comparison semantics; inspect those outputs.
The current help describes `--baseline`, `--data-caliber`, `--period-type`,
`--data-region` and `--force-show`. They do not override user constraints or
supply statistical policy. Wrong data-region routing can yield successful
responses with all-null values; investigate routing before asserting true lack
of data. An asynchronous query timeout is a query failure with continuation
information, not missing metric identity.

## Ad-report discovery and exact reads

A `/report/ad/<report_id>` URL identifies an ad-report, not an app or ordinary
metric-group. Keep report, config-group and metric separate. Metadata discovery
can retain UI names, descriptions, expressions, variables and available filters:

Advertising directories can contain folders, tabs and reports. Freshness words
alone do not select a surface; source evidence pointing to advertising report
navigation or a report route supports entering this family. Preserve the source
path even when the exact report is not yet known. Report discovery and known-report
framework reads are separate capabilities. Check current CLI help before assuming
a directory command exists.

In bytedcli 0.163.0 the official SDK preview request carries `flightId`,
`layerId`, `managerType` and `tagIdList`; it has no explicit app-ID argument.
Record those inputs, the flight's resolved app context and returned scope.
Empty tags do not establish a full directory; a readable known report may be
absent from the preview. Names
under a different folder or tab do not become equivalent because they mention
the same business. If the official tool lacks old/full-directory discovery,
record that capability gap or use an available official source/UI with the
existing identity. Do not change experiment tags, guess endpoints or declare
global absence from a preview. Read-only metadata can use an official SDK POST;
the operation's meaning, rather than HTTP method alone, determines whether it
is a read.

```bash
bytedcli --json --site <site> libra ad-report get --url '<ad_report_url>' --summary-only
```

Summary mode provides metadata/group names, not observations, and cannot be
combined with group/metric selectors. When resolving a business name, inspect
all metrics in every returned config group before claiming uniqueness. Retain
the one complete metadata entry that closes report, config-group, metric and
name together. Zero matches, multiple real matches and incomplete enumeration
are different unresolved facts; partial metadata cannot prove a unique identity.
A detail value response cannot repair a failed identity lookup. The calling
entry owns any expressly supported creation-stage user-confirmed identity path;
it does not establish an analysis observation.

Direct reads use
`--flight-id`, `--report-id`, `--group-id` and `--metric-id`. A closed HPO identity
must use its entry's existing projection contract; official CLI features do not
add new fields or filters to that contract.

Current CLI help treats non-structural URL query keys as raw string filters,
percent-decodes values and splits selections on `@`. Explicit `--filter` can
override URL values; numeric `--dimension` is explicit and not inferred from the
URL. Check current help rather than inheriting an older URL-parser rule.
Preserve every present boolean including `false`; do not add absent defaults.
Reference flight/dates and numeric query fields are clues with their actual
semantics, not automatic current-flight/group substitutes.

## Dynamic advertising scope and argv transport

The successor advertising scope has `dimensions: {key: [number, ...]}` and
`filters: {key: [string, ...]}` plus optional `balance_unequal_traffic`,
`data_group_style`, `multi_compare` and `versions_merge` booleans. These options
accept actual booleans; missing and explicit `false` are different. Explicit
null is invalid. A present map may be empty; each value array is non-empty. An empty map stays
explicit in the canonical scope and differs from absence, while both emit no
parameter for that container. Numeric
strings and booleans are not dimensions; numeric/boolean filter meanings stay
raw strings such as `"0"` or `"false"`. Numbers must be finite and safely
representable as JavaScript integers when integral. The complete scope is
bounded JSON (256 nodes and 16 KiB), without per-business-key quotas.

Use [the pure argv builder](scripts/build_ad_report_command.py) with the entry's
fixed site/flight/report/config-group/metric and complete scope. It emits one
`--dimension key=number@number` or `--filter key=string@string` argument pair per
key. New business keys, Unicode, interior spaces and structural-looking keys
such as `flight_id` or `token_type` are ordinary nested data. They never replace
routing, caller identity, selectors or standalone options. Do not flatten the
maps into a request body or execute their contents as shell text. Pass the
printed array to a process API as argv, not a joined shell command.

The official CLI splits on the first `=` and then on `@`, trims keys and
values, and drops empty selections. To preserve meaning, reject empty keys or
values, boundary whitespace, NUL, keys containing `=` and string values
containing `@` before execution. `=` within a value, literal percent text,
`+`, `&`, Unicode and interior whitespace remain raw argv data. CLI flags do
not URL-decode `%40`; escaping a literal `@` as `%40` changes its value. URL
query parsing separately percent-decodes and converts `+` to space before
splitting, so a source URL is not a lossless argv encoding for arbitrary values.

The scope preserves each array's raw order and duplicates; it does not merge
repeated keys. JSON input with repeated object keys is rejected by the builder
rather than silently choosing a last value. The official raw CLI merges and
deduplicates repeated filter selections and keeps the last repeated dimension
key, so inspect actual returned scope and population instead of inferring that
all transport details are Provider semantics. A key appearing in both maps is
rejected because the Provider's cross-container precedence is not established.
Do not recast a raw string filter as a numeric dimension or silently trim/split
an unrepresentable user selection.

Syntactic acceptance does not certify that a key exists in that report. Read
actual metric/report filter or dimension definitions, including units,
expressions, available values and population. Keep unknown or unsupported
metadata as a precise gap. Verify the executed query's scope and returned data;
a successful envelope alone does not prove filters were applied. Ordinary
metric-group selections, realtime dashboard configuration, deep-analysis bodies
and Metrics-FE expressions retain their own supported shapes; this scope does
not create a universal filter language for them.

Keep the report's selectable-filter catalogue and default template, the config
group's fixed predicates, and a known key's value enumeration separate. Their
requests may cover different scopes. Enumerated values do not establish that
the report accepts that key; a fixed group condition is not automatically a
user-selectable filter. A missing key in one catalogue does not prove global
absence. Preserve the actual definitions and raw value types, and verify how
the Provider applies the requested selection alongside the group conditions.
Client-produced `request_payload` or `filter_values` fields are request intent,
not a backend execution echo. If the query fails, retain its actual error;
do not compare it as zero or treat it as proof that the filter was ignored.

Inspect the actual response mode: a direct metric uses `group_data`, a full
report can use `group_data_list` with per-group failures, and summary uses
`ad_report`. For a direct result check `has_data`, `base_row`, `rows` and their
version IDs. A diff stored on `base_row` under a treatment key differs from a
reverse comparison stored on the treatment row. Keep the Provider's direction
and units; do not invent confidence or a significance threshold. Multiple raw
metric IDs, table/name mode and full-report reads have different capabilities;
consult help instead of imposing a fixed per-metric call count or sequence.

## Realtime hierarchy and filtering

This surface is for user realtime dashboards, not every metric whose data is
fresh. Establish the dashboard/group relationship from source definitions.
In bytedcli 0.163.0 the implicit flight directory uses app -1 despite reading
the flight's real app. An explicit `--list-dashboards --app-id` selects the app,
while `--dashboard-info` does not forward the supplied app in that version.
Inspect current tool behavior and returned scope; these limitations do not
prove metric absence or explain an unresolved advertising-report identity.

```bash
bytedcli --json --site <site> libra experiment realtime --flight-id <flight_id>
bytedcli --json --site <site> libra experiment realtime --list-dashboards --app-id <app_id>
bytedcli --json --site <site> libra experiment realtime --dashboard-info <dashboard_id> --show-sql
bytedcli --json --site <site> libra experiment realtime   --flight-id <flight_id> --metric-group <realtime_group_id>   --start '<YYYY-MM-DD HH:mm:ss>' --end '<YYYY-MM-DD HH:mm:ss>' --period-type h
```

The dashboard list is a directory, not proof of which dashboard matches the
business. Inspect `realtime_dashboard.metric_groups`, their metrics/definitions,
group SQL views and `filters`; a business metric may be nested under a dashboard
whose title does not contain its name. Use original links, business paths,
definitions, app/site and region to establish the match. The existence of a
ROW dashboard does not establish suitability for a different region.

Use the site's time zone for the actual window: official documentation uses
UTC for TikTok ROW/US and local CST for China. Preserve explicit windows and
record time zone/granularity. The native realtime command does not expose
`--data-region`, dashboard filters or a single-metric selector. It queries a
whole realtime group; unknown `metric_id`/`metric_ids` parameters do not prove
server-side narrowing. Inspect the metric's baseline/treatment rows and pairwise
diff keys in `realtime_report.merge_data` rather than selecting a first row.

When the requirement needs dashboard filters that native help cannot express,
current official `insearch get` supports a readonly plain GET for allowlisted
internal URLs using the caller's managed auth. It is a query method within the
existing authorization, not permission to change identity or use raw secrets.
The realtime data endpoint is:

```text
GET https://<authorized-libra-host>/datatester/report/api/v3/app/<app_id>/experiment/<flight_id>/realtime/dashboard/data
```

Its normal query keys include `flight_id`, `metric_group`, `period_type`,
`view_type=merge`, `start_date` and `end_date`. Dashboard `filters[].key` supplies
the exact backend filter key. The referenced implementation uses each key as a
URL parameter with an operator/value expression (such as `=,0`); percent-encode
keys and values from the actual definition rather than guessing from the label
or adding a generic `filters=` JSON parameter. Preserve selected enum values
and exact exclusions; substring exclusion can remove another real value.

Check the actual final response SQL for the requested conditions in `WHERE`.
If the filter is absent or cannot be verified, correct the query or report that
the scoped requirement cannot be judged. All-zero rows after verified filtering
do not prove the filter was ignored. Keep this concrete method's limitations
in the attempt; do not invent a Task query scope or fallback to unfiltered values.

## Deep-analysis definitions and supported computation

An advertising config group can also expose official deep-analysis datasource,
metric and dimension definitions. Use current `libra deep-analysis` help to
choose metadata reads; datasource lists can contain metric name/ID summaries,
while detail reads supply definitions and expressions. Search the complete
returned definitions, not a first-page display excerpt. Keep datasource IDs,
metric IDs, dimension catalogue IDs and detail ordinals distinct. A similar
GMV formula is not the requested metric without matching attribution, unit and
population. Missing unit/filter evidence remains unresolved.

Metadata reads do not calculate values or prove statistics are available.
Current query help requires a supported structured `--body-file`; URL input
is a locator and does not supply or override that body. Inspect supported
select/where/time shapes and reject unsupported grouping/dimension fields
instead of assuming arbitrary SQL or request fields are accepted. Preserve
the actual request and verify any intended filters in execution evidence.
Follow the official client's current authentication-validity checks: a success
envelope alone can still contain an invalid session or unusable result.
Do not export credentials or bypass a rejected shape/auth check.

For the calling HPO entry, definition evidence can guide resolution into an
existing supported identity. If the only usable value query cannot be faithfully
represented by its locked schema, record the precise contract/capability gap in
existing analysis fields. Do not invent a datasource union member, append query
fields to closed identities or relabel a deep-analysis result as another query.

## Large realtime responses

A realtime group can return all metrics, all version rows and pairwise diffs,
plus executed SQL. Reducing the time window need not reduce that structure.
Native Libra and `insearch get` have different envelopes: native JSON commonly
uses `data.realtime_report`; plain GET wraps the raw body under `data.body`
(which itself may contain the Provider `data`). Inspect status, `bodyKind`,
`truncated` and actual shape before choosing a JSON path. A null jq projection
alone is not proof of missing data.

The current `insearch get` plain-GET wrapper has its own response byte limit;
redirecting stdout or increasing `--http-body-limit` does not raise that limit.
For a truncated wrapper, official HTTP response-body trace can be a recovery
route using `--http-print b`, `--http-trace-file <local_file>` and an appropriate
`--http-body-limit <bytes>`, with the same readonly request. Choose the limit
from actual response size, not a copied fixed budget. This selects response
body tracing without selecting authentication headers. Keep trace and bodies
local; do not enable default header tracing or print complete bodies in context.

Trace is diagnostic output, may contain multiple responses, redaction and its
own `[truncated]` marker. Locate the intended successful data response, verify
that its complete JSON parses and Provider status is successful, and verify
that the metric, comparison rows and required SQL are present. Do not blindly
pick the last line or call a partial body complete. If recovery is unavailable
or incomplete, report a query error rather than metric missing. Extract only
the target metric/rows and relevant scope evidence into existing analysis;
retain full files under the calling entry's existing evidence rules.
