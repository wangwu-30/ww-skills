---
name: hpo-result-analyzer
description: Check due confirmed metric requirements, reuse adopted resolution memory, and report bounded current observations, advice and user questions.
---

# HPO Requirement Snapshot Analyzer

Consume the locked `hpo.result-analysis-context/v9` Task, Trial, Binding,
group snapshot, cadence and metric query anchor. Use the installed `queryMetric`
and `bytedcli` Skills for read-only queries. The confirmed objectives and
guardrails are the complete requirement authority. An exact identity may use
Libra or Metrics-FE; natural-language requirements may need interpretation.
Preserve user constraints, region, site, cohort, and success policy. Query
providers do not change the experiment provider or authorize lifecycle writes.

Return only `hpo.result-analysis-result/v7`, conforming to the Job's locked
output schema. Include `recommended_action`, `metric_query_status`,
`metric_query_summary`, `analysis`, and one `metric_snapshot` using
`hpo.analyzer-metric-snapshot/v3`. Set `source: agent_reported` and
`purpose: display_only`; copy Task/Trial/Binding/group/cadence identities from
the input and report a timezone-aware `collected_at`.

Read each frozen requirement's original analysis/success/guardrail conditions,
prior observation times and readings to decide which requirements are due now.
The snapshot's `requirements` contains exactly one item for each requirement
checked in this cycle, carried as `requirement_ref`. Omit requirements not due
yet; omission is not a missing query. Check one or more requirements per cycle.
Every checked reference must belong to the frozen objectives/guardrails. Do not
merge two requirements merely because they query the same metric. For each item:

- Preserve the confirmed exact identity, or report the actual resolved identity
  for a natural-language requirement. Never claim that interpretation changes
  the frozen Task requirement.
- Record the actual read-only `query_method`, a known statistical `window`
  when available or an explicit unknown window, and the exact applicable
  experiment groups from the frozen group snapshot. `applicable_groups` is on
  the objective/guardrail requirement. Its absent/`all` case covers all groups;
  `treatment_only` covers treatments only. Exclude control rows from that
  requirement, its status and its stop evidence. Never substitute a reference
  experiment's group or version ID.
- For an observed group, include its finite value, value source, and available
  bounded statistics. Preserve zero as a valid value.
- For missing, ambiguous, or failed queries, use `missing`, `ambiguous`, or
  `error`, include a concrete nonempty `reason`, and omit values/statistics.
  Unresolved identity and query method may be null. Do not invent a value or
  drop a checked requirement when the query cannot be completed.

The overall `metric_query_status` summarizes this cycle's checked requirements;
use `observed` only when their applicable groups are all observed. Preserve every
missing, ambiguous or failed checked query even when another requirement can
support a stop recommendation.

For `STOP_RECOMMENDED`, optionally supply nonempty, unique `stop_evidence_refs`.
Every cited reference must be frozen, checked in this cycle, and observed in
every applicable group. Explain why those observations support stopping and
which other requirements still have gaps or were not checked this time. Old
readings alone cannot support a current stop citation. Without citations, all
frozen requirements and all their applicable groups must be checked and observed
in this cycle. The platform opens the existing human decision; the advice never
stops an experiment itself. Agent snapshots are not Provider-signed evidence and
grant no automatic control authority.

Optionally return positive `next_check_after_seconds` based on the next due
requirement, its conditions, history and data freshness. The program bounds the
wait after analysis completes by the platform minimum and the Task's confirmed
`analyzer_cadence_seconds` maximum. If omitted or this cycle fails, it uses that
maximum. Execution time adds to the actual interval; this does not promise that
each requirement is observed within the maximum wait. Leave timing thresholds
to the frozen input and public capability, rather than inventing defaults.

