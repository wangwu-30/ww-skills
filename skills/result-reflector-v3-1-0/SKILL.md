---
name: hpo-result-reflector
description: Reflect on one authoritatively stopped fresh HPO Trial using full Analyzer result references while preserving advisory-only routing semantics.
---

# HPO Result Reflector 3.1.0

Use only `hpo.reflection-context/v3`: the immutable stopped-Trial snapshot,
persisted stop receipt, completed Analyzer Job result references, their bounded
v4 advisory projections, previous Reflector/Episode references, and the locked
read-only `queryMetric` and `bytedcli` dependencies supplied by the Agent Job.
Each Analyzer reference identifies the complete result under that Job's locked
output contract (v5 metric snapshots or v6 per-requirement snapshots).
For v6, preserve exact and natural-language requirements, query failure reasons
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
