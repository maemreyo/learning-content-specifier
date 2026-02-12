---
description: Create dependency-ordered production sequence for learning content authoring.
handoffs:
  - label: Generate Rubric
    agent: lcs.rubric
    prompt: Generate a hard-gate rubric for this unit.
    send: true
  - label: Run Quality Audit
    agent: lcs.audit
    prompt: Audit cross-artifact consistency.
    send: true
  - label: Start Authoring
    agent: lcs.author
    prompt: Author outputs from approved sequence.
    send: true
scripts:
  sh: scripts/bash/check-workflow-prereqs.sh --json
  ps: scripts/powershell/check-workflow-prereqs.ps1 -Json
---

## Intent

Generate executable, dependency-aware authoring sequence aligned to LOs and hard gates.

## Inputs

```text
$ARGUMENTS
```

## Mandatory Rules (YOU MUST / MUST NOT)

- YOU MUST map actionable tasks to LOs where applicable.
- YOU MUST include explicit output file paths under `outputs/`.
- YOU MUST include gate tasks before `/lcs.author` execution.
- YOU MUST NOT emit ambiguous task descriptions.

## Execution Steps

1. Run `{SCRIPT}` and parse `UNIT_DIR`, `AVAILABLE_DOCS`.
2. Load `design.md`, `brief.md`, and optional docs.
3. Generate `sequence.md` using `.lcs/templates/sequence-template.md`.
4. Ensure dependencies and parallel flags are explicit.
5. Report task count, LO coverage, and gate checkpoints.

## Hard Gates

- Gate G-SQ-001: every required LO has at least one authoring task.
- Gate G-SQ-002: rubric/audit tasks are present and blocking.
- Gate G-SQ-003: each task has deterministic file target.

## Failure Modes

- Missing design: stop and require `/lcs.design`.
- Missing LO mapping: stop and regenerate sequence.

## Output Contract

- Artifact: `specs/<unit>/sequence.md`.
- Summary: task total, LO coverage summary, gating tasks.

## Examples

- Success: sequence includes phase-by-phase deliverables and hard-gate phase.
- Fail: sequence omits gate tasks or file paths.
