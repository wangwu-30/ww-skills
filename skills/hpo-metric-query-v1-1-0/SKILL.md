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

The metric identity's `query_type` is routing authority:

- `libra_metric_group` uses only the locked metric-group identity and the
  documented metric-group query.
- `libra_ad_report` uses only `libra ad-report get`, the current Binding's
  explicit `site` and `flight_id`, and the locked
  `report_id/config_group_id/metric_id/query_scope` bytes. Pass every present
  boolean even when its value is `false`; never add an absent option. Do not
  translate this identity to metric-group or realtime.

Use `scripts/build_ad_report_command.py` to project the closed ad-report scope
to exact read-only argv. The script only prints argv and performs no Provider
I/O.

See:

- [references/query-contract.md](references/query-contract.md)
- [references/libra.md](references/libra.md)
- [references/metrics-fe.md](references/metrics-fe.md)
