---
name: hpo-result-analyzer
description: Analyze every confirmed metric requirement and report one bounded display-only cycle snapshot with values or explicit query failure reasons.
---

# HPO Requirement Snapshot Analyzer 5.1

Consume the locked `hpo.result-analysis-context/v7` Task, Trial, Binding,
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
- For missing, ambiguous, or failed queries, use `missing`, `ambiguous`, or
  `error`, include a concrete nonempty `reason`, and omit values/statistics.
  Unresolved identity and query method may be null. Do not invent a value or
  drop the requirement when the query cannot be completed.

Use overall `observed` only when every requirement/group is observed. Otherwise
report the unresolved/failure status and return `CONTINUE`. A
`STOP_RECOMMENDED` advisory requires unambiguous observed metrics and explains
the objective/guardrail evidence; it never stops an experiment. Snapshots only
support display/history and are not Provider evidence or inputs to automatic
stop, Guardrail, Graph routing, Human Decision or lifecycle policy.

Keep sanitized query receipts in the Runtime trace. Never put raw tool output,
credentials, trace text, or undeclared fields into the bounded result. Never
perform Task, Provider, experiment or evidence writes.
