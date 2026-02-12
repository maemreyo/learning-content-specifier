# Compatibility Matrix (Contract Package v1)

## Versioning Policy

- Contract schema format: JSON Schema 2020-12
- Contract ID pattern: `lcs.artifact.<type>.v1`
- Semver policy:
- `major`: breaking change
- `minor`: additive backward-compatible fields
- `patch`: non-structural fixes

## Interop Baseline

- Required: `xapi` block in `outputs/manifest.json`
- Optional adapters: `case`, `qti`, `lti`, `cmi5`

## Consumer Compatibility Rules

- Consumers MUST pin `contract_version` from `contracts/index.json`.
- Consumers MUST verify checksums before ingest.
- Consumers MUST block ingest on incompatible major versions.
- Consumers MUST use manifest-first resolution, no path guessing.

## LCS Runtime Alignment

Required machine contracts:

- `brief.json`
- `design.json`
- `sequence.json`
- `audit-report.json`
- `outputs/manifest.json`

Hard-gate implication:

- `authoring_eligible` is `true` only when deterministic gate checks return `PASS`.
