---
description: Generate a hard-gate rubric for learning-content quality validation.
argument-hint: "[rubric focus, risk emphasis, or unit selector]"
scripts:
  sh: factory/scripts/bash/check-workflow-prereqs.sh --json --require-design-contracts --stage rubric
  ps: factory/scripts/powershell/check-workflow-prereqs.ps1 -Json -RequireDesignContracts -Stage rubric
---

## Intent

Produce machine-readable quality gates for deterministic authoring approval.

## Inputs

```text
$ARGUMENTS
```

## Mandatory Rules (YOU MUST / MUST NOT)

- YOU MUST output canonical rubric gates to `UNIT_DIR/rubric-gates.json`.
- YOU MUST keep markdown rubric files optional and non-canonical.
- YOU MUST keep canonical gate entries deterministic (`gate_id`, `group`, `status`, `severity`, `evidence`, `checked`).
- YOU MUST include gate groups: alignment, pedagogy, accessibility/readability, metadata.
- YOU MUST include template compliance gates for schema and semantic rule conformance.
- YOU MUST NOT mark PASS without evidence reference.
- YOU MUST NOT generate or mutate exercise `scoring_rubric` content in this command; `/lcs.rubric` is quality-gate only.

## Execution Steps

1. Run `{SCRIPT}` and parse `UNIT_DIR`, `AVAILABLE_DOCS`.
2. Load key canonical artifacts (`brief.json`, `design.json`, `sequence.json`, `exercise-design.json`).
3. Generate/update `UNIT_DIR/rubric-gates.json`.
4. If sidecar mode is enabled, optionally render markdown rubric files under `UNIT_DIR/rubrics/`.
5. Ensure canonical gate entries remain machine-parseable.
6. Report rubric gate file path, gate count, and unresolved gate count.

## Hard Gates

- Gate G-RB-001: all mandatory gate groups exist.
- Gate G-RB-002: each gate has ID/status/severity/evidence fields.
- Gate G-RB-003: non-pass statuses (`FAIL|BLOCK|UNSET|TODO`) remain unchecked.

## Failure Modes

- Missing core artifacts: stop and state missing files.
- Non-parseable rubric structure: stop and regenerate.
- PASS without evidence: stop and correct gate line.

## Output Contract

- Canonical artifact: `programs/<program_id>/units/<unit_id>/rubric-gates.json`.
- Optional sidecar: `programs/<program_id>/units/<unit_id>/rubrics/<name>.md`.
- Initial status should default to non-pass unless evidence exists.
- Report MUST include a `Follow-up Tasks` section with exact prompts:
  - `/lcs.audit ...`
  - `/lcs.programs workflow-status --program <program_id>`.

## Examples

- Success: rubric includes explicit evidence links for each PASS gate.
- Fail: checklist-only rubric with no machine-readable status fields.
