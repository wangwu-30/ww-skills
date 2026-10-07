---
name: hpo-metric-query
description: Resolve and query HPO metrics through exact read-only Provider commands while preserving the Task-owned objective and guardrail semantics.
---

# HPO Metric Query

Use this Skill only as the `queryMetric` dependency of an HPO Agent Job.  The
business primary Skill owns the Job's structured result; this dependency does
not add fields to that result and does not create a second platform evidence
record.

Read the immutable `task_context` carried by the current Agent Job.  Resolve
every requested observation against Provider metadata before querying values,
then explain the exact identity, scope, window, aggregation, baseline and any
missing or ambiguous data to the primary Skill.  Do not infer a metric from a
similar name or ID.

Use only read-only query commands documented in the references.  Never start,
pause, resume, stop, close or otherwise mutate an experiment.  Missing,
ambiguous or failed observations are analysis inputs; they are not permission
to recommend or execute a Provider lifecycle write.

See:

- [references/query-contract.md](references/query-contract.md)
- [references/libra.md](references/libra.md)
- [references/metrics-fe.md](references/metrics-fe.md)
