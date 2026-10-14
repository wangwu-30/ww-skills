# Sources

- Anthropic, [Skill Creator](https://claude.com/plugins/skill-creator): official Claude Code plugin with Create, Eval, Improve and Benchmark modes; executor, grader, blind comparator, analyzer, repeated trigger tests, and variance aggregation. This is the closest direct starting point.
- Anthropic, [anthropics/skills skill-creator](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md): concrete run organization, paired with-skill/baseline execution, repeated trials, grading and analysis guidance.
- Anthropic, [Testing and iteration guide](https://claude.com/resources/guides/skills-testing-and-iteration): scripted repeatable tests, API evaluation suites, and skill-creator workflow.
- OpenAI, [Testing Agent Skills Systematically with Evals](https://developers.openai.com/blog/eval-skills): skills evaluated as lightweight end-to-end tests with recorded trajectories and explicit scoring.
- OpenAI, [openai/plugins plugin-eval evaluate-skill](https://github.com/openai/plugins/blob/main/plugins/plugin-eval/skills/evaluate-skill/SKILL.md): local skill analysis and benchmark scenario initialization for Codex.
- TiesPetersen, [SkillBenchmark](https://github.com/TiesPetersen/SkillBenchmark): community paired runs with a separate blind judge and confidence intervals; useful pattern, not an official standard.
- [SkillsBench](https://www.skillsbench.ai/): community benchmark emphasizing curated tasks, paired skill/no-skill evaluation and repeated trials.

## Starting point

The eval skill follows Anthropic's paired, repeated, artifact-preserving skill-creator loop and OpenAI's end-to-end trajectory framing. It adds dev/val/holdout separation, cross-model reversal checks, step-level latency/cause attribution, and explicit operational isolation requirements for controlled runs.
