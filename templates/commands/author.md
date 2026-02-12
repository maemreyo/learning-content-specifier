---
description: Execute approved production sequence and author local output assets.
scripts:
  sh: scripts/bash/check-workflow-prereqs.sh --json --require-sequence --include-sequence
  ps: scripts/powershell/check-workflow-prereqs.ps1 -Json -RequireSequence -IncludeSequence
gate_scripts:
  sh: scripts/bash/validate-author-gates.sh --json
  ps: scripts/powershell/validate-author-gates.ps1 -Json
---

## Intent

Author learning assets only after deterministic hard-gate approval.

## Inputs

```text
$ARGUMENTS
```

## Mandatory Rules (YOU MUST / MUST NOT)

- YOU MUST run both `{SCRIPT}` and `{GATE_SCRIPT}` before authoring.
- YOU MUST stop immediately if gate status is `BLOCK`.
- YOU MUST write outputs only under `UNIT_DIR/outputs/`.
- YOU MUST maintain `outputs/manifest.json` as the canonical entrypoint for downstream consumers.
- YOU MUST mark completed sequence tasks as `[X]` in `sequence.md` and mirror progress in `sequence.json`.
- YOU MUST NOT bypass rubric/audit blockers.

## Execution Steps

1. Run `{SCRIPT}` and parse `UNIT_DIR`, `AVAILABLE_DOCS`.
2. Run `{GATE_SCRIPT}` and parse `STATUS`, contract status, blocker counters, and blocker reasons.
3. If `STATUS=BLOCK`, stop and return blockers.
4. Load `sequence.md` and `sequence.json`; execute tasks in dependency order.
5. Persist generated assets to `outputs/` and register them in `outputs/manifest.json`.
6. Update sequence completion state and report results.

## Hard Gates

- Gate G-AU-001: validator result must be `STATUS=PASS`.
- Gate G-AU-002: unresolved CRITICAL/HIGH findings are forbidden.
- Gate G-AU-003: rubric unchecked items are forbidden.
- Gate G-AU-004: artifact contract validator must pass before output publication.

## Failure Modes

- Gate validator returns BLOCK: stop with blocker list.
- Sequence missing/dependency conflict: stop and request sequence fix.
- Output path outside `outputs/`: stop and correct destination.
- Manifest not updated for new outputs: stop and require manifest sync.

## Output Contract

- Updated `specs/<unit>/outputs/*` assets.
- Updated `specs/<unit>/outputs/manifest.json`.
- Updated `specs/<unit>/sequence.md` and `specs/<unit>/sequence.json` completion state.
- Final summary includes produced files + remaining tasks.

## Examples

- Success: gates pass, assets authored under `outputs/`, manifest updated, sequence synced.
- Fail: audit json has open HIGH finding -> authoring blocked.
