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

## Three-Repo Compatibility Rules

- `learning-content-specifier` publishes contract package (`contracts/index.json` + checksums).
- `lcs-output-consumer` MUST ingest only compatible major versions of published contracts.
- `tutoring-platform` MUST pin required major in `contracts/consumer-contract-version.txt`.
- `tutoring-platform` BFF MUST block startup/catalog sync on major mismatch.
- Frontend apps MUST integrate through BFF only; direct consumer calls are not allowed.

## LCS Runtime Alignment

Required machine contracts:

- `brief.json`
- `design.json`
- `sequence.json`
- `audit-report.json`
- `outputs/manifest.json`

Hard-gate implication:

- `authoring_eligible` is `true` only when deterministic gate checks return `PASS`.
