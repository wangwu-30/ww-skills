# Query contract

The Job's persisted `task_context` is the sole Task input.  Keep these concerns
separate:

- identity: the Provider, query type and complete namespace actually queried;
- observation: flight, treatment/baseline IDs, time window and aggregation;
- policy: the objective or guardrail rule copied into this Job;
- outcome: observed, missing, ambiguous or error.

Require an exact Provider namespace.  A bare metric ID is not enough.  The
supported routing keys are:

| provider | query type | required namespace |
|---|---|---|
| `libra` | `libra_metric_group` | site + flight + metric-group + metric |
| `libra` | `libra_ad_report` | site + flight + report + config-group + metric |
| `libra` | `libra_realtime_group` | site + flight + dashboard + realtime-group |
| `metrics_fe` | `metrics_fe_bosun` | site + region + canonical metric name |

Provider metadata must be checked before values.  Report the exact query and
sanitized outcome to the primary Skill as analysis context.  Do not introduce
a machine receipt or a second top-level Job output: the primary Skill must
still return only the structured output locked by the Agent Job.

For `libra_ad_report`, the exact allowlisted dimensions, filters and boolean
query options are locked in the ad-report branch of `provider_metric_ref`.
They travel with the namespace because changing them changes the queried
metric population.  Preserve those bytes exactly; do not replace them with a
digest, synthesize defaults or move them into a second Task fact field.

Missing or ambiguous required data must be described explicitly.  It must not
be converted into a lifecycle action.
