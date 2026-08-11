---
name: requirement-frame
description: Frame an explicitly admitted non-trivial requirement before research, proposal, or implementation. Use only when invoked by `$requirement-workflow-router` or explicitly requested for the framing stage. Establish the desired outcome, observable success, scope, constraints, truth surfaces, authority boundaries, unknowns, and research decision without asking for discoverable project or public facts.
---

# Requirement Frame

Build the smallest complete frame that prevents later work from solving the wrong problem.

## Method

1. Read the controller-provided goal and bounded context first.
2. Separate the user's desired outcome from an implementation idea or inherited plan.
3. Resolve project and public facts yourself. Ask only when a fact exists only in the user's private context and would change the valid solution set.
4. Ask at most three questions and return them to the controller as one batch. If work can continue safely, state a bounded assumption instead.
5. Decide whether the task needs deep research, focused repository verification, public research, a limited experiment, or no research.
6. Do not draft a roadmap or edit product code.

## Output

Create or revise `需求与边界.md` using [references/frame-template.md](references/frame-template.md). Keep it human-readable; never copy slot, stage, owner-generation, or approval state into the file.

The output must make these points unambiguous:

- what user-observable result matters;
- what is explicitly outside this requirement;
- which sources own current truth;
- what authority is and is not granted;
- what uncertainty could change the recommendation;
- why the selected research depth is proportionate.

Use `$decision-partner-communication` when reporting the frame.
