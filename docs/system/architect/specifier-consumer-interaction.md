# Specifier-Consumer Interaction Contract

This document is the canonical integration boundary between:

- Producer: `learning-content-specifier`
- Library backbone: `lcs-output-consumer`

## Scope

1. `learning-content-specifier` installs workflow assets into any content repo (`lcs init .`).
2. `lcs-output-consumer` ingests generated artifacts from that content repo.
3. Neither side requires sibling folder layout.

## Integration channels

1. Contract channel (control plane)
- Source of truth: `contracts/index.json`.
- Package includes `contracts/schemas/*`, `contracts/docs/*`, `contracts/fixtures/*`.
- Consumer MUST verify checksum entries from `contracts/index.json`.

2. Artifact channel (data plane)
- Producer writes artifacts under `programs/<program-id>/units/<unit>/` in the content repo.
- Consumer entrypoint is strictly `programs/<program-id>/units/<unit>/outputs/manifest.json`.
- Consumer MUST NOT resolve files by path guessing outside manifest references.

3. Compatibility channel (version policy)
- Consumer pin: `contracts/consumer-contract-version.txt`.
- Runtime gate: major(`contracts/index.json.contract_version`) MUST equal major(pin).

## Failure taxonomy

- `IO_*`: missing files/paths, unavailable artifacts.
- `SCHEMA_*`: malformed JSON, schema mismatch, checksum mismatch, contract version mismatch.
- `CONSISTENCY_*`: cross-artifact mismatch (LO parity, audit markdown/json parity, counters).
- `GATE_*`: rubric/audit gate unresolved, authoring decision must block.
- `SECURITY_*`: disallowed repo path, path escape, unauthorized request.
- `SYSTEM_*`: infra/runtime failures.

## Policy locks (clean break)

1. No default dependency on a sibling contracts path in local workspace layout.
2. Consumer contract sync defaults to release source; local path sync must be explicit dev mode.
3. Producer JSON artifacts must stamp `contract_version` dynamically from `contracts/index.json`.
