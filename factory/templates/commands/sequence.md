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
  sh: factory/scripts/bash/check-workflow-prereqs.sh --json --require-design-contracts
  ps: factory/scripts/powershell/check-workflow-prereqs.ps1 -Json -RequireDesignContracts
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
- YOU MUST treat missing design contracts (`assessment-blueprint.json`, `template-selection.json`, `exercise-design.json`) as blocking.
- YOU MUST update both `sequence.md` and `sequence.json`.
- YOU MUST propagate `template_id` metadata from `template-selection.json` into task metadata when task maps to an exercise type.
- YOU MUST map exercise authoring tasks from `exercise-design.json` (one task per `exercise_id` unless explicitly merged).
- YOU MUST NOT emit ambiguous task descriptions.

## Execution Steps

1. Run `{SCRIPT}` and parse `UNIT_DIR`, `AVAILABLE_DOCS`.
2. Load `design.md`, `brief.md`, `assessment-blueprint.json`, `template-selection.json`, `exercise-design.json`, and optional docs.
3. Generate `sequence.md` using `.lcs/templates/sequence-template.md`.
4. Generate/update `sequence.json` with deterministic task objects (`task_id`, dependencies, LO refs, target paths).
5. Ensure dependencies and parallel flags are explicit.
6. Report task count, LO coverage, and gate checkpoints.

## Hard Gates

- Gate G-SQ-001: every required LO has at least one authoring task.
- Gate G-SQ-002: rubric/audit tasks are present and blocking.
- Gate G-SQ-003: each task has deterministic file target.
- Gate G-SQ-004: `sequence.json` is consistent with `sequence.md` task IDs.
- Gate G-SQ-005: LO-to-template coverage in sequence is consistent with `assessment-blueprint.json`.
- Gate G-SQ-006: every exercise in `exercise-design.json` has at least one sequence task targeting its `target_path`.

## Failure Modes

- Missing design: stop and require `/lcs.design`.
- Missing LO mapping: stop and regenerate sequence.
- Divergent markdown/json sequence: stop and resolve mismatch.

## Output Contract

- Artifacts: `programs/<program_id>/units/<unit_id>/sequence.md`, `programs/<program_id>/units/<unit_id>/sequence.json`.
- Summary: task total, LO coverage summary, gating tasks.
- Summary MUST include a `Follow-up Tasks` section with exact prompts:
  - `/lcs.rubric ...`
  - `/lcs.audit ...`
  - `/lcs.author ...`
  - `/lcs.programs workflow-status --program <program_id>`.

## Examples

- Success: sequence includes phase-by-phase deliverables, hard-gate phase, and matching json contract.
- Fail: sequence omits gate tasks, file paths, or json parity.
