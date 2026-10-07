# Query contract

The Job's persisted `task_context` is the sole Task input.  Keep these concerns
separate:

- identity: the Provider, query type and complete namespace actually queried;
- observation: flight, treatment/baseline IDs, time window and aggregation;
- policy: the objective or guardrail rule copied into this Job;
- outcome: observed, missing, ambiguous or error.

Require an exact Provider namespace.  A bare metric ID is not enough.  The
supported routing keys are:

| provider | query type | required query context (not an output-field list) |
|---|---|---|
| `libra` | `libra_metric_group` | site + flight + metric-group + metric |
| `libra` | `libra_ad_report` | site + flight + report + config-group + metric |
| `libra` | `libra_realtime_group` | site + flight + dashboard + realtime-group |
| `metrics_fe` | `metrics_fe_bosun` | site + region + canonical metric name |

When the requirement has only natural-language clues, use official read-only
discovery to establish this namespace. Preserve the original requirement and
record the resolved identity in the primary role's per-attempt result; do not
rewrite the Task or require a new approval merely to choose a legal query method.
If the identity is already exact, preserve its namespace and explicit scope.
The Job's output schema owns the representation: for realtime the resolved
identity contains site, dashboard_id and realtime_group_id with the schema's
fixed tags; flight and experiment groups come from the Job's observation context.
The selected metric key
and its metadata evidence belong in the existing query method and analysis
fields. Do not add undeclared metric fields to the closed identity object.

Provider metadata establishes identity. Report the exact query and
sanitized outcome to the primary Skill as analysis context.  Do not introduce
a machine receipt or a second top-level Job output: the primary Skill must
still return only the structured output locked by the Agent Job.

For `libra_ad_report`, the exact allowlisted dimensions, filters and boolean
query options are locked in the ad-report branch of `provider_metric_ref`.
They travel with the namespace because changing them changes the queried
metric population.  Preserve those bytes exactly; do not replace them with a
digest, synthesize defaults or move them into a second Task fact field.

Describe the attempted query, observation time, result/error and unresolved
items. Distinguish actual ambiguity between candidates from failed discovery,
and distinguish either from a resolved metric whose values are missing. An old
timeout does not prove the current identity is ambiguous or the current data
is empty. Use the existing result and Runtime trace; do not introduce another
receipt store, fixed command sequence or retry-count gate. None of these
uncertain states can be converted into a lifecycle action.
