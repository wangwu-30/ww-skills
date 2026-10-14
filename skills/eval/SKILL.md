---
name: eval
description: Evaluate or optimize an agent skill with fixed tasks, repeated paired runs, quality grading, latency/token/tool-call measurement, and controlled candidates. Use when asked to benchmark, speed up, compare, validate, or tune a skill.
---

# Skill evaluation

Use Anthropic's skill-creator paired benchmark pattern: freeze tasks and arms, execute repeated runs, preserve outputs and failures, grade outputs independently, then analyze trajectories. This skill supplies a provider-neutral protocol, plan validator, and aggregation script; it does not claim statistical significance from small synthetic suites.

## Brief and protocol freeze

Before running, record an explicit brief with all four fields:

- **Goal:** observable quality and efficiency objective.
- **Context:** skill/version, runtime, available tools, task environment.
- **Constraints:** allowed side effects, model/provider restrictions, isolation, budget.
- **Done when:** upfront quality gate and efficiency target, with handling for inconclusive results.

Freeze an eval set before changing the skill. Use separate `dev`, `val`, and `holdout` cases. Tune only on dev; use val to choose among candidates; open holdout once for final confirmation. Keep the same prompts, inputs, tool environment, and scoring rubric for all arms. Use at least 3 repetitions per case, arm, and model. Treat cases as the independent units; repetitions estimate variability and are not extra cases. Define the plan in JSON and run `scripts/validate_plan.py plan.json` before execution.

Define the gate before execution. Report the mean of the metric over all planned runs as the primary summary and list failures, invalid runs, timeouts, and missing data separately. Never drop failures or select best runs. For quality, define essential obligations and forbidden outcomes before outputs exist, and trace each obligation to an explicit task requirement or a named contract the task invokes. Do not grade an unstated deliverable as an essential obligation. Use a separate judge model, blind to arm labels and skill text; calibrate it on good/bad rubric examples that exercise every criterion before grading, and preserve disagreements or invalid grades. Human adjudication may be needed for consequential claims.

Run at least two non-OpenRouter models. Record per-model outcomes and explicitly flag cross-model reversals where an edit improves one model and harms another. Pin model IDs/configs, temperature, tools, runtime and skill-triggering method. Never select an OpenRouter model/provider.

## Isolation

For Codex, make a fresh temporary `HOME` for every run and set `CODEX_HOME=$HOME/.codex`; start with `codex exec --ignore-user-config`. Copy only the required auth file (normally `auth.json`) into `$CODEX_HOME`, install only the arm under test at `$HOME/.agents/skills/<skill-name>/SKILL.md`, and add only references the skill requires. Do not symlink broad config or skill directories. If a CLI needs credentials from HOME, identify the exact files it reads, symlink only those files, and record them. Keep per-task workspaces separate.

Before executing benchmark tasks, run `codex debug prompt-input` under the same temporary HOME/CODEX_HOME and inspect the rendered JSON. Confirm that no user-level or unrelated project skills are visible, only the tested version of the target skill is installed, and the tested skill's full body is present in model-visible input. A skill name/description/path alone is not the body. Codex may inject built-in `.system` skills even with a clean HOME. A benchmark may explicitly list skills that are invariant across both arms; pass those names to `scripts/isolate_codex.py` with repeated `--allowed-system-skill NAME` options, record their exact identities/content and presence in the audit, and allow only that list. Any other skill fails isolation. Do not treat `--ignore-user-config` as proof of isolation. Preserve the audit JSON and exact command/environment manifest.

The generic helper `scripts/isolate_codex.py` prepares this layout and performs the prompt-input audit. A failed audit is a hard stop; do not launch benchmark runs. Preserve required authentication without copying credentials into the workspace or logs. Record the isolation boundary and any unavoidable inherited state. If a clean environment cannot be made, disclose contamination risk and do not claim a controlled comparison.

## Controlled iteration

Change one thing at a time. Save immutable baseline and candidate bytes, hashes, task set, rubric and run config. Attribute each redundant step to the exact skill sentence or section that prompted it; cite the observed step/trajectory evidence. Do not label a step redundant merely because it is slow: explain why the task contract did not require it. Measure task end-to-end wall time and per-step time (model wait, tool execution, setup/other when available), input/output/cached tokens when available, and tool-call/agent-step counts. Never infer hidden reasoning duration from token counts.

For each run preserve: case/arm/repetition/model, status and failure, wall time, token counts, ordered steps with timestamps/durations/tool names, output, and provenance/config. Aggregate with `scripts/aggregate.py runs.jsonl --plan plan.json`, using the original pre-registered plan (`arms`, `models`, `tasks`, `repetitions`) or an existing per-run `planned.json` list. The plan supplies each arm/model/split denominator, including entirely unrecorded groups; do not substitute a hand-entered count. Means use every recorded numeric value, including values from failed runs; missing metrics and unrecorded planned runs are reported separately and never silently imputed. Do not treat a benchmark mean as proof of general quality or causal impact outside the frozen suite.

## Output

Deliver the frozen brief and gate, task split, arm hashes/diff, run-level data, aggregate table by model and split, failure list, quality grades/disagreements, cross-model reversals, per-step timing, sentence-to-step attribution, limitations, and a clear pass/fail/inconclusive decision. Keep holdout results separate from tuning decisions.
