---
description: Create or update a learning unit brief from a natural language learning-content request.
handoffs:
  - label: Refine Unit Brief
    agent: lcs.refine
    prompt: Refine ambiguous areas in this brief.
    send: true
  - label: Build Learning Design
    agent: lcs.design
    prompt: Design the learning unit from this brief.
scripts:
  sh: scripts/bash/create-new-unit.sh --json "{ARGS}"
  ps: scripts/powershell/create-new-unit.ps1 -Json "{ARGS}"
---

## Intent

Transform a raw learning-content request into a complete `brief.md` contract.

## Inputs

```text
$ARGUMENTS
```

## Mandatory Rules (YOU MUST / MUST NOT)

- YOU MUST run `{SCRIPT}` exactly once.
- YOU MUST populate all mandatory sections from `.lcs/templates/brief-template.md`.
- YOU MUST express learning outcomes as observable, measurable outcomes.
- YOU MUST keep content implementation-agnostic and learner-centric.
- YOU MUST NOT leave ambiguous gaps without explicit assumptions.

## Execution Steps

1. Run `{SCRIPT}` and parse `UNIT_NAME`, `BRIEF_FILE`, `UNIT_NUM`.
2. Load `.lcs/templates/brief-template.md`.
3. Write brief sections: audience/context, outcomes, scope boundaries, requirements, accessibility/readability, metrics, risks.
4. Save to `BRIEF_FILE`.
5. Return completion summary and next command options.

## Hard Gates

- Gate G-DF-001: each LO contains statement, evidence, and acceptance criteria.
- Gate G-DF-002: accessibility/readability requirements are explicit.
- Gate G-DF-003: success metrics are measurable.

## Failure Modes

- Empty request: stop and ask for minimum unit intent.
- Missing template: stop with path to expected template.
- Non-measurable outcomes: stop and revise LO wording.

## Output Contract

- Artifact: `specs/<unit>/brief.md`.
- Completion report: `UNIT_NAME`, `BRIEF_FILE`, readiness for `/lcs.refine` or `/lcs.design`.

## Examples

- Success: 3 measurable LOs with evidence and acceptance criteria.
- Fail: LO written as vague aspiration without observable behavior.
