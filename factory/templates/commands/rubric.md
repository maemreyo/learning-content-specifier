---
description: Generate a hard-gate rubric for learning-content quality validation.
scripts:
  sh: factory/scripts/bash/check-workflow-prereqs.sh --json
  ps: factory/scripts/powershell/check-workflow-prereqs.ps1 -Json
---

## Intent

Produce machine-readable quality gates for deterministic authoring approval.

## Inputs

```text
$ARGUMENTS
```

## Mandatory Rules (YOU MUST / MUST NOT)

- YOU MUST output rubric files under `UNIT_DIR/rubrics/`.
- YOU MUST use parseable gate lines containing `Gate ID`, `Status`, `Severity`, `Evidence`.
- YOU MUST keep gate lines compatible with deterministic parser regex used by author gate scripts.
- YOU MUST include gate groups: alignment, pedagogy, accessibility/readability, metadata.
- YOU MUST include template compliance gates for schema and semantic rule conformance.
- YOU MUST NOT mark PASS without evidence reference.

## Execution Steps

1. Run `{SCRIPT}` and parse `UNIT_DIR`, `AVAILABLE_DOCS`.
2. Load key artifacts (`brief.md`, `design.md`, optional `sequence.md`).
3. Create `UNIT_DIR/rubrics/` if missing.
4. Generate rubric from `.lcs/templates/rubric-template.md` with contextual checks.
5. Ensure each gate line follows the template format from rubric template.
6. Report rubric path, gate count, and unresolved gate count.

## Hard Gates

- Gate G-RB-001: all mandatory gate groups exist.
- Gate G-RB-002: each gate has ID/status/severity/evidence fields.
- Gate G-RB-003: non-pass statuses (`FAIL|BLOCK|UNSET|TODO`) remain unchecked.

## Failure Modes

- Missing core artifacts: stop and state missing files.
- Non-parseable rubric structure: stop and regenerate.
- PASS without evidence: stop and correct gate line.

## Output Contract

- Artifact: `specs/<unit>/rubrics/<name>.md`.
- Initial status should default to non-pass unless evidence exists.

## Examples

- Success: rubric includes explicit evidence links for each PASS gate.
- Fail: checklist-only rubric with no machine-readable status fields.
