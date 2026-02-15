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
  sh: factory/scripts/bash/create-new-unit.sh --json "{ARGS}"
  ps: factory/scripts/powershell/create-new-unit.ps1 -Json "{ARGS}"
---

## Intent

Transform a raw learning-content request into a complete unit brief contract under the active program.

## Inputs

```text
$ARGUMENTS
```

## Mandatory Rules (YOU MUST / MUST NOT)

- YOU MUST run `{SCRIPT}` exactly once.
- YOU MUST populate all mandatory sections from `.lcs/templates/brief-template.md`.
- YOU MUST create or update `brief.json` alongside `brief.md`.
- YOU MUST include program session-range metadata in `brief.json` when roadmap exists (`program_scope.session_start/session_end`).
- YOU MUST express learning outcomes as observable, measurable outcomes.
- YOU MUST keep content implementation-agnostic and learner-centric.
- YOU MUST NOT leave ambiguous gaps without explicit assumptions.

## Execution Steps

1. Run `{SCRIPT}` and parse `PROGRAM_ID`, `UNIT_NAME`, `UNIT_DIR`, `BRIEF_FILE`, `UNIT_NUM`, `SESSION_START`, `SESSION_END`, `ESTIMATED_DAY_START`, `ESTIMATED_DAY_END`, `EXPECTED_UNITS`.
2. Load `.lcs/templates/brief-template.md`.
3. Write brief sections: audience/context, outcomes, scope boundaries, requirements, accessibility/readability, metrics, risks.
4. Create/update `programs/<program_id>/units/<unit_id>/brief.json` with matching LO IDs and metadata.
5. Save to `BRIEF_FILE`.
6. Return completion summary and next command options.

## Hard Gates

- Gate G-DF-001: each LO contains statement, evidence, and acceptance criteria.
- Gate G-DF-002: accessibility/readability requirements are explicit.
- Gate G-DF-003: success metrics are measurable.

## Failure Modes

- Empty request: stop and ask for minimum unit intent.
- Missing template: stop with path to expected template.
- Non-measurable outcomes: stop and revise LO wording.

## Output Contract

- Artifact: `programs/<program_id>/units/<unit_id>/brief.md`.
- Artifact: `programs/<program_id>/units/<unit_id>/brief.json`.
- Completion report: `PROGRAM_ID`, `UNIT_NAME`, `BRIEF_FILE`, readiness for `/lcs.refine` or `/lcs.design`.
- Completion report MUST include a `Follow-up Tasks` section with exact prompts:
  - `/lcs.refine Refine unit <unit_id> ...`
  - `/lcs.design Design unit <unit_id> ...`
  - `/lcs.programs workflow-status --program <program_id>` to see remaining units.

## Examples

- Success: 3 measurable LOs with evidence and acceptance criteria.
- Fail: LO written as vague aspiration without observable behavior.
