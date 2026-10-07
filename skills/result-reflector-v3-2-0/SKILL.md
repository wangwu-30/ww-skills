---
name: hpo-result-reflector
description: Reflect on one authoritatively stopped fresh HPO Trial using full Analyzer result references while preserving advisory-only routing semantics.
---

# HPO Result Reflector

Use only `hpo.reflection-context/v4`: the immutable stopped-Trial snapshot,
persisted stop receipt, completed Analyzer Job result references, their bounded
v4 advisory projections, previous Reflector/Episode references, and the locked
read-only `queryMetric` and `bytedcli` dependencies supplied by the Agent Job.
Each Analyzer reference identifies the complete result under that Job's locked
output contract, `hpo.result-analysis-result/v6`, with per-requirement snapshots.
Preserve exact and natural-language requirements, query failure reasons
and Metrics-FE identities; absent observations never become invented values. A projection digest is not a substitute for the
complete Job result digest. Missing or conflicting lineage is not permission
to guess.

Return only the unchanged immutable `hpo.reflection-result/v2` with a
non-empty bounded `reflection` and `recommended_action` exactly
`CONTINUE_SEARCH` or `COMPLETE_RECOMMENDED`. Both values are advisory. The
concrete `CONTINUE_SEARCH|COMPLETE_TASK` choice belongs to the subsequent
deterministic or Human Gate. Do not copy an Analyzer metric snapshot into the
reflection output or claim that Agent-reported values are Provider-signed
evidence.

Never create, pause, resume, stop, or close an experiment; never mutate Task,
Trial, Episode, Insight, Decision, or terminal state; and never replace a
persisted fact with an Agent-authored observation.

Read the `analyzer_history_scope` coverage before interpreting the supplied Analyzer reports.
The input contains up to `limit` recent valid completed reports from this
Trial, frozen at dispatch in cadence order. Each projection preserves the complete `analysis`
and `metric_query_summary` and references the full persisted Job result with
its digest. Raw metric snapshots remain in those complete persisted results.
Do not truncate or summarize the supplied report bodies. Earlier reports are
omitted from this input; there is no additional history retrieval entry point
in this release.

Your `reflection` must state the supplied completed-report count and selected
cadence range, and the omitted count and last omitted cadence provided by
`analyzer_history_scope`. Limit conclusions to that stated coverage. Do not describe the recent window as the
entire Trial or infer what omitted reports said.
