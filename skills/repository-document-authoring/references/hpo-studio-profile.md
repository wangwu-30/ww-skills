# HPO Studio documentation profile

Use this profile only inside the HPO Studio repository. Re-read the current target revision before relying on it; the paths define authorities, while a previously observed commit does not prove current state.

## Authority order

1. `AGENTS.md` is the complete project constraint entry point. Its “最终产物正文与投影” rule governs author behavior.
2. `docs/architecture/MAP.md` §13 owns reader/source/projection topology.
3. `docs/TARGET_STATE_0.3.md`, `docs/ACCEPTANCE.md`, and linked contract documents own product semantics and evidence status.
4. Executable Server capability, CLI help, schemas, repository scripts, and runtime readback own dynamic fields and commands.
5. `docs/MERGE_REQUEST_CHECKLIST.md` carries the author/reviewer Gate.
6. `docs/WIKI_PROJECTION.md` owns the HPO Studio Wiki mapping, navigation copy, receipt, shortcut migration, and publication acceptance.

Chat, external Wiki bodies, local `origin/*` caches, plans, test output, and agent reports are not substitutes for these authorities.

## Reader-owned sources

| Reader | Repository source | Owns | Defers to |
|---|---|---|---|
| Product evaluator | `docs/PLATFORM_POSITIONING.md` | Problem, audience, product boundary, success criteria | Architecture, target state, deployment evidence |
| Maintainer | `QUICKSTART.md` | Local sandbox, shared-deployment entry, minimum smoke, operations handoff | Shared deployment runbook, deployment docs/SOPs, scripts |
| Platform user | `docs/USER_GUIDE.md` | Task lifecycle, Human Gate, observation, result interpretation | Concepts, Server capability/readback, current UI/CLI |
| Agent | `docs/AGENT_ONBOARDING.md` | CLI login, Platform Skill installation, preflight | Installed `platform_skill/hpo-platform/SKILL.md`, CLI help, Server capability |
| Runtime onboarding Agent | `docs/TRAE_RUNTIME_ONBOARDING.md` | Local Trae Runtime registration and acceptance | Runtime guide, CLI help, Server Runtime identity/heartbeat |

Supporting pages such as `docs/ARCHITECTURE.md`, `docs/CONCEPTS.md`, `docs/CODEX_RUNTIME.md`, `docs/SKILL_FORMAT.md`, and `docs/SHARED_DEPLOYMENT_RUNBOOK.md` provide deeper authority. `README.md` is navigation and overview, not another runbook.

## HPO Studio Wiki rules

- The exact page mapping lives only in `docs/WIKI_PROJECTION.md`; do not reproduce a stale mapping in the Skill.
- Repository correction and review normally precede Wiki projection. If an owner authorizes early sync, freeze the exact reviewed source commit/tree and state that the later MR remains separate.
- Directory pages explain who should enter, what task they can complete, and which child page to read first. They do not copy child bodies.
- Projected pages are normal Wiki documents backed by repository sources. An external document without a repository source stays outside the projection write set.
- Dynamic product facts link to executable authorities rather than being frozen in Wiki prose.
- Every projected body carries source path, commit, source-byte SHA-256, and UTC sync time.
- Completion requires structural and content readback, not only write receipts.

## HPO Studio review record

For a document MR, record:

- the source path and affected external projections;
- the reader role, owned task, required inputs, mandatory path, stop conditions, and observable acceptance;
- the product authority checked and any gap between target and current behavior;
- the focused validation performed;
- the exact SHA/digest used for any external projection;
- anything deliberately left out of the operating body, such as development evidence or historical discussion.

Do not claim full Gate, MR Ready, deployed behavior, or publication merely because one of the others passed.
