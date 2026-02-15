---
description: Perform deterministic cross-artifact audit across brief, design, sequence, and rubric artifacts.
scripts:
  sh: factory/scripts/bash/check-workflow-prereqs.sh --json --require-sequence --include-sequence
  ps: factory/scripts/powershell/check-workflow-prereqs.ps1 -Json -RequireSequence -IncludeSequence
---

## Intent

Generate blocking/non-blocking audit findings and publish deterministic gate decisions for authoring.

## Inputs

```text
$ARGUMENTS
```

## Mandatory Rules (YOU MUST / MUST NOT)

- YOU MUST run read-only analysis on existing artifacts; only audit report artifacts may be written.
- YOU MUST classify findings by `CRITICAL|HIGH|MEDIUM|LOW`.
- YOU MUST write explicit `Gate Decision: PASS|BLOCK` in markdown and `gate_decision` in json.
- YOU MUST include `Open Critical` and `Open High` counters.
- YOU MUST include role readiness booleans: `teacher_ready`, `creator_ready`, `ops_ready`.
- YOU MUST apply web-research triggers when confidence is low, domain is time-sensitive, or artifact signals conflict.
- YOU MUST NOT allow `/lcs.author` when decision is `BLOCK`.

## Execution Steps

1. Run `{SCRIPT}` and parse `UNIT_DIR`, `AVAILABLE_DOCS`.
2. Load `brief.md`, `design.md`, `sequence.md`, rubric files, and available json contracts.
3. Validate cross-artifact consistency:
   - LO coverage alignment,
   - pedagogy consistency,
   - template distribution compliance (`assessment-blueprint.json` vs `template-selection.json`),
   - exercise plan coverage (`exercise-design.json` vs `sequence.json`),
   - accessibility/readability coverage,
   - metadata completeness,
   - manifest-first readiness.
4. If required by trigger policy, update `research.md` references used in audit rationale.
5. Write `UNIT_DIR/audit-report.md` and `UNIT_DIR/audit-report.json` with deterministic schema.
6. Return decision summary.

## Hard Gates

- Gate G-AD-001: report includes decision and severity counters in markdown and json.
- Gate G-AD-002: any unresolved CRITICAL/HIGH yields `BLOCK`.
- Gate G-AD-003: json report contains role readiness fields.

## Failure Modes

- Missing required artifact: stop and report missing prerequisite.
- Incomplete report schema: stop and rewrite both report artifacts.
- Markdown/json mismatch in decision counters: stop and resolve mismatch.

## Output Contract

Write these artifacts:

- `programs/<program_id>/units/<unit_id>/audit-report.md`
- `programs/<program_id>/units/<unit_id>/audit-report.json`

Required markdown headers:

- `# Audit Report: <unit>`
- `Gate Decision: PASS|BLOCK`
- `Open Critical: <number>`
- `Open High: <number>`
- `## Findings` (numbered list with severity, artifact, issue, remediation)

Required json keys:

- `contract_version`, `unit_id`, `gate_decision`, `open_critical`, `open_high`, `findings`, `role_readiness`

## Examples

- Success: markdown/json both report `PASS`, counters at zero, and readiness flags true.
- Fail: unresolved HIGH finding keeps decision `BLOCK` across markdown and json.
