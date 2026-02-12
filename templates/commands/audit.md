---
description: Perform deterministic cross-artifact audit across brief, design, sequence, and rubric artifacts.
scripts:
  sh: scripts/bash/check-workflow-prereqs.sh --json --require-sequence --include-sequence
  ps: scripts/powershell/check-workflow-prereqs.ps1 -Json -RequireSequence -IncludeSequence
---

## Intent

Generate blocking/non-blocking audit findings and publish gate decision for authoring.

## Inputs

```text
$ARGUMENTS
```

## Mandatory Rules (YOU MUST / MUST NOT)

- YOU MUST run read-only analysis on existing artifacts; only `audit-report.md` may be written.
- YOU MUST classify findings by `CRITICAL|HIGH|MEDIUM|LOW`.
- YOU MUST write explicit `Gate Decision: PASS|BLOCK`.
- YOU MUST include `Open Critical` and `Open High` counters.
- YOU MUST NOT allow `/lcs.author` when decision is `BLOCK`.

## Execution Steps

1. Run `{SCRIPT}` and parse `UNIT_DIR`, `AVAILABLE_DOCS`.
2. Load `brief.md`, `design.md`, `sequence.md`, rubric files.
3. Validate cross-artifact consistency:
   - LO coverage alignment,
   - pedagogy consistency,
   - accessibility/readability coverage,
   - metadata completeness.
4. Write `UNIT_DIR/audit-report.md` with deterministic schema.
5. Return decision summary.

## Hard Gates

- Gate G-AD-001: report includes decision and severity counters.
- Gate G-AD-002: any unresolved CRITICAL/HIGH yields `Gate Decision: BLOCK`.

## Failure Modes

- Missing required artifact: stop and report missing prerequisite.
- Incomplete report schema: stop and rewrite `audit-report.md`.

## Output Contract

Write `specs/<unit>/audit-report.md` with these headers:

- `# Audit Report: <unit>`
- `Gate Decision: PASS|BLOCK`
- `Open Critical: <number>`
- `Open High: <number>`
- `## Findings` (numbered list with severity, artifact, issue, remediation)

## Examples

- Success: `Gate Decision: PASS`, `Open Critical: 0`, `Open High: 0`.
- Fail: any unresolved HIGH finding keeps `Gate Decision: BLOCK`.
