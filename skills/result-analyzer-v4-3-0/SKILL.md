---
name: hpo-result-analyzer
description: Analyze one normal HPO experiment through locked read-only queryMetric
  and bytedcli Skills and return a closed advisory.
---

# HPO Result Analyzer 4.3.0

Use only the immutable `hpo.result-analysis-context/v7`, Binding/group
snapshot, and observation policy supplied by the Agent Job. Its complete
Task-owned objective, guardrail, success-policy, acceptance, exact identity,
natural-language, and constraint bytes are the analysis requirements. Do not
replace an unresolved requirement with a guessed identity or value, promote an
objective to primary, add a threshold, or treat `explicitly_none` as an
implicit success test.

Where the user left the analysis method, comparison, aggregation or observation
window unspecified, choose and explain a suitable method for this attempt
within the locked read-only query capability. Keep that choice in the analysis
and query evidence; it must not become a new persisted Task constraint or an
invented measurement. Explicit user constraints always take precedence.

Use the locked `queryMetric` and `bytedcli` Skills. `queryMetric@1.1.0`
supports the closed `metrics_fe_bosun` query namespace as well as its existing
Libra routes; preserve the supplied scope and constraints. A real observation
requires the runtime-captured request, exit status, sanitized response
reference/digest, and observation time in this same Job. Skill prose alone is
not query evidence.

Return only `hpo.result-analysis-result/v4` with `recommended_action`,
`metric_query_status`, `metric_query_summary`, and `analysis`.
`metric_query_status` is exactly `observed`, `missing`, `ambiguous`, or
`error`; use the latter three instead of guessing and return `CONTINUE`.
`recommended_action` is exactly `CONTINUE` or `STOP_RECOMMENDED`. A stop
recommendation is allowed only for unambiguous observed metrics, is advisory,
and must explain the objective/guardrail evidence; it does not stop the
experiment or create any new STOP authority.

Never perform Provider or Task writes. Preserve the exact query receipts/tool
traces in the same Job and do not create a second monitoring or result record.
