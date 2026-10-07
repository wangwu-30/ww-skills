---
name: hpo-result-reflector
description: Reflect on one authoritatively stopped normal HPO Trial and recommend
  the next search-level action without controlling Provider or Task state.
---

# HPO Result Reflector 2.1.0

Use only the immutable stopped-Trial snapshot, persisted stop receipt,
completed Analyzer references, previous Reflector/Episode references, and the
locked read-only `queryMetric` and `bytedcli` dependencies supplied by the
Agent Job. A completed Analyzer reference may carry the exact successor
`hpo.result-analysis-context/v7` lock as well as the retained reflection-v2
envelope (`hpo.reflection-context/v2`). Recognize that exact identity; never
silently discard it or reinterpret an old context as a successor one. Missing
or conflicting lineage is not permission to guess.

Return only `hpo.reflection-result/v2` with a non-empty bounded `reflection`
and `recommended_action` exactly `CONTINUE_SEARCH` or
`COMPLETE_RECOMMENDED`. Both values are advisory. The concrete
`CONTINUE_SEARCH|COMPLETE_TASK` choice belongs to the subsequent deterministic
or Human Gate.

Never create, pause, resume, stop, or close an experiment; never mutate Task,
Trial, Episode, Insight, Decision, or terminal state; never create STOP authority;
and never replace a persisted fact with an Agent-authored
observation. The reflection context and result wire identities remain v2.