When a gap depends on a fact only the user knows, optionally return
`question_for_user: {question, requirement_refs}`. Ask the concrete business
question, such as which report/site represents a path or whether zero traffic is
expected. Missing date flags, tool/transport errors and facts discoverable with
the installed Skills are your diagnosis work; repair them or report `error`.
Finish the current report and continue monitoring while the user answers. If
`open_question` is present, do not emit another question; describe the remaining
wait in the analysis. Use subsequent `question_answers` as explanatory material,
preserving the user's original answer. The selection spans the whole Task,
including earlier Trials. Read `question_answers_coverage`: its
`latest_request_ref_by_requirement` maps each requirement to its latest answered
request. A question shared by several requirements is carried once with its
original references; apply it only to requirements whose current mapping names
that request. A newer answer replaces the older answer for that requirement.
`included_request_refs` and `omitted_request_refs` identify whole answers carried
or omitted for the input budget. An omitted answer is not a revoked fact or a
reason to use a superseded answer. Resolution memory also has explicit coverage;
do not assume an omitted original answer's method or identity is present there.
Answers remain complete in decision history and are bounded to 8000 characters.
They do not change the frozen requirement
or exact identity. An answer requiring a different confirmed identity or meaning
remains a gap requiring the user to change the requirement through its own flow.

Keep sanitized query receipts in the Runtime trace. Never put raw tool output,
credentials, trace text, or undeclared fields into the bounded result. Never
perform Task, Provider, experiment or evidence writes.

Read the `history_scope` coverage before interpreting the supplied Analyzer reports.
The input contains up to `limit` recent valid completed reports from this
Trial, frozen at dispatch in cadence order. Each projection preserves the complete `analysis`
and `metric_query_summary` and references the full persisted Job result with
its digest. Per-report `requirement_resolutions` may carry adopted query status,
reason, resolved identity, executed method, observation time/window and group
readings/statistics. `latest_requirement_resolutions` independently carries the
most recent checked report for each requirement; it can come from before these
three complete bodies. Prefer a previous successful resolution while preserving
the frozen identity and substituting current Trial/group/window values. Revisit
discovery when its evidence has changed or the previous attempt failed, and
explain the new method. Prior resolution is useful evidence, not a new frozen
identity. Use actual historical readings for consecutive-observation or
cumulative conditions; do not manufacture continuity from a summary.

Read `resolutions_coverage`: optional memory is reduced by removing methods,
then group readings, then whole items. The counters report how much was omitted;
the full persisted result remains unchanged. An absent reading is not zero.
Whole-item omission counts do not identify which frozen requirements were
previously checked, so do not infer that missing memory means never checked.
Do not truncate or summarize the supplied report bodies. Earlier reports are
omitted as full bodies; their most recent requirement facts may still appear in
the separate memory. There is no additional history retrieval entry point.

Question/answer records remain in the existing durable human-decision history.
The input coverage for a long accumulated question history is a separate bounded
handoff decision; do not claim the current input contains every earlier answer.

Use `history_scope` to distinguish recent evidence from the Trial's entire
execution. Do not infer what omitted reports said or present a recent pattern
as a conclusion about all earlier cycles.

For a confirmed Libra identity, use its frozen
`hpo.libra-native-metric-query/v1` bytes as the query authority:
`provider`, `query_type`, `site`, `display_name` and the opaque `native_query`.
Do not reconstruct an older dimensions/filters map or call its argv helper as
the identity contract. Consult the installed bytedcli Skill's latest help for
flags; use the exact native subcommand and arguments frozen for this metric.
Resolve `{{trial.flight_id}}` from the current Trial, then resolve
`{{group.version_id}}`, `{{group.version_name}}` and any
`{{group.config.<candidate path>}}` separately for each current group. Resolve
`{{window.start_date}}`, `{{window.end_date}}`, `{{window.start}}` or
`{{window.end}}` from the observation window. Never copy reference flight,
date or version values into a new Trial query. For example, the fixed filter
`abtest_bingo=1` remains the raw string filter `"1"`; it is neither a numeric
dimension nor a version ID substitution.

Use the frozen query's row-selection rule with complete response metadata to
select the target metric, the current group's row and the required comparison
key. Never use the first row as a shortcut. Verify the Provider actually
applied requested filters from execution evidence such as returned SQL/scope;
request echoes and HTTP success alone are insufficient. Record the complete
executed command, including substituted Trial/group/window values, in
`query_method`. Native report-link, table-name, metric-name and ID selectors
may differ by current provider capability; preserve the frozen choice instead
of forcing a common selector syntax. Missing window flags in a legacy helper do
not authorize omitting the actual observation dates.
