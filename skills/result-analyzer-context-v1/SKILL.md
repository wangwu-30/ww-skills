---
name: hpo-result-analyzer
description: Analyze every confirmed metric requirement and report one bounded display-only cycle snapshot with values or explicit query failure reasons.
---

# HPO Requirement Snapshot Analyzer

Consume the locked `hpo.result-analysis-context/v8` Task, Trial, Binding,
group snapshot, cadence and metric query anchor. Use the installed `queryMetric`
and `bytedcli` Skills for read-only queries. The confirmed objectives and
guardrails are the complete requirement authority. An exact identity may use
Libra or Metrics-FE; natural-language requirements may need interpretation.
Preserve user constraints, region, site, cohort, and success policy. Query
providers do not change the experiment provider or authorize lifecycle writes.

Return only `hpo.result-analysis-result/v6`, conforming to the Job's locked
output schema. Include `recommended_action`, `metric_query_status`,
`metric_query_summary`, `analysis`, and one `metric_snapshot` using
`hpo.analyzer-metric-snapshot/v2`. Set `source: agent_reported` and
`purpose: display_only`; copy Task/Trial/Binding/group/cadence identities from
the input and report a timezone-aware `collected_at`.

The snapshot's `requirements` contains exactly one item for every confirmed
`objective_ref` and `guardrail_ref`, carried as `requirement_ref`. Do not merge
two requirements merely because they query the same metric. For each item:

- Preserve the confirmed exact identity, or report the actual resolved identity
  for a natural-language requirement. Never claim that interpretation changes
  the frozen Task requirement.
- Record the actual read-only `query_method`, a known statistical `window`
  when available or an explicit unknown window, and every exact experiment
  group from the frozen group snapshot.
- For an observed group, include its finite value, value source, and available
  bounded statistics. Preserve zero as a valid value.
- Classify each requirement and group from its own actual identity-discovery
  and value-query receipts, even when several items share a report. Use
  `error` when discovery or a value query fails, including a timeout that
  leaves a unique identity unresolved. Use `ambiguous` only when the available
  evidence establishes multiple plausible identities or interpretations that
  cannot be distinguished. Use `missing` only after the exact identity is
  established and its value query succeeds but yields no usable observation.
  An unresolved identity or unattempted/failed value query is not `missing`.
  For each non-observed group, include a concrete nonempty `reason` and omit
  values/statistics. Unresolved identity and query method may be null. Do not
  invent a value or drop the requirement when the query cannot be completed.

Use overall `observed` only when every requirement/group is observed. Otherwise
report the actual unresolved/failure status and return `CONTINUE`. If statuses
differ, describe the mix in `metric_query_summary`; never recast individual
requirement/group statuses to match the overall status.
A `STOP_RECOMMENDED` advisory requires unambiguous observed metrics and explains
the objective/guardrail evidence; it never stops an experiment. Snapshots only
support display/history and are not Provider evidence or inputs to automatic
stop, Guardrail, Graph routing, Human Decision or lifecycle policy.

Keep sanitized query receipts in the Runtime trace. Never put raw tool output,
credentials, trace text, or undeclared fields into the bounded result. Never
perform Task, Provider, experiment or evidence writes.

Read the `history_scope` coverage before interpreting the supplied Analyzer reports.
The input contains up to `limit` recent valid completed reports from this
Trial, frozen at dispatch in cadence order. Each projection preserves the complete `analysis`
and `metric_query_summary` and references the full persisted Job result with
its digest. Raw metric snapshots remain in those complete persisted results.
Do not truncate or summarize the supplied report bodies. Earlier reports are
omitted from this input; there is no additional history retrieval entry point
in this release.

Use `history_scope` to distinguish recent evidence from the Trial's entire
execution. Do not infer what omitted reports said or present a recent pattern
as a conclusion about all earlier cycles.
