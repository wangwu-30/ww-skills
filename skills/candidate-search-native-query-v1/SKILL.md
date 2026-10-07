---
name: hpo-candidate-search
description: Generate action-free treatment configurations for one normal HPO Candidate
  from the locked Task requirements and control snapshot.
---

# HPO Candidate Search

Use only the immutable `hpo.candidate-search-input/v7` supplied by the Agent
Job. The Task-owned requirement roots, user constraints, objective focus, and
success-policy state are inputs to treatment selection, not values this Skill
may reinterpret. Preserve every exact identity and scope; preserve accepted
natural language and deliberately unspecified focus without adding a primary
objective, a metric ID, a numerical threshold, a query method, or a success
claim. `explicitly_none` means no success condition is requested.

Return exactly the injected `hpo.candidate-search-result/v8` contract. Choose
the actual treatment count within the locked `min_treatment_count` and
`max_treatment_count` interval. The top-level object contains only:

- `schema_version`;
- a non-empty `treatments` array whose entries contain only a complete
  JSON-object `config`; and
- the required bounded `summary` string.

Do not emit `action`, `candidate`, `questions`, `control`, `REQUEST_HUMAN`, or
`NO_OP`. This Skill never owns the control group: the immutable Task control
snapshot carried by the Agent Job is combined exactly once by the Job-to-Trial
normalizer after successful completion.

Produce every treatment config as a complete JSON object. Never return
parameter patches or omit unchanged fields expecting the platform to fill
them. Do not derive a shape from historical treatments. Do not emit template
or parameter-binding authority, user parameter ranges, control bytes, or
platform identities. Do not create or control an experiment, mutate Task
state, choose a route, query a Provider, or report an observation.

When `output_validation_feedback` is present, it is the bounded receipt from
the immediately preceding attempt in the same valid claim. Correct only the
reported structural failure and still return the exact v8 shape.

Advertising query scope carries Provider parameter keys as data inside the
confirmed dimensions and filters maps. Preserve their numeric/raw-string types,
array order, empty containers, and the distinction between absent options and
explicit false. A new parameter name does not permit changing the confirmed
report, metric, site, population, window or comparison. Do not substitute a
nearby metric or silently remove a filter to obtain a value.

When `recent_reflection` is present, use the adopted previous round’s full
reflection and suggested improvements to choose the next treatments. Its
`outer_loop` and Job/result references identify the source. It is advisory:
retain confirmed Task requirements, control bytes and search constraints; do
not turn the Reflector recommendation into a route or a success claim.
