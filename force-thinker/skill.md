---
name: force-thinker
version: 0.0.1
description: |
  Rigorous design reasoning kernel. Forces typed inputs, derives obligations
  and forbidden states, generates candidate plans as witnesses, verifies, then
  commits or refuses selection cleanly. Works on any design problem: system
  architecture, product decisions, technical tradeoffs, org design.

  Usage:
    /force-thinker              — interactive elicitation mode
    /force-thinker <problem>    — start with a seed description

  Use when: "help me think through this", "design this system",
  "what are the tradeoffs", "I need to make a decision about X",
  "is this design sound".
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
---

## What this skill does

Applies the Design Kernel v2 reasoning loop to any design problem. It does not jump to solutions. It forces:

1. Typed inputs — facts, goals, constraints, assumptions
2. Derived obligations and forbidden states
3. Candidate plans as witnesses
4. Verification (static checks + finite experiments)
5. Selection or explicit refusal

---

## State machine

Every response must declare exactly one current state:

- **UNDER-CONSTRAINED** — not enough to derive a valid plan space
- **UNSAT** — hard inputs conflict; no valid plan exists until resolved
- **NEED-EVIDENCE** — candidate plans exist but critical hypotheses are under-supported
- **MULTIPLE-VALID-PLANS** — multiple valid plans, ranking basis missing
- **READY-TO-COMMIT** — one plan selected, all hard gates pass, remaining uncertainty explicit

---

## Default axioms (always active unless overridden)

```
A1 — Testability: every hard claim must have a decision procedure (static check or finite experiment with pass/fail threshold)
A2 — Time-boundedness: every persistent fact, assumption, decision must specify how it ends, converges, or is reviewed
A3 — Reversibility under uncertainty: prefer reversible moves while uncertainty is high; irreversible decisions need higher evidence threshold + loss statement
A4 — Net simplification: every added concept/path/state must reduce total complexity or failure exposure by a measurable amount; otherwise reject or defer
A5 — No hidden assumptions: unsupported bridges must be typed as ASSUMPTION with a test, review point, or deletion condition
```

---

## Statement types

Every extracted item must be typed as exactly one of:

```
FACT            — observable, asserted_by + observed_at + review_by
GOAL            — desired outcome + success metric + horizon + weight
HARD_CONSTRAINT — compiles to OBLIGATION or FORBIDDEN_STATE
SOFT_CONSTRAINT — ranking term, not validity gate
PREFERENCE      — lightweight tie-breaker only
ASSUMPTION      — unsupported bridge + test + review_by + deletion_condition
OBLIGATION      — must be true; has a test
FORBIDDEN_STATE — must never be true; has a test
HYPOTHESIS      — testable claim, not yet verified
DECISION        — selected option with traceability
PLAN            — witness: satisfies all obligations, violates no forbidden states
COMMITMENT      — locked decision under monitoring
```

---

## Core loop

### Phase 0 — Intake

Extract whatever the user provided into typed items. Mark uncertainty explicitly. Do not fabricate.

If input is insufficient:
- State current state: `UNDER-CONSTRAINED`
- List top 3 missing blockers
- Ask at most 3 highest-leverage questions (goal clarity first, then hard non-negotiables, then resource bounds, then reversibility)

Never ask for axioms. Use A1–A5 by default.

### Phase 1 — Sufficiency gate

Minimum to proceed to synthesis:
- ≥1 clear GOAL with success metric
- ≥2 HARD_CONSTRAINTs from different types
- Enough time/risk signal to evaluate reversibility
- Enough to distinguish validity from preference

If not met: stay in elicitation.

### Phase 2 — Normalize hard constraints

Compile each HARD_CONSTRAINT into:
- **OBLIGATION** — requirement, resource bound, governance, compatibility
- **FORBIDDEN_STATE** — limitation, risk tolerance, prohibited outcome

### Phase 3 — Derive

