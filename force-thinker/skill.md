---
name: force-thinker
version: 0.0.5
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

Applies the Design Kernel reasoning loop to any design problem. Does not jump to solutions. Forces:

1. Typed inputs — facts, goals, constraints, assumptions
2. Derived obligations and forbidden states
3. Candidate plans as witnesses
4. Verification (static checks + finite experiments)
5. Selection or explicit refusal

---

## Work modes

Every response declares exactly one mode at the top. Mode tells the user how much weight to place on the output.

- **DISCOVERY** — extracting and typing inputs; asking elicitation questions; everything here is scaffolding, may be revised
- **FORMALIZATION** — deriving obligations/forbidden states; generating candidate plans; this is structural and load-bearing
- **REVIEW** — running V0/V1 checks; selecting or refusing; producing the final iteration log

Mode transitions are explicit and announced. A single response stays in one mode. If the natural response crosses a boundary, stop at the boundary, announce the switch, and continue in the next turn.

**COMMENTARY is not a mode.** It is an inline annotation attached to any agent-invented abstraction. See Noun Budget below.

---

## Noun budget

Every response may introduce at most **2 agent-invented abstractions** (named concepts the agent coins that are not already present in the user's input, domain vocabulary, or established typed items).

User-supplied terms, domain nouns, plan labels (Plan A/B/C), and typed category names (GOAL, OB, FS...) do not count against the budget.

Each agent-invented abstraction must be immediately annotated inline:

```
[TERM: <name>]
  Replaces: <plain-language phrase this replaces>
  Why not existing: <why no current term covers it>
  Deletable if: <condition under which this folds back>
```

If a response would naturally require more than 2 new abstractions:
1. Pick the 2 highest-leverage ones, annotate them
2. Defer the rest, note explicitly what was deferred and why

Cognitive debt from unchecked abstraction proliferation is a design defect, not a feature.

---

## State machine

Every response also declares exactly one state:

- **UNDER-CONSTRAINED** — not enough to derive a valid plan space
- **UNSAT** — hard inputs conflict; no valid plan until resolved
- **NEED-EVIDENCE** — blocked from committing: either (a) candidate plans exist but critical hypotheses are under-supported, or (b) one or more OBs/FSs/ASSUMPTIONs lack a required test and cannot be verified
- **MULTIPLE-VALID-PLANS** — multiple valid plans, ranking basis missing
- **READY-TO-COMMIT** — one plan selected, all hard gates pass, remaining uncertainty explicit

---

## Default axioms (always active unless user overrides)

```
A1 — Testability
     Every hard claim must have a decision procedure:
     a static check or a finite experiment with a pass/fail threshold.
     Without one, the claim cannot be verified — it becomes a BLOCKER
     (stays in the validity model, blocks progress until a test is defined).

A2 — Time-boundedness
     Volatile items (assumptions, commitments, decisions under uncertainty)
     must specify how they end, converge, or are reviewed.
     Structural facts that do not change do not require expiry.

A3 — Reversibility under uncertainty
     Prefer reversible moves while uncertainty is high.
     Irreversible decisions require: higher evidence threshold + explicit loss statement.

A4 — Net simplification
     Every agent-invented abstraction must reduce total complexity or failure
     exposure by a measurable amount. Otherwise reject or defer.

A5 — No hidden assumptions
     Unsupported bridges must be typed as ASSUMPTION with a test,
     review point, or deletion condition.
```

---

## Type system

Two ledgers. Source types are extracted from user input. Derived types are computed from source types. Never mix them.

**Source ledger** (extracted during DISCOVERY):

```
FACT            — asserted_by + observed_at
                  review_by only if volatile (can change over time)
GOAL            — desired outcome + success metric + horizon + weight
HARD_CONSTRAINT — raw constraint; compiles to OB or FS in FORMALIZATION
SOFT_CONSTRAINT — ranking term; affects selection, not validity
PREFERENCE      — lightweight tie-breaker only
ASSUMPTION      — unsupported bridge
                  required: test + review_by + deletion_condition (all three)
                  an assumption without a test is itself a BLOCKER
```

**Derived ledger** (computed during FORMALIZATION):

```
OBLIGATION      — must be true; cites upstream HC or GOAL; has a test
FORBIDDEN_STATE — must never be true; cites upstream HC or GOAL; has a test
HYPOTHESIS      — testable claim not yet verified; has a proposed test
PLAN            — witness: satisfies all OBs, violates no FSs; lists assumptions used
DECISION        — selected option with traceability to OBs/FSs it resolves
                  if irreversible: evidence_threshold + loss_statement required
COMMITMENT      — locked DECISION under monitoring
```

HARD_CONSTRAINT is a source type only. It does not appear in the derived ledger. Once compiled to OB/FS it is superseded.

---

## Core loop

### Phase 0 — Intake (DISCOVERY)

Extract whatever the user provided into the source ledger. Mark uncertainty explicitly. Do not fabricate.

**Provisional synthesis rule:** If there is ≥1 GOAL with a success metric and ≥1 HARD_CONSTRAINT, proceed to FORMALIZATION with explicit uncertainty. Do not require a complete input block. Remaining unknowns become ASSUMPTIONs.

If even this minimum is not met: stay in DISCOVERY, list top 3 missing blockers, ask at most 3 questions. Goal clarity first, then hard non-negotiables, then resource bounds.

Never ask for axioms. Use A1–A5 by default.

### Phase 1 — Normalize (FORMALIZATION)

Compile each HARD_CONSTRAINT and GOAL into OB or FS:
- Requirement, resource bound, compatibility (from HC or GOAL) → OBLIGATION
- Prohibited outcome, risk tolerance (from HC or GOAL) → FORBIDDEN_STATE

Each OB/FS must cite its upstream HC or GOAL. A plan is valid only if it satisfies all OBs and violates no FSs — including those derived from GOALs. This is the only validity gate.

### Phase 2 — Derive (FORMALIZATION)

Mechanically:
- Every OB/FS gets at least one test (A1); if no test can be defined, the OB/FS is a BLOCKER — do not downgrade it to HYPOTHESIS (that would silently remove it from the validity model); instead stay in NEED-EVIDENCE until a test is specified
- Every ASSUMPTION gets test + review_by + deletion_condition (A1, A2, A5); missing any of the three is a BLOCKER
- Every irreversible decision gets: evidence threshold + loss statement (A3)
- Every agent-invented abstraction gets a noun budget annotation (A4)
- Conflicting hard constraints → UNSAT; return smallest conflicting set

### Phase 3 — Generate candidate plans (FORMALIZATION)

At most 3 plans. Each plan is a witness:
- OBs satisfied (list each)
- FSs avoided (list each)
- ASSUMPTIONs used
- Irreversible parts + loss statement
- Open HYPOTHESEs

If no credible ranking basis: state MULTIPLE-VALID-PLANS.

**Ranking:** When multiple valid plans exist, rank using: (1) soft constraints and preferences as scoring terms, (2) dominance — if Plan A satisfies all OBs Plan B satisfies and avoids all FSs Plan B avoids, and additionally satisfies more or takes on less irreversibility, Plan A dominates. State the ranking basis explicitly. If ranking is genuinely tied, say so.

### Phase 4 — Verify (REVIEW)

**V0 — Static checks** (each reported as PASS / FAIL / SKIP + one-line evidence):

```
V0-1  Source ledger: all items typed, no fabricated metadata
V0-2  Derived ledger: every OB/FS cites upstream source item
V0-3  Every OB/FS has a test (A1)
V0-4  Every ASSUMPTION has review_by + deletion_condition (A2, A5)
V0-5  Every irreversible decision has evidence threshold + loss statement (A3)
V0-6  Every agent-invented abstraction has noun budget annotation (A4)
V0-7  Satisfiability: no conflicting hard inputs
V0-8  [READY-TO-COMMIT only] Selected plan satisfies all OBs, violates no FSs
V0-9  [READY-TO-COMMIT only] Ranking basis is explicit
```

V0-8 and V0-9 are SKIP when the final state is not READY-TO-COMMIT.

**V1 — Finite experiments** (only for live uncertainties):

V1-E1 and V1-E3 apply only when state is READY-TO-COMMIT (they reference the selected plan).
V1-E2 and V1-E4 apply in any state where candidate plans exist.

```
E1  [READY-TO-COMMIT only] Counterexample attack: can the selected plan fail under a plausible scenario?
E2  Constraint flip: if the tightest constraint were relaxed, would ranking change?
E3  [READY-TO-COMMIT only] Exit/rollback rehearsal: if the irreversible commitment proves wrong, what is the recovery path?
E4  Assumption kill: if the highest-risk assumption is false, does any candidate plan survive?
```

### Phase 5 — Decide (REVIEW)

Select one plan only if:
- Valid witness (all OBs satisfied, no FSs violated)
- Ranking over alternatives is explicit (dominance or scored)
- Irreversible parts cleared V0-5
- Remaining uncertainty explicitly accepted

Otherwise: stay in NEED-EVIDENCE or MULTIPLE-VALID-PLANS. Refusal with precise blockers is a valid completion.

---

## Output format

**DISCOVERY response** (lightweight):

```
MODE: DISCOVERY
STATE: <state>

SOURCE LEDGER (extracted so far)
  Facts: ...
  Goals: ...
  Hard constraints: ...
  Soft constraints: ...
  Preferences: ...
  Assumptions: ...

BLOCKERS
  B1: ...

QUESTIONS (≤3)
  Q1: ...
```

**FORMALIZATION response**:

```
MODE: FORMALIZATION
STATE: <state>

[NOUN BUDGET — only if agent-invented abstractions introduced]
  [TERM: <name>] Replaces: ... Why not existing: ... Deletable if: ...

SOURCE LEDGER (updated)
  ...

DERIVED LEDGER
  OB1: ... (← HC1) | test: ...
  FS1: ... (← HC2) | test: ...

CANDIDATE PLANS
  Plan A: OBs satisfied: ... | FSs avoided: ... | Assumptions: ... | Irreversible: ... | Evidence threshold: ... | Loss statement: ...
  Plan B: ...

RANKING
  ...

BLOCKERS & NEXT ACTIONS
  ...
```

**REVIEW response** (full):

```
MODE: REVIEW
STATE: <state>

VERIFICATION
  V0-1: PASS/FAIL/SKIP — <evidence>
  ...
  V1-E1: <attack scenario and result>
  ...

SELECTED PLAN / REFUSAL
  ...

REMAINING UNCERTAINTY ACCEPTED
  ...

ITERATION LOG
  state_before: ...
  state_after: ...
  decisions: ...
  accepted_uncertainty: ...
```

---

## Completion conditions

The skill is complete when it reaches any of these with a justified output:

- `READY-TO-COMMIT` — one plan selected, ranking explicit, hard gates pass
- `UNSAT` — smallest conflicting hard set identified
- `MULTIPLE-VALID-PLANS` — valid options remain, ranking basis missing
- `NEED-EVIDENCE` — required experiments specified
- `UNDER-CONSTRAINED` — minimal blocker set and next questions specified

Refusal with precise blockers is a valid completion. Do not require selection.

---

## What NOT to do

- Do not fabricate metadata (use `unknown` for missing fields in DISCOVERY)
- Do not mix source types and derived types in the same ledger
- Do not apply expiry/review_by to structural facts that cannot change
- Do not count user-supplied terms or domain nouns against the noun budget
- Do not span more than one mode in a single response
- Do not treat DISCOVERY output as structural — it is scaffolding until confirmed
- Do not invent facts; unsupported bridges become ASSUMPTIONs
- Do not confuse obligations with plans, validity with selection, hypotheses with facts
- Do not pretend to be in a later state than the evidence allows
- Do not run V0-8/V0-9 when the final state is not READY-TO-COMMIT
