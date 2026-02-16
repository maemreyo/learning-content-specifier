---
description: Perform deterministic cross-artifact audit across brief, design, sequence, and rubric artifacts.
argument-hint: "[audit scope, risk emphasis, or unit selector]"
scripts:
  sh: factory/scripts/bash/check-workflow-prereqs.sh --json --require-design-contracts --require-sequence --include-sequence --stage audit
  ps: factory/scripts/powershell/check-workflow-prereqs.ps1 -Json -RequireDesignContracts -RequireSequence -IncludeSequence -Stage audit
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
- YOU MUST write canonical `gate_decision` in `audit-report.json`.
- YOU MUST include `Open Critical` and `Open High` counters.
- YOU MUST include role readiness booleans: `teacher_ready`, `creator_ready`, `ops_ready`.
- YOU MUST apply web-research triggers when confidence is low, domain is time-sensitive, or artifact signals conflict.
- YOU MUST NOT allow `/lcs.author` when decision is `BLOCK`.
- YOU MUST treat template-pack availability/compliance findings as blocking when severity is `CRITICAL|HIGH`.

## Execution Steps

1. Run `{SCRIPT}` and parse `UNIT_DIR`, `AVAILABLE_DOCS`.
2. Load canonical artifacts `brief.json`, `design.json`, `sequence.json`, `rubric-gates.json`, and other available JSON contracts.
3. Validate cross-artifact consistency:
   - LO coverage alignment,
   - pedagogy consistency,
   - template distribution compliance (`assessment-blueprint.json` vs `template-selection.json`),
   - exercise plan coverage (`exercise-design.json` vs `sequence.json`),
   - accessibility/readability coverage,
   - metadata completeness,
   - manifest-first readiness.
4. If required by trigger policy, update `research.md` references used in audit rationale.
5. Write canonical `UNIT_DIR/audit-report.json` with deterministic schema.
6. If sidecar mode is enabled, optionally render `UNIT_DIR/audit-report.md`.
7. Return decision summary.

## Hard Gates

- Gate G-AD-001: canonical report includes decision and severity counters in JSON.
- Gate G-AD-002: any unresolved CRITICAL/HIGH yields `BLOCK`.
- Gate G-AD-003: json report contains role readiness fields.

## Failure Modes

- Missing required artifact: stop and report missing prerequisite.
- Incomplete report schema: stop and rewrite both report artifacts.
- Canonical audit JSON missing/inconsistent: stop and resolve.

## Output Contract

Write canonical artifact:

- `programs/<program_id>/units/<unit_id>/audit-report.json`

Optional sidecar artifact:

- `programs/<program_id>/units/<unit_id>/audit-report.md`

Required json keys:

- `contract_version`, `unit_id`, `gate_decision`, `open_critical`, `open_high`, `findings`, `role_readiness`
- Response MUST include a `Follow-up Tasks` section with exact prompts:
  - if `gate_decision=BLOCK`: `/lcs.refine ...` or `/lcs.redesign ...` for blocking artifacts,
  - if `gate_decision=PASS`: `/lcs.author ...`,
  - `/lcs.programs workflow-status --program <program_id>` for remaining units.

## Examples

- Success: markdown/json both report `PASS`, counters at zero, and readiness flags true.
- Fail: unresolved HIGH finding keeps decision `BLOCK` across markdown and json.