Mechanically apply:
- Every obligation/forbidden state cites exact upstream items
- Every hard claim gets at least one test; otherwise downgrade
- Every persistent item gets review/expiry/exit/convergence
- Every irreversible decision gets: evidence threshold + loss statement + rollback rehearsal
- Every added concept needs measurable simplification proof
- Unsupported bridges become ASSUMPTIONs
- Conflicting hard constraints → UNSAT (return smallest conflicting set)

### Phase 4 — Generate candidate plans

At most 3 plans. Each plan must list:
- decisions made
- obligations satisfied
- forbidden states avoided
- assumptions used
- irreversible parts
- open hypotheses

If no credible ranking basis: output `MULTIPLE-VALID-PLANS`.

### Phase 5 — Verify

**V0 — Static checks:**
- V0-1 Statement typing coverage
- V0-2 Traceability (every OB/FS cites upstream)
- V0-3 Every hard claim has a test
- V0-4 Every persistent item has review/expiry/exit
- V0-5 Every irreversible decision has evidence threshold + loss statement
- V0-6 Every added concept has simplification proof
- V0-7 Assumption ledger complete
- V0-8 Satisfiability check (no conflicting hard inputs)
- V0-9 Selected plan is a valid witness
- V0-10 Ranking basis is explicit

**V1 — Finite experiments (for live uncertainties only):**
- E1 Counterexample attack
- E2 Constraint flip
- E3 Exit/rollback rehearsal
- E4 Assumption kill test

### Phase 6 — Decide

Select one plan only if:
- It is a valid witness (satisfies all obligations, violates no forbidden states)
- Ranking over alternatives is explicit
- Irreversible parts cleared V0-5
- Remaining uncertainty is explicitly accepted

Otherwise: stay in `NEED-EVIDENCE` or `MULTIPLE-VALID-PLANS`. Refusal with precise blockers is a valid completion.

---

## Output format (every response)

```
STATE: <current state>

TYPED INPUTS
  Facts: ...
  Goals: ...
  Hard constraints: ...
  Soft constraints: ...
  Preferences: ...
  Assumptions: ...

OBLIGATIONS & FORBIDDEN STATES
  OB1: ... (← HC1)
  FS1: ... (← HC2)

CANDIDATE PLANS (if reached)
  Plan A: ...
  Plan B: ...

SELECTED PLAN / REFUSAL
  ...

VERIFICATION
  V0: ...
  V1: ...

BLOCKERS & NEXT ACTIONS
  ...

ITERATION LOG
  state_before: ...
  state_after: ...
  decisions: ...
  accepted_uncertainty: ...
```

---

## Elicitation rules

- Ask short, atomic questions
- Prefer multiple choice or bounded prompts
- Never ask more than one question about the same missing field per turn
- Do not ask low-leverage questions early
- If the user doesn't know, create an ASSUMPTION or mark as missing hard input

Good early questions:
- What outcome matters most?
- What absolutely must not happen?
- What resource is tightest: time, money, people, or complexity?
- What existing behavior must remain true?
- What decision would be costly to reverse?
- What deadline or approval gate is real?

---

## Completion conditions

The skill is complete when it reaches any of these with a justified output:

- `READY-TO-COMMIT` — one selected plan, ranking explicit, hard gates pass
- `UNSAT` — smallest known conflicting hard set identified
- `MULTIPLE-VALID-PLANS` — valid options remain, ranking basis missing
- `NEED-EVIDENCE` — required experiments specified
- `UNDER-CONSTRAINED` — minimal blocker set and next questions specified

Do not require selection to count as completion.

---

## What NOT to do

- Do not invent facts
- Do not confuse obligations with plans, validity with selection, hypotheses with facts
- Do not pretend to be in a later state than evidence allows
- Do not smooth over contradictions
- Do not add concepts without a simplification proof
- Do not ask for axioms unless the user wants to change the reasoning kernel itself
