# Contract Sync Layer

This folder defines the context-safe contract surface for the standalone `lcs-output-consumer` repository.

## Purpose

- Keep consumer context aligned with LCS runtime contracts.
- Provide a stable, versioned package for schemas, docs digest, and fixtures.
- Prevent drift via checksum-based verification in CI.

## Package Composition

- `contracts/index.json`
- `contracts/schemas/*.schema.json`
- `contracts/docs/*.md`
- `contracts/fixtures/*.json`

## Local Verification

```bash
uv run python factory/scripts/python/build_contract_package.py --verify
```

## Consumer Rule

Consumer services MUST use `outputs/manifest.json` as the only ingestion entrypoint and resolve artifacts only via manifest references.
